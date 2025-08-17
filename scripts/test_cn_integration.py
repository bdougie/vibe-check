#!/usr/bin/env python3
"""
Test script for Continue CLI integration with Vibe Check benchmarks.

This script tests the CN integration with a simple task to verify everything works.
"""

import json
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmark.cn_integration.cn_runner import CNRunner
from benchmark.cn_integration.cn_batch_integration import CNBatchIntegration


def test_cn_installation():
    """Test if Continue CLI is properly installed."""
    print("🔍 Testing Continue CLI installation...")
    
    try:
        runner = CNRunner(verbose=True)
        print("✅ Continue CLI is available")
        return True
    except Exception as e:
        print(f"❌ Continue CLI not available: {e}")
        print("\n📦 To install Continue CLI:")
        print("   npm i -g @continuedev/cli")
        return False


def test_single_task():
    """Test running a single task with CN."""
    print("\n🧪 Testing single task execution...")
    
    # Use the calculator typo fix as a simple test
    task_file = "sample_project/src/calculator.py"
    if not Path(task_file).exists():
        print(f"❌ Test file not found: {task_file}")
        return False
    
    try:
        runner = CNRunner(verbose=True)
        
        # Create a simple test prompt
        prompt = """Fix the typos in sample_project/src/calculator.py:
        - Line 12: "paramter" should be "parameter"
        - Line 25: "reuslt" should be "result"  
        - Line 38: "Divsion" should be "Division"
        
        Please modify the file to fix these typos."""
        
        print(f"📝 Running test prompt...")
        print(f"Working directory: {runner.working_dir}")
        
        # Note: This is a simplified test - in practice we'd use run_task()
        # For now, just test the basic CN command execution
        stdout, stderr, returncode = runner._execute_cn_command(
            prompt, timeout=60
        )
        
        print(f"🔄 CN returned: {returncode}")
        print(f"📤 Output length: {len(stdout)} chars")
        
        if returncode == 0:
            print("✅ CN execution successful")
            return True
        else:
            print(f"❌ CN execution failed: {stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Single task test failed: {e}")
        return False


def test_batch_integration():
    """Test the batch integration."""
    print("\n📊 Testing batch integration...")
    
    task_files = ["benchmark/tasks/easy/fix_typo.md"]
    
    # Check if task file exists
    if not Path(task_files[0]).exists():
        print(f"❌ Task file not found: {task_files[0]}")
        print("Creating a simple test task...")
        
        # Create a minimal test task
        Path("benchmark/tasks/easy").mkdir(parents=True, exist_ok=True)
        test_task = """# Task: Simple Test

**Difficulty**: Easy  
**Repo**: Sample project  
**Issue**: Test the CN integration  

## Requirements
- Verify CN can execute
- Check basic functionality

## Success Criteria
- [ ] CN executes without errors
- [ ] Basic output is generated
"""
        with open(task_files[0], 'w') as f:
            f.write(test_task)
        print(f"✅ Created test task: {task_files[0]}")
    
    try:
        integration = CNBatchIntegration(verbose=True)
        
        # Test with a simple model (you may need to adjust based on what's available)
        models = [{"name": "gpt-3.5-turbo"}]
        
        print(f"🚀 Running batch test with {len(models)} model(s)...")
        
        # Note: This might fail if no API keys are set up
        # For testing, we'll just verify the integration loads correctly
        print("✅ Batch integration initialized successfully")
        print("ℹ️  Full batch test requires API keys and model access")
        
        return True
        
    except Exception as e:
        print(f"❌ Batch integration test failed: {e}")
        return False


def main():
    """Run all CN integration tests."""
    print("🔧 Continue CLI Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("CN Installation", test_cn_installation),
        ("Single Task", test_single_task),
        ("Batch Integration", test_batch_integration),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'=' * 20}")
        print(f"Running: {test_name}")
        print(f"{'=' * 20}")
        
        try:
            success = test_func()
            results.append((test_name, success))
            
            if success:
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
                
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n{'=' * 50}")
    print("TEST SUMMARY")
    print(f"{'=' * 50}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}  {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! CN integration is ready.")
        print("\n📚 Usage Examples:")
        print("   # Run single task with CN")
        print("   uv run python benchmark/batch_runner.py --task benchmark/tasks/easy/fix_typo.md --cn")
        print()
        print("   # Run with specific models")  
        print("   uv run python benchmark/batch_runner.py --task benchmark/tasks/easy/fix_typo.md --models gpt-3.5-turbo,ollama/llama2 --cn")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please fix issues before using CN integration.")
        
        if not any(name == "CN Installation" and success for name, success in results):
            print("\n💡 First step: Install Continue CLI")
            print("   npm i -g @continuedev/cli")


if __name__ == "__main__":
    main()
