#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

from metrics import BenchmarkMetrics


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


def run_benchmark_task(model_name, task_file):
    """Simple POC task runner"""
    print(f"\n{'=' * 60}")
    print(f"Starting benchmark: {model_name}")
    print(f"Task file: {task_file}")
    print(f"{'=' * 60}\n")

    # Load task
    task_path = Path(task_file)
    if not task_path.exists():
        print(f"Error: Task file not found: {task_file}")
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

    success = input("Was the task completed successfully? (y/n): ").lower() == "y"

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
        use_git = input("Use these stats? (y/n) [default: y]: ").strip().lower()
        if use_git != "n":
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
    if len(sys.argv) == 1:
        print("Usage: python benchmark/task_runner.py <model_name> <task_file>")
        print("\nExample:")
        print(
            "  python benchmark/task_runner.py 'Claude-4-Sonnet' 'benchmark/tasks/easy/fix_typo.md'"
        )

        tasks = list_available_tasks()
        if tasks:
            print("\nAvailable tasks:")
            for task in tasks:
                print(f"  • {task}")
        sys.exit(1)

    if len(sys.argv) != 3:
        print("Error: Incorrect number of arguments")
        print("Usage: python benchmark/task_runner.py <model_name> <task_file>")
        sys.exit(1)

    run_benchmark_task(sys.argv[1], sys.argv[2])
