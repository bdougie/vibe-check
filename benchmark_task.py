#!/usr/bin/env python3
"""
Benchmark task runner for AI coding agent evaluation.
Compatible with Continue VS Code extension.
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

# Import benchmark modules
sys.path.insert(0, str(Path(__file__).parent))

from benchmark.metrics import BenchmarkMetrics


class BenchmarkSession:
    """Manages a benchmark session for AI coding agents"""

    def __init__(self):
        self.active_tasks = {}
        self.session_file = Path('.benchmark_session.json')

    def load_session(self):
        """Load active session from file"""
        if self.session_file.exists():
            with self.session_file.open() as f:
                self.active_tasks = json.load(f)

    def save_session(self):
        """Save active session to file"""
        with self.session_file.open('w') as f:
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
            'model': model_name,
            'task_name': task_name,
            'task_file': str(task_file),
            'start_time': time.time(),
            'status': 'active',
            'content': task_content
        }

        self.save_session()

        print("\n" + "="*70)
        print("🚀 BENCHMARK STARTED")
        print("="*70)
        print(f"Model: {model_name}")
        print(f"Task: {task_name}")
        print(f"Session ID: {task_id}")
        print("\n" + "-"*70)
        print("TASK DESCRIPTION:")
        print("-"*70)
        print(task_content)
        print("-"*70)
        print("\n⚡ Continue integration active - metrics will be tracked automatically")
        print("📝 Manual tracking reminders:")
        print("  • Note any manual code edits")
        print("  • Track when you override AI suggestions")
        print("  • Record any errors or issues")
        print("\n" + "="*70 + "\n")

        return task_id

    def complete_task(self, task_id=None):
        """Complete a benchmark task"""
        if not task_id and self.active_tasks:
            # Get most recent active task
            active = [(k, v) for k, v in self.active_tasks.items() if v['status'] == 'active']
            if active:
                task_id = active[-1][0]

        if not task_id or task_id not in self.active_tasks:
            print("No active task found to complete")
            return False

        task = self.active_tasks[task_id]
        task['status'] = 'completed'
        task['end_time'] = time.time()
        task['duration'] = task['end_time'] - task['start_time']

        # Create metrics object to save results
        metrics = BenchmarkMetrics(task['model'], task['task_name'])
        metrics.start_time = task['start_time']

        # Collect final metrics
        print("\n" + "="*70)
        print("📊 TASK COMPLETION")
        print("="*70)
        print(f"Task: {task['task_name']}")
        print(f"Duration: {task['duration']/60:.1f} minutes")

        success = input("\n✅ Was the task completed successfully? (y/n): ").lower() == 'y'

        # Manual metric input
        prompts = input("📝 How many prompts did you send? [0]: ").strip()
        metrics.metrics['prompts_sent'] = int(prompts) if prompts else 0

        interventions = input("👤 Manual interventions? [0]: ").strip()
        metrics.metrics['human_interventions'] = int(interventions) if interventions else 0

        files = input("📁 Files modified? [0]: ").strip()
        metrics.metrics['files_modified'] = int(files) if files else 0

        # Complete and save
        result_file = metrics.complete_task(success)

        print("\n" + "="*70)
        print("✅ BENCHMARK COMPLETED!")
        print(f"📊 Results saved to: {result_file}")
        print("="*70 + "\n")

        self.save_session()
        return True

    def list_tasks(self):
        """List all active and completed tasks"""
        if not self.active_tasks:
            print("No benchmark sessions found")
            return

        print("\n" + "="*70)
        print("📋 BENCHMARK SESSIONS")
        print("="*70)

        for task_id, task in self.active_tasks.items():
            status_icon = "🟢" if task['status'] == 'active' else "✅"
            print(f"\n{status_icon} {task_id}")
            print(f"   Model: {task['model']}")
            print(f"   Task: {task['task_name']}")
            print(f"   Status: {task['status']}")
            if 'duration' in task:
                print(f"   Duration: {task['duration']/60:.1f} minutes")

        print("\n" + "="*70 + "\n")


def list_available_tasks():
    """List all available benchmark tasks"""
    tasks_dir = Path("benchmark/tasks")
    if not tasks_dir.exists():
        print("No tasks directory found")
        return

    print("\n" + "="*70)
    print("📚 AVAILABLE BENCHMARK TASKS")
    print("="*70)

    for difficulty in ['easy', 'medium', 'hard']:
        task_path = tasks_dir / difficulty
        if task_path.exists():
            tasks = list(task_path.glob("*.md"))
            if tasks:
                print(f"\n{difficulty.upper()} ({len(tasks)} tasks):")
                for task_file in tasks:
                    print(f"  • {task_file.stem}")

    print("\n" + "="*70 + "\n")


def main():
    """Main entry point for benchmark task runner"""
    parser = argparse.ArgumentParser(description='AI Coding Agent Benchmark Framework')
    parser.add_argument('--start', action='store_true', help='Start a new benchmark task')
    parser.add_argument('--complete', action='store_true', help='Complete current task')
    parser.add_argument('--list', action='store_true', help='List active sessions')
    parser.add_argument('--tasks', action='store_true', help='List available tasks')
    parser.add_argument('--model', type=str, help='Model name (e.g., Claude-3.5-Sonnet)')
    parser.add_argument('--task', type=str, help='Task file path')

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
            print("Example: python benchmark_task.py --start --model 'Claude-3.5' --task 'benchmark/tasks/easy/fix_typo.md'")
            sys.exit(1)
        session.start_task(args.model, args.task)
    elif args.complete:
        session.complete_task()
    else:
        print("vibe-check: AI Coding Agent Benchmark Framework")
        print("\nUsage:")
        print("  python benchmark_task.py --tasks           # List available tasks")
        print("  python benchmark_task.py --start --model <name> --task <file>  # Start benchmark")
        print("  python benchmark_task.py --complete        # Complete current task")
        print("  python benchmark_task.py --list            # List sessions")


if __name__ == "__main__":
    main()