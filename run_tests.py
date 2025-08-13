#!/usr/bin/env python3
"""
Simple test runner to verify test setup without installing dependencies
"""

import sys
import os
import traceback
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "benchmark"))

def test_imports():
    """Test that all modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import benchmark.metrics
        print("✅ benchmark.metrics imported successfully")
    except Exception as e:
        print(f"❌ Failed to import benchmark.metrics: {e}")
        return False
    
    try:
        import benchmark_task
        print("✅ benchmark_task imported successfully")
    except Exception as e:
        print(f"❌ Failed to import benchmark_task: {e}")
        return False
    
    try:
        import benchmark.task_runner
        print("✅ benchmark.task_runner imported successfully")
    except Exception as e:
        print(f"❌ Failed to import benchmark.task_runner: {e}")
        return False
    
    return True

def test_basic_functionality():
    """Test basic functionality of core components"""
    print("\n🧪 Testing basic functionality...")
    
    try:
        from benchmark.metrics import BenchmarkMetrics
        
        # Test metrics creation
        metrics = BenchmarkMetrics("test_model", "test_task")
        print("✅ BenchmarkMetrics created successfully")
        
        # Test basic operations
        metrics.start_task()
        metrics.log_prompt("test prompt", "test response")
        metrics.log_human_intervention("test")
        metrics.update_git_stats(1, 5, 2)
        print("✅ BenchmarkMetrics basic operations work")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        traceback.print_exc()
        return False

def test_task_files():
    """Test that task files exist and are properly formatted"""
    print("\n🧪 Testing task files...")
    
    tasks_dir = Path("benchmark/tasks")
    if not tasks_dir.exists():
        print("❌ Tasks directory does not exist")
        return False
    
    total_tasks = 0
    
    for difficulty in ["easy", "medium", "hard"]:
        difficulty_dir = tasks_dir / difficulty
        if not difficulty_dir.exists():
            print(f"❌ {difficulty} tasks directory missing")
            continue
            
        tasks = list(difficulty_dir.glob("*.md"))
        total_tasks += len(tasks)
        print(f"✅ Found {len(tasks)} {difficulty} tasks")
        
        # Check task format
        for task_file in tasks:
            try:
                content = task_file.read_text()
                required_sections = [
                    "# Task:",
                    "**Difficulty**:",
                    "## Requirements", 
                    "## Expected Outcome",
                    "**Time Estimate**:",
                    "## Success Criteria"
                ]
                
                for section in required_sections:
                    if section not in content:
                        print(f"❌ {task_file.name} missing section: {section}")
                        return False
                        
                print(f"✅ {task_file.name} properly formatted")
                
            except Exception as e:
                print(f"❌ Error reading {task_file}: {e}")
                return False
    
    if total_tasks < 6:
        print(f"❌ Expected at least 6 tasks, found {total_tasks}")
        return False
        
    print(f"✅ All {total_tasks} tasks are properly formatted")
    return True

def test_file_structure():
    """Test that all required files exist"""
    print("\n🧪 Testing file structure...")
    
    required_files = [
        "README.md",
        "setup.md", 
        "requirements.txt",
        "pyproject.toml",
        ".gitignore",
        ".github/workflows/ci.yml",
        "benchmark/metrics.py",
        "benchmark/task_runner.py",
        "benchmark_task.py",
        "tests/__init__.py",
        "tests/test_metrics.py",
        "tests/test_benchmark_task.py",
        "tests/test_task_runner.py",
        "tests/test_analyze.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path} exists")
    
    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        return False
    
    print("✅ All required files exist")
    return True

def main():
    """Run all tests"""
    print("🚀 Running vibe-check test suite...")
    print("=" * 50)
    
    all_passed = True
    
    # Run all test categories
    tests = [
        test_file_structure,
        test_imports, 
        test_basic_functionality,
        test_task_files
    ]
    
    for test_func in tests:
        try:
            if not test_func():
                all_passed = False
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
            traceback.print_exc()
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! Setup is ready for GitHub CI.")
        print("\n📋 Next steps:")
        print("1. Commit and push to trigger GitHub CI")
        print("2. Check that CI passes with 80%+ test coverage")
        print("3. Set up Codecov for coverage reporting")
        return 0
    else:
        print("❌ Some tests failed. Fix issues before deploying.")
        return 1

if __name__ == "__main__":
    sys.exit(main())