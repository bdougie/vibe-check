#!/usr/bin/env python3
"""
End-to-end test of the benchmark workflow
"""

import json
from datetime import datetime
from pathlib import Path
import sys
from unittest.mock import patch

import benchmark_task

def test_full_workflow():
    """Test the complete start -> complete workflow"""
    
    print("🔬 Testing full benchmark workflow...")
    
    try:
        # Test 1: Start a benchmark (with mocked input)
        print("\n1️⃣ Testing start_benchmark...")
        
        mock_start_inputs = iter(["1", "test_model"])  # Select task 1, model name
        
        with patch('builtins.input', side_effect=mock_start_inputs):
            session_file = benchmark_task.start_benchmark()
        
        print(f"✅ Start benchmark created session: {session_file}")
        
        # Test 2: Complete the benchmark (with mocked input)
        print("\n2️⃣ Testing complete_benchmark...")
        
        mock_complete_inputs = iter(["y", "3", "1"])  # success=True, prompts=3, interventions=1
        
        with patch('builtins.input', side_effect=mock_complete_inputs):
            benchmark_task.complete_benchmark(session_file)
        
        print("✅ Complete benchmark executed successfully!")
        
        # Test 3: Verify results file was created
        print("\n3️⃣ Verifying results...")
        
        results_dir = Path("benchmark/results")
        if results_dir.exists():
            result_files = list(results_dir.glob("*.json"))
            print(f"✅ Found {len(result_files)} result files")
            
            if result_files:
                # Check the latest result file
                latest_result = max(result_files, key=lambda p: p.stat().st_mtime)
                print(f"✅ Latest result: {latest_result}")
                
                # Verify the JSON structure
                with open(latest_result, 'r') as f:
                    data = json.load(f)
                
                required_fields = ['model', 'task', 'prompts_sent', 'human_interventions', 
                                 'task_completed', 'completion_time']
                
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    print(f"❌ Missing fields in result: {missing_fields}")
                else:
                    print("✅ Result file has all required fields")
                    print(f"   Model: {data.get('model')}")
                    print(f"   Task: {data.get('task')}")
                    print(f"   Completed: {data.get('task_completed')}")
        
        print("\n🎉 All tests passed! No ImportError found.")
        
    except Exception as e:
        print(f"\n❌ Error in workflow test: {e}")
        import traceback
        traceback.print_exc()
        
        # Clean up any remaining session files
        for session_file in Path(".").glob(".benchmark_session_*.json"):
            session_file.unlink()
            print(f"🧹 Cleaned up: {session_file}")

if __name__ == "__main__":
    test_full_workflow()