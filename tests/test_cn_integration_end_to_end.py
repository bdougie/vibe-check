#!/usr/bin/env python3
"""
End-to-end integration tests for Continue CLI integration

These tests verify the complete CN integration workflow from task execution
to metrics collection and reporting.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest


class TestCNIntegrationEndToEnd(unittest.TestCase):
    """End-to-end tests for CN integration."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
        
        # Create a realistic task file
        self.task_content = """# Task: Fix Calculator Typos

**Difficulty**: Easy  
**Repo**: Sample project  
**Issue**: Fix typos in calculator.py  

## Requirements
- Fix "paramter" to "parameter"
- Fix "reuslt" to "result"  
- Fix "Divsion" to "Division"

## Success Criteria
- [ ] All typos are fixed
- [ ] Code runs without errors
- [ ] File is properly saved
"""
        
        self.task_file = self.temp_path / "fix_typos.md"
        with open(self.task_file, 'w') as f:
            f.write(self.task_content)
        
        # Create a sample source file to modify
        self.sample_code = """def add(a, b):
    '''Add two numbers.
    
    Args:
        a: First paramter
        b: Second parameter
    '''
    reuslt = a + b  # Divsion operation
    return reuslt
"""
        
        self.sample_file = self.temp_path / "calculator.py"
        with open(self.sample_file, 'w') as f:
            f.write(self.sample_code)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('benchmark.cn_integration.cn_runner.validate_task_file')
    @patch('subprocess.run')
    def test_complete_workflow_mock(self, mock_run, mock_validate):
        """Test complete CN workflow with mocked subprocess calls."""
        from benchmark.cn_integration.cn_runner import CNRunner
        
        # Mock validate_task_file to return the path directly
        mock_validate.return_value = self.task_file
        
        # Mock CN availability check
        def subprocess_side_effect(cmd, **kwargs):
            cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
            
            if "cn --help" in cmd_str:
                return Mock(returncode=0, stdout="Continue CLI help")
            elif "cn -p" in cmd_str:
                # Mock CN execution with realistic output
                return Mock(
                    returncode=0,
                    stdout="""Reading file: calculator.py
Found typo: paramter -> parameter
Found typo: reuslt -> result  
Found typo: Divsion -> Division
Writing to file: calculator.py
Fixed 3 typos successfully
Task completed""",
                    stderr=""
                )
            elif "git diff --name-only" in cmd_str:
                return Mock(returncode=0, stdout="calculator.py\n")
            elif "git diff --numstat" in cmd_str:
                return Mock(returncode=0, stdout="3\t3\tcalculator.py\n")
            else:
                return Mock(returncode=0, stdout="", stderr="")
        
        mock_run.side_effect = subprocess_side_effect
        
        # Initialize CN runner
        runner = CNRunner(working_dir=self.temp_path, verbose=True)
        
        # Run the task
        result = runner.run_task(
            str(self.task_file),
            "gpt-4",
            provider="openai",
            timeout=60
        )
        
        # Verify results
        self.assertTrue(result["success"])
        self.assertEqual(result["model_name"], "gpt-4")
        self.assertEqual(result["task_name"], "fix_typos")
        self.assertGreater(result["execution_time"], 0)
        
        # Verify metrics
        metrics = result["metrics"]
        self.assertEqual(metrics["prompts_sent"], 1)
        self.assertGreater(metrics["tool_calls"], 0)
        self.assertTrue(metrics["success"])
        self.assertEqual(metrics["files_modified"], 1)
        self.assertEqual(metrics["lines_added"], 3)
        self.assertEqual(metrics["lines_removed"], 3)
    
    @patch('subprocess.run')
    def test_batch_integration_workflow(self, mock_run):
        """Test complete batch integration workflow."""
        from benchmark.cn_integration.cn_batch_integration import CNBatchIntegration
        
        # Mock subprocess calls
        def subprocess_side_effect(cmd, **kwargs):
            cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd)
            
            if "cn --help" in cmd_str:
                return Mock(returncode=0)
            elif "cn -p" in cmd_str:
                # Different responses for different models
                if "gpt-4" in str(kwargs.get("cwd", "")):
                    stdout = "Successfully completed task with GPT-4"
                    returncode = 0
                else:
                    stdout = "Task completed with alternative model"
                    returncode = 0
                
                return Mock(
                    returncode=returncode,
                    stdout=f"Reading file: calculator.py\nWriting to file: calculator.py\n{stdout}",
                    stderr=""
                )
            elif "git" in cmd_str:
                if "diff --name-only" in cmd_str:
                    return Mock(returncode=0, stdout="calculator.py\n")
                elif "diff --numstat" in cmd_str:
                    return Mock(returncode=0, stdout="2\t2\tcalculator.py\n")
                else:
                    return Mock(returncode=0, stdout="")
            else:
                return Mock(returncode=0, stdout="", stderr="")
        
        mock_run.side_effect = subprocess_side_effect
        
        # Initialize batch integration
        integration = CNBatchIntegration(working_dir=self.temp_path, verbose=False)
        
        # Run batch
        task_files = [str(self.task_file)]
        models = [{"name": "gpt-4"}, {"name": "gpt-3.5-turbo"}]
        
        with patch('builtins.print'):  # Suppress output during test
            result = integration.run_batch_with_cn(
                task_files, models, timeout=60
            )
        
        # Verify batch results
        self.assertIn("batch_id", result)
        self.assertEqual(result["execution_method"], "continue_cli")
        self.assertEqual(result["models_tested"], 2)
        self.assertEqual(result["total_runs"], 2)
        self.assertGreaterEqual(result["successful"], 0)
        self.assertEqual(result["successful"] + result["failed"], 2)
        
        # Verify output files were created (they should be in a results directory)
        # Since we're mocking, we can't verify actual file creation, but we can
        # verify the result structure is correct
        self.assertIn("results", result)
        self.assertEqual(len(result["results"]), 2)
        
        for res in result["results"]:
            self.assertIn("model", res)
            self.assertIn("task", res)
            self.assertIn("success", res)
            self.assertIn("execution_method", res)
            self.assertEqual(res["execution_method"], "continue_cli")
    
    @patch('benchmark.cn_integration.cn_runner.validate_task_file')
    @patch('subprocess.run')
    def test_error_handling_workflow(self, mock_run, mock_validate):
        """Test error handling in the complete workflow."""
        from benchmark.cn_integration.cn_runner import CNRunner, CNExecutionError
        
        # Mock validate_task_file to return the path directly
        mock_validate.return_value = self.task_file
        
        # Mock CN failure
        def subprocess_side_effect(cmd, **kwargs):
            if "cn --help" in " ".join(cmd):
                return Mock(returncode=0)
            elif "cn -p" in " ".join(cmd):
                # Simulate CN failure
                return Mock(
                    returncode=1,
                    stdout="",
                    stderr="Error: Model not available"
                )
            else:
                return Mock(returncode=0, stdout="")
        
        mock_run.side_effect = subprocess_side_effect
        
        runner = CNRunner(working_dir=self.temp_path)
        
        # Run task that should fail
        result = runner.run_task(str(self.task_file), "nonexistent-model")
        
        # Verify failure is handled gracefully
        self.assertFalse(result["success"])
        # Error should be in cn_errors within metrics or as a top-level field
        self.assertTrue(
            "error" in result or 
            (result.get("metrics", {}).get("cn_errors") and "Error" in result["metrics"]["cn_errors"])
        )
        self.assertEqual(result["task_name"], "fix_typos")
        self.assertGreater(result["execution_time"], 0)
    
    @patch('subprocess.run')
    def test_metrics_collection_workflow(self, mock_run):
        """Test comprehensive metrics collection workflow."""
        from benchmark.cn_integration.cn_metrics import CNMetricsCollector
        
        # Mock git commands
        def subprocess_side_effect(cmd, **kwargs):
            if "rev-parse --git-dir" in " ".join(cmd):
                return Mock(returncode=0, stdout=".git\n")
            elif "diff --name-only" in " ".join(cmd):
                return Mock(returncode=0, stdout="calculator.py\nREADME.md\n")
            elif "diff --numstat" in " ".join(cmd):
                return Mock(returncode=0, stdout="5\t3\tcalculator.py\n2\t0\tREADME.md\n")
            else:
                return Mock(returncode=0, stdout="")
        
        mock_run.side_effect = subprocess_side_effect
        
        collector = CNMetricsCollector(working_dir=self.temp_path)
        
        # Test comprehensive metrics generation
        cn_output = """Reading file: calculator.py
Reading file: README.md
Found 3 typos in calculator.py
Writing to file: calculator.py
Modified file: README.md
Successfully fixed all typos
Task completed without errors"""
        
        metrics = collector.generate_comprehensive_metrics(
            str(self.task_file),
            "gpt-4",
            cn_output,
            "",
            45.5,
            True
        )
        
        # Verify comprehensive metrics structure
        self.assertIn("timestamp", metrics)
        self.assertIn("task_file", metrics)
        self.assertIn("model_name", metrics)
        self.assertEqual(metrics["model_name"], "gpt-4")
        self.assertEqual(metrics["execution_time"], 45.5)
        self.assertTrue(metrics["command_success"])
        
        # Verify git metrics
        git_metrics = metrics["git"]
        self.assertEqual(git_metrics["files_modified"], 2)
        self.assertEqual(git_metrics["lines_added"], 7)  # 5 + 2
        self.assertEqual(git_metrics["lines_removed"], 3)
        
        # Verify output analysis
        output_analysis = metrics["output_analysis"]
        self.assertGreaterEqual(output_analysis["files_read"], 2)
        self.assertGreaterEqual(output_analysis["files_written"], 2)
        self.assertGreater(output_analysis["success_indicators"], 0)
        self.assertTrue(output_analysis["likely_success"])
        
        # Verify completion analysis
        completion_analysis = metrics["completion_analysis"]
        self.assertEqual(completion_analysis["total_requirements"], 3)
        self.assertEqual(completion_analysis["total_success_criteria"], 3)
        self.assertGreater(completion_analysis["completion_percentage"], 0)
        
        # Verify summary
        summary = metrics["summary"]
        self.assertEqual(summary["files_changed"], 2)
        self.assertGreater(summary["total_tool_calls"], 0)
        self.assertGreater(summary["completion_rate"], 0)
        self.assertTrue(summary["likely_success"])
        self.assertGreater(summary["performance_score"], 0)
    
    def test_task_prompt_preparation(self):
        """Test task prompt preparation from markdown."""
        from benchmark.cn_integration.cn_runner import CNRunner
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0)
            
            runner = CNRunner(working_dir=self.temp_path)
            prompt = runner._prepare_task_prompt(self.task_file)
            
            # Verify prompt contains expected elements
            self.assertIn("Task: Fix Calculator Typos", prompt)
            self.assertIn("Fix \"paramter\" to \"parameter\"", prompt)
            self.assertIn("All typos are fixed", prompt)
            self.assertIn("Working directory:", prompt)
            self.assertIn(str(self.temp_path), prompt)
    
    def test_config_creation_workflow(self):
        """Test configuration creation workflow."""
        from benchmark.cn_integration.cn_config import CNConfigManager
        
        manager = CNConfigManager()
        
        try:
            # Test various model configurations
            test_cases = [
                ("gpt-4", "auto"),
                ("ollama/llama2", "auto"),
                ("claude-3-sonnet", "anthropic")
            ]
            
            for model, provider in test_cases:
                config_path = manager.create_config(model, provider)
                
                # Verify config file was created
                self.assertTrue(config_path.exists())
                
                # Verify config can be loaded as YAML
                import yaml
                with open(config_path) as f:
                    config = yaml.safe_load(f)
                
                self.assertIn("models", config)
                self.assertIn("chat", config["models"])
                
                # Clean up individual configs (manager will clean all at end)
                
        finally:
            manager.cleanup_temp_configs()
    
    @patch('subprocess.run')
    def test_permission_system_workflow(self, mock_run):
        """Test permission system workflow."""
        from benchmark.cn_integration.cn_runner import CNRunner
        
        mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
        
        runner = CNRunner(working_dir=self.temp_path)
        
        # Test different permission levels
        test_cases = [
            ("analysis", ["--allow", "Read()", "--exclude", "Write()"]),
            ("safe", ["--allow", "Read()", "--allow", "Write()", "--exclude", "Bash()"]),
            ("default", ["--allow", "Read()", "--allow", "Write()", "--ask", "Bash(*)"])
        ]
        
        for task_type, expected_flags in test_cases:
            flags = runner._get_permission_flags(task_type)
            self.assertEqual(flags, expected_flags)
    
    @pytest.mark.integration
    @patch('benchmark.cn_integration.cn_runner.validate_task_file')
    def test_integration_with_real_files(self, mock_validate):
        """Integration test with actual file system operations."""
        # This test would work with real files if CN CLI is available
        # For now, we'll create a comprehensive mock scenario
        
        # Mock validate_task_file to return the path directly
        mock_validate.return_value = self.task_file
        
        from benchmark.cn_integration.cn_runner import CNRunner
        
        with patch('subprocess.run') as mock_run:
            # Mock CN availability and execution
            def subprocess_side_effect(cmd, **kwargs):
                if "cn --help" in " ".join(cmd):
                    return Mock(returncode=0)
                elif "cn -p" in " ".join(cmd) and kwargs.get("cwd") == self.temp_path:
                    # Simulate actual file modification
                    # In reality, CN would modify the file, but we'll simulate it
                    fixed_code = self.sample_code.replace("paramter", "parameter")
                    fixed_code = fixed_code.replace("reuslt", "result") 
                    fixed_code = fixed_code.replace("Divsion", "Division")
                    
                    # Write the "fixed" file
                    with open(self.sample_file, 'w') as f:
                        f.write(fixed_code)
                    
                    return Mock(
                        returncode=0,
                        stdout="File modified successfully. Fixed 3 typos.",
                        stderr=""
                    )
                else:
                    return Mock(returncode=0, stdout="", stderr="")
            
            mock_run.side_effect = subprocess_side_effect
            
            runner = CNRunner(working_dir=self.temp_path, verbose=True)
            
            # Verify initial file content has typos
            with open(self.sample_file) as f:
                original_content = f.read()
            self.assertIn("paramter", original_content)
            self.assertIn("reuslt", original_content) 
            self.assertIn("Divsion", original_content)
            
            # Run the task
            result = runner.run_task(str(self.task_file), "gpt-4")
            
            # Verify task succeeded
            self.assertTrue(result["success"])
            
            # Verify file was actually modified
            with open(self.sample_file) as f:
                fixed_content = f.read()
            
            self.assertNotIn("paramter", fixed_content)
            self.assertNotIn("reuslt", fixed_content) 
            self.assertNotIn("Divsion", fixed_content)
            self.assertIn("parameter", fixed_content)
            self.assertIn("result", fixed_content)
            self.assertIn("Division", fixed_content)


if __name__ == "__main__":
    unittest.main()
