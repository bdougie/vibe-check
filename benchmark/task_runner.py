#!/usr/bin/env python3
import logging
from pathlib import Path
import subprocess
import sys
from typing import Optional

from benchmark.metrics import BenchmarkMetrics
from benchmark.ollama_check import OllamaChecker

try:
    from benchmark.validators import (
        validate_model_name,
        validate_task_file,
        get_safe_user_input,
        ValidationError
    )
except ImportError:
    # Fallback if validators module is not available
    def validate_model_name(name: str) -> str:
        return name.strip() if name else name
    
    def validate_task_file(path):
        return Path(path)
    
    def get_safe_user_input(prompt: str, valid_options: list) -> str:
        return input(prompt).strip().lower()
    
    class ValidationError(Exception):
        pass

# Set up logging
logger = logging.getLogger(__name__)


def get_git_diff_stats():
    """Get git diff statistics for modified files"""
    try:
        # Get list of modified files
        result = subprocess.run(
            ["git", "diff", "--stat"], capture_output=True, text=True, check=False
        )

        if result.returncode == 0 and result.stdout:
            lines = result.stdout.strip().split("\n")
            if lines and "files changed" in lines[-1]:
                # Parse the summary line
                summary = lines[-1]
                files_modified = 0
                lines_added = 0
                lines_removed = 0

                parts = summary.split(",")
                for part_item in parts:
                    part_item = part_item.strip()
                    if "file" in part_item:
                        files_modified = int(part_item.split()[0])
                    elif "insertion" in part_item:
                        lines_added = int(part_item.split()[0])
                    elif "deletion" in part_item:
                        lines_removed = int(part_item.split()[0])

                return files_modified, lines_added, lines_removed
    except Exception as e:
        print(f"Error getting git stats: {e}")

    return 0, 0, 0


def check_ollama_setup(model_name: Optional[str] = None) -> bool:
    """Run Ollama pre-flight checks.

    Args:
        model_name: Optional specific model to check

    Returns:
        True if Ollama is ready, False otherwise
    """
    print("\n🔍 Running Ollama pre-flight checks...")
    print("-" * 40)

    checker = OllamaChecker(verbose=True)

    # Check installation and service
    if not checker.check_installation():
        return False

    if not checker.check_service_running():
        return False

    # List available models
    models = checker.list_available_models()

    # Check specific model if provided
    if model_name and model_name.lower().startswith("ollama"):
        # Extract model name from format like "ollama/llama2" or "ollama-llama2"
        if "/" in model_name:
            specific_model = model_name.split("/", 1)[1]
        elif "-" in model_name:
            specific_model = model_name.split("-", 1)[1]
        else:
            specific_model = None

        if specific_model:
            # Validate model name first
            try:
                specific_model = validate_model_name(specific_model)
            except ValidationError as e:
                print(f"\n❌ Invalid model name: {e}")
                return False
            
            if not checker.check_model_available(specific_model):
                print(f"\n⚠️  Model '{specific_model}' is not available locally.")
                try:
                    pull_model = get_safe_user_input(
                        f"Would you like to pull '{specific_model}'? (y/n): ",
                        ['y', 'n', 'yes', 'no']
                    )
                except ValidationError:
                    print("\n❌ Invalid input provided multiple times.")
                    return False
                
                if pull_model in ['y', 'yes']:
                    if not checker.pull_model(specific_model):
                        return False
                else:
                    print(
                        f"Please pull the model manually: ollama pull {specific_model}"
                    )
                    return False

    # Final check
    if not models and model_name and model_name.lower().startswith("ollama"):
        print("\n⚠️  No Ollama models found.")
        print("Please pull at least one model before running benchmarks.")
        print("Example: ollama pull llama2")
        return False

    print("\n✅ Ollama pre-flight checks passed!")
    return True


def run_benchmark_task(model_name: str, task_file: str, skip_ollama_check: bool = False) -> None:
    """Simple POC task runner

    Args:
        model_name: Name of the model to benchmark
        task_file: Path to the task file
        skip_ollama_check: Whether to skip Ollama setup verification
    """
    print(f"\n{'=' * 60}")
    print(f"Starting benchmark: {model_name}")
    print(f"Task file: {task_file}")
    print(f"{'=' * 60}\n")

    # Validate model name
    try:
        model_name = validate_model_name(model_name)
    except ValidationError as e:
        print(f"\n❌ Invalid model name: {e}")
        sys.exit(1)
    
    # Run Ollama checks if using Ollama model
    if not skip_ollama_check and model_name.lower().startswith("ollama"):
        if not check_ollama_setup(model_name):
            print(
                "\n❌ Ollama setup incomplete. Please fix the issues above and try again."
            )
            sys.exit(1)

    # Validate and load task file
    try:
        task_path = validate_task_file(task_file)
    except ValidationError as e:
        print(f"\n❌ Invalid task file: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n❌ Task file not found: {task_file}")
        sys.exit(1)

    with task_path.open() as f:
        task_content = f.read()

    print("Task Description:")
    print("-" * 40)
    print(task_content)
    print("-" * 40)

    # Initialize metrics
    task_name = task_path.stem
    metrics = BenchmarkMetrics(model_name, task_name)
    metrics.start_task()

    print(f"\nMetrics tracking started for {model_name}")
    print("\n📊 Now use Continue to solve this task!")
    print("\nManual tracking points to remember:")
    print("  • Count each prompt you send to the AI")
    print("  • Note when you manually edit code")
    print("  • Track when you change the AI's suggestion")
    print("  • Record any issues or errors encountered")

    print("\n" + "=" * 60)
    input("Press Enter when you complete the task...")
    print("=" * 60)

    # Collect metrics
    print("\n📝 Task Completion Metrics")
    print("-" * 40)

    try:
        success_input = get_safe_user_input(
            "Was the task completed successfully? (y/n): ",
            ['y', 'n', 'yes', 'no']
        )
        success = success_input in ['y', 'yes']
    except ValidationError:
        print("\n❌ Invalid input provided multiple times. Marking as failed.")
        success = False

    # Manual input for POC
    prompts = input("How many prompts did you send? [default: 0]: ").strip()
    metrics.metrics["prompts_sent"] = int(prompts) if prompts else 0

    interventions = input(
        "How many times did you manually intervene? [default: 0]: "
    ).strip()
    metrics.metrics["human_interventions"] = int(interventions) if interventions else 0

    # Try to get git stats automatically
    files_mod, lines_add, lines_rem = get_git_diff_stats()
    if files_mod > 0:
        print(
            f"\nDetected git changes: {files_mod} files, +{lines_add}/-{lines_rem} lines"
        )
        try:
            use_git = get_safe_user_input(
                "Use these stats? (y/n) [default: y]: ",
                ['y', 'n', 'yes', 'no', '']
            )
        except ValidationError:
            use_git = 'y'  # Default to yes on validation error
        
        if use_git not in ['n', 'no']:
            metrics.update_git_stats(files_mod, lines_add, lines_rem)
        else:
            files = input("How many files were modified? [default: 0]: ").strip()
            metrics.metrics["files_modified"] = int(files) if files else 0
    else:
        files = input("How many files were modified? [default: 0]: ").strip()
        metrics.metrics["files_modified"] = int(files) if files else 0

    # Complete and save
    result_file = metrics.complete_task(success)

    print("\n" + "=" * 60)
    print("✅ Benchmark completed!")
    print(f"📁 Results saved to: {result_file}")
    print("=" * 60 + "\n")


def list_available_tasks():
    """List all available benchmark tasks"""
    tasks_dir = Path("benchmark/tasks")
    if not tasks_dir.exists():
        return []

    tasks = []
    for difficulty in ["easy", "medium", "hard"]:
        task_path = tasks_dir / difficulty
        if task_path.exists():
            tasks.extend(str(task_file) for task_file in task_path.glob("*.md"))

    return tasks


if __name__ == "__main__":
    # Check for special commands
    if len(sys.argv) == 2 and sys.argv[1] == "--check-ollama":
        # Run Ollama health check
        checker = OllamaChecker(verbose=True)
        results = checker.run_full_check()
        sys.exit(0 if results["ready"] else 1)

    if len(sys.argv) == 1:
        print("Usage: python benchmark/task_runner.py <model_name> <task_file>")
        print("       python benchmark/task_runner.py --check-ollama")
        print("\nExample:")
        print(
            "  python benchmark/task_runner.py 'Claude-4-Sonnet' 'benchmark/tasks/easy/fix_typo.md'"
        )
        print("\nSpecial commands:")
        print("  --check-ollama    Run Ollama installation and health check")

        tasks = list_available_tasks()
        if tasks:
            print("\nAvailable tasks:")
            for task in tasks:
                print(f"  • {task}")
        sys.exit(1)

    if len(sys.argv) != 3:
        print("Error: Incorrect number of arguments")
        print("Usage: python benchmark/task_runner.py <model_name> <task_file>")
        print("       python benchmark/task_runner.py --check-ollama")
        sys.exit(1)

    # Parse optional flags
    skip_ollama = "--skip-ollama-check" in sys.argv
    if skip_ollama:
        sys.argv.remove("--skip-ollama-check")

    run_benchmark_task(sys.argv[1], sys.argv[2], skip_ollama_check=skip_ollama)
