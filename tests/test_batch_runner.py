#!/usr/bin/env python3
"""
Test suite for benchmark/batch_runner.py
"""

import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import MagicMock, patch

import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from benchmark.batch_runner import BatchRunner


class TestBatchRunner:
    """Test cases for BatchRunner class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.batch_runner = BatchRunner(output_dir=self.temp_dir)

    def teardown_method(self):
        """Clean up after tests."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init(self):
        """Test BatchRunner initialization."""
        runner = BatchRunner()
        assert runner.output_dir is not None
        assert runner.models_config_path == Path("benchmark/models_config.yaml")
        assert runner.available_models == []
        assert runner.results == []

    def test_create_output_dir(self):
        """Test output directory creation."""
        runner = BatchRunner()
        assert runner.output_dir.exists()
        assert runner.batch_id is not None
        assert runner.batch_id.startswith("batch_")

    @patch("benchmark.batch_runner.OllamaChecker")
    def test_detect_ollama_models(self, mock_ollama_checker):
        """Test Ollama model detection."""
        mock_checker = MagicMock()
        mock_checker.list_available_models.return_value = [
            "llama2",
            "codellama",
            "mistral",
        ]
        mock_ollama_checker.return_value = mock_checker

        models = self.batch_runner._detect_ollama_models()

        assert models == ["llama2", "codellama", "mistral"]
        mock_checker.list_available_models.assert_called_once()

    def test_load_configured_models(self):
        """Test loading models from config file."""
        # Create a temporary config file
        config_data = {
            "models": [
                {
                    "name": "gpt-4",
                    "provider": "openai",
                    "display_name": "GPT-4",
                    "enabled": True,
                },
                {
                    "name": "claude-3",
                    "provider": "anthropic",
                    "display_name": "Claude 3",
                    "enabled": False,
                },
            ]
        }

        config_path = Path(self.temp_dir) / "models_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        self.batch_runner.models_config_path = config_path
        models = self.batch_runner._load_configured_models()

        assert len(models) == 1  # Only enabled models
        assert models[0]["name"] == "gpt-4"
        assert models[0]["provider"] == "openai"

    @patch("benchmark.batch_runner.OllamaChecker")
    def test_detect_available_models(self, mock_ollama_checker):
        """Test detection of all available models."""
        # Mock Ollama models
        mock_checker = MagicMock()
        mock_checker.check_installation.return_value = True
        mock_checker.check_service_running.return_value = True
        mock_checker.list_available_models.return_value = ["llama2", "codellama"]
        mock_ollama_checker.return_value = mock_checker

        # Create config file
        config_data = {
            "models": [
                {
                    "name": "gpt-4",
                    "provider": "openai",
                    "display_name": "GPT-4",
                    "enabled": True,
                }
            ]
        }

        config_path = Path(self.temp_dir) / "models_config.yaml"
        with open(config_path, "w") as f:
            yaml.dump(config_data, f)

        self.batch_runner.models_config_path = config_path
        models = self.batch_runner.detect_available_models()

        assert len(models) == 3  # 2 Ollama + 1 configured

        # Check Ollama models
        ollama_models = [m for m in models if m["provider"] == "ollama"]
        assert len(ollama_models) == 2
        assert any(m["name"] == "ollama/llama2" for m in ollama_models)
        assert any(m["name"] == "ollama/codellama" for m in ollama_models)

        # Check configured model
        config_models = [m for m in models if m["provider"] == "openai"]
        assert len(config_models) == 1
        assert config_models[0]["name"] == "gpt-4"

    def test_save_model_result(self):
        """Test saving individual model results."""
        result = {
            "model": "ollama/llama2",
            "task": "test_task",
            "success": True,
            "completion_time": 10.5,
            "prompts_sent": 3,
        }

        self.batch_runner._save_model_result("ollama/llama2", result)

        result_file = self.batch_runner.output_dir / "ollama_llama2_result.json"
        assert result_file.exists()

        with open(result_file, "r") as f:
            saved_data = json.load(f)

        assert saved_data == result

    def test_generate_comparison_report(self):
        """Test comparison report generation."""
        self.batch_runner.start_time = 100.0  # Mock start time

        with patch("time.time", return_value=110.0):  # Mock current time
            results = [
                {
                    "model": "model1",
                    "task": "test_task",
                    "success": True,
                    "completion_time": 5.0,
                    "prompts_sent": 3,
                    "human_interventions": 1,
                    "files_modified": 2,
                },
                {
                    "model": "model2",
                    "task": "test_task",
                    "success": True,
                    "completion_time": 8.0,
                    "prompts_sent": 5,
                    "human_interventions": 0,
                    "files_modified": 1,
                },
                {
                    "model": "model3",
                    "task": "test_task",
                    "success": False,
                    "completion_time": 0,
                    "prompts_sent": 0,
                    "human_interventions": 0,
                    "files_modified": 0,
                },
            ]

            comparison = self.batch_runner._generate_comparison_report(
                results, "test_task"
            )

        assert comparison["task"] == "test_task"
        assert comparison["models_tested"] == 3
        assert comparison["successful"] == 2
        assert comparison["failed"] == 1
        assert comparison["total_time"] == 10.0

        # Check rankings
        assert comparison["rankings"]["fastest"] == "model1"
        assert comparison["rankings"]["most_efficient"] == "model1"
        assert comparison["rankings"]["least_intervention"] == "model2"

        # Check summary stats
        stats = comparison["summary_stats"]
        assert stats["avg_completion_time"] == 6.5  # (5 + 8) / 2
        assert stats["min_completion_time"] == 5.0
        assert stats["max_completion_time"] == 8.0

    def test_generate_html_report(self):
        """Test HTML report generation."""
        comparison = {
            "batch_id": "batch_test",
            "task": "test_task",
            "total_time": 100.0,
            "models_tested": 2,
            "successful": 1,
            "failed": 1,
            "results": [
                {
                    "model": "model1",
                    "success": True,
                    "completion_time": 10.0,
                    "prompts_sent": 3,
                    "human_interventions": 1,
                    "files_modified": 2,
                }
            ],
            "rankings": {
                "fastest": "model1",
                "most_efficient": "model1",
                "least_intervention": "model1",
            },
        }

        self.batch_runner._generate_html_report(comparison)

        html_file = self.batch_runner.output_dir / "comparison_report.html"
        assert html_file.exists()

        content = html_file.read_text()
        assert "test_task" in content
        assert "model1" in content
        assert "✅ Success" in content

    def test_generate_csv_report(self):
        """Test CSV report generation."""
        comparison = {
            "results": [
                {
                    "model": "model1",
                    "task": "test_task",
                    "success": True,
                    "completion_time": 10.0,
                    "prompts_sent": 3,
                    "human_interventions": 1,
                    "files_modified": 2,
                    "lines_added": 10,
                    "lines_removed": 5,
                    "timestamp": "2024-01-01T10:00:00",
                }
            ]
        }

        self.batch_runner._generate_csv_report(comparison)

        csv_file = self.batch_runner.output_dir / "comparison_report.csv"
        assert csv_file.exists()

        import csv

        with open(csv_file, "r") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["model"] == "model1"
        assert rows[0]["success"] == "True"
        assert rows[0]["prompts_sent"] == "3"

    @patch("benchmark.batch_runner.BenchmarkMetrics")
    def test_run_single_model_task(self, mock_metrics_class):
        """Test running a single model task."""
        mock_metrics = MagicMock()
        mock_metrics_class.return_value = mock_metrics

        with patch("time.sleep"):  # Speed up test
            result = self.batch_runner._run_single_model_task(
                "test_model", "test_task.md", "test_task", 60
            )

        assert result["model"] == "test_model"
        assert result["task"] == "test_task"
        assert result["success"] is True
        assert "completion_time" in result
        assert "timestamp" in result

        mock_metrics.start_task.assert_called_once()
        mock_metrics.complete_task.assert_called_once_with(True)

    def test_load_completed_models(self):
        """Test loading completed models from previous batch."""
        # Create a new batch runner with our temp directory as the base
        test_batch_runner = BatchRunner()

        # Create the batch directory structure
        batch_id = "batch_test"
        batch_dir = Path("benchmark/results") / batch_id
        batch_dir.mkdir(parents=True, exist_ok=True)

        # Create mock result files
        result1 = {"model": "model1", "success": True}
        result2 = {"model": "model2", "success": False}

        with open(batch_dir / "model1_result.json", "w") as f:
            json.dump(result1, f)

        with open(batch_dir / "model2_result.json", "w") as f:
            json.dump(result2, f)

        # Test loading completed models
        completed = test_batch_runner._load_completed_models(batch_id)

        # Clean up the test files
        import shutil

        shutil.rmtree(batch_dir, ignore_errors=True)

        assert "model1" in completed
        assert "model2" in completed
        assert len(completed) == 2

    @patch("benchmark.batch_runner.validate_task_file")
    @patch("benchmark.batch_runner.BatchRunner.detect_available_models")
    @patch("benchmark.batch_runner.BatchRunner._run_with_progress")
    @patch("benchmark.batch_runner.BatchRunner._run_simple")
    @patch("benchmark.batch_runner.MachineInfoCollector.save_to_file")
    @patch("benchmark.batch_runner.MachineInfoCollector.collect_all")
    @patch("benchmark.batch_runner.BatchRunner._generate_comparison_report")
    @patch("benchmark.batch_runner.BatchRunner._save_batch_results")
    @patch("benchmark.batch_runner.BatchRunner._display_batch_info")
    @patch("benchmark.batch_runner.BatchRunner._display_summary")
    def test_run_batch_benchmark(
        self,
        mock_display_summary,
        mock_display_info,
        mock_save_results,
        mock_generate_report,
        mock_collect_all,
        mock_save_to_file,
        mock_run_simple,
        mock_run_with_progress,
        mock_detect_models,
        mock_validate_task,
    ):
        """Test the main batch benchmark run."""
        # Mock task validation
        mock_task_path = MagicMock()
        mock_task_path.stem = "test_task"
        mock_validate_task.return_value = mock_task_path

        # Mock model detection
        mock_detect_models.return_value = [
            {"name": "model1", "provider": "test", "display_name": "Model 1"},
            {"name": "model2", "provider": "test", "display_name": "Model 2"},
        ]

        # Mock run results (both _run_simple and _run_with_progress)
        run_results = [
            {"model": "model1", "success": True},
            {"model": "model2", "success": True},
        ]
        mock_run_simple.return_value = run_results
        mock_run_with_progress.return_value = run_results

        # Mock comparison report
        mock_generate_report.return_value = {
            "batch_id": "test_batch",
            "successful": 2,
            "failed": 0,
        }
        
        # Mock machine info collection
        mock_collect_all.return_value = {
            "system": {"platform": "test"},
            "cpu": {"model": "test"},
            "memory": {"total_gb": 16},
        }

        # Run batch benchmark
        result = self.batch_runner.run_batch_benchmark(
            task_file="test_task.md", models=None
        )

        # Verify calls
        mock_validate_task.assert_called_once_with("test_task.md")
        mock_detect_models.assert_called_once()
        # Either _run_simple or _run_with_progress should be called
        assert mock_run_simple.called or mock_run_with_progress.called
        mock_generate_report.assert_called_once()
        mock_save_results.assert_called_once()
        mock_display_info.assert_called_once()
        mock_display_summary.assert_called_once()

        assert result["successful"] == 2
        assert result["failed"] == 0


