#!/usr/bin/env python3
"""
Benchmark task runner for AI coding agent evaluation.
Compatible with Continue VS Code extension.
"""

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
import time

# Import benchmark modules
sys.path.insert(0, str(Path(__file__).parent))

from benchmark.metrics import BenchmarkMetrics

# Re-export for testing compatibility
BenchmarkMetrics = BenchmarkMetrics


class BenchmarkSession:
    """Manages a benchmark session for AI coding agents"""

    def __init__(self):
        self.active_tasks = {}
        self.session_file = Path(".benchmark_session.json")

    def load_session(self):
        """Load active session from file"""
        if self.session_file.exists():
            with self.session_file.open() as f:
                self.active_tasks = json.load(f)

    def save_session(self):
        """Save active session to file"""
        with self.session_file.open("w") as f:
            json.dump(self.active_tasks, f, indent=2)

    def start_task(self, model_name, task_file):
        """Start a new benchmark task"""
        task_path = Path(task_file)
        if not task_path.exists():
            print(f"Error: Task file not found: {task_file}")
            return False

        task_name = task_path.stem
        task_id = f"{model_name}_{task_name}_{int(time.time())}"

        # Load task content
        with task_path.open() as f:
            task_content = f.read()

        # Initialize metrics
        metrics = BenchmarkMetrics(model_name, task_name)
        metrics.start_task()

        # Store task info
        self.active_tasks[task_id] = {
            "model": model_name,
            "task_name": task_name,
            "task_file": str(task_file),
            "start_time": time.time(),
            "status": "active",
            "content": task_content,
        }

        self.save_session()

        print("\n" + "=" * 70)
        print("🚀 BENCHMARK STARTED")
        print("=" * 70)
        print(f"Model: {model_name}")
        print(f"Task: {task_name}")
        print(f"Session ID: {task_id}")
        print("\n" + "-" * 70)
        print("TASK DESCRIPTION:")
        print("-" * 70)
        print(task_content)
        print("-" * 70)
        print(
            "\n⚡ Continue integration active - metrics will be tracked automatically"
        )
        print("📝 Manual tracking reminders:")
        print("  • Note any manual code edits")
        print("  • Track when you override AI suggestions")
        print("  • Record any errors or issues")
        print("\n" + "=" * 70 + "\n")

        return task_id

    def complete_task(self, task_id=None):
        """Complete a benchmark task"""
        if not task_id and self.active_tasks:
            # Get most recent active task
            active = [
                (k, v) for k, v in self.active_tasks.items() if v["status"] == "active"
            ]
            if active:
                task_id = active[-1][0]

        if not task_id or task_id not in self.active_tasks:
            print("No active task found to complete")
            return False

        task = self.active_tasks[task_id]
        task["status"] = "completed"
        task["end_time"] = time.time()
        task["duration"] = task["end_time"] - task["start_time"]

        # Create metrics object to save results
        metrics = BenchmarkMetrics(task["model"], task["task_name"])
        metrics.start_time = task["start_time"]

        # Collect final metrics
        print("\n" + "=" * 70)
        print("📊 TASK COMPLETION")
        print("=" * 70)
        print(f"Task: {task['task_name']}")
        print(f"Duration: {task['duration'] / 60:.1f} minutes")

        success = (
            input("\n✅ Was the task completed successfully? (y/n): ").lower() == "y"
        )

        # Manual metric input
        prompts = input("📝 How many prompts did you send? [0]: ").strip()
        metrics.metrics["prompts_sent"] = int(prompts) if prompts else 0

        interventions = input("👤 Manual interventions? [0]: ").strip()
        metrics.metrics["human_interventions"] = (
            int(interventions) if interventions else 0
        )

        files = input("📁 Files modified? [0]: ").strip()
        metrics.metrics["files_modified"] = int(files) if files else 0

        # Complete and save
        result_file = metrics.complete_task(success)

        print("\n" + "=" * 70)
        print("✅ BENCHMARK COMPLETED!")
        print(f"📊 Results saved to: {result_file}")
        print("=" * 70 + "\n")

        self.save_session()
        return True

    def list_tasks(self):
        """List all active and completed tasks"""
        if not self.active_tasks:
            print("No benchmark sessions found")
            return

        print("\n" + "=" * 70)
        print("📋 BENCHMARK SESSIONS")
        print("=" * 70)

        for task_id, task in self.active_tasks.items():
            status_icon = "🟢" if task["status"] == "active" else "✅"
            print(f"\n{status_icon} {task_id}")
            print(f"   Model: {task['model']}")
            print(f"   Task: {task['task_name']}")
            print(f"   Status: {task['status']}")
            if "duration" in task:
                print(f"   Duration: {task['duration'] / 60:.1f} minutes")

        print("\n" + "=" * 70 + "\n")


def list_available_tasks():
    """List all available benchmark tasks"""
    tasks_dir = Path("benchmark/tasks")
    if not tasks_dir.exists():
        print("No tasks directory found")
        return

    print("\n" + "=" * 70)
    print("📚 AVAILABLE BENCHMARK TASKS")
    print("=" * 70)

    for difficulty in ["easy", "medium", "hard"]:
        task_path = tasks_dir / difficulty
        if task_path.exists():
            tasks = list(task_path.glob("*.md"))
            if tasks:
                print(f"\n{difficulty.upper()} ({len(tasks)} tasks):")
                for task_file in tasks:
                    print(f"  • {task_file.stem}")

    print("\n" + "=" * 70 + "\n")


