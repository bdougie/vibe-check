#!/usr/bin/env python3
"""
Continue slash command for running benchmark tasks
This script integrates with Continue's custom slash commands
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add benchmark directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'benchmark'))

from metrics import BenchmarkMetrics

def list_tasks():
    """List all available benchmark tasks"""
    tasks_dir = Path("benchmark/tasks")
    tasks = {
        "easy": [],
        "medium": [],
        "hard": []
    }
    
    for difficulty in tasks.keys():
        task_path = tasks_dir / difficulty
        if task_path.exists():
            for task_file in task_path.glob("*.md"):
                tasks[difficulty].append({
                    "name": task_file.stem,
                    "path": str(task_file)
                })
    
    return tasks

def start_benchmark(model_name=None, task_path=None):
    """Start a benchmark task with Continue integration"""
    
    # If no parameters, show interactive menu
    if not model_name or not task_path:
        tasks = list_tasks()
        
        print("🎯 Available Benchmark Tasks")
        print("=" * 50)
        
        all_tasks = []
        for difficulty, task_list in tasks.items():
            if task_list:
                print(f"\n📝 {difficulty.upper()} Tasks:")
                for idx, task in enumerate(task_list):
                    global_idx = len(all_tasks)
                    all_tasks.append(task)
                    print(f"  [{global_idx + 1}] {task['name']}")
        
        if not all_tasks:
            print("\n❌ No benchmark tasks found!")
            print("Create tasks in benchmark/tasks/{easy,medium,hard}/")
            return
        
        print("\n" + "=" * 50)
        
        # Get task selection
        try:
            task_idx = int(input("Select task number: ")) - 1
            if task_idx < 0 or task_idx >= len(all_tasks):
                print("Invalid task number")
                return
            selected_task = all_tasks[task_idx]
        except (ValueError, KeyboardInterrupt):
            print("\nBenchmark cancelled")
            return
        
        # Get model name
        print("\nEnter model name (e.g., 'Claude-4-Sonnet', 'GPT-4o', 'Qwen2.5-Coder-7B'):")
        model_name = input("Model: ").strip()
        if not model_name:
            model_name = "Unknown"
        
        task_path = selected_task['path']
    
    # Load and display task
    with open(task_path, 'r') as f:
        task_content = f.read()
    
    print("\n" + "=" * 60)
    print("📋 BENCHMARK TASK")
    print("=" * 60)
    print(f"Model: {model_name}")
    print(f"Task: {Path(task_path).stem}")
    print("-" * 60)
    print(task_content)
    print("=" * 60)
    
    # Initialize metrics
    task_name = Path(task_path).stem
    metrics = BenchmarkMetrics(model_name, task_name)
    metrics.start_task()
    
    # Create a session file for Continue to track
    session_file = Path(f".benchmark_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    session_data = {
        "model": model_name,
        "task": task_name,
        "task_path": task_path,
        "start_time": datetime.now().isoformat(),
        "status": "in_progress"
    }
    
    with open(session_file, 'w') as f:
        json.dump(session_data, f, indent=2)
    
    print("\n✅ Benchmark session started!")
    print(f"📁 Session file: {session_file}")
    print("\n📌 Next Steps:")
    print("1. Use Continue to solve the task above")
    print("2. Track your prompts and interventions")
    print("3. Run '/benchmark-complete' when done")
    print("\n💡 Tips:")
    print("• Try different approaches with the AI")
    print("• Note when you need to correct the AI's suggestions")
    print("• Pay attention to how many prompts are needed")
    
    return str(session_file)

def complete_benchmark(session_file=None):
    """Complete a benchmark session and save results"""
    
    # Find the most recent session if not specified
    if not session_file:
        sessions = list(Path(".").glob(".benchmark_session_*.json"))
        if not sessions:
            print("❌ No active benchmark sessions found")
            print("Start a benchmark with '/benchmark-task' first")
            return
        
        session_file = max(sessions, key=lambda p: p.stat().st_mtime)
    
    # Load session data
    session_path = Path(session_file)
    if not session_path.exists():
        print(f"❌ Session file not found: {session_file}")
        return
    
    with open(session_path, 'r') as f:
        session_data = json.load(f)
    
    print("\n" + "=" * 60)
    print("📊 COMPLETING BENCHMARK")
    print("=" * 60)
    print(f"Model: {session_data['model']}")
    print(f"Task: {session_data['task']}")
    print("-" * 60)
    
    # Collect completion metrics
    success = input("Was the task completed successfully? (y/n): ").lower() == 'y'
    prompts = int(input("How many prompts did you send? ") or "0")
    interventions = int(input("How many manual interventions? ") or "0")
    
    # Create and save metrics
    metrics = BenchmarkMetrics(session_data['model'], session_data['task'])
    metrics.metrics['prompts_sent'] = prompts
    metrics.metrics['human_interventions'] = interventions
    metrics.metrics['task_completed'] = success
    
    # Calculate elapsed time
    start_time = datetime.fromisoformat(session_data['start_time'])
    elapsed = (datetime.now() - start_time).total_seconds()
    metrics.metrics['completion_time'] = elapsed
    
    # Save results
    result_file = metrics.complete_task(success)
    
    # Clean up session file
    session_path.unlink()
    
    print("\n" + "=" * 60)
    print("✅ Benchmark completed!")
    print(f"📊 Results saved to: {result_file}")
    print(f"⏱️  Time taken: {elapsed/60:.1f} minutes")
    print("\nRun 'python benchmark/analyze.py' to see aggregated results")
    print("=" * 60)

def main():
    """Main entry point for Continue slash command"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Benchmark task runner for Continue")
    parser.add_argument('--start', action='store_true', help='Start a new benchmark')
    parser.add_argument('--complete', action='store_true', help='Complete current benchmark')
    parser.add_argument('--model', type=str, help='Model name for benchmark')
    parser.add_argument('--task', type=str, help='Task file path')
    parser.add_argument('--session', type=str, help='Session file for completion')
    
    args = parser.parse_args()
    
    if args.complete:
        complete_benchmark(args.session)
    else:
        # Default to start if no action specified
        start_benchmark(args.model, args.task)

if __name__ == "__main__":
    main()