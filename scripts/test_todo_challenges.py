#!/usr/bin/env python3
"""
Test script for the new todo app challenges.
Validates that the challenge files are properly formatted and can be loaded.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmark.validators import validate_task_file, ValidationError
from benchmark.cn_integration.cn_runner import CNRunner


def test_task_file(task_path: str) -> bool:
    """Test if a task file is valid and can be loaded.
    
    Args:
        task_path: Path to the task file
        
    Returns:
        True if valid, False otherwise
    """
    print(f"\n📋 Testing: {task_path}")
    print("-" * 50)
    
    try:
        # Validate file path
        validated_path = validate_task_file(task_path)
        print(f"✅ File path validated: {validated_path}")
        
        # Load and parse the file
        with open(validated_path, 'r') as f:
            content = f.read()
            
        # Check for required sections
        required_sections = [
            "# Task:",
            "## Requirements",
            "## Expected Outcome",
            "## Success Criteria"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section not in content:
                missing_sections.append(section)
                
        if missing_sections:
            print(f"❌ Missing required sections: {', '.join(missing_sections)}")
            return False
            
        print("✅ All required sections present")
        
        # Try to prepare as CN prompt (if CN runner available)
        try:
            runner = CNRunner()
            prompt = runner._prepare_task_prompt(validated_path)
            print(f"✅ Can be converted to CN prompt")
            print(f"   Prompt preview: {prompt[:100]}...")
        except Exception as e:
            print(f"ℹ️  CN runner not available (optional): {e}")
            
        # Check difficulty level
        if "**Difficulty**:" in content:
            for line in content.split('\n'):
                if "**Difficulty**:" in line:
                    difficulty = line.split("**Difficulty**:")[1].strip()
                    print(f"📊 Difficulty: {difficulty}")
                    break
                    
        # Count success criteria
        criteria_count = content.count("- [ ]")
        print(f"📌 Success criteria items: {criteria_count}")
        
        return True
        
    except ValidationError as e:
        print(f"❌ Validation error: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ File not found: {task_path}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def main():
    """Main test function."""
    print("\n🧪 TODO APP CHALLENGES VALIDATION TEST")
    print("=" * 60)
    
    # Define the new challenge files
    challenges = [
        "benchmark/tasks/medium/basic_todo_app.md",
        "benchmark/tasks/hard/advanced_todo_app.md"
    ]
    
    results = []
    
    for challenge in challenges:
        success = test_task_file(challenge)
        results.append((challenge, success))
        
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for path, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        name = Path(path).stem.replace('_', ' ').title()
        print(f"{status}  {name}")
        
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All todo app challenges are valid and ready to use!")
        print("\n📝 To run these challenges:")
        print("  • Manual: uv run benchmark/task_runner.py <model> <task_file>")
        print("  • Batch: uv run benchmark/batch_runner.py")
        print("  • CN CLI: uv run scripts/run_cn_demo")
    else:
        print("\n⚠️  Some challenges failed validation. Please fix issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()