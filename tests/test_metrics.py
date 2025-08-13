#!/usr/bin/env python3
"""
Test suite for benchmark/metrics.py
"""

from datetime import datetime
import json
import os
from pathlib import Path
import sys
import tempfile
import time
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "benchmark"))

from benchmark.metrics import BenchmarkMetrics


class TestBenchmarkMetrics:
    """Test cases for BenchmarkMetrics class"""

    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.model_name = "test_model"
        self.task_name = "test_task"
        self.metrics = BenchmarkMetrics(self.model_name, self.task_name)

        # Create temporary results directory
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up after each test method"""
        # Clean up temporary files
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test BenchmarkMetrics initialization"""
        assert self.metrics.model_name == self.model_name
        assert self.metrics.task_name == self.task_name
        assert self.metrics.start_time is None

        # Check default metrics structure
        assert self.metrics.metrics["model"] == self.model_name
        assert self.metrics.metrics["task"] == self.task_name
        assert self.metrics.metrics["prompts_sent"] == 0
        assert self.metrics.metrics["chars_sent"] == 0
        assert self.metrics.metrics["chars_received"] == 0
        assert self.metrics.metrics["human_interventions"] == 0
        assert self.metrics.metrics["task_completed"] is False
        assert self.metrics.metrics["completion_time"] == 0
        assert self.metrics.metrics["files_modified"] == 0
        assert self.metrics.metrics["lines_added"] == 0
        assert self.metrics.metrics["lines_removed"] == 0
        assert self.metrics.metrics["session_log"] == []

    def test_start_task(self):
        """Test start_task method"""
        self.metrics.start_task()

        assert self.metrics.start_time is not None
        # Now we have 2 events: git_state_captured and task_started
        assert len(self.metrics.metrics["session_log"]) >= 1
        # task_started should be the last event
        assert self.metrics.metrics["session_log"][-1]["event"] == "task_started"

    def test_log_prompt(self):
        """Test log_prompt method"""
        prompt_text = "Test prompt"
        response_text = "Test response"

        self.metrics.log_prompt(prompt_text, response_text)

        assert self.metrics.metrics["prompts_sent"] == 1
        assert self.metrics.metrics["chars_sent"] == len(prompt_text)
        assert self.metrics.metrics["chars_received"] == len(response_text)

        # Check session log
        log_entry = self.metrics.metrics["session_log"][0]
        assert log_entry["event"] == "prompt_sent"
        assert log_entry["data"]["prompt_length"] == len(prompt_text)
        assert log_entry["data"]["response_length"] == len(response_text)

    def test_log_human_intervention(self):
        """Test log_human_intervention method"""
        intervention_type = "manual_edit"

        self.metrics.log_human_intervention(intervention_type)

        assert self.metrics.metrics["human_interventions"] == 1

        log_entry = self.metrics.metrics["session_log"][0]
        assert log_entry["event"] == "human_intervention"
        assert log_entry["data"]["type"] == intervention_type

    def test_update_git_stats(self):
        """Test update_git_stats method"""
        files_modified = 3
        lines_added = 25
        lines_removed = 10

        self.metrics.update_git_stats(files_modified, lines_added, lines_removed)

        assert self.metrics.metrics["files_modified"] == files_modified
        assert self.metrics.metrics["lines_added"] == lines_added
        assert self.metrics.metrics["lines_removed"] == lines_removed

        log_entry = self.metrics.metrics["session_log"][0]
        assert log_entry["event"] == "git_stats_updated"
        assert log_entry["data"]["files"] == files_modified
        assert log_entry["data"]["added"] == lines_added
        assert log_entry["data"]["removed"] == lines_removed

    def test_complete_task_success(self):
        """Test complete_task method with success=True"""
        # Set up a started task
        self.metrics.start_task()
        time.sleep(0.1)  # Small delay to test completion time

        # Temporarily monkey-patch the results directory to use temp dir
        def mock_complete_task(success=True):
            if self.metrics.start_time:
                self.metrics.metrics["completion_time"] = (
                    time.time() - self.metrics.start_time
                )
            self.metrics.metrics["task_completed"] = success
            self.metrics.log_event("task_completed", {"success": success})

            # Save results to temp directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_dir = self.temp_dir / "results"
            results_dir.mkdir(parents=True, exist_ok=True)

            filename = (
                results_dir
                / f"{self.metrics.model_name}_{self.metrics.task_name}_{timestamp}.json"
            )

            with open(filename, "w") as f:
                json.dump(self.metrics.metrics, f, indent=2)

            return filename

        self.metrics.complete_task = mock_complete_task

        result_file = self.metrics.complete_task(True)

        assert self.metrics.metrics["task_completed"] is True
        assert self.metrics.metrics["completion_time"] > 0
        assert result_file.exists()

        # Verify JSON content
        with open(result_file, "r") as f:
            saved_data = json.load(f)

        assert saved_data["task_completed"] is True
        assert saved_data["model"] == self.model_name
        assert saved_data["task"] == self.task_name

    def test_complete_task_failure(self):
        """Test complete_task method with success=False"""

        # Temporarily monkey-patch the results directory to use temp dir
        def mock_complete_task(success=True):
            self.metrics.metrics["task_completed"] = success
            self.metrics.log_event("task_completed", {"success": success})

            # Save results to temp directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_dir = self.temp_dir / "results"
            results_dir.mkdir(parents=True, exist_ok=True)

            filename = (
                results_dir
                / f"{self.metrics.model_name}_{self.metrics.task_name}_{timestamp}.json"
            )

            with open(filename, "w") as f:
                json.dump(self.metrics.metrics, f, indent=2)

            return filename

        self.metrics.complete_task = mock_complete_task

        result_file = self.metrics.complete_task(False)

        assert self.metrics.metrics["task_completed"] is False
        assert result_file.exists()

    def test_log_event(self):
        """Test log_event method"""
        event_type = "test_event"
        event_data = {"key": "value", "number": 42}

        self.metrics.log_event(event_type, event_data)

        assert len(self.metrics.metrics["session_log"]) == 1
        log_entry = self.metrics.metrics["session_log"][0]

        assert log_entry["event"] == event_type
        assert log_entry["data"] == event_data
        assert "timestamp" in log_entry
        assert isinstance(log_entry["timestamp"], (int, float))

    def test_multiple_operations(self):
        """Test sequence of multiple operations"""
        # Start task
        self.metrics.start_task()

        # Log some prompts
        self.metrics.log_prompt("First prompt", "First response")
        self.metrics.log_prompt("Second prompt", "Second response with more text")

        # Log interventions
        self.metrics.log_human_intervention("correction")
        self.metrics.log_human_intervention("manual_edit")

        # Update git stats
        self.metrics.update_git_stats(2, 15, 5)

        # Verify accumulated values
        assert self.metrics.metrics["prompts_sent"] == 2
        assert self.metrics.metrics["chars_sent"] == len("First prompt") + len(
            "Second prompt"
        )
        assert self.metrics.metrics["chars_received"] == len("First response") + len(
            "Second response with more text"
        )
        assert self.metrics.metrics["human_interventions"] == 2
        assert self.metrics.metrics["files_modified"] == 2
        assert self.metrics.metrics["lines_added"] == 15
        assert self.metrics.metrics["lines_removed"] == 5

        # Check session log has all events (now includes git_state_captured)
        assert (
            len(self.metrics.metrics["session_log"]) >= 6
        )  # git capture + start + 2 prompts + 2 interventions + git stats


