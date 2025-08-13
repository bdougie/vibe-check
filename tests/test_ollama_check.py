#!/usr/bin/env python3
"""
Test suite for benchmark/ollama_check.py
"""

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from benchmark.ollama_check import OllamaChecker


class TestOllamaChecker:
    """Test cases for OllamaChecker class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.checker = OllamaChecker(verbose=False)

    def test_init(self):
        """Test OllamaChecker initialization"""
        checker = OllamaChecker(verbose=True)
        assert checker.verbose is True
        assert checker.ollama_binary is None
        assert checker.is_installed is False
        assert checker.is_running is False
        assert checker.available_models == []
        assert checker.errors == []
        assert checker.warnings == []

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_check_installation_found(self, mock_run, mock_which):
        """Test check_installation when Ollama is found"""
        mock_which.return_value = "/usr/local/bin/ollama"
        mock_run.return_value = MagicMock(
            returncode=0, stdout="ollama version 0.1.0\n", stderr=""
        )

        result = self.checker.check_installation()

        assert result is True
        assert self.checker.is_installed is True
        assert self.checker.ollama_binary == "/usr/local/bin/ollama"
        mock_which.assert_called_once_with("ollama")
        mock_run.assert_called_once()

    @patch("shutil.which")
    def test_check_installation_not_found(self, mock_which):
        """Test check_installation when Ollama is not found"""
        mock_which.return_value = None

        result = self.checker.check_installation()

        assert result is False
        assert self.checker.is_installed is False
        assert self.checker.ollama_binary is None
        assert len(self.checker.errors) == 1
        assert "not installed" in self.checker.errors[0]

    @patch("subprocess.run")
    def test_check_service_running_success(self, mock_run):
        """Test check_service_running when service is active"""
        self.checker.is_installed = True
        mock_run.return_value = MagicMock(
            returncode=0, stdout="NAME    ID    SIZE\n", stderr=""
        )

        result = self.checker.check_service_running()

        assert result is True
        assert self.checker.is_running is True
        mock_run.assert_called_once_with(
            ["ollama", "list"], capture_output=True, text=True, timeout=5
        )

    @patch("subprocess.run")
    def test_check_service_running_not_active(self, mock_run):
        """Test check_service_running when service is not running"""
        self.checker.is_installed = True
        mock_run.return_value = MagicMock(
            returncode=1, stdout="", stderr="Error: connection refused"
        )

        result = self.checker.check_service_running()

        assert result is False
        assert self.checker.is_running is False
        assert len(self.checker.errors) == 1
        assert "not running" in self.checker.errors[0]

    def test_check_service_running_not_installed(self):
        """Test check_service_running when Ollama is not installed"""
        self.checker.is_installed = False

        result = self.checker.check_service_running()

        assert result is False
        assert self.checker.is_running is False

    @patch("subprocess.run")
    def test_list_available_models_with_models(self, mock_run):
        """Test list_available_models when models are available"""
        self.checker.is_running = True
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="NAME                           ID              SIZE      MODIFIED\n"
            "llama2:latest                  abc123          3.8 GB    2 days ago\n"
            "codellama:13b                  def456          7.3 GB    1 week ago\n",
            stderr="",
        )

        models = self.checker.list_available_models()

        assert len(models) == 2
        assert "llama2" in models
        assert "codellama" in models
        assert self.checker.available_models == models

    @patch("subprocess.run")
    def test_list_available_models_no_models(self, mock_run):
        """Test list_available_models when no models are installed"""
        self.checker.is_running = True
        mock_run.return_value = MagicMock(
            returncode=0, stdout="NAME    ID    SIZE    MODIFIED\n", stderr=""
        )

        models = self.checker.list_available_models()

        assert len(models) == 0
        assert len(self.checker.warnings) == 1

    def test_list_available_models_service_not_running(self):
        """Test list_available_models when service is not running"""
        self.checker.is_running = False

        models = self.checker.list_available_models()

        assert models == []

    def test_check_model_available_exists(self):
        """Test check_model_available when model exists"""
        self.checker.available_models = ["llama2", "codellama", "mistral"]

        assert self.checker.check_model_available("llama2") is True
        assert self.checker.check_model_available("llama2:latest") is True
        assert self.checker.check_model_available("codellama") is True

    def test_check_model_available_not_exists(self):
        """Test check_model_available when model doesn't exist"""
        self.checker.available_models = ["llama2", "codellama"]

        assert self.checker.check_model_available("gpt4") is False
        assert self.checker.check_model_available("claude") is False

    @patch("subprocess.Popen")
    def test_pull_model_success(self, mock_popen):
        """Test pull_model when successful"""
        self.checker.is_running = True
        mock_process = MagicMock()
        mock_process.stdout = ["Pulling model...\n", "Done!\n"]
        mock_process.wait.return_value = None
        mock_process.returncode = 0
        mock_popen.return_value = mock_process

        with patch.object(self.checker, "list_available_models"):
            result = self.checker.pull_model("llama2")

        assert result is True
        mock_popen.assert_called_once_with(
            ["ollama", "pull", "llama2"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

    @patch("subprocess.Popen")
    def test_pull_model_failure(self, mock_popen):
        """Test pull_model when it fails"""
        self.checker.is_running = True
        mock_process = MagicMock()
        mock_process.stdout = ["Error pulling model\n"]
        mock_process.wait.return_value = None
        mock_process.returncode = 1
        mock_popen.return_value = mock_process

        result = self.checker.pull_model("invalid_model")

        assert result is False

    def test_pull_model_service_not_running(self):
        """Test pull_model when service is not running"""
        self.checker.is_running = False

        result = self.checker.pull_model("llama2")

        assert result is False

    @patch.object(OllamaChecker, "check_installation")
    @patch.object(OllamaChecker, "check_service_running")
    @patch.object(OllamaChecker, "list_available_models")
    def test_run_full_check_ready(
        self, mock_list_models, mock_check_service, mock_check_install
    ):
        """Test run_full_check when everything is ready"""
        checker = OllamaChecker(verbose=False)

        # Set up the mocks to modify the checker's state
        def mock_install():
            checker.is_installed = True
            return True

        def mock_service():
            checker.is_running = True
            return True

        def mock_models():
            checker.available_models = ["llama2", "codellama"]
            return ["llama2", "codellama"]

        mock_check_install.side_effect = mock_install
        mock_check_service.side_effect = mock_service
        mock_list_models.side_effect = mock_models

        results = checker.run_full_check()

        assert results["installed"] is True
        assert results["running"] is True
        assert results["models"] == ["llama2", "codellama"]
        assert results["ready"] is True
        assert len(results["errors"]) == 0

    @patch.object(OllamaChecker, "check_installation")
    @patch.object(OllamaChecker, "check_service_running")
    @patch.object(OllamaChecker, "list_available_models")
    def test_run_full_check_not_ready(
        self, mock_list_models, mock_check_service, mock_check_install
    ):
        """Test run_full_check when not ready"""
        mock_check_install.return_value = False
        mock_check_service.return_value = False
        mock_list_models.return_value = []

        checker = OllamaChecker(verbose=False)
        results = checker.run_full_check()

        assert results["installed"] is False
        assert results["running"] is False
        assert results["models"] == []
        assert results["ready"] is False

    @patch.object(OllamaChecker, "check_model_available")
    def test_ensure_model_available_exists(self, mock_check):
        """Test ensure_model_available when model exists"""
        mock_check.return_value = True

        result = self.checker.ensure_model_available("llama2", auto_pull=False)

        assert result is True
        mock_check.assert_called_once_with("llama2")

    @patch.object(OllamaChecker, "check_model_available")
    @patch.object(OllamaChecker, "pull_model")
    def test_ensure_model_available_auto_pull(self, mock_pull, mock_check):
        """Test ensure_model_available with auto_pull"""
        mock_check.return_value = False
        mock_pull.return_value = True

        result = self.checker.ensure_model_available("llama2", auto_pull=True)

        assert result is True
        mock_check.assert_called_once_with("llama2")
        mock_pull.assert_called_once_with("llama2")

    @patch.object(OllamaChecker, "check_model_available")
    def test_ensure_model_available_not_found_no_pull(self, mock_check):
        """Test ensure_model_available when model not found and no auto_pull"""
        mock_check.return_value = False

        result = self.checker.ensure_model_available("llama2", auto_pull=False)

        assert result is False
        mock_check.assert_called_once_with("llama2")

    def test_print_message_verbose_true(self, capsys):
        """Test print_message when verbose is True"""
        checker = OllamaChecker(verbose=True)
        checker.print_message("Test message", "info")

        captured = capsys.readouterr()
        assert "Test message" in captured.out
        assert "ℹ️" in captured.out

    def test_print_message_verbose_false(self, capsys):
        """Test print_message when verbose is False"""
        checker = OllamaChecker(verbose=False)
        checker.print_message("Test message", "info")

        captured = capsys.readouterr()
        assert captured.out == ""


class TestOllamaCheckerIntegration:
    """Integration tests for OllamaChecker (requires Ollama installed)"""

    @pytest.mark.integration
    def test_real_ollama_check(self):
        """Test with actual Ollama installation (if available)"""
        checker = OllamaChecker(verbose=False)

        # This test will pass/fail based on actual Ollama installation
        results = checker.run_full_check()

        # Check that all expected keys are present
        assert "installed" in results
        assert "running" in results
        assert "models" in results
        assert "errors" in results
        assert "warnings" in results
        assert "ready" in results

        # If Ollama is installed, do more checks
        if results["installed"]:
            assert isinstance(results["models"], list)
            assert isinstance(results["errors"], list)
            assert isinstance(results["warnings"], list)


class TestOllamaCheckMain:
    """Test cases for main function and CLI"""

    @patch("sys.argv", ["ollama_check.py"])
    @patch.object(OllamaChecker, "run_full_check")
    def test_main_no_args(self, mock_run_check):
        """Test main function with no arguments"""
        mock_run_check.return_value = {
            "installed": True,
            "running": True,
            "models": ["llama2"],
            "errors": [],
            "warnings": [],
            "ready": True,
        }

        with patch("sys.exit") as mock_exit:
            from benchmark.ollama_check import main

            main()
            mock_exit.assert_called_once_with(0)

    @patch("sys.argv", ["ollama_check.py", "--quiet"])
    @patch.object(OllamaChecker, "run_full_check")
    def test_main_quiet_mode(self, mock_run_check):
        """Test main function in quiet mode"""
        mock_run_check.return_value = {
            "installed": True,
            "running": True,
            "models": ["llama2"],
            "errors": [],
            "warnings": [],
            "ready": True,
        }

        with patch("sys.exit") as mock_exit:
            from benchmark.ollama_check import main

            main()
            mock_exit.assert_called_once_with(0)

    @patch("sys.argv", ["ollama_check.py", "--json"])
    @patch.object(OllamaChecker, "run_full_check")
    def test_main_json_output(self, mock_run_check, capsys):
        """Test main function with JSON output"""
        mock_run_check.return_value = {
            "installed": True,
            "running": True,
            "models": ["llama2"],
            "errors": [],
            "warnings": [],
            "ready": True,
        }

        with patch("sys.exit") as mock_exit:
            from benchmark.ollama_check import main

            main()

            captured = capsys.readouterr()
            output = json.loads(captured.out)
            assert output["ready"] is True
            mock_exit.assert_called_once_with(0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
