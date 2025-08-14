#!/usr/bin/env python3
"""
Batch Benchmark Runner

Allows running the same task across multiple models automatically for comparison.
Supports both local (Ollama) and commercial models with progress tracking and
result aggregation.
"""

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import sys
import time
from typing import Dict, List, Optional

try:
    from rich.console import Console
    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TextColumn,
        TimeRemainingColumn,
    )
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("⚠️  Rich library not available. Install for better progress tracking:")
    print("   uv pip install rich")

import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from benchmark.metrics import BenchmarkMetrics
from benchmark.ollama_check import OllamaChecker
from benchmark.task_runner import validate_task_file
from benchmark.validators import ValidationError
from benchmark.machine_info import MachineInfoCollector


class BatchRunner:
    """Orchestrates running benchmarks across multiple models."""

    def __init__(self, output_dir: Optional[str] = None):
        """Initialize the batch runner.

        Args:
            output_dir: Optional custom output directory for results
        """
        self.console = Console() if RICH_AVAILABLE else None
        self.batch_id = None
        self.output_dir = Path(output_dir) if output_dir else self._create_output_dir()
        self.models_config_path = Path("benchmark/models_config.yaml")
        self.available_models = []
        self.results = []
        self.start_time = None

    def _create_output_dir(self) -> Path:
        """Create a timestamped output directory for batch results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.batch_id = f"batch_{timestamp}"
        output_path = Path(f"benchmark/results/{self.batch_id}")
        output_path.mkdir(parents=True, exist_ok=True)
        return output_path

    def detect_available_models(self) -> List[Dict[str, str]]:
        """Detect all available models (Ollama + configured).

        Returns:
            List of model dictionaries with name and provider
        """
        models = []

        # Detect Ollama models
        if self._is_ollama_available():
            ollama_models = self._detect_ollama_models()
            for model in ollama_models:
                models.append(
                    {
                        "name": f"ollama/{model}",
                        "provider": "ollama",
                        "display_name": f"Ollama {model}",
                    }
                )

        # Load configured models
        if self.models_config_path.exists():
            configured_models = self._load_configured_models()
            models.extend(configured_models)

        self.available_models = models
        return models

    def _is_ollama_available(self) -> bool:
        """Check if Ollama is installed and running."""
        try:
            checker = OllamaChecker(verbose=False)
            return checker.check_installation() and checker.check_service_running()
        except Exception:
            return False

    def _detect_ollama_models(self) -> List[str]:
        """Detect available Ollama models."""
        try:
            checker = OllamaChecker(verbose=False)
            # Need to run checks first to populate the models list
            if checker.check_installation() and checker.check_service_running():
                models = checker.list_available_models()
                # The OllamaChecker already returns the base model names without tags
                return models if models else []
            return []
        except Exception as e:
            if self.console:
                self.console.print(
                    f"[yellow]Error detecting Ollama models: {e}[/yellow]"
                )
            return []

    def _load_configured_models(self) -> List[Dict[str, str]]:
        """Load models from configuration file."""
        try:
            with open(self.models_config_path, "r") as f:
                config = yaml.safe_load(f)
                models = []
                for model in config.get("models", []):
                    if model.get("enabled", True):
                        models.append(
                            {
                                "name": model["name"],
                                "provider": model["provider"],
                                "display_name": model.get(
                                    "display_name", model["name"]
                                ),
                            }
                        )
                return models
        except (FileNotFoundError, yaml.YAMLError) as e:
            if self.console:
                self.console.print(
                    f"[yellow]Could not load models config: {e}[/yellow]"
                )
            return []

    def run_batch_benchmark(
        self,
        task_file: str,
        models: Optional[List[str]] = None,
        parallel: bool = False,
        timeout: int = 1800,
        resume_from: Optional[str] = None,
    ) -> Dict[str, any]:
        """Run a benchmark task across multiple models.

        Args:
            task_file: Path to the task file
            models: List of model names or None for all available
            parallel: Whether to run models in parallel
            timeout: Maximum time per model in seconds
            resume_from: Optional batch ID to resume from

        Returns:
            Dictionary with batch results and comparison metrics
        """
        self.start_time = time.time()

        # Validate task file
        try:
            task_path = validate_task_file(task_file)
            task_name = task_path.stem
        except (ValidationError, FileNotFoundError) as e:
            if self.console:
                self.console.print(f"[red]Invalid task file: {e}[/red]")
            else:
                print(f"❌ Invalid task file: {e}")
            sys.exit(1)

        # Detect available models
        available_models = self.detect_available_models()
        if not available_models:
            if self.console:
                self.console.print(
                    "[red]No models available. Please install Ollama or configure models.[/red]"
                )
            else:
                print(
                    "❌ No models available. Please install Ollama or configure models."
                )
            sys.exit(1)

        # Filter models if specific ones requested
        if models and models != ["all"]:
            selected_models = []
            for model_spec in models:
                found = False
                for available in available_models:
                    if (
                        model_spec in available["name"]
                        or model_spec == available["name"]
                    ):
                        selected_models.append(available)
                        found = True
                        break
                if not found:
                    if self.console:
                        self.console.print(
                            f"[yellow]Warning: Model '{model_spec}' not found[/yellow]"
                        )
                    else:
                        print(f"⚠️  Model '{model_spec}' not found")

            if not selected_models:
                if self.console:
                    self.console.print("[red]No valid models selected[/red]")
                else:
                    print("❌ No valid models selected")
                sys.exit(1)

            models_to_run = selected_models
        else:
            models_to_run = available_models

        # Display batch information
        self._display_batch_info(task_name, models_to_run)

        # Check for resume
        completed_models = []
        if resume_from:
            completed_models = self._load_completed_models(resume_from)
            models_to_run = [
                m for m in models_to_run if m["name"] not in completed_models
            ]

        # Run benchmarks with progress tracking
        if RICH_AVAILABLE and self.console:
            results = self._run_with_progress(
                task_file, task_name, models_to_run, timeout
            )
        else:
            results = self._run_simple(task_file, task_name, models_to_run, timeout)

        # Generate comparison report
        comparison = self._generate_comparison_report(results, task_name)

        # Save batch results
        self._save_batch_results(comparison)

        # Display summary
        self._display_summary(comparison)

        return comparison

    def _display_batch_info(self, task_name: str, models: List[Dict]):
        """Display information about the batch run."""
        if RICH_AVAILABLE and self.console:
            table = Table(title=f"Batch Benchmark: {task_name}")
            table.add_column("Model", style="cyan")
            table.add_column("Provider", style="magenta")

            for model in models:
                table.add_row(model["display_name"], model["provider"])

            self.console.print(table)
            self.console.print(f"\n[bold]Batch ID:[/bold] {self.batch_id}")
            self.console.print(f"[bold]Output Directory:[/bold] {self.output_dir}\n")
        else:
            print(f"\n{'=' * 60}")
            print(f"Batch Benchmark: {task_name}")
            print(f"{'=' * 60}")
            print(f"Batch ID: {self.batch_id}")
            print(f"Output Directory: {self.output_dir}")
            print(f"\nModels to test ({len(models)}):")
            for model in models:
                print(f"  • {model['display_name']} ({model['provider']})")
            print(f"{'=' * 60}\n")

    def _run_with_progress(
        self, task_file: str, task_name: str, models: List[Dict], timeout: int
    ) -> List[Dict]:
        """Run benchmarks with rich progress display."""
        results = []

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=self.console,
        ) as progress:
            task = progress.add_task("[cyan]Running benchmarks...", total=len(models))

            for i, model in enumerate(models):
                progress.update(
                    task, description=f"[cyan]Testing {model['display_name']}..."
                )

                result = self._run_single_model_task(
                    model["name"], task_file, task_name, timeout
                )
                results.append(result)

                progress.update(task, advance=1)

                # Save intermediate result
                self._save_model_result(model["name"], result)

        return results

    def _run_simple(
        self, task_file: str, task_name: str, models: List[Dict], timeout: int
    ) -> List[Dict]:
        """Run benchmarks with simple console output."""
        results = []
        total = len(models)

        for i, model in enumerate(models, 1):
            print(f"\n[{i}/{total}] Testing {model['display_name']}...")
            print("-" * 40)

            result = self._run_single_model_task(
                model["name"], task_file, task_name, timeout
            )
            results.append(result)

            # Save intermediate result
            self._save_model_result(model["name"], result)

            if result["success"]:
                print(f"✅ {model['display_name']} completed successfully")
            else:
                print(f"❌ {model['display_name']} failed or timed out")

        return results

    def _run_single_model_task(
        self, model_name: str, task_file: str, task_name: str, timeout: int
    ) -> Dict:
        """Run a single model on the task.

        Returns:
            Dictionary with model results
        """
        start_time = time.time()

        # Initialize result structure
        result = {
            "model": model_name,
            "task": task_name,
            "success": False,
            "error": None,
            "completion_time": 0,
            "prompts_sent": 0,
            "human_interventions": 0,
            "files_modified": 0,
            "lines_added": 0,
            "lines_removed": 0,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            # Create a subprocess to run the task
            # This allows us to capture metrics without user interaction
            metrics = BenchmarkMetrics(model_name, task_name)
            metrics.start_task()

            # Simulate task completion for batch mode
            # In real implementation, this would integrate with Continue or other agents
            print(f"\n📋 Task: {task_file}")
            print(f"🤖 Model: {model_name}")
            print("⏳ Simulating benchmark run...")
            print("   (In production, this would launch the actual AI agent)")

            # For now, mark as successful with mock data
            # This will be replaced with actual agent integration
            time.sleep(2)  # Simulate some processing time

            result["success"] = True
            result["completion_time"] = time.time() - start_time
            result["prompts_sent"] = 3  # Mock data
            result["human_interventions"] = 1  # Mock data

            # Complete the task
            metrics.complete_task(True)

        except Exception as e:
            result["error"] = str(e)
            result["completion_time"] = time.time() - start_time

        return result

    def _save_model_result(self, model_name: str, result: Dict):
        """Save individual model result to file."""
        safe_model_name = model_name.replace("/", "_").replace(":", "_")
        result_file = self.output_dir / f"{safe_model_name}_result.json"

        with open(result_file, "w") as f:
            json.dump(result, f, indent=2)

    def _load_completed_models(self, batch_id: str) -> List[str]:
        """Load list of completed models from a previous batch."""
        batch_dir = Path(f"benchmark/results/{batch_id}")
        if not batch_dir.exists():
            return []

        completed = []
        for result_file in batch_dir.glob("*_result.json"):
            try:
                with open(result_file, "r") as f:
                    data = json.load(f)
                    completed.append(data["model"])
            except Exception:
                continue

        return completed

    def _generate_comparison_report(self, results: List[Dict], task_name: str) -> Dict:
        """Generate a comparison report from results."""
        total_time = time.time() - self.start_time

        # Calculate statistics
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        # Sort by performance metrics
        successful.sort(key=lambda x: x["completion_time"])

        comparison = {
            "batch_id": self.batch_id,
            "task": task_name,
            "timestamp": datetime.now().isoformat(),
            "total_time": total_time,
            "models_tested": len(results),
            "successful": len(successful),
            "failed": len(failed),
            "machine_info": MachineInfoCollector.collect_all(),
            "results": results,
            "rankings": {
                "fastest": successful[0]["model"] if successful else None,
                "most_efficient": (
                    min(successful, key=lambda x: x["prompts_sent"])["model"]
                    if successful
                    else None
                ),
                "least_intervention": (
                    min(successful, key=lambda x: x["human_interventions"])["model"]
                    if successful
                    else None
                ),
            },
            "summary_stats": self._calculate_summary_stats(successful),
        }

        return comparison

    def _calculate_summary_stats(self, results: List[Dict]) -> Dict:
        """Calculate summary statistics for successful runs."""
        if not results:
            return {}

        import statistics

        return {
            "avg_completion_time": statistics.mean(
                [r["completion_time"] for r in results]
            ),
            "median_completion_time": statistics.median(
                [r["completion_time"] for r in results]
            ),
            "avg_prompts": statistics.mean([r["prompts_sent"] for r in results]),
            "avg_interventions": statistics.mean(
                [r["human_interventions"] for r in results]
            ),
            "min_completion_time": min([r["completion_time"] for r in results]),
            "max_completion_time": max([r["completion_time"] for r in results]),
        }

    def _save_batch_results(self, comparison: Dict):
        """Save the complete batch results and comparison report."""
        # Save JSON report
        report_file = self.output_dir / "comparison_report.json"
        with open(report_file, "w") as f:
            json.dump(comparison, f, indent=2)
        
        # Save machine info separately for easy access
        machine_info_file = self.output_dir / "machine_info.json"
        MachineInfoCollector.save_to_file(str(machine_info_file))

        # Generate HTML report
        self._generate_html_report(comparison)

        # Generate CSV for analysis
        self._generate_csv_report(comparison)

    def _generate_html_report(self, comparison: Dict):
        """Generate an HTML comparison report."""
        html_file = self.output_dir / "comparison_report.html"

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Benchmark Comparison - {comparison["task"]}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #333; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #4CAF50; color: white; }}
                tr:nth-child(even) {{ background-color: #f2f2f2; }}
                .success {{ color: green; font-weight: bold; }}
                .failed {{ color: red; font-weight: bold; }}
                .summary {{ background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <h1>Benchmark Comparison Report</h1>
            <div class="summary">
                <h2>Summary</h2>
                <p><strong>Batch ID:</strong> {comparison["batch_id"]}</p>
                <p><strong>Task:</strong> {comparison["task"]}</p>
                <p><strong>Total Time:</strong> {comparison["total_time"]:.2f} seconds</p>
                <p><strong>Models Tested:</strong> {comparison["models_tested"]}</p>
                <p><strong>Successful:</strong> <span class="success">{comparison["successful"]}</span></p>
                <p><strong>Failed:</strong> <span class="failed">{comparison["failed"]}</span></p>
            </div>
            
            <h2>Results</h2>
            <table>
                <tr>
                    <th>Model</th>
                    <th>Status</th>
                    <th>Completion Time (s)</th>
                    <th>Prompts Sent</th>
                    <th>Human Interventions</th>
                    <th>Files Modified</th>
                </tr>
        """

        for result in comparison["results"]:
            status = (
                '<span class="success">✅ Success</span>'
                if result["success"]
                else '<span class="failed">❌ Failed</span>'
            )
            html_content += f"""
                <tr>
                    <td>{result["model"]}</td>
                    <td>{status}</td>
                    <td>{result["completion_time"]:.2f}</td>
                    <td>{result["prompts_sent"]}</td>
                    <td>{result["human_interventions"]}</td>
                    <td>{result["files_modified"]}</td>
                </tr>
            """

        html_content += """
            </table>
        """

        if comparison.get("rankings") and comparison["rankings"].get("fastest"):
            html_content += f"""
            <div class="summary">
                <h2>Rankings</h2>
                <p><strong>🏆 Fastest:</strong> {comparison["rankings"]["fastest"]}</p>
                <p><strong>💬 Most Efficient (fewest prompts):</strong> {comparison["rankings"]["most_efficient"]}</p>
                <p><strong>🤖 Most Autonomous (least intervention):</strong> {comparison["rankings"]["least_intervention"]}</p>
            </div>
            """

        html_content += """
        </body>
        </html>
        """

        with open(html_file, "w") as f:
            f.write(html_content)

    def _generate_csv_report(self, comparison: Dict):
        """Generate a CSV report for data analysis."""
        import csv

        csv_file = self.output_dir / "comparison_report.csv"

        with open(csv_file, "w", newline="") as f:
            fieldnames = [
                "model",
                "task",
                "success",
                "completion_time",
                "prompts_sent",
                "human_interventions",
                "files_modified",
                "lines_added",
                "lines_removed",
                "timestamp",
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            writer.writeheader()
            for result in comparison["results"]:
                writer.writerow(
                    {
                        "model": result["model"],
                        "task": result["task"],
                        "success": result["success"],
                        "completion_time": result["completion_time"],
                        "prompts_sent": result["prompts_sent"],
                        "human_interventions": result["human_interventions"],
                        "files_modified": result["files_modified"],
                        "lines_added": result["lines_added"],
                        "lines_removed": result["lines_removed"],
                        "timestamp": result["timestamp"],
                    }
                )

    def _display_summary(self, comparison: Dict):
        """Display a summary of the batch run."""
        if RICH_AVAILABLE and self.console:
            # Create summary table
            table = Table(title="Batch Benchmark Results")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")

            table.add_row("Batch ID", comparison["batch_id"])
            table.add_row("Task", comparison["task"])
            table.add_row("Total Time", f"{comparison['total_time']:.2f} seconds")
            table.add_row("Models Tested", str(comparison["models_tested"]))
            table.add_row("Successful", str(comparison["successful"]))
            table.add_row("Failed", str(comparison["failed"]))

            self.console.print("\n")
            self.console.print(table)

            if comparison.get("rankings") and comparison["rankings"].get("fastest"):
                rankings_table = Table(title="Performance Rankings")
                rankings_table.add_column("Category", style="cyan")
                rankings_table.add_column("Winner", style="green")

                rankings_table.add_row("🏆 Fastest", comparison["rankings"]["fastest"])
                rankings_table.add_row(
                    "💬 Most Efficient", comparison["rankings"]["most_efficient"]
                )
                rankings_table.add_row(
                    "🤖 Most Autonomous", comparison["rankings"]["least_intervention"]
                )

                self.console.print("\n")
                self.console.print(rankings_table)

            self.console.print(
                f"\n[bold green]✅ Results saved to:[/bold green] {self.output_dir}"
            )
        else:
            print(f"\n{'=' * 60}")
            print("Batch Benchmark Complete!")
            print(f"{'=' * 60}")
            print(f"Batch ID: {comparison['batch_id']}")
            print(f"Task: {comparison['task']}")
            print(f"Total Time: {comparison['total_time']:.2f} seconds")
            print(f"Models Tested: {comparison['models_tested']}")
            print(f"Successful: {comparison['successful']}")
            print(f"Failed: {comparison['failed']}")

            if comparison.get("rankings") and comparison["rankings"].get("fastest"):
                print(f"\n{'=' * 60}")
                print("Performance Rankings:")
                print(f"🏆 Fastest: {comparison['rankings']['fastest']}")
                print(f"💬 Most Efficient: {comparison['rankings']['most_efficient']}")
                print(
                    f"🤖 Most Autonomous: {comparison['rankings']['least_intervention']}"
                )

            print(f"\n✅ Results saved to: {self.output_dir}")
            print(f"{'=' * 60}\n")


def main():
    """Main entry point for the batch runner."""
    parser = argparse.ArgumentParser(
        description="Run benchmark tasks across multiple AI models"
    )

    parser.add_argument("--task", required=True, help="Path to the task file")

    parser.add_argument(
        "--models",
        help="Comma-separated list of models or 'all' (default: all)",
        default="all",
    )

    parser.add_argument("--output", help="Output directory for results", default=None)

    parser.add_argument(
        "--parallel", action="store_true", help="Run models in parallel (experimental)"
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="Maximum time per model in seconds (default: 30 minutes)",
    )

    parser.add_argument(
        "--resume", help="Resume from a previous batch ID", default=None
    )

    args = parser.parse_args()

    # Parse models list
    if args.models == "all":
        models = None
    else:
        models = [m.strip() for m in args.models.split(",")]

    # Create and run batch
    runner = BatchRunner(output_dir=args.output)
    runner.run_batch_benchmark(
        task_file=args.task,
        models=models,
        parallel=args.parallel,
        timeout=args.timeout,
        resume_from=args.resume,
    )


if __name__ == "__main__":
    main()
