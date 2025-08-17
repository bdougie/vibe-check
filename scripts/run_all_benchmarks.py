#!/usr/bin/env python3
"""
Run all benchmark tasks on specified models.
Usage: uv run run_all_benchmarks.py
"""

import subprocess
import sys
from pathlib import Path
import json
from datetime import datetime

# Models to test
MODELS = ["ollama/gpt-oss:20b", "ollama/qwen2.5-coder:7b"]

def get_all_tasks():
    """Get all task files from benchmark/tasks directory."""
    tasks_dir = Path("benchmark/tasks")
    tasks = list(tasks_dir.glob("**/*.md"))
    return sorted(tasks)

def run_benchmark(task_path, models):
    """Run a single benchmark task on specified models."""
    models_str = ",".join(models)
    cmd = [
        sys.executable, 
        "benchmark/batch_runner.py",
        "--task", str(task_path),
        "--models", models_str,
        "--timeout", "3600"  # 1 hour timeout per model
    ]
    
    print(f"\n{'='*60}")
    print(f"Running: {task_path.name}")
    print(f"Models: {models_str}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"⚠️  Warning: Task {task_path.name} had issues")
            print(f"Error: {result.stderr}")
        else:
            print(f"✅ Completed: {task_path.name}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Failed to run {task_path.name}: {e}")
        return False

def main():
    """Run all benchmarks and create summary."""
    tasks = get_all_tasks()
    
    print(f"🚀 Vibe Check - Running All Benchmarks")
    print(f"📊 Found {len(tasks)} tasks")
    print(f"🤖 Models: {', '.join(MODELS)}")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    successful = 0
    failed = 0
    
    for i, task in enumerate(tasks, 1):
        print(f"\n📍 Task {i}/{len(tasks)}")
        success = run_benchmark(task, MODELS)
        results[str(task)] = success
        if success:
            successful += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"📈 BENCHMARK COMPLETE")
    print(f"{'='*60}")
    print(f"✅ Successful: {successful}/{len(tasks)}")
    print(f"❌ Failed: {failed}/{len(tasks)}")
    print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Save summary
    summary_file = Path(f"benchmark_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    with open(summary_file, 'w') as f:
        json.dump({
            "models": MODELS,
            "total_tasks": len(tasks),
            "successful": successful,
            "failed": failed,
            "results": results,
            "timestamp": datetime.now().isoformat()
        }, f, indent=2)
    
    print(f"\n💾 Summary saved to: {summary_file}")
    print(f"📊 Detailed results in: benchmark/results/")

if __name__ == "__main__":
    main()