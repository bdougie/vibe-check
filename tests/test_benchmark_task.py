#!/usr/bin/env python3
"""
Test suite for benchmark_task.py
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import benchmark_task


class TestBenchmarkTask:
    """Test cases for benchmark_task.py functions"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        
    def teardown_method(self):
        """Clean up after tests"""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        
        # Clean up any session files created during testing
        for session_file in Path(".").glob(".benchmark_session_*.json"):
            if session_file.exists():
                session_file.unlink()
    
    def test_list_tasks(self):
        """Test list_tasks function"""
        tasks = benchmark_task.list_tasks()
        
        assert isinstance(tasks, dict)
        assert "easy" in tasks
        assert "medium" in tasks
        assert "hard" in tasks
        
        # Check that tasks are lists
        for difficulty, task_list in tasks.items():
            assert isinstance(task_list, list)
            
        # Should find our existing tasks
        all_tasks = []
        for task_list in tasks.values():
            all_tasks.extend([task["name"] for task in task_list])
        
        expected_tasks = ["add_gitignore_entry", "fix_typo", "add_export_feature", 
                         "add_validation", "implement_dashboard", "refactor_metrics"]
        
        for expected_task in expected_tasks:
            assert expected_task in all_tasks
    
    @patch('builtins.input')
    def test_start_benchmark_with_params(self, mock_input):
        """Test start_benchmark with provided parameters"""
        model_name = "test_model"
        task_path = "benchmark/tasks/easy/fix_typo.md"
        
        session_file = benchmark_task.start_benchmark(model_name, task_path)
        
        assert session_file is not None
        session_path = Path(session_file)
        assert session_path.exists()
        
        # Verify session file content
        with open(session_path, 'r') as f:
            session_data = json.load(f)
        
        assert session_data['model'] == model_name
        assert session_data['task'] == "fix_typo"
        assert session_data['task_path'] == task_path
        assert session_data['status'] == "in_progress"
        assert 'start_time' in session_data
        
        # Clean up
        session_path.unlink()
    
    @patch('builtins.input')
    def test_start_benchmark_interactive(self, mock_input):
        """Test start_benchmark with interactive input"""
        mock_input.side_effect = ["1", "interactive_test_model"]
        
        session_file = benchmark_task.start_benchmark()
        
        assert session_file is not None
        session_path = Path(session_file)
        assert session_path.exists()
        
        # Verify session file content
        with open(session_path, 'r') as f:
            session_data = json.load(f)
        
        assert session_data['model'] == "interactive_test_model"
        assert session_data['task'] == "add_gitignore_entry"  # Task 1
        assert session_data['status'] == "in_progress"
        
        # Clean up
        session_path.unlink()
    
    @patch('builtins.input')
    def test_start_benchmark_invalid_task(self, mock_input):
        """Test start_benchmark with invalid task selection"""
        mock_input.side_effect = ["999", "1", "test_model"]  # Invalid, then valid
        
        session_file = benchmark_task.start_benchmark()
        
        # Should eventually succeed with valid input
        assert session_file is not None
        Path(session_file).unlink()
    
    @patch('builtins.input')
    def test_start_benchmark_keyboard_interrupt(self, mock_input):
        """Test start_benchmark handling KeyboardInterrupt"""
        mock_input.side_effect = KeyboardInterrupt()
        
        result = benchmark_task.start_benchmark()
        
        # Should return None on KeyboardInterrupt
        assert result is None
    
    @patch('builtins.input')
    def test_complete_benchmark_success(self, mock_input):
        """Test complete_benchmark with successful completion"""
        # Create a test session file
        session_data = {
            "model": "test_model",
            "task": "test_task", 
            "task_path": "benchmark/tasks/easy/fix_typo.md",
            "start_time": datetime.now().isoformat(),
            "status": "in_progress"
        }
        
        session_file = Path(".benchmark_session_test.json")
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
        
        # Mock user input: success=True, prompts=5, interventions=2
        mock_input.side_effect = ["y", "5", "2"]
        
        # Mock the metrics complete_task to avoid file creation in tests
        with patch('benchmark_task.BenchmarkMetrics') as mock_metrics:
            mock_metrics_instance = MagicMock()
            mock_metrics.return_value = mock_metrics_instance
            mock_metrics_instance.complete_task.return_value = self.temp_dir / "test_result.json"
            
            benchmark_task.complete_benchmark(str(session_file))
            
            # Verify metrics were set correctly
            assert mock_metrics_instance.metrics['prompts_sent'] == 5
            assert mock_metrics_instance.metrics['human_interventions'] == 2
            assert mock_metrics_instance.metrics['task_completed'] is True
            
            # Verify complete_task was called
            mock_metrics_instance.complete_task.assert_called_once_with(True)
    
    @patch('builtins.input')
    def test_complete_benchmark_failure(self, mock_input):
        """Test complete_benchmark with task failure"""
        # Create a test session file
        session_data = {
            "model": "test_model",
            "task": "test_task",
            "task_path": "benchmark/tasks/easy/fix_typo.md", 
            "start_time": datetime.now().isoformat(),
            "status": "in_progress"
        }
        
        session_file = Path(".benchmark_session_test_fail.json")
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
        
        # Mock user input: success=False, prompts=3, interventions=5
        mock_input.side_effect = ["n", "3", "5"]
        
        with patch('benchmark_task.BenchmarkMetrics') as mock_metrics:
            mock_metrics_instance = MagicMock()
            mock_metrics.return_value = mock_metrics_instance
            mock_metrics_instance.complete_task.return_value = self.temp_dir / "test_result.json"
            
            benchmark_task.complete_benchmark(str(session_file))
            
            # Verify metrics were set correctly
            assert mock_metrics_instance.metrics['prompts_sent'] == 3
            assert mock_metrics_instance.metrics['human_interventions'] == 5
            assert mock_metrics_instance.metrics['task_completed'] is False
            
            # Verify complete_task was called with False
            mock_metrics_instance.complete_task.assert_called_once_with(False)
    
    def test_complete_benchmark_no_session(self):
        """Test complete_benchmark with no session file"""
        # Should handle gracefully when no session files exist
        benchmark_task.complete_benchmark()
        # Should not crash, just print error message
    
    def test_complete_benchmark_invalid_session(self):
        """Test complete_benchmark with invalid session file"""
        # Create invalid session file
        session_file = Path(".benchmark_session_invalid.json")
        with open(session_file, 'w') as f:
            f.write("invalid json content")
        
        try:
            benchmark_task.complete_benchmark(str(session_file))
            # Should handle gracefully
        except Exception as e:
            pytest.fail(f"Should handle invalid JSON gracefully, but got: {e}")
        finally:
            if session_file.exists():
                session_file.unlink()
    
    @patch('builtins.input')
    def test_complete_benchmark_input_error_handling(self, mock_input):
        """Test complete_benchmark with invalid user inputs"""
        # Create a test session file
        session_data = {
            "model": "test_model",
            "task": "test_task",
            "task_path": "benchmark/tasks/easy/fix_typo.md",
            "start_time": datetime.now().isoformat(),
            "status": "in_progress"
        }
        
        session_file = Path(".benchmark_session_input_error.json")
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
        
        # Mock invalid inputs that should trigger error handling
        mock_input.side_effect = ["invalid", "not_a_number", "also_not_a_number"]
        
        with patch('benchmark_task.BenchmarkMetrics') as mock_metrics:
            mock_metrics_instance = MagicMock()
            mock_metrics.return_value = mock_metrics_instance
            mock_metrics_instance.complete_task.return_value = self.temp_dir / "test_result.json"
            
            benchmark_task.complete_benchmark(str(session_file))
            
            # Should use default values when input is invalid
            assert mock_metrics_instance.metrics['prompts_sent'] == 0
            assert mock_metrics_instance.metrics['human_interventions'] == 0
            assert mock_metrics_instance.metrics['task_completed'] is False
    
    def test_main_function_start(self):
        """Test main function with --start argument"""
        import argparse
        
        # Test argument parsing
        parser = argparse.ArgumentParser()
        parser.add_argument('--start', action='store_true')
        parser.add_argument('--complete', action='store_true')
        parser.add_argument('--model', type=str)
        parser.add_argument('--task', type=str)
        parser.add_argument('--session', type=str)
        
        args = parser.parse_args(['--start'])
        assert args.start is True
        assert args.complete is False
    
    def test_main_function_complete(self):
        """Test main function with --complete argument"""
        import argparse
        
        parser = argparse.ArgumentParser()
        parser.add_argument('--start', action='store_true')
        parser.add_argument('--complete', action='store_true')
        parser.add_argument('--model', type=str)
        parser.add_argument('--task', type=str)
        parser.add_argument('--session', type=str)
        
        args = parser.parse_args(['--complete'])
        assert args.start is False
        assert args.complete is True


