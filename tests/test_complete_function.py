#!/usr/bin/env python3
"""
Test the actual complete_benchmark function directly
"""

from datetime import datetime
import json
from pathlib import Path
import sys
from unittest.mock import patch

# Add scripts directory to path to import benchmark_task
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

# Import the module
import benchmark_task


def test_complete_benchmark_function():
    """Test the actual complete_benchmark function with mocked input"""

    # Create a test session file
    session_data = {
        "model": "test_model",
        "task": "test_task",
        "task_path": "benchmark/tasks/easy/fix_typo.md",
        "start_time": datetime.now().isoformat(),
        "status": "in_progress",
    }

    session_file = Path(".benchmark_session_test_direct.json")
    with open(session_file, "w") as f:
        json.dump(session_data, f, indent=2)

    print(f"Created test session: {session_file}")

    try:
        # Mock the input function to provide automated responses
        mock_inputs = iter(["y", "5", "2"])  # success=True, prompts=5, interventions=2

        with patch("builtins.input", side_effect=mock_inputs):
            # Call the actual complete_benchmark function
            benchmark_task.complete_benchmark(str(session_file))

        print("✅ complete_benchmark function executed successfully!")

    except Exception as e:
        print(f"❌ Error in complete_benchmark: {e}")
        print(f"❌ Error type: {type(e)}")
        import traceback

        traceback.print_exc()

    finally:
        # Clean up
        if session_file.exists():
            session_file.unlink()


if __name__ == "__main__":
    test_complete_benchmark_function()