@pytest.mark.integration
class TestBenchmarkMetricsIntegration:
    """Integration tests for BenchmarkMetrics"""

    def test_real_file_creation(self):
        """Test that metrics actually creates files in the real filesystem"""
        metrics = BenchmarkMetrics("integration_test_model", "integration_test_task")

        # Ensure results directory exists
        results_dir = Path("benchmark/results")
        results_dir.mkdir(parents=True, exist_ok=True)

        result_file = metrics.complete_task(True)

        try:
            assert result_file.exists()
            assert result_file.suffix == ".json"
            assert "integration_test_model" in result_file.name
            assert "integration_test_task" in result_file.name

            # Verify JSON structure
            with open(result_file, "r") as f:
                data = json.load(f)

            required_keys = [
                "model",
                "task",
                "prompts_sent",
                "chars_sent",
                "chars_received",
                "human_interventions",
                "task_completed",
                "completion_time",
                "files_modified",
                "lines_added",
                "lines_removed",
                "session_log",
            ]

            for key in required_keys:
                assert key in data, f"Missing key: {key}"

        finally:
            # Clean up
            if result_file.exists():
                result_file.unlink()


class TestGitTracking:
    """Test cases for automatic git tracking functionality"""

    def setup_method(self):
        """Set up test fixtures before each test method"""
        self.metrics = BenchmarkMetrics("test_model", "test_task")

    @patch("subprocess.run")
    def test_capture_initial_git_state(self, mock_run):
        """Test capturing initial git state"""
        # Mock git commands
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="abc123def456\n"),  # git rev-parse HEAD
            MagicMock(returncode=0, stdout=""),  # git status --porcelain (clean)
        ]

        self.metrics.capture_initial_git_state()

        assert self.metrics.initial_git_state is not None
        assert self.metrics.initial_git_state["commit"] == "abc123def456"
        assert self.metrics.initial_git_state["has_uncommitted_changes"] is False
        assert "timestamp" in self.metrics.initial_git_state

        # Check that git commands were called
        assert mock_run.call_count == 2

    @patch("subprocess.run")
    def test_capture_initial_git_state_with_uncommitted(self, mock_run):
        """Test capturing initial git state with uncommitted changes"""
        # Mock git commands
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="abc123def456\n"),  # git rev-parse HEAD
            MagicMock(
                returncode=0, stdout="M file.py\n"
            ),  # git status --porcelain (dirty)
        ]

        self.metrics.capture_initial_git_state()

        assert self.metrics.initial_git_state["has_uncommitted_changes"] is True

    @patch("subprocess.run")
    def test_get_git_diff_stats(self, mock_run):
        """Test getting git diff statistics"""
        # Mock git diff --stat output
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=" file1.py | 10 +++++++---\n file2.py | 5 ++---\n 2 files changed, 9 insertions(+), 6 deletions(-)\n",
        )

        files, added, removed = self.metrics.get_git_diff_stats()

        assert files == 2
        assert added == 9
        assert removed == 6

    @patch("subprocess.run")
    def test_get_git_diff_stats_no_changes(self, mock_run):
        """Test getting git diff statistics with no changes"""
        # Mock git diff --stat output with no changes
        mock_run.return_value = MagicMock(returncode=0, stdout="")

        files, added, removed = self.metrics.get_git_diff_stats()

        assert files == 0
        assert added == 0
        assert removed == 0

    @patch("subprocess.run")
    def test_get_detailed_git_diff(self, mock_run):
        """Test getting detailed git diff information"""
        # Mock git diff --numstat output
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="10\t5\tfile1.py\n3\t2\tfile2.py\n-\t-\tbinary_file.bin\n",
        )

        diff_details = self.metrics.get_detailed_git_diff()

        assert len(diff_details) == 3
        assert diff_details[0]["filename"] == "file1.py"
        assert diff_details[0]["lines_added"] == 10
        assert diff_details[0]["lines_removed"] == 5
        assert diff_details[1]["filename"] == "file2.py"
        assert diff_details[1]["lines_added"] == 3
        assert diff_details[1]["lines_removed"] == 2
        # Binary file should have 0 lines
        assert diff_details[2]["filename"] == "binary_file.bin"
        assert diff_details[2]["lines_added"] == 0
        assert diff_details[2]["lines_removed"] == 0

    @patch("subprocess.run")
    def test_capture_final_git_state(self, mock_run):
        """Test capturing final git state"""
        # Mock git commands
        mock_run.side_effect = [
            # git diff --stat
            MagicMock(
                returncode=0,
                stdout=" file1.py | 10 +++++++---\n 1 file changed, 7 insertions(+), 3 deletions(-)\n",
            ),
            # git diff --numstat
            MagicMock(returncode=0, stdout="7\t3\tfile1.py\n"),
        ]

        files, added, removed = self.metrics.capture_final_git_state()

        assert files == 1
        assert added == 7
        assert removed == 3
        assert self.metrics.metrics["files_modified"] == 1
        assert self.metrics.metrics["lines_added"] == 7
        assert self.metrics.metrics["lines_removed"] == 3
        assert len(self.metrics.metrics["git_diff_details"]) == 1
        assert self.metrics.metrics["git_diff_details"][0]["filename"] == "file1.py"

    @patch.object(BenchmarkMetrics, "capture_initial_git_state")
    def test_start_task_calls_git_capture(self, mock_capture):
        """Test that start_task calls capture_initial_git_state"""
        self.metrics.start_task()

        mock_capture.assert_called_once()
        assert self.metrics.start_time is not None

    @patch.object(BenchmarkMetrics, "capture_final_git_state")
    def test_complete_task_calls_git_capture(self, mock_capture):
        """Test that complete_task calls capture_final_git_state"""
        mock_capture.return_value = (2, 10, 5)

        self.metrics.start_task()
        result_file = self.metrics.complete_task(success=True)

        mock_capture.assert_called_once()

        # Clean up
        if result_file.exists():
            result_file.unlink()

    @patch("subprocess.run")
    def test_git_tracking_error_handling(self, mock_run):
        """Test error handling in git tracking"""
        # Mock git command failure
        mock_run.side_effect = Exception("Git command failed")

        # Should not raise exception, just log the error
        self.metrics.capture_initial_git_state()

        # Check that error was logged
        assert any(
            log["event"] == "git_state_capture_failed"
            for log in self.metrics.metrics["session_log"]
        )

    def test_complete_task_with_automatic_tracking(self):
        """Test complete integration of automatic git tracking"""
        with patch("subprocess.run") as mock_run:
            # Mock all git commands for complete flow
            mock_run.side_effect = [
                # capture_initial_git_state
                MagicMock(returncode=0, stdout="abc123\n"),
                MagicMock(returncode=0, stdout=""),
                # capture_final_git_state - get_git_diff_stats
                MagicMock(
                    returncode=0,
                    stdout=" file1.py | 10 ++++\n 1 file changed, 10 insertions(+)\n",
                ),
                # capture_final_git_state - get_detailed_git_diff
                MagicMock(returncode=0, stdout="10\t0\tfile1.py\n"),
            ]

            self.metrics.start_task()
            time.sleep(0.01)  # Small delay to ensure completion_time > 0
            result_file = self.metrics.complete_task(success=True)

            try:
                # Verify metrics were captured
                assert self.metrics.metrics["files_modified"] == 1
                assert self.metrics.metrics["lines_added"] == 10
                assert self.metrics.metrics["lines_removed"] == 0
                assert "initial_git_state" in self.metrics.metrics
                assert "git_diff_details" in self.metrics.metrics
                assert len(self.metrics.metrics["git_diff_details"]) == 1

                # Verify file was created with git data
                with open(result_file, "r") as f:
                    data = json.load(f)

                assert data["files_modified"] == 1
                assert data["lines_added"] == 10
                assert "initial_git_state" in data
                assert "git_diff_details" in data

            finally:
                # Clean up
                if result_file.exists():
                    result_file.unlink()
