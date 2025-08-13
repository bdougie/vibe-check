#!/usr/bin/env python3
"""
Test suite for benchmark/task_runner.py
"""

import os
from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "benchmark"))

from benchmark.task_runner import (
    list_available_tasks,
    run_benchmark_task,
)


class TestTaskRunner:
    """Test cases for task_runner.py functions"""

    def test_list_available_tasks(self):
        """Test list_available_tasks function"""
        tasks = list_available_tasks()

        # Should return a list
        assert isinstance(tasks, list)

        # Task files should exist in benchmark/tasks
        expected_files = [
            "benchmark/tasks/easy/fix_typo.md",
            "benchmark/tasks/easy/add_gitignore_entry.md",
            "benchmark/tasks/medium/add_validation.md",
        ]

        # Convert tasks to strings for comparison
        task_names = [str(task) for task in tasks]

        # Check that at least some expected files are present
        for expected_file in expected_files:
            assert expected_file in task_names

    # Note: get_git_diff_stats tests removed as the function has been deleted
    # Git tracking is now handled automatically by BenchmarkMetrics class

    @patch("builtins.input")
    @patch("benchmark.task_runner.BenchmarkMetrics")
    def test_run_benchmark_task_success(self, mock_metrics_class, mock_input):
        """Test run_benchmark_task with successful completion"""
        # Mock user inputs - no longer asks about git stats
        mock_input.side_effect = [
            "",  # Press Enter to start
            "y",  # Task completed successfully
            "5",  # Number of prompts
            "2",  # Number of interventions
        ]

        # Mock metrics
        mock_metrics = MagicMock()
        mock_metrics.metrics = {}  # Make metrics a real dict to track assignments
        mock_metrics_class.return_value = mock_metrics
        mock_metrics.complete_task.return_value = Path("test_result.json")

        # Test with existing task file
        task_file = "benchmark/tasks/easy/fix_typo.md"

        run_benchmark_task("test_model", task_file)

        # Verify metrics initialization
        mock_metrics_class.assert_called_once_with("test_model", "fix_typo")
        mock_metrics.start_task.assert_called_once()

        # Verify metrics were set
        assert mock_metrics.metrics["prompts_sent"] == 5
        assert mock_metrics.metrics["human_interventions"] == 2

        # Git stats are now captured automatically in complete_task, not manually

        # Verify task completion
        mock_metrics.complete_task.assert_called_once_with(True)

    @patch("builtins.input")
    @patch("benchmark.task_runner.BenchmarkMetrics")
    def test_run_benchmark_task_failure(self, mock_metrics_class, mock_input):
        """Test run_benchmark_task with task failure"""
        # Mock user inputs - no longer asks about git stats
        mock_input.side_effect = [
            "",  # Press Enter to start
            "n",  # Task failed
            "3",  # Number of prompts
            "5",  # Number of interventions
        ]

        # Mock metrics
        mock_metrics = MagicMock()
        mock_metrics.metrics = {}  # Make metrics a real dict to track assignments
        mock_metrics_class.return_value = mock_metrics
        mock_metrics.complete_task.return_value = Path("test_result.json")

        task_file = "benchmark/tasks/easy/fix_typo.md"

        run_benchmark_task("test_model", task_file)

        # Verify task completion with failure
        mock_metrics.complete_task.assert_called_once_with(False)

        # Files modified is now captured automatically by complete_task

    def test_run_benchmark_task_missing_file(self):
        """Test run_benchmark_task with missing task file"""
        with pytest.raises(SystemExit):
            run_benchmark_task("test_model", "nonexistent_task.md")

    @patch("builtins.input")
    @patch("benchmark.task_runner.BenchmarkMetrics")
    def test_run_benchmark_task_git_changes_rejected(
        self, mock_metrics_class, mock_input
    ):
        """Test run_benchmark_task with automatic git tracking"""
        # Mock user inputs - git stats no longer asked
        mock_input.side_effect = [
            "",  # Press Enter to start
            "y",  # Task completed successfully
            "4",  # Number of prompts
            "1",  # Number of interventions
        ]

        # Mock metrics
        mock_metrics = MagicMock()
        mock_metrics.metrics = {
            "files_modified": 3,
            "lines_added": 15,
            "lines_removed": 7,
        }  # Simulating automatic capture
        mock_metrics_class.return_value = mock_metrics
        mock_metrics.complete_task.return_value = Path("test_result.json")

        task_file = "benchmark/tasks/easy/fix_typo.md"

        run_benchmark_task("test_model", task_file)

        # Verify metrics were set
        assert mock_metrics.metrics["prompts_sent"] == 4
        assert mock_metrics.metrics["human_interventions"] == 1

        # Git stats are now captured automatically by complete_task
        mock_metrics.complete_task.assert_called_once_with(True)

    @patch("builtins.input")
    @patch("benchmark.task_runner.BenchmarkMetrics")
    def test_run_benchmark_task_default_values(self, mock_metrics_class, mock_input):
        """Test run_benchmark_task with default values for empty inputs"""
        # Mock user inputs with empty strings (should use defaults)
        mock_input.side_effect = [
            "",  # Press Enter to start
            "y",  # Task completed successfully
            "",  # Empty prompts (should default to 0)
            "",  # Empty interventions (should default to 0)
        ]

        # Mock metrics
        mock_metrics = MagicMock()
        mock_metrics.metrics = {}  # Make metrics a real dict to track assignments
        mock_metrics_class.return_value = mock_metrics
        mock_metrics.complete_task.return_value = Path("test_result.json")

        task_file = "benchmark/tasks/easy/fix_typo.md"

        run_benchmark_task("test_model", task_file)

        # Verify default values were used
        assert mock_metrics.metrics["prompts_sent"] == 0
        assert mock_metrics.metrics["human_interventions"] == 0
        # Files modified is captured automatically by complete_task, not manually set


@pytest.mark.integration
class TestTaskRunnerIntegration:
    """Integration tests for task_runner.py"""

    def test_task_files_exist(self):
        """Test that all expected task files actually exist"""
        tasks = list_available_tasks()

        for task_path in tasks:
            assert Path(task_path).exists(), f"Task file missing: {task_path}"

            # Verify file content
            with open(task_path, "r") as f:
                content = f.read()
                assert len(content) > 0, f"Task file is empty: {task_path}"
                assert "# Task:" in content, f"Task file missing header: {task_path}"