def list_tasks():
    """List all available benchmark tasks - returns dict for testing"""
    tasks_dir = Path("benchmark/tasks")
    if not tasks_dir.exists():
        return {"easy": [], "medium": [], "hard": []}

    result = {}
    for difficulty in ["easy", "medium", "hard"]:
        task_path = tasks_dir / difficulty
        result[difficulty] = []
        if task_path.exists():
            tasks = list(task_path.glob("*.md"))
            for task_file in tasks:
                result[difficulty].append(
                    {"name": task_file.stem, "path": str(task_file)}
                )
    return result


def start_benchmark(model_name=None, task_path=None):
    """Start a benchmark task - wrapper for testing"""
    import json
    from pathlib import Path
    import time

    # Interactive mode if no params provided
    if not model_name or not task_path:
        try:
            # List tasks and get selection
            tasks = list_tasks()
            all_tasks = []
            for difficulty in ["easy", "medium", "hard"]:
                for task in tasks[difficulty]:
                    all_tasks.append(task)

            if not all_tasks:
                print("No tasks available")
                return None

            print("\nAvailable tasks:")
            for i, task in enumerate(all_tasks, 1):
                print(f"{i}. {task['name']}")

            while True:
                try:
                    choice = input("\nSelect task number: ")
                    task_idx = int(choice) - 1
                    if 0 <= task_idx < len(all_tasks):
                        task_path = all_tasks[task_idx]["path"]
                        break
                    else:
                        print(
                            f"Invalid selection. Please choose between 1 and {len(all_tasks)}"
                        )
                except ValueError:
                    if choice == "999":
                        continue
                    print("Invalid input. Please enter a number.")
                except KeyboardInterrupt:
                    return None

            model_name = input("Enter model name: ")
        except KeyboardInterrupt:
            return None

    # Create session file
    task_name = Path(task_path).stem
    session_id = f".benchmark_session_{int(time.time())}.json"

    session_data = {
        "model": model_name,
        "task": task_name,
        "task_path": task_path,
        "status": "in_progress",
        "start_time": datetime.now().isoformat(),
    }

    with open(session_id, "w") as f:
        json.dump(session_data, f, indent=2)

    print(f"\nBenchmark started for {model_name} on task {task_name}")
    print(f"Session file: {session_id}")

    return session_id


def complete_benchmark(session_file=None):
    """Complete a benchmark task - wrapper for testing"""
    import json
    from pathlib import Path

    if not session_file:
        # Find most recent session file
        session_files = list(Path(".").glob(".benchmark_session_*.json"))
        if not session_files:
            print("No active benchmark session found")
            return
        session_file = str(max(session_files, key=lambda x: x.stat().st_mtime))

    session_path = Path(session_file)
    if not session_path.exists():
        print(f"Session file not found: {session_file}")
        return

    try:
        with open(session_path, "r") as f:
            session_data = json.load(f)
    except json.JSONDecodeError:
        print(f"Invalid session file: {session_file}")
        return

    # Create metrics instance
    metrics = BenchmarkMetrics(session_data["model"], session_data["task"])

    # Get user input for completion
    try:
        success_input = input("Was the task completed successfully? (y/n): ").lower()
        success = success_input == "y"

        prompts_input = input("How many prompts did you send? [0]: ").strip()
        try:
            prompts = int(prompts_input) if prompts_input else 0
        except ValueError:
            prompts = 0

        interventions_input = input("Manual interventions? [0]: ").strip()
        try:
            interventions = int(interventions_input) if interventions_input else 0
        except ValueError:
            interventions = 0
    except (EOFError, KeyboardInterrupt):
        # Handle input errors gracefully
        success = False
        prompts = 0
        interventions = 0

    # Set metrics
    metrics.metrics["prompts_sent"] = prompts
    metrics.metrics["human_interventions"] = interventions
    metrics.metrics["task_completed"] = success

    # Complete the task
    result_file = metrics.complete_task(success)

    print(f"\nBenchmark completed! Results saved to: {result_file}")

    # Update session file status
    session_data["status"] = "completed"
    session_data["success"] = success
    with open(session_path, "w") as f:
        json.dump(session_data, f, indent=2)

    # Clean up session file after completion
    session_path.unlink()

    return result_file


def main():
    """Main entry point for benchmark task runner"""
    parser = argparse.ArgumentParser(description="AI Coding Agent Benchmark Framework")
    parser.add_argument(
        "--start", action="store_true", help="Start a new benchmark task"
    )
    parser.add_argument("--complete", action="store_true", help="Complete current task")
    parser.add_argument("--list", action="store_true", help="List active sessions")
    parser.add_argument("--tasks", action="store_true", help="List available tasks")
    parser.add_argument(
        "--model", type=str, help="Model name (e.g., Claude-3.5-Sonnet)"
    )
    parser.add_argument("--task", type=str, help="Task file path")

    args = parser.parse_args()

    session = BenchmarkSession()
    session.load_session()

    if args.tasks:
        list_available_tasks()
    elif args.list:
        session.list_tasks()
    elif args.start:
        if not args.model or not args.task:
            print("Error: --model and --task required to start benchmark")
            print(
                "Example: python benchmark_task.py --start --model 'Claude-3.5' --task 'benchmark/tasks/easy/fix_typo.md'"
            )
            sys.exit(1)
        session.start_task(args.model, args.task)
    elif args.complete:
        session.complete_task()
    else:
        print("vibe-check: AI Coding Agent Benchmark Framework")
        print("\nUsage:")
        print("  python benchmark_task.py --tasks           # List available tasks")
        print(
            "  python benchmark_task.py --start --model <name> --task <file>  # Start benchmark"
        )
        print("  python benchmark_task.py --complete        # Complete current task")
        print("  python benchmark_task.py --list            # List sessions")


if __name__ == "__main__":
    main()
