#!/usr/bin/env python3
"""
Integration module to add Continue CLI support to the existing batch runner.

This module extends the BatchRunner class to support CN-based execution alongside
the existing manual benchmarking approach.
"""

from datetime import datetime
import json
import logging
from pathlib import Path
import time
from typing import Any, Dict, List, Optional

from benchmark.cn_integration.cn_config import CNConfigManager
from benchmark.cn_integration.cn_metrics import CNMetricsCollector
from benchmark.cn_integration.cn_runner import CNRunner

logger = logging.getLogger(__name__)


class CNBatchIntegration:
    """Integrates Continue CLI execution into the batch benchmarking system."""
    
    def __init__(self, working_dir: Optional[Path] = None, verbose: bool = False):
        """Initialize CN batch integration.
        
        Args:
            working_dir: Working directory for task execution
            verbose: Enable verbose logging
        """
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()
        self.verbose = verbose
        self.cn_runner = CNRunner(working_dir=working_dir, verbose=verbose)
        self.config_manager = CNConfigManager()
        self.metrics_collector = CNMetricsCollector(working_dir=working_dir)
        
        if verbose:
            logging.basicConfig(level=logging.DEBUG)
    
    def run_cn_task(self, task_file: str, model_spec: str, timeout: int = 600) -> Dict[str, Any]:
        """Run a single task using Continue CLI.
        
        Args:
            task_file: Path to the task markdown file
            model_spec: Model specification (e.g., "gpt-4", "ollama/llama2")
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with task results compatible with batch runner format
        """
        start_time = time.time()
        task_path = Path(task_file)
        task_name = task_path.stem
        
        logger.info(f"Running CN task: {task_name} with model: {model_spec}")
        
        # Capture initial state
        self.metrics_collector.capture_initial_state()
        
        try:
            # Run the task using CN
            cn_result = self.cn_runner.run_task(
                task_file=task_file,
                model_name=model_spec,
                timeout=timeout
            )
            
            # Convert CN result to batch runner format
            batch_result = self._convert_cn_result_to_batch_format(cn_result, task_name)
            
            logger.info(f"CN task completed: {task_name} - Success: {batch_result['success']}")
            return batch_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"CN task failed: {task_name} - Error: {e}")
            
            return {
                "model": model_spec,
                "task": task_name,
                "success": False,
                "error": str(e),
                "completion_time": execution_time,
                "prompts_sent": 0,
                "human_interventions": 0,
                "files_modified": 0,
                "lines_added": 0,
                "lines_removed": 0,
                "timestamp": datetime.now().isoformat(),
                "execution_method": "continue_cli"
            }
    
    def _convert_cn_result_to_batch_format(self, cn_result: Dict[str, Any], task_name: str) -> Dict[str, Any]:
        """Convert CN result format to batch runner format.
        
        Args:
            cn_result: Result from CN runner
            task_name: Name of the task
            
        Returns:
            Result in batch runner format
        """
        metrics = cn_result.get("metrics", {})
        
        return {
            "model": cn_result.get("model_name", "unknown"),
            "task": task_name,
            "success": cn_result.get("success", False),
            "error": cn_result.get("error", None),
            "completion_time": cn_result.get("execution_time", 0),
            "prompts_sent": metrics.get("prompts_sent", 1),  # CN headless = 1 prompt
            "human_interventions": 0,  # CN is fully automated
            "files_modified": metrics.get("files_modified", 0),
            "lines_added": metrics.get("lines_added", 0),
            "lines_removed": metrics.get("lines_removed", 0),
            "timestamp": cn_result.get("timestamp", datetime.now().isoformat()),
            "execution_method": "continue_cli",
            "tool_calls": metrics.get("tool_calls", 0),
            "cn_returncode": cn_result.get("cn_returncode", -1),
            "cn_metrics": metrics  # Store detailed CN metrics
        }
    
    def run_batch_with_cn(self, task_files: List[str], models: List[Dict[str, str]], 
                         timeout: int = 600, output_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Run a batch of tasks using Continue CLI.
        
        Args:
            task_files: List of task file paths
            models: List of model dictionaries with 'name' and 'provider'
            timeout: Timeout per task in seconds
            output_dir: Output directory for results
            
        Returns:
            Batch results dictionary compatible with BatchRunner
        """
        batch_start_time = time.time()
        batch_id = f"cn_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if output_dir is None:
            output_dir = Path(f"benchmark/results/{batch_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Starting CN batch: {batch_id}")
        logger.info(f"Tasks: {len(task_files)}, Models: {len(models)}")
        
        all_results = []
        successful_results = []
        failed_results = []
        
        total_tasks = len(task_files) * len(models)
        current_task = 0
        
        for task_file in task_files:
            task_name = Path(task_file).stem
            
            for model_info in models:
                current_task += 1
                model_name = model_info.get("name", str(model_info))
                
                print(f"\n[{current_task}/{total_tasks}] Running {task_name} with {model_name}")
                print("-" * 60)
                
                try:
                    result = self.run_cn_task(task_file, model_name, timeout)
                    all_results.append(result)
                    
                    if result["success"]:
                        successful_results.append(result)
                        print(f"✅ {model_name}: PASSED ({result['completion_time']:.1f}s)")
                    else:
                        failed_results.append(result)
                        error_msg = result.get("error", "Unknown error")
                        print(f"❌ {model_name}: FAILED - {error_msg}")
                    
                    # Save individual result
                    self._save_individual_result(result, output_dir)
                    
                except Exception as e:
                    error_result = {
                        "model": model_name,
                        "task": task_name,
                        "success": False,
                        "error": str(e),
                        "completion_time": 0,
                        "timestamp": datetime.now().isoformat(),
                        "execution_method": "continue_cli"
                    }
                    all_results.append(error_result)
                    failed_results.append(error_result)
                    print(f"❌ {model_name}: ERROR - {e}")
        
        # Generate batch summary
        batch_summary = self._generate_batch_summary(
            batch_id, all_results, successful_results, failed_results, 
            batch_start_time, task_files, models
        )
        
        # Save batch summary
        self._save_batch_summary(batch_summary, output_dir)
        
        # Cleanup temporary configs
        self.config_manager.cleanup_temp_configs()
        
        return batch_summary
    
    def _save_individual_result(self, result: Dict[str, Any], output_dir: Path):
        """Save individual task result to file."""
        model_name = result["model"].replace("/", "_").replace(":", "_")
        task_name = result["task"]
        filename = f"{model_name}_{task_name}_result.json"
        
        result_file = output_dir / filename
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)
    
    def _generate_batch_summary(self, batch_id: str, all_results: List[Dict],
                              successful: List[Dict], failed: List[Dict],
                              start_time: float, task_files: List[str],
                              models: List[Dict]) -> Dict[str, Any]:
        """Generate comprehensive batch summary."""
        total_time = time.time() - start_time
        
        summary = {
            "batch_id": batch_id,
            "execution_method": "continue_cli",
            "timestamp": datetime.now().isoformat(),
            "total_time": total_time,
            "task_files": task_files,
            "models_tested": len(models),
            "total_runs": len(all_results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(all_results) * 100 if all_results else 0,
            "results": all_results
        }
        
        # Calculate rankings for successful runs
        if successful:
            # Sort by completion time for speed ranking
            speed_ranking = sorted(successful, key=lambda x: x["completion_time"])
            
            # Sort by tool calls for efficiency ranking
            efficiency_ranking = sorted(
                successful, 
                key=lambda x: x.get("tool_calls", 999)
            )
            
            summary["rankings"] = {
                "fastest": speed_ranking[0]["model"] if speed_ranking else None,
                "most_efficient": efficiency_ranking[0]["model"] if efficiency_ranking else None,
                "most_autonomous": speed_ranking[0]["model"]  # CN is always fully autonomous
            }
            
            # Calculate summary statistics
            completion_times = [r["completion_time"] for r in successful]
            tool_calls = [r.get("tool_calls", 0) for r in successful]
            
            summary["summary_stats"] = {
                "avg_completion_time": sum(completion_times) / len(completion_times),
                "min_completion_time": min(completion_times),
                "max_completion_time": max(completion_times),
                "avg_tool_calls": sum(tool_calls) / len(tool_calls),
                "total_files_modified": sum(r.get("files_modified", 0) for r in successful),
                "total_lines_changed": sum(
                    r.get("lines_added", 0) + r.get("lines_removed", 0) 
                    for r in successful
                )
            }
        
        return summary
    
    def _save_batch_summary(self, summary: Dict[str, Any], output_dir: Path):
        """Save batch summary to files."""
        # Save JSON summary
        json_file = output_dir / "cn_batch_summary.json"
        with open(json_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # Generate and save HTML report
        html_file = output_dir / "cn_batch_report.html"
        self._generate_html_report(summary, html_file)
        
        # Generate and save CSV for analysis
        csv_file = output_dir / "cn_batch_results.csv"
        self._generate_csv_report(summary, csv_file)
        
        print("\n📊 CN Batch Results:")
        print(f"   JSON Report: {json_file}")
        print(f"   HTML Report: {html_file}")
        print(f"   CSV Data: {csv_file}")
    
    def _generate_html_report(self, summary: Dict[str, Any], html_file: Path):
        """Generate HTML report for CN batch results."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Continue CLI Batch Report - {summary['batch_id']}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #2563eb; color: white; padding: 20px; border-radius: 8px; }}
                .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
                .stat-card {{ background: #f8fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #2563eb; }}
                .stat-value {{ font-size: 2em; font-weight: bold; color: #2563eb; }}
                .stat-label {{ color: #64748b; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #e2e8f0; padding: 12px; text-align: left; }}
                th {{ background: #f1f5f9; }}
                .success {{ color: #16a34a; font-weight: bold; }}
                .failed {{ color: #dc2626; font-weight: bold; }}
                .cn-badge {{ background: #8b5cf6; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.8em; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Continue CLI Batch Benchmark Report</h1>
                <p><span class="cn-badge">CONTINUE CLI</span> Automated execution • {summary['batch_id']}</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{summary['success_rate']:.1f}%</div>
                    <div class="stat-label">Success Rate</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{summary['successful']}/{summary['total_runs']}</div>
                    <div class="stat-label">Successful Runs</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{summary['total_time']/60:.1f}min</div>
                    <div class="stat-label">Total Time</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{summary['models_tested']}</div>
                    <div class="stat-label">Models Tested</div>
                </div>
            </div>
            
            <h2>Results</h2>
            <table>
                <tr>
                    <th>Model</th>
                    <th>Task</th>
                    <th>Status</th>
                    <th>Time (s)</th>
                    <th>Tool Calls</th>
                    <th>Files Modified</th>
                </tr>
        """
        
        for result in summary["results"]:
            status_class = "success" if result["success"] else "failed"
            status_text = "✅ Success" if result["success"] else "❌ Failed"
            
            html_content += f"""
                <tr>
                    <td>{result['model']}</td>
                    <td>{result['task']}</td>
                    <td class="{status_class}">{status_text}</td>
                    <td>{result['completion_time']:.2f}</td>
                    <td>{result.get('tool_calls', 0)}</td>
                    <td>{result.get('files_modified', 0)}</td>
                </tr>
            """
        
        if summary.get("rankings"):
            html_content += f"""
            </table>
            
            <h2>🏆 Performance Rankings</h2>
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">🏃‍♂️</div>
                    <div class="stat-label">Fastest: {summary['rankings']['fastest']}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">⚡</div>
                    <div class="stat-label">Most Efficient: {summary['rankings']['most_efficient']}</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">🤖</div>
                    <div class="stat-label">Fully Automated via CN CLI</div>
                </div>
            </div>
            """
        
        html_content += """
        </body>
        </html>
        """
        
        with open(html_file, 'w') as f:
            f.write(html_content)
    
    def _generate_csv_report(self, summary: Dict[str, Any], csv_file: Path):
        """Generate CSV report for data analysis."""
        import csv
        
        with open(csv_file, 'w', newline='') as f:
            fieldnames = [
                'model', 'task', 'success', 'completion_time', 'tool_calls',
                'files_modified', 'lines_added', 'lines_removed', 'timestamp',
                'execution_method', 'cn_returncode'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in summary["results"]:
                writer.writerow({
                    'model': result.get('model', ''),
                    'task': result.get('task', ''),
                    'success': result.get('success', False),
                    'completion_time': result.get('completion_time', 0),
                    'tool_calls': result.get('tool_calls', 0),
                    'files_modified': result.get('files_modified', 0),
                    'lines_added': result.get('lines_added', 0),
                    'lines_removed': result.get('lines_removed', 0),
                    'timestamp': result.get('timestamp', ''),
                    'execution_method': result.get('execution_method', 'continue_cli'),
                    'cn_returncode': result.get('cn_returncode', -1)
                })


def test_cn_batch_integration():
    """Test the CN batch integration."""
    integration = CNBatchIntegration(verbose=True)
    
    # Test with a simple task and model
    task_files = ["benchmark/tasks/easy/fix_typo.md"]
    models = [{"name": "gpt-3.5-turbo"}]
    
    if Path(task_files[0]).exists():
        result = integration.run_batch_with_cn(task_files, models, timeout=120)
        print(f"Batch test result: {json.dumps(result, indent=2)}")
    else:
        print(f"Test task not found: {task_files[0]}")


if __name__ == "__main__":
    test_cn_batch_integration()
