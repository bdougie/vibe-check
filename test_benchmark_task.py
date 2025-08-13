#!/usr/bin/env python3
"""
Test script to check for the ImportError in benchmark_task.py
"""

from datetime import datetime
import json
from pathlib import Path


def test_complete_benchmark():
    """Test the complete_benchmark function to check for ImportError"""

    # Create a test session file
    session_data = {
        "model": "test_model",
        "task": "test_task",
        "task_path": "benchmark/tasks/easy/fix_typo.md",
        "start_time": datetime.now().isoformat(),
        "status": "in_progress",
    }

    session_file = Path(".benchmark_session_test.json")
    with open(session_file, "w") as f:
        json.dump(session_data, f, indent=2)

    print(f"Created test session: {session_file}")

    try:
        # Test the complete_benchmark function
        # We'll simulate the function without user input

        # Load session data (mimicking complete_benchmark function)
        with open(session_file, "r") as f:
            session_data = json.load(f)

        print(f"Loaded session data: {session_data}")

        # Create metrics object
        from benchmark.metrics import BenchmarkMetrics

        metrics = BenchmarkMetrics(session_data["model"], session_data["task"])

        # Set some test data
        metrics.metrics["prompts_sent"] = 5
        metrics.metrics["human_interventions"] = 2
        metrics.metrics["task_completed"] = True

        # Calculate elapsed time
        start_time = datetime.fromisoformat(session_data["start_time"])
        elapsed = (datetime.now() - start_time).total_seconds()
        metrics.metrics["completion_time"] = elapsed

        # This is the line that should cause the issue (line 173 equivalent)
        result_file = metrics.complete_task(True)

        print(f"✅ complete_task returned: {result_file}")
        print(f"✅ Type: {type(result_file)}")

        # Test printing it (line 180 equivalent)
        print(f"✅ Results saved to: {result_file}")

        # Clean up
        session_file.unlink()
        if result_file.exists():
            result_file.unlink()

        print("✅ Test completed successfully - no ImportError found!")

    except Exception as e:
        print(f"❌ Error found: {e}")
        print(f"❌ Error type: {type(e)}")
        # Clean up on error
        if session_file.exists():
            session_file.unlink()
        raise


if __name__ == "__main__":
    test_complete_benchmark()
