# Scripts Directory

This directory contains various utility and runner scripts for the vibe-check benchmark suite.

## Benchmark Runners

### `run_all_benchmarks.py`
Runs all benchmark tasks across all configured models. This is the main entry point for comprehensive benchmark testing.

### `run_smoke_test.py`
Runs a quick smoke test with a simple task to verify the benchmark system is working correctly. Good for testing setup and configuration.

### `run_demo`
Shell script that demonstrates the benchmark system with a sample run. Useful for quick demos and testing.

### `run_hard`
Shell script specifically for running hard difficulty benchmark tasks. Use this when you want to test model performance on complex tasks.

### `benchmark_task.py`
Core benchmark task execution module that handles running individual tasks and collecting results.

## Utility Scripts

### `clear_benchmark_results.sh`
Cleans up benchmark results from the `benchmark/results/` directory and removes the summary CSV file. Run this to free up space or start fresh.

Usage: `./scripts/clear_benchmark_results.sh`

### `setup_wizard.py`
Interactive setup wizard that helps configure the benchmark environment, including:
- Model configuration
- API keys setup
- Continue CLI configuration
- Dependency installation

### `reset_sample_project.py`
Resets the sample project to its original state. Useful after running benchmarks that modify the sample project files.

### `demo_git_tracking.py`
Demonstrates git tracking functionality within the benchmark system. Shows how changes are tracked during task execution.

## Testing

### `run_tests.py`
Main test runner that executes the full test suite. Includes options for coverage reporting and specific test selection.

Usage: `python scripts/run_tests.py [options]`