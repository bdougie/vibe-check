#!/usr/bin/env python3
"""
Test suite for Continue CLI Batch Integration

Tests the CNBatchIntegration class and its batch processing functionality.
"""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from benchmark.cn_integration.cn_batch_integration import CNBatchIntegration


class TestCNBatchIntegration(unittest.TestCase):
    """Test cases for CNBatchIntegration class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Mock the CN components to avoid external dependencies
        with patch('benchmark.cn_integration.cn_batch_integration.CNRunner'), \
             patch('benchmark.cn_integration.cn_batch_integration.CNConfigManager'), \
             patch('benchmark.cn_integration.cn_batch_integration.CNMetricsCollector'):
            
            self.integration = CNBatchIntegration(
                working_dir=self.temp_path,
                verbose=True
            )
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_with_working_dir(self):
        """Test initialization with working directory."""
        with patch('benchmark.cn_integration.cn_batch_integration.CNRunner'), \
             patch('benchmark.cn_integration.cn_batch_integration.CNConfigManager'), \
             patch('benchmark.cn_integration.cn_batch_integration.CNMetricsCollector'):
            
            integration = CNBatchIntegration(working_dir=self.temp_path, verbose=True)
            
            self.assertEqual(integration.working_dir, self.temp_path)
            self.assertTrue(integration.verbose)
    
    def test_convert_cn_result_to_batch_format_success(self):
        """Test conversion of successful CN result to batch format."""
        cn_result = {
            "model_name": "gpt-4",
            "success": True,
            "execution_time": 30.5,
            "timestamp": "2024-01-01T12:00:00",
            "metrics": {
                "prompts_sent": 1,
                "tool_calls": 3,
                "files_modified": 2,
                "lines_added": 10,
                "lines_removed": 5
            },
            "cn_returncode": 0
        }
        
        batch_result = self.integration._convert_cn_result_to_batch_format(
            cn_result, "test_task"
        )
        
        expected = {
            "model": "gpt-4",
            "task": "test_task",
            "success": True,
            "error": None,
            "completion_time": 30.5,
            "prompts_sent": 1,
            "human_interventions": 0,  # Always 0 for CN
            "files_modified": 2,
            "lines_added": 10,
            "lines_removed": 5,
            "timestamp": "2024-01-01T12:00:00",
            "execution_method": "continue_cli",
            "tool_calls": 3,
            "cn_returncode": 0,
            "cn_metrics": cn_result["metrics"]
        }
        
        self.assertEqual(batch_result, expected)
    
    def test_convert_cn_result_to_batch_format_failure(self):
        """Test conversion of failed CN result to batch format."""
        cn_result = {
            "model_name": "gpt-3.5-turbo",
            "success": False,
            "error": "Timeout occurred",
            "execution_time": 600.0,
            "timestamp": "2024-01-01T12:00:00",
            "metrics": {
                "prompts_sent": 1,
                "tool_calls": 0,
                "files_modified": 0,
                "lines_added": 0,
                "lines_removed": 0
            },
            "cn_returncode": 1
        }
        
        batch_result = self.integration._convert_cn_result_to_batch_format(
            cn_result, "failed_task"
        )
        
        self.assertEqual(batch_result["model"], "gpt-3.5-turbo")
        self.assertEqual(batch_result["task"], "failed_task")
        self.assertFalse(batch_result["success"])
        self.assertEqual(batch_result["error"], "Timeout occurred")
        self.assertEqual(batch_result["completion_time"], 600.0)
        self.assertEqual(batch_result["human_interventions"], 0)
        self.assertEqual(batch_result["execution_method"], "continue_cli")
    
    @patch.object(CNBatchIntegration, 'run_cn_task')
    def test_run_cn_task_mocked(self, mock_run_task):
        """Test run_cn_task method with mocking."""
        # Setup mock return value
        expected_result = {
            "model": "gpt-4",
            "task": "test_task",
            "success": True,
            "completion_time": 25.0,
            "execution_method": "continue_cli"
        }
        mock_run_task.return_value = expected_result
        
        # Create a test task file
        task_file = self.temp_path / "test_task.md"
        task_file.write_text("# Task: Test Task")
        
        result = self.integration.run_cn_task(str(task_file), "gpt-4", timeout=60)
        
        self.assertEqual(result, expected_result)
        mock_run_task.assert_called_once_with(str(task_file), "gpt-4", timeout=60)
    
    def test_save_individual_result(self):
        """Test saving individual task result to file."""
        result = {
            "model": "gpt-4",
            "task": "test_task",
            "success": True,
            "completion_time": 30.0,
            "execution_method": "continue_cli"
        }
        
        output_dir = self.temp_path / "results"
        output_dir.mkdir()
        
        self.integration._save_individual_result(result, output_dir)
        
        # Check file was created
        expected_file = output_dir / "gpt-4_test_task_result.json"
        self.assertTrue(expected_file.exists())
        
        # Check file content
        with open(expected_file) as f:
            saved_result = json.load(f)
        
        self.assertEqual(saved_result, result)
    
    def test_save_individual_result_special_chars(self):
        """Test saving result with special characters in model name."""
        result = {
            "model": "ollama/llama2:7b",
            "task": "test_task",
            "success": True
        }
        
        output_dir = self.temp_path / "results"
        output_dir.mkdir()
        
        self.integration._save_individual_result(result, output_dir)
        
        # Special chars should be replaced
        expected_file = output_dir / "ollama_llama2_7b_test_task_result.json"
        self.assertTrue(expected_file.exists())
    
    def test_generate_batch_summary_basic(self):
        """Test batch summary generation."""
        successful_results = [
            {
                "model": "gpt-4",
                "task": "task1", 
                "success": True,
                "completion_time": 20.0,
                "tool_calls": 3
            },
            {
                "model": "gpt-3.5-turbo",
                "task": "task1",
                "success": True, 
                "completion_time": 30.0,
                "tool_calls": 5
            }
        ]
        
        failed_results = [
            {
                "model": "claude-3-haiku",
                "task": "task1",
                "success": False,
                "completion_time": 60.0
            }
        ]
        
        all_results = successful_results + failed_results
        
        summary = self.integration._generate_batch_summary(
            "test_batch_123",
            all_results,
            successful_results,
            failed_results,
            100.0,  # start_time (100 seconds ago)
            ["task1.md"],
            [{"name": "gpt-4"}, {"name": "gpt-3.5-turbo"}, {"name": "claude-3-haiku"}]
        )
        
        # Verify basic structure
        self.assertEqual(summary["batch_id"], "test_batch_123")
        self.assertEqual(summary["execution_method"], "continue_cli")
        self.assertEqual(summary["models_tested"], 3)
        self.assertEqual(summary["total_runs"], 3)
        self.assertEqual(summary["successful"], 2)
        self.assertEqual(summary["failed"], 1)
        self.assertAlmostEqual(summary["success_rate"], 66.67, places=1)
        
        # Verify rankings
        self.assertIn("rankings", summary)
        self.assertEqual(summary["rankings"]["fastest"], "gpt-4")  # 20s vs 30s
        self.assertEqual(summary["rankings"]["most_efficient"], "gpt-4")  # 3 vs 5 tool calls
        
        # Verify summary stats
        self.assertIn("summary_stats", summary)
        stats = summary["summary_stats"]
        self.assertEqual(stats["avg_completion_time"], 25.0)  # (20+30)/2
        self.assertEqual(stats["min_completion_time"], 20.0)
        self.assertEqual(stats["max_completion_time"], 30.0)
        self.assertEqual(stats["avg_tool_calls"], 4.0)  # (3+5)/2
    
    def test_generate_batch_summary_no_successful_results(self):
        """Test batch summary generation when no results are successful."""
        failed_results = [
            {"model": "gpt-4", "task": "task1", "success": False},
            {"model": "claude-3-sonnet", "task": "task1", "success": False}
        ]
        
        summary = self.integration._generate_batch_summary(
            "failed_batch",
            failed_results,
            [],  # No successful results
            failed_results,
            50.0,
            ["task1.md"],
            [{"name": "gpt-4"}, {"name": "claude-3-sonnet"}]
        )
        
        self.assertEqual(summary["successful"], 0)
        self.assertEqual(summary["failed"], 2)
        self.assertEqual(summary["success_rate"], 0.0)
        
        # Rankings should not be present or be None
        rankings = summary.get("rankings")
        if rankings:
            self.assertIsNone(rankings["fastest"])
    
    def test_generate_html_report(self):
        """Test HTML report generation."""
        summary = {
            "batch_id": "test_batch",
            "success_rate": 75.0,
            "successful": 3,
            "total_runs": 4,
            "total_time": 120.0,
            "models_tested": 2,
            "results": [
                {
                    "model": "gpt-4",
                    "task": "task1",
                    "success": True,
                    "completion_time": 30.0,
                    "tool_calls": 3,
                    "files_modified": 1
                },
                {
                    "model": "gpt-3.5-turbo", 
                    "task": "task1",
                    "success": False,
                    "completion_time": 60.0,
                    "tool_calls": 0,
                    "files_modified": 0
                }
            ],
            "rankings": {
                "fastest": "gpt-4",
                "most_efficient": "gpt-4"
            }
        }
        
        html_file = self.temp_path / "test_report.html"
        self.integration._generate_html_report(summary, html_file)
        
        # Check file was created
        self.assertTrue(html_file.exists())
        
        # Check content contains expected elements
        with open(html_file) as f:
            html_content = f.read()
        
        self.assertIn("Continue CLI Batch Benchmark Report", html_content)
        self.assertIn("test_batch", html_content)
        self.assertIn("75.0%", html_content)
        self.assertIn("gpt-4", html_content)
        self.assertIn("✅ Success", html_content)
        self.assertIn("❌ Failed", html_content)
        self.assertIn("Performance Rankings", html_content)
    
    def test_generate_csv_report(self):
        """Test CSV report generation."""
        summary = {
            "results": [
                {
                    "model": "gpt-4",
                    "task": "task1", 
                    "success": True,
                    "completion_time": 30.0,
                    "tool_calls": 3,
                    "files_modified": 1,
                    "lines_added": 10,
                    "lines_removed": 5,
                    "timestamp": "2024-01-01T12:00:00",
                    "execution_method": "continue_cli",
                    "cn_returncode": 0
                }
            ]
        }
        
        csv_file = self.temp_path / "test_report.csv"
        self.integration._generate_csv_report(summary, csv_file)
        
        # Check file was created
        self.assertTrue(csv_file.exists())
        
        # Check CSV content
        import csv
        with open(csv_file, newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["model"], "gpt-4")
        self.assertEqual(row["task"], "task1")
        self.assertEqual(row["success"], "True")
        self.assertEqual(row["completion_time"], "30.0")
        self.assertEqual(row["execution_method"], "continue_cli")
    
    def test_save_batch_summary(self):
        """Test complete batch summary saving."""
        summary = {
            "batch_id": "test_batch",
            "results": [
                {
                    "model": "gpt-4",
                    "task": "task1",
                    "success": True,
                    "completion_time": 30.0,
                    "tool_calls": 3,
                    "files_modified": 1,
                    "lines_added": 10,
                    "lines_removed": 5,
                    "timestamp": "2024-01-01T12:00:00",
                    "execution_method": "continue_cli",
                    "cn_returncode": 0
                }
            ],
            "success_rate": 100.0,
            "successful": 1,
            "total_runs": 1,
            "models_tested": 1,
            "total_time": 30.0
        }
        
        output_dir = self.temp_path / "results"
        output_dir.mkdir()
        
        with patch('builtins.print'):  # Suppress print output in tests
            self.integration._save_batch_summary(summary, output_dir)
        
        # Check all expected files were created
        json_file = output_dir / "cn_batch_summary.json"
        html_file = output_dir / "cn_batch_report.html"
        csv_file = output_dir / "cn_batch_results.csv"
        
        self.assertTrue(json_file.exists())
        self.assertTrue(html_file.exists())
        self.assertTrue(csv_file.exists())
        
        # Verify JSON content
        with open(json_file) as f:
            saved_summary = json.load(f)
        self.assertEqual(saved_summary, summary)
    
    @patch.object(CNBatchIntegration, 'run_cn_task')
    @patch.object(CNBatchIntegration, '_save_batch_summary')
    @patch('builtins.print')
    def test_run_batch_with_cn_basic(self, mock_print, mock_save, mock_run_task):
        """Test basic batch run with CN."""
        # Setup mock responses
        mock_run_task.side_effect = [
            {
                "model": "gpt-4",
                "task": "task1", 
                "success": True,
                "completion_time": 30.0,
                "execution_method": "continue_cli"
            },
            {
                "model": "gpt-3.5-turbo",
                "task": "task1",
                "success": False,
                "error": "Timeout",
                "completion_time": 60.0,
                "execution_method": "continue_cli"
            }
        ]
        
        # Create test task file
        task_file = self.temp_path / "task1.md"
        task_file.write_text("# Task: Test Task")
        
        task_files = [str(task_file)]
        models = [{"name": "gpt-4"}, {"name": "gpt-3.5-turbo"}]
        
        result = self.integration.run_batch_with_cn(
            task_files, models, timeout=60
        )
        
        # Verify result structure
        self.assertIn("batch_id", result)
        self.assertIn("execution_method", result)
        self.assertEqual(result["execution_method"], "continue_cli")
        self.assertEqual(result["models_tested"], 2)
        self.assertEqual(result["total_runs"], 2)
        self.assertEqual(result["successful"], 1)
        self.assertEqual(result["failed"], 1)
        
        # Verify methods were called correctly
        self.assertEqual(mock_run_task.call_count, 2)
        mock_save.assert_called_once()


class TestCNBatchIntegrationEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions for CNBatchIntegration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_empty_task_list(self):
        """Test batch run with empty task list."""
        with patch('benchmark.cn_integration.cn_batch_integration.CNRunner'), \
             patch('benchmark.cn_integration.cn_batch_integration.CNConfigManager'), \
             patch('benchmark.cn_integration.cn_batch_integration.CNMetricsCollector'):
            
            integration = CNBatchIntegration(working_dir=self.temp_path)
            
            with patch('builtins.print'):
                result = integration.run_batch_with_cn(
                    [], [{"name": "gpt-4"}], timeout=60
                )
            
            self.assertEqual(result["total_runs"], 0)
            self.assertEqual(result["successful"], 0)
            self.assertEqual(result["failed"], 0)
    
    def test_empty_models_list(self):
        """Test batch run with empty models list."""
        with patch('benchmark.cn_integration.cn_batch_integration.CNRunner'), \
             patch('benchmark.cn_integration.cn_batch_integration.CNConfigManager'), \
             patch('benchmark.cn_integration.cn_batch_integration.CNMetricsCollector'):
            
            integration = CNBatchIntegration(working_dir=self.temp_path)
            
            task_file = self.temp_path / "task1.md"
            task_file.write_text("# Task: Test")
            
            with patch('builtins.print'):
                result = integration.run_batch_with_cn(
                    [str(task_file)], [], timeout=60
                )
            
            self.assertEqual(result["total_runs"], 0)
            self.assertEqual(result["models_tested"], 0)


if __name__ == "__main__":
    unittest.main()