class TestBatchRunnerCLI:
    """Test cases for CLI functionality."""

    @patch("benchmark.batch_runner.BatchRunner")
    @patch("sys.argv", ["batch_runner.py", "--task", "test.md"])
    def test_cli_basic(self, mock_runner_class):
        """Test basic CLI invocation."""
        mock_runner = MagicMock()
        mock_runner_class.return_value = mock_runner

        from benchmark.batch_runner import main

        main()

        mock_runner.run_batch_benchmark.assert_called_once_with(
            task_file="test.md",
            models=None,
            parallel=False,
            timeout=1800,
            resume_from=None,
        )

    @patch("benchmark.batch_runner.BatchRunner")
    @patch(
        "sys.argv",
        [
            "batch_runner.py",
            "--task",
            "test.md",
            "--models",
            "model1,model2",
            "--timeout",
            "3600",
            "--parallel",
        ],
    )
    def test_cli_with_options(self, mock_runner_class):
        """Test CLI with multiple options."""
        mock_runner = MagicMock()
        mock_runner_class.return_value = mock_runner

        from benchmark.batch_runner import main

        main()

        mock_runner.run_batch_benchmark.assert_called_once_with(
            task_file="test.md",
            models=["model1", "model2"],
            parallel=True,
            timeout=3600,
            resume_from=None,
        )
