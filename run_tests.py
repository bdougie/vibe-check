#!/usr/bin/env python3
"""
Simple test runner for vibe-check benchmark framework.
Runs basic smoke tests when pytest is not available.
"""

import sys
from pathlib import Path


def test_file_structure():
    """Test that all required files exist"""
    print("🧪 Testing file structure...")
    required_files = [
        'README.md',
        'setup.md',
        'requirements.txt',
        'pyproject.toml',
        '.gitignore',
        '.github/workflows/ci.yml',
        'benchmark/metrics.py',
        'benchmark/task_runner.py',
        'benchmark_task.py',
        'tests/__init__.py',
        'tests/test_metrics.py',
        'tests/test_benchmark_task.py',
        'tests/test_task_runner.py',
        'tests/test_analyze.py'
    ]

    missing_files = []
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            missing_files.append(file_path)

    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    return True


def test_imports():
    """Test that all modules can be imported"""
    print("🧪 Testing imports...")

    # Test benchmark.metrics import
    try:
        import benchmark.metrics
        print("✅ benchmark.metrics imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import benchmark.metrics: {e}")
        return False

    # Test benchmark_task import
    try:
        import benchmark_task  # noqa: F401
        print("✅ benchmark_task imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import benchmark_task: {e}")
        return False

    # Test benchmark.task_runner import
    try:
        import benchmark.task_runner  # noqa: F401
        print("✅ benchmark.task_runner imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import benchmark.task_runner: {e}")
        return False

    return True


def test_basic_functionality():
    """Test basic functionality of the benchmark framework"""
    print("\n🧪 Testing basic functionality...")

    # Test BenchmarkMetrics creation
    try:
        from benchmark.metrics import BenchmarkMetrics

        metrics = BenchmarkMetrics('test_model', 'test_task')
        print("✅ BenchmarkMetrics created successfully")

        # Test basic operations
        metrics.start_task()
        metrics.log_prompt('test prompt', 'test response')
        metrics.log_human_intervention('test_intervention')
        print("✅ BenchmarkMetrics basic operations work")

        return True
    except Exception as e:
        print(f"❌ BenchmarkMetrics test failed: {e}")
        return False


def test_task_files():
    """Test that task files are properly formatted"""
    print("\n🧪 Testing task files...")

    tasks_dir = Path('benchmark/tasks')
    if not tasks_dir.exists():
        print("❌ Tasks directory doesn't exist")
        return False

    all_valid = True
    for difficulty in ['easy', 'medium', 'hard']:
        task_path = tasks_dir / difficulty
        if not task_path.exists():
            continue

        tasks = list(task_path.glob('*.md'))
        print(f"✅ Found {len(tasks)} {difficulty} tasks")

        for task_file in tasks:
            content = task_file.read_text()

            # Check for required sections
            required_sections = [
                '# Task:',
                '**Difficulty**:',
                '## Requirements',
                '## Expected Outcome',
                '**Time Estimate**:',
                '## Success Criteria'
            ]

            valid = True
            for section in required_sections:
                if section not in content:
                    print(f"❌ {task_file.name} missing section: {section}")
                    valid = False
                    all_valid = False

            if valid:
                print(f"✅ {task_file.name} properly formatted")

    if all_valid:
        print("✅ All 6 tasks are properly formatted")
    return all_valid


def run_all_tests():
    """Run all tests and report results"""
    print("🚀 Running vibe-check test suite...")
    print("=" * 50)

    test_results = []

    # Run each test
    test_results.append(('File Structure', test_file_structure()))
    test_results.append(('Imports', test_imports()))
    test_results.append(('Basic Functionality', test_basic_functionality()))
    test_results.append(('Task Files', test_task_files()))

    print("\n" + "=" * 50)

    # Summary
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)

    if passed == total:
        print(f"✅ All {total} tests passed!")
        return 0
    else:
        print(f"❌ {total - passed}/{total} tests failed")
        print("\n❌ Some tests failed. Fix issues before deploying.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())