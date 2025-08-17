#!/usr/bin/env python3
"""
Test suite for Continue CLI Metrics Collector

Tests the CNMetricsCollector class and its metrics analysis functionality.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from benchmark.cn_integration.cn_metrics import CNMetricsCollector


class TestCNMetricsCollector(unittest.TestCase):
    """Test cases for CNMetricsCollector class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        self.metrics_collector = CNMetricsCollector(working_dir=self.temp_path)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_with_working_dir(self):
        """Test initialization with working directory."""
        collector = CNMetricsCollector(working_dir=self.temp_path)
        self.assertEqual(collector.working_dir, self.temp_path)
    
    def test_init_without_working_dir(self):
        """Test initialization without working directory."""
        collector = CNMetricsCollector()
        self.assertEqual(collector.working_dir, Path.cwd())
    
    @patch('subprocess.run')
    def test_get_git_stats_success(self, mock_run):
        """Test successful git statistics collection."""
        # Mock git commands
        def git_side_effect(cmd, **kwargs):
            if "rev-parse --git-dir" in " ".join(cmd):
                return Mock(returncode=0, stdout=".git\n")
            elif "diff --name-only" in " ".join(cmd):
                return Mock(returncode=0, stdout="file1.py\nfile2.py\n")
            elif "diff --numstat" in " ".join(cmd):
                return Mock(returncode=0, stdout="10\t5\tfile1.py\n3\t2\tfile2.py\n")
            return Mock(returncode=0, stdout="")
        
        mock_run.side_effect = git_side_effect
        
        stats = self.metrics_collector.get_git_stats()
        
        self.assertTrue(stats["git_available"])
        self.assertEqual(stats["files_modified"], 2)
        self.assertEqual(stats["lines_added"], 13)  # 10 + 3
        self.assertEqual(stats["lines_removed"], 7)  # 5 + 2
        self.assertEqual(stats["modified_files"], ["file1.py", "file2.py"])
    
    @patch('subprocess.run')
    def test_get_git_stats_not_git_repo(self, mock_run):
        """Test git stats when not in a git repository."""
        mock_run.return_value = Mock(returncode=1, stdout="", stderr="not a git repository")
        
        stats = self.metrics_collector.get_git_stats()
        
        self.assertFalse(stats["git_available"])
        self.assertEqual(stats["files_modified"], 0)
        self.assertEqual(stats["lines_added"], 0)
        self.assertEqual(stats["lines_removed"], 0)
    
    @patch('subprocess.run')
    def test_get_git_stats_no_changes(self, mock_run):
        """Test git stats when no changes exist."""
        def git_side_effect(cmd, **kwargs):
            if "rev-parse --git-dir" in " ".join(cmd):
                return Mock(returncode=0, stdout=".git\n")
            else:
                return Mock(returncode=0, stdout="")
        
        mock_run.side_effect = git_side_effect
        
        stats = self.metrics_collector.get_git_stats()
        
        self.assertTrue(stats["git_available"])
        self.assertEqual(stats["files_modified"], 0)
        self.assertEqual(stats["lines_added"], 0)
        self.assertEqual(stats["lines_removed"], 0)
        self.assertEqual(stats["modified_files"], [])
    
    @patch('subprocess.run')
    def test_get_git_stats_exception(self, mock_run):
        """Test git stats when subprocess raises exception."""
        mock_run.side_effect = Exception("Command failed")
        
        stats = self.metrics_collector.get_git_stats()
        
        self.assertFalse(stats["git_available"])
        self.assertEqual(stats["files_modified"], 0)
        self.assertIn("error", stats)
    
    def test_analyze_cn_output_basic(self):
        """Test basic CN output analysis."""
        stdout = """
        Reading file: test.py
        Writing to file: test.py
        Task completed successfully
        """
        stderr = ""
        
        metrics = self.metrics_collector.analyze_cn_output(stdout, stderr)
        
        self.assertGreater(metrics["files_read"], 0)
        self.assertGreater(metrics["files_written"], 0)
        self.assertGreater(metrics["success_indicators"], 0)
        self.assertGreater(metrics["tool_calls"], 0)
        self.assertTrue(metrics["likely_success"])
        self.assertGreater(metrics["success_score"], 0)
    
    def test_analyze_cn_output_with_errors(self):
        """Test CN output analysis with errors."""
        stdout = "Error: File not found\nFailed to complete task"
        stderr = "Warning: Deprecated function used"
        
        metrics = self.metrics_collector.analyze_cn_output(stdout, stderr)
        
        self.assertGreater(metrics["errors_detected"], 0)
        self.assertLessEqual(metrics["success_score"], 0)
        self.assertFalse(metrics["likely_success"])
    
    def test_analyze_cn_output_with_bash_commands(self):
        """Test CN output analysis with bash commands."""
        stdout = """
        Running command: ls -la
        Executing: grep pattern file.txt
        Command: git status
        """
        stderr = ""
        
        metrics = self.metrics_collector.analyze_cn_output(stdout, stderr)
        
        self.assertGreaterEqual(metrics["bash_commands"], 3)
        self.assertGreater(metrics["tool_calls"], 0)
        self.assertIn("bash_commands_details", metrics)
    
    def test_analyze_cn_output_detailed_extraction(self):
        """Test detailed extraction of CN output elements."""
        stdout = """
        Reading file: src/main.py
        Reading file: tests/test_main.py
        Writing to file: src/main.py
        Modified file: src/utils.py
        Running command: python -m pytest
        Successfully fixed all typos
        Task completed
        """
        stderr = ""
        
        metrics = self.metrics_collector.analyze_cn_output(stdout, stderr)
        
        # Check detailed extractions
        self.assertEqual(metrics["files_read"], 2)
        self.assertEqual(metrics["files_written"], 2)  # Writing + Modified
        self.assertEqual(metrics["bash_commands"], 2)  # "Running command" and "Command:"
        self.assertEqual(metrics["success_indicators"], 3)  # "Successfully", "completed", "Task completed"
        
        # Check details are captured
        self.assertIn("files_read_details", metrics)
        self.assertIn("files_written_details", metrics)
        self.assertIn("bash_commands_details", metrics)
        self.assertIn("success_indicators_details", metrics)
    
    def test_extract_requirements_basic(self):
        """Test extraction of requirements from task markdown."""
        task_content = """# Task: Test Task

## Requirements
- Fix typo in file
- Ensure no formatting issues
- Test the changes

## Other Section
- Not a requirement
"""
        
        requirements = self.metrics_collector._extract_requirements(task_content)
        
        expected = [
            "Fix typo in file",
            "Ensure no formatting issues", 
            "Test the changes"
        ]
        self.assertEqual(requirements, expected)
    
    def test_extract_requirements_no_section(self):
        """Test requirements extraction when no requirements section exists."""
        task_content = """# Task: Test Task

## Description
This is just a description.
"""
        
        requirements = self.metrics_collector._extract_requirements(task_content)
        self.assertEqual(requirements, [])
    
    def test_extract_success_criteria_basic(self):
        """Test extraction of success criteria from task markdown."""
        task_content = """# Task: Test Task

## Success Criteria
- [ ] Typo is fixed
- [ ] Tests pass
- [ ] Code is formatted

## Other Section
- Not a criteria
"""
        
        criteria = self.metrics_collector._extract_success_criteria(task_content)
        
        expected = [
            "Typo is fixed",
            "Tests pass",
            "Code is formatted"
        ]
        self.assertEqual(criteria, expected)
    
    def test_extract_success_criteria_no_section(self):
        """Test criteria extraction when no success criteria section exists."""
        task_content = """# Task: Test Task

## Requirements
- Do something
"""
        
        criteria = self.metrics_collector._extract_success_criteria(task_content)
        self.assertEqual(criteria, [])
    
    def test_check_requirement_met_positive(self):
        """Test requirement checking with positive indicators."""
        requirement = "Fix typo in calculator file"
        cn_output = "Successfully fixed typo in calculator.py. The file has been updated."
        
        met = self.metrics_collector._check_requirement_met(requirement, cn_output)
        self.assertTrue(met)
    
    def test_check_requirement_met_negative(self):
        """Test requirement checking with no indicators."""
        requirement = "Fix typo in calculator file"
        cn_output = "Analyzed the codebase structure. Found several files."
        
        met = self.metrics_collector._check_requirement_met(requirement, cn_output)
        self.assertFalse(met)
    
    def test_check_requirement_met_partial_match(self):
        """Test requirement checking with partial keyword matches."""
        requirement = "Update documentation"
        cn_output = "Modified documentation files. Updated README with new instructions."
        
        met = self.metrics_collector._check_requirement_met(requirement, cn_output)
        self.assertTrue(met)
    
    def test_analyze_task_completion_full_task(self):
        """Test task completion analysis with full task file."""
        # Create a test task file
        task_content = """# Task: Fix Calculator Typos

## Requirements
- Fix paramter to parameter
- Fix reuslt to result
- Ensure no syntax errors

## Success Criteria
- [ ] All typos fixed
- [ ] Code runs without errors
- [ ] File is saved properly
"""
        
        task_file = self.temp_path / "test_task.md"
        with open(task_file, 'w') as f:
            f.write(task_content)
        
        cn_output = """
        Reading file: calculator.py
        Fixed paramter to parameter in docstring
        Fixed reuslt to result in variable name
        Writing to file: calculator.py
        Successfully completed all fixes
        Task completed without errors
        """
        
        analysis = self.metrics_collector.analyze_task_completion(str(task_file), cn_output)
        
        self.assertEqual(analysis["total_requirements"], 3)
        self.assertEqual(analysis["total_success_criteria"], 3)
        self.assertGreater(analysis["requirements_met"], 0)
        self.assertGreater(analysis["criteria_met"], 0)
        self.assertGreater(analysis["completion_percentage"], 0)
        self.assertIn("requirements_analysis", analysis)
        self.assertIn("criteria_analysis", analysis)
    
    def test_analyze_task_completion_file_not_found(self):
        """Test task completion analysis when task file doesn't exist."""
        analysis = self.metrics_collector.analyze_task_completion("nonexistent.md", "output")
        self.assertIn("error", analysis)
    
    def test_calculate_performance_score_perfect(self):
        """Test performance score calculation with perfect metrics."""
        execution_time = 10.0  # Fast
        git_stats = {"files_modified": 1}
        output_metrics = {
            "tool_calls": 2,  # Efficient
            "errors_detected": 0,  # No errors
            "success_indicators": 3  # Multiple success indicators
        }
        completion_analysis = {"completion_percentage": 100}  # Perfect completion
        
        score = self.metrics_collector._calculate_performance_score(
            execution_time, git_stats, output_metrics, completion_analysis
        )
        
        self.assertGreaterEqual(score, 80)  # Should be high score
        self.assertLessEqual(score, 100)
    
    def test_calculate_performance_score_poor(self):
        """Test performance score calculation with poor metrics."""
        execution_time = 300.0  # Very slow
        git_stats = {"files_modified": 0}
        output_metrics = {
            "tool_calls": 20,  # Inefficient
            "errors_detected": 5,  # Many errors
            "success_indicators": 0  # No success
        }
        completion_analysis = {"completion_percentage": 10}  # Poor completion
        
        score = self.metrics_collector._calculate_performance_score(
            execution_time, git_stats, output_metrics, completion_analysis
        )
        
        self.assertLessEqual(score, 30)  # Should be low score
        self.assertGreaterEqual(score, 0)
    
    def test_calculate_performance_score_balanced(self):
        """Test performance score calculation with balanced metrics."""
        execution_time = 60.0  # Moderate speed
        git_stats = {"files_modified": 2}
        output_metrics = {
            "tool_calls": 5,  # Moderate efficiency
            "errors_detected": 1,  # Few errors
            "success_indicators": 2  # Some success
        }
        completion_analysis = {"completion_percentage": 75}  # Good completion
        
        score = self.metrics_collector._calculate_performance_score(
            execution_time, git_stats, output_metrics, completion_analysis
        )
        
        self.assertGreaterEqual(score, 40)  # Should be moderate score
        self.assertLessEqual(score, 80)
    
    @patch.object(CNMetricsCollector, 'get_git_stats')
    @patch.object(CNMetricsCollector, 'analyze_cn_output')
    @patch.object(CNMetricsCollector, 'analyze_task_completion')
    def test_generate_comprehensive_metrics(self, mock_completion, mock_output, mock_git):
        """Test comprehensive metrics generation."""
        # Setup mocks
        mock_git.return_value = {
            "files_modified": 2,
            "lines_added": 10,
            "lines_removed": 5
        }
        mock_output.return_value = {
            "tool_calls": 3,
            "success_indicators": 2,
            "errors_detected": 0,
            "likely_success": True
        }
        mock_completion.return_value = {
            "completion_percentage": 85,
            "requirements_met": 3,
            "total_requirements": 3
        }
        
        # Create test task file
        task_file = self.temp_path / "test_task.md"
        task_file.write_text("# Task: Test")
        
        # Generate metrics
        metrics = self.metrics_collector.generate_comprehensive_metrics(
            str(task_file), "gpt-4", "cn output", "", 30.0, True
        )
        
        # Verify structure
        self.assertIn("timestamp", metrics)
        self.assertIn("task_file", metrics)
        self.assertIn("model_name", metrics)
        self.assertIn("execution_time", metrics)
        self.assertIn("git", metrics)
        self.assertIn("output_analysis", metrics)
        self.assertIn("completion_analysis", metrics)
        self.assertIn("summary", metrics)
        
        # Verify summary
        summary = metrics["summary"]
        self.assertEqual(summary["files_changed"], 2)
        self.assertEqual(summary["total_tool_calls"], 3)
        self.assertEqual(summary["completion_rate"], 85)
        self.assertTrue(summary["likely_success"])
        self.assertIn("performance_score", summary)
    
    def test_capture_initial_state(self):
        """Test capturing initial state."""
        with patch.object(self.metrics_collector, 'get_git_stats') as mock_git:
            mock_git.return_value = {"files_modified": 0}
            
            self.metrics_collector.capture_initial_state()
            
            self.assertIsNotNone(self.metrics_collector.initial_git_state)
            mock_git.assert_called_once()


if __name__ == "__main__":
    unittest.main()
