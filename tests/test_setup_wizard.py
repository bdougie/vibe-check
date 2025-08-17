#!/usr/bin/env python3
"""
Test suite for setup_wizard.py
"""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from setup_wizard import Colors, SetupWizard


class TestSetupWizard:
    """Test cases for the SetupWizard class."""

    def test_init(self):
        """Test wizard initialization."""
        wizard = SetupWizard()
        assert wizard.python_version == sys.version_info
        assert wizard.has_uv is False
        assert wizard.has_ollama is False
        assert wizard.ollama_models == []
        assert wizard.continue_installed is False
        assert wizard.setup_complete is False

    def test_check_python_version_success(self):
        """Test Python version check with valid version."""
        wizard = SetupWizard()
        # Current Python should always pass since we require 3.8+
        result = wizard.check_python_version()
        assert result is True

    def test_check_python_version_failure(self):
        """Test Python version check with old version."""
        wizard = SetupWizard()
        # Mock an old Python version using a namedtuple
        from collections import namedtuple

        VersionInfo = namedtuple(
            "version_info", ["major", "minor", "micro", "releaselevel", "serial"]
        )
        wizard.python_version = VersionInfo(
            major=3, minor=7, micro=0, releaselevel="final", serial=0
        )
        result = wizard.check_python_version()
        assert result is False

    @patch("shutil.which")
    @patch("setup_wizard.ask_yes_no")
    def test_check_dependencies_no_git(self, mock_ask, mock_which):
        """Test dependency check when Git is missing."""
        wizard = SetupWizard()
        mock_which.return_value = None  # Git not found
        mock_ask.return_value = False  # Don't install uv
        result = wizard.check_dependencies()
        assert result is False

    @patch("shutil.which")
    @patch("subprocess.run")
    @patch("setup_wizard.ask_yes_no")
    def test_check_dependencies_with_git(self, mock_ask, mock_run, mock_which):
        """Test dependency check when Git is present."""
        wizard = SetupWizard()

        def which_side_effect(cmd):
            if cmd == "git":
                return "/usr/bin/git"
            return None

        mock_which.side_effect = which_side_effect
        mock_run.return_value = MagicMock(returncode=0)
        mock_ask.return_value = False  # Don't install uv

        # Mock the requirements.txt file
        with patch("pathlib.Path.exists", return_value=True):
            result = wizard.check_dependencies()
            assert result is True

    @patch("shutil.which")
    def test_setup_ollama_not_installed(self, mock_which):
        """Test Ollama setup when not installed."""
        wizard = SetupWizard()
        mock_which.return_value = None

        with patch("setup_wizard.ask_yes_no", return_value=False):
            result = wizard.setup_ollama()
            assert result is False
            assert wizard.has_ollama is False

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_setup_ollama_installed(self, mock_run, mock_which):
        """Test Ollama setup when installed and running."""
        wizard = SetupWizard()
        mock_which.return_value = "/usr/local/bin/ollama"

        # Mock successful ollama list command
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "NAME\t\t\tID\t\t\tSIZE\nllama3:latest\tabc123\t\t4.7GB\ncodellama:latest\tdef456\t\t3.8GB"
        mock_run.return_value = mock_result

        result = wizard.setup_ollama()
        assert result is True
        assert wizard.has_ollama is True
        assert "llama3" in wizard.ollama_models
        assert "codellama" in wizard.ollama_models

    def test_parse_ollama_models(self):
        """Test parsing of ollama list output."""
        wizard = SetupWizard()

        output = """NAME                    ID              SIZE    
llama3:latest          365c0bd3c000    4.7 GB  
codellama:13b          8fdf8f752f6e    7.4 GB  
mistral:latest         2ae6f6dd7a3d    4.1 GB  
"""
        wizard.parse_ollama_models(output)

        assert "llama3" in wizard.ollama_models
        assert "codellama" in wizard.ollama_models
        assert "mistral" in wizard.ollama_models
        assert len(wizard.ollama_models) == 3

    def test_generate_continue_config(self):
        """Test Continue configuration generation."""
        wizard = SetupWizard()
        wizard.ollama_models = ["llama3", "codellama"]

        config = wizard.generate_continue_config()

        assert "llama3" in config
        assert "codellama" in config
        assert 'provider: "ollama"' in config
        assert "models:" in config

    def test_save_setup_status(self):
        """Test saving setup status to file."""
        wizard = SetupWizard()
        wizard.setup_complete = True
        wizard.has_ollama = True
        wizard.ollama_models = ["llama3"]

        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp directory
            original_cwd = Path.cwd()
            try:
                import os

                os.chdir(tmpdir)

                wizard.save_setup_status()

                status_file = Path(".vibe_check_setup.json")
                assert status_file.exists()

                with open(status_file) as f:
                    status = json.load(f)

                assert status["setup_complete"] is True
                assert status["has_ollama"] is True
                assert "llama3" in status["ollama_models"]
                assert "python_version" in status
                assert "setup_date" in status

            finally:
                os.chdir(original_cwd)

    @patch("subprocess.run")
    def test_download_model_success(self, mock_run):
        """Test successful model download."""
        wizard = SetupWizard()
        wizard.has_ollama = True

        mock_run.return_value = MagicMock(returncode=0)

        result = wizard.download_model("llama3:latest")

        assert result is True
        assert "llama3" in wizard.ollama_models
        mock_run.assert_called_once_with(
            ["ollama", "pull", "llama3:latest"], check=True
        )

    @patch("subprocess.run")
    def test_download_model_failure(self, mock_run):
        """Test failed model download."""
        wizard = SetupWizard()
        wizard.has_ollama = True

        mock_run.side_effect = subprocess.CalledProcessError(1, "ollama pull")

        result = wizard.download_model("invalid-model")

        assert result is False
        assert "invalid-model" not in wizard.ollama_models

    def test_print_git_install_instructions(self):
        """Test Git installation instructions for different platforms."""
        wizard = SetupWizard()

        # Test macOS
        wizard.os_type = "Darwin"
        wizard.print_git_install_instructions()  # Should not raise

        # Test Linux
        wizard.os_type = "Linux"
        wizard.print_git_install_instructions()  # Should not raise

        # Test Windows
        wizard.os_type = "Windows"
        wizard.print_git_install_instructions()  # Should not raise

    def test_print_ollama_install_instructions(self):
        """Test Ollama installation instructions for different platforms."""
        wizard = SetupWizard()

        # Test macOS
        wizard.os_type = "Darwin"
        wizard.print_ollama_install_instructions()  # Should not raise

        # Test Linux
        wizard.os_type = "Linux"
        wizard.print_ollama_install_instructions()  # Should not raise

        # Test Windows
        wizard.os_type = "Windows"
        wizard.print_ollama_install_instructions()  # Should not raise


class TestColors:
    """Test the Colors class for ANSI codes."""

    def test_color_codes(self):
        """Test that color codes are defined."""
        assert Colors.HEADER == "\033[95m"
        assert Colors.BLUE == "\033[94m"
        assert Colors.CYAN == "\033[96m"
        assert Colors.GREEN == "\033[92m"
        assert Colors.WARNING == "\033[93m"
        assert Colors.FAIL == "\033[91m"
        assert Colors.ENDC == "\033[0m"
        assert Colors.BOLD == "\033[1m"


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
