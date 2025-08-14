#!/usr/bin/env python3
"""
Quick smoke test to verify the benchmark system is working.
This should complete in under 30 seconds.
"""

import json
from pathlib import Path
import subprocess
import sys
import time


def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"🔥 {title}")
    print("=" * 60 + "\n")


def check_dependencies():
    """Check if required dependencies are installed"""
    print_header("CHECKING DEPENDENCIES")

    # Check Python version
    python_version = sys.version_info
    print(
        f"✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}"
    )

    if python_version.major < 3 or (
        python_version.major == 3 and python_version.minor < 7
    ):
        print("❌ Python 3.7+ is required")
        return False

    # Check if sample project exists
    sample_project = Path("sample_project")
    if not sample_project.exists():
        print("❌ Sample project not found")
        print("   Please ensure sample_project directory exists")
        return False
    else:
        print("✅ Sample project found")

    # Check if benchmark module exists
    benchmark_module = Path("benchmark")
    if not benchmark_module.exists():
        print("❌ Benchmark module not found")
        return False
    else:
        print("✅ Benchmark module found")

    # Check if smoke test task exists
    smoke_task = Path("benchmark/tasks/smoke/add_comment.md")
    if not smoke_task.exists():
        print("❌ Smoke test task not found")
        print(f"   Expected at: {smoke_task}")
        return False
    else:
        print("✅ Smoke test task found")

    return True


def run_smoke_test():
    """Run the actual smoke test"""
    print_header("RUNNING SMOKE TEST")

    print("This is a minimal test to verify the benchmark system works.")
    print("The task is to add a simple comment to a Python file.")
    print("\nStarting in 3 seconds...")
    time.sleep(3)

    # Run the smoke test
    cmd = [
        sys.executable,
        "benchmark/task_runner.py",
        "test_model",
        "benchmark/tasks/smoke/add_comment.md",
        "--smoke-test",
        "--skip-ollama-check",
    ]

    print(f"\nCommand: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(cmd, capture_output=False, text=True)

        if result.returncode == 0:
            print("\n✅ Smoke test command executed successfully")
            return True
        else:
            print(f"\n❌ Smoke test failed with exit code: {result.returncode}")
            return False

    except Exception as e:
        print(f"\n❌ Error running smoke test: {e}")
        return False


def verify_results():
    """Check if smoke test results were saved"""
    print_header("VERIFYING RESULTS")

    results_dir = Path("benchmark/results")
    if not results_dir.exists():
        print("⚠️  Results directory doesn't exist yet")
        print("   This is normal for first run")
        return True

    # Look for recent test_model results
    test_results = list(results_dir.glob("test_model_add_comment_*.json"))

    if test_results:
        # Get the most recent result
        latest_result = max(test_results, key=lambda p: p.stat().st_mtime)
        print(f"✅ Found smoke test result: {latest_result.name}")

        # Load and check the result
        with open(latest_result) as f:
            data = json.load(f)

        if data.get("smoke_test"):
            print("✅ Result correctly marked as smoke test")

        if data.get("task_completed"):
            print("✅ Task marked as completed")
        else:
            print("⚠️  Task not marked as completed")

        duration = data.get("duration_seconds", 0)
        if duration > 0:
            print(f"✅ Test duration: {duration:.1f} seconds")
            if duration < 30:
                print("✅ Completed within 30-second target")
            else:
                print("⚠️  Took longer than 30-second target")
    else:
        print("⚠️  No smoke test results found")
        print("   This is expected if you cancelled the test")

    return True


def main():
    """Main smoke test runner"""
    print("\n" + "🔥" * 30)
    print("     VIBE-CHECK SMOKE TEST     ")
    print("🔥" * 30)

    # Step 1: Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed")
        print("Please fix the issues above and try again")
        sys.exit(1)

    # Step 2: Run smoke test
    print("\n" + "-" * 60)
    print("Ready to run smoke test!")
    print("When prompted:")
    print("  1. Press Enter to start the task")
    print("  2. Complete the simple task (add a comment)")
    print("  3. Press Enter when done")
    print("  4. Answer 'y' when asked if successful")
    print("-" * 60)

    input("\nPress Enter to continue...")

    if not run_smoke_test():
        print("\n⚠️  Smoke test encountered an issue")
        print("This might be normal if you cancelled the test")

    # Step 3: Verify results
    verify_results()

    # Final summary
    print_header("SMOKE TEST COMPLETE")
    print("The smoke test has finished!")
    print("\nNext steps:")
    print("  1. If successful, the system is ready for full benchmarks")
    print("  2. Try running a real benchmark with your preferred model")
    print("  3. Use: uv run benchmark/task_runner.py <model> <task_file>")
    print("\nExample:")
    print(
        "  uv run benchmark/task_runner.py 'Claude-3-Sonnet' 'benchmark/tasks/easy/fix_typo.md'"
    )
    print("\n" + "🔥" * 30 + "\n")


if __name__ == "__main__":
    main()
