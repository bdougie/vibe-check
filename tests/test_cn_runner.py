#!/usr/bin/env python3
"""
Fixed test suite for Continue CLI Runner
"""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch


class TestCNRunner(unittest.TestCase):
    """Test cases for CNRunner class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("subprocess.run")
    def test_check_cn_available_success(self, mock_run):
        """Test successful CN availability check."""
        mock_run.return_value = Mock(returncode=0)

        # Import here to avoid double initialization
        from benchmark.cn_integration.cn_runner import CNRunner

        runner = CNRunner(working_dir=self.temp_path)
        self.assertTrue(runner._check_cn_available())

        # Should be called at least once (in __init__ and in _check_cn_available)
        mock_run.assert_called()

    @patch("subprocess.run")
    def test_check_cn_available_failure(self, mock_run):
        """Test CN availability check failure."""
        mock_run.side_effect = FileNotFoundError()

        from benchmark.cn_integration.cn_runner import CNExecutionError, CNRunner

        with self.assertRaises(CNExecutionError):
            CNRunner(working_dir=self.temp_path)

    def test_prepare_task_prompt_basic(self):
        """Test basic task prompt preparation."""
        # Create a test task file
        task_content = """# Task: Fix Typo

**Difficulty**: Easy

## Requirements
- Fix typo in file
- Ensure no formatting issues

## Success Criteria
- [ ] Typo is fixed
- [ ] Code still works
"""

        task_file = self.temp_path / "test_task.md"
        with open(task_file, "w") as f:
            f.write(task_content)

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)

            from benchmark.cn_integration.cn_runner import CNRunner

            runner = CNRunner(working_dir=self.temp_path)

            prompt = runner._prepare_task_prompt(task_file)

            self.assertIn("Task: Fix Typo", prompt)
            self.assertIn("Fix typo in file", prompt)
            self.assertIn("Typo is fixed", prompt)
            self.assertIn("Working directory:", prompt)

    @patch("subprocess.run")
    def test_execute_cn_command_success(self, mock_run):
        """Test successful CN command execution."""
        mock_run.return_value = Mock(
            returncode=0, stdout="Task completed successfully", stderr=""
        )

        from benchmark.cn_integration.cn_runner import CNRunner

        with patch.object(CNRunner, "_check_cn_available", return_value=True):
            runner = CNRunner(working_dir=self.temp_path)

        stdout, stderr, returncode = runner._execute_cn_command(
            "Test prompt", timeout=60
        )

        self.assertEqual(returncode, 0)
        self.assertEqual(stdout, "Task completed successfully")
        self.assertEqual(stderr, "")

    @patch("subprocess.run")
    def test_execute_cn_command_timeout(self, mock_run):
        """Test CN command timeout handling."""
        from subprocess import TimeoutExpired

        from benchmark.cn_integration.cn_runner import CNExecutionError, CNRunner

        mock_run.side_effect = TimeoutExpired("cn", 60)

        with patch.object(CNRunner, "_check_cn_available", return_value=True):
            runner = CNRunner(working_dir=self.temp_path)

        with self.assertRaises(CNExecutionError) as cm:
            runner._execute_cn_command("Test prompt", timeout=60)

        self.assertIn("timed out", str(cm.exception))

    @patch("benchmark.cn_integration.cn_runner.validate_task_file")
    @patch("subprocess.run")
    def test_run_task_success(self, mock_run, mock_validate):
        """Test successful task execution."""
        from benchmark.cn_integration.cn_runner import CNRunner

        # Setup mocks
        task_file = self.temp_path / "test_task.md"
        task_file.write_text("# Task: Test\n## Requirements\n- Do something")

        # Mock validate_task_file to return the path directly
        mock_validate.return_value = task_file

        def mock_run_side_effect(cmd, **kwargs):
            if "cn" in cmd[0] and "--help" in cmd:
                return Mock(returncode=0)
            elif "cn" in cmd[0] and "-p" in cmd:
                return Mock(returncode=0, stdout="Task completed", stderr="")
            elif "git" in cmd[0]:
                if "diff --name-only" in cmd:
                    return Mock(returncode=0, stdout="file.py\n")
                elif "diff --numstat" in cmd:
                    return Mock(returncode=0, stdout="5\t2\tfile.py\n")
                else:
                    return Mock(returncode=0, stdout="")
            return Mock(returncode=0, stdout="", stderr="")

        mock_run.side_effect = mock_run_side_effect

        runner = CNRunner(working_dir=self.temp_path)

        result = runner.run_task(str(task_file), "gpt-3.5-turbo", timeout=60)

        self.assertTrue(result["success"])
        self.assertEqual(result["model_name"], "gpt-3.5-turbo")
        self.assertEqual(result["task_name"], "test_task")
        self.assertIn("metrics", result)
        self.assertIn("execution_time", result)

    @patch("benchmark.cn_integration.cn_runner.validate_task_file")
    @patch("subprocess.run")
    def test_run_task_failure(self, mock_run, mock_validate):
        """Test task execution failure."""
        from benchmark.cn_integration.cn_runner import CNRunner

        task_file = self.temp_path / "test_task.md"
        task_file.write_text("# Task: Test")

        # Mock validate_task_file to return the path directly
        mock_validate.return_value = task_file

        def mock_run_side_effect(cmd, **kwargs):
            if "cn" in cmd[0] and "--help" in cmd:
                return Mock(returncode=0)
            else:
                raise Exception("Command failed")

        mock_run.side_effect = mock_run_side_effect

        runner = CNRunner(working_dir=self.temp_path)

        result = runner.run_task(str(task_file), "gpt-3.5-turbo")

        self.assertFalse(result["success"])
        self.assertIn("error", result)


if __name__ == "__main__":
    unittest.main()
