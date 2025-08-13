#!/usr/bin/env python3
"""
Test suite for Continue configuration generator
"""

import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest
import yaml

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from benchmark.continue_config_generator import ContinueConfigGenerator


class TestContinueConfigGenerator:
    """Test cases for Continue configuration generator."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.generator = ContinueConfigGenerator()
        # Use temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.generator.continue_dir = Path(self.temp_dir) / ".continue"
        self.generator.config_path = self.generator.continue_dir / "config.yaml"

    def teardown_method(self):
        """Clean up after each test."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_initialization(self):
        """Test generator initialization."""
        assert self.generator.config["name"] == "Continue Configuration"
        assert self.generator.config["version"] == "1.0"
        assert self.generator.config["schema"] == "1.0.0"
        assert self.generator.config["models"] == []
        assert self.generator.ollama_models == []

    @patch("subprocess.run")
    def test_detect_ollama_models_success(self, mock_run):
        """Test successful detection of Ollama models."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="NAME                    ID              SIZE      MODIFIED\n"
            "llama2:latest          abc123          3.8 GB    2 days ago\n"
            "codestral:latest       def456          7.1 GB    1 week ago\n"
            "mistral:7b             ghi789          4.1 GB    3 days ago\n",
        )

        models = self.generator.detect_ollama_models()

        assert len(models) == 3
        assert "llama2" in models
        assert "codestral" in models
        assert "mistral" in models
        mock_run.assert_called_once_with(
            ["ollama", "list"], capture_output=True, text=True, check=False, timeout=10
        )

    @patch("subprocess.run")
    def test_detect_ollama_models_not_installed(self, mock_run):
        """Test when Ollama is not installed."""
        mock_run.side_effect = FileNotFoundError()

        models = self.generator.detect_ollama_models()

        assert models == []

    @patch("subprocess.run")
    def test_detect_ollama_models_timeout(self, mock_run):
        """Test when Ollama command times out."""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("ollama", 10)

        models = self.generator.detect_ollama_models()

        assert models == []

    def test_add_ollama_models(self):
        """Test adding Ollama models to configuration."""
        self.generator.ollama_models = ["llama2", "codestral", "mistral"]

        self.generator.add_ollama_models()

        assert len(self.generator.config["models"]) == 3

        # Check codestral configuration (should have autocomplete)
        codestral_config = next(
            m for m in self.generator.config["models"] if "codestral" in m["model"]
        )
        assert "autocomplete" in codestral_config["roles"]
        assert "autocompleteOptions" in codestral_config
        assert self.generator.config["tabAutocompleteModel"] is not None

        # Check llama2 configuration
        llama_config = next(
            m for m in self.generator.config["models"] if "llama2" in m["model"]
        )
        assert "chat" in llama_config["roles"]
        assert "edit" in llama_config["roles"]

    @patch("builtins.input")
    def test_add_commercial_models_with_keys(self, mock_input):
        """Test adding commercial models with API keys."""
        mock_input.side_effect = [
            "y",  # Configure OpenAI
            "test-openai-key",  # OpenAI API key
            "y",  # Configure Anthropic
            "test-anthropic-key",  # Anthropic API key
        ]

        self.generator.add_commercial_models()

        assert len(self.generator.config["models"]) == 2

        # Check OpenAI configuration
        openai_config = next(
            m for m in self.generator.config["models"] if m["provider"] == "openai"
        )
        assert openai_config["apiKey"] == "test-openai-key"
        assert openai_config["model"] == "gpt-4"

        # Check Anthropic configuration
        anthropic_config = next(
            m for m in self.generator.config["models"] if m["provider"] == "anthropic"
        )
        assert anthropic_config["apiKey"] == "test-anthropic-key"
        assert anthropic_config["model"] == "claude-3-5-sonnet-20241022"

    @patch("builtins.input")
    def test_add_commercial_models_without_keys(self, mock_input):
        """Test adding commercial models without API keys."""
        mock_input.side_effect = [
            "n",  # Don't configure OpenAI
            "n",  # Don't configure Anthropic
        ]

        self.generator.add_commercial_models()

        assert len(self.generator.config["models"]) == 2

        # Check placeholders are present
        openai_config = next(
            m for m in self.generator.config["models"] if m["provider"] == "openai"
        )
        assert openai_config["apiKey"] == "YOUR_OPENAI_API_KEY"

        anthropic_config = next(
            m for m in self.generator.config["models"] if m["provider"] == "anthropic"
        )
        assert anthropic_config["apiKey"] == "YOUR_ANTHROPIC_API_KEY"

    def test_add_context_providers(self):
        """Test adding context providers."""
        self.generator.add_context_providers()

        assert "contextProviders" in self.generator.config
        providers = self.generator.config["contextProviders"]
        provider_names = [p["name"] for p in providers]

        assert "code" in provider_names
        assert "docs" in provider_names
        assert "diff" in provider_names
        assert "terminal" in provider_names
        assert "problems" in provider_names
        assert "folder" in provider_names
        assert "codebase" in provider_names

    def test_add_slash_commands(self):
        """Test adding slash commands."""
        self.generator.add_slash_commands()

        assert "slashCommands" in self.generator.config
        commands = self.generator.config["slashCommands"]
        command_names = [c["name"] for c in commands]

        assert "edit" in command_names
        assert "comment" in command_names
        assert "share" in command_names
        assert "cmd" in command_names
        assert "commit" in command_names

    def test_add_custom_commands(self):
        """Test adding custom commands."""
        self.generator.add_custom_commands()

        assert "customCommands" in self.generator.config
        commands = self.generator.config["customCommands"]
        command_names = [c["name"] for c in commands]

        assert "test" in command_names
        assert "check" in command_names
        assert "benchmark" in command_names

        # Check structure of a custom command
        test_command = next(c for c in commands if c["name"] == "test")
        assert "prompt" in test_command
        assert "description" in test_command

    def test_save_configuration_new(self):
        """Test saving a new configuration."""
        self.generator.config["models"] = [
            {"name": "test", "provider": "ollama", "model": "test"}
        ]

        self.generator.save_configuration(backup=False)

        assert self.generator.config_path.exists()

        # Load and verify saved configuration
        with open(self.generator.config_path, "r") as f:
            saved_config = yaml.safe_load(f)

        assert saved_config["name"] == "Continue Configuration"
        assert len(saved_config["models"]) == 1
        assert saved_config["models"][0]["name"] == "test"

    def test_save_configuration_with_backup(self):
        """Test saving configuration with backup of existing file."""
        # Create an existing config file
        self.generator.continue_dir.mkdir(parents=True, exist_ok=True)
        with open(self.generator.config_path, "w") as f:
            yaml.dump({"existing": "config"}, f)

        self.generator.config["models"] = [{"name": "new"}]
        self.generator.save_configuration(backup=True)

        # Check backup was created
        backup_path = self.generator.config_path.with_suffix(".yaml.backup")
        assert backup_path.exists()

        # Verify backup content
        with open(backup_path, "r") as f:
            backup_config = yaml.safe_load(f)
        assert backup_config["existing"] == "config"

        # Verify new config was saved
        with open(self.generator.config_path, "r") as f:
            new_config = yaml.safe_load(f)
        assert new_config["models"][0]["name"] == "new"

    @patch("builtins.input")
    @patch("subprocess.run")
    def test_generate_config_complete_flow(self, mock_run, mock_input):
        """Test complete configuration generation flow."""
        # Mock Ollama detection
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="NAME                    ID              SIZE      MODIFIED\n"
            "codestral:latest       abc123          7.1 GB    1 week ago\n",
        )

        # Mock user inputs
        mock_input.side_effect = [
            "n",  # Don't configure OpenAI
            "n",  # Don't configure Anthropic
        ]

        result = self.generator.generate_config()

        assert result is True
        assert self.generator.config_path.exists()

        # Verify generated configuration
        with open(self.generator.config_path, "r") as f:
            config = yaml.safe_load(f)

        # Should have Ollama model + 2 commercial templates
        assert len(config["models"]) == 3
        assert "contextProviders" in config
        assert "slashCommands" in config
        assert "customCommands" in config

    @patch("builtins.input")
    def test_generate_config_cancelled(self, mock_input):
        """Test cancelling configuration generation."""
        # Create existing config
        self.generator.continue_dir.mkdir(parents=True, exist_ok=True)
        with open(self.generator.config_path, "w") as f:
            yaml.dump({"existing": "config"}, f)

        # User chooses not to overwrite
        mock_input.return_value = "n"

        result = self.generator.generate_config()

        assert result is False

    def test_print_instructions(self, capsys):
        """Test printing manual configuration instructions."""
        self.generator.print_instructions()

        captured = capsys.readouterr()
        assert "MANUAL CONFIGURATION INSTRUCTIONS" in captured.out
        assert str(self.generator.config_path) in captured.out
        assert "YOUR_OPENAI_API_KEY" in captured.out
        assert "YOUR_ANTHROPIC_API_KEY" in captured.out
        assert "https://docs.continue.dev/reference" in captured.out


class TestContinueConfigIntegration:
    """Integration tests for Continue configuration generator."""

    @pytest.mark.integration
    @patch("builtins.input")
    @patch("subprocess.run")
    def test_full_integration_with_ollama(self, mock_run, mock_input):
        """Test full integration with Ollama models detected."""
        generator = ContinueConfigGenerator()

        # Use temp directory
        temp_dir = tempfile.mkdtemp()
        generator.continue_dir = Path(temp_dir) / ".continue"
        generator.config_path = generator.continue_dir / "config.yaml"

        try:
            # Mock Ollama with multiple models
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="NAME                    ID              SIZE      MODIFIED\n"
                "llama2:latest          abc123          3.8 GB    2 days ago\n"
                "codestral:latest       def456          7.1 GB    1 week ago\n"
                "deepseek-coder:6.7b    ghi789          3.8 GB    3 days ago\n",
            )

            # Mock user inputs
            mock_input.side_effect = [
                "y",  # Configure OpenAI
                "sk-test-key",  # OpenAI key
                "n",  # Don't configure Anthropic
            ]

            success = generator.generate_config()

            assert success is True
            assert generator.config_path.exists()

            # Load and verify configuration
            with open(generator.config_path, "r") as f:
                config = yaml.safe_load(f)

            # Should have 3 Ollama + 1 OpenAI + 1 Anthropic template
            assert len(config["models"]) == 5

            # Verify autocomplete model was set
            assert config["tabAutocompleteModel"] is not None
            assert "codestral" in config["tabAutocompleteModel"]["model"]

            # Verify OpenAI has real key
            openai_model = next(
                m for m in config["models"] if m["provider"] == "openai"
            )
            assert openai_model["apiKey"] == "sk-test-key"

        finally:
            # Cleanup
            import shutil

            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