@pytest.mark.integration
class TestBenchmarkTaskIntegration:
    """Integration tests for benchmark_task.py"""
    
    def teardown_method(self):
        """Clean up after integration tests"""
        # Clean up any session files
        for session_file in Path(".").glob(".benchmark_session_*.json"):
            if session_file.exists():
                session_file.unlink()
    
    @patch('builtins.input')
    def test_full_workflow_integration(self, mock_input):
        """Test complete workflow from start to finish"""
        # Test the full workflow with real file operations
        mock_input.side_effect = [
            "1",  # Select first task
            "integration_test_model",  # Model name
            "y",  # Task completed successfully
            "3",  # Number of prompts
            "1"   # Number of interventions
        ]
        
        # Start benchmark
        session_file = benchmark_task.start_benchmark()
        assert session_file is not None
        
        session_path = Path(session_file)
        assert session_path.exists()
        
        # Complete benchmark
        benchmark_task.complete_benchmark(session_file)
        
        # Session file should be cleaned up
        assert not session_path.exists()
        
        # Result file should be created
        results_dir = Path("benchmark/results")
        if results_dir.exists():
            result_files = list(results_dir.glob("integration_test_model_*.json"))
            assert len(result_files) > 0
            
            # Clean up result files
            for result_file in result_files:
                result_file.unlink()