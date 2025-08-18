#!/usr/bin/env python3
"""
Configuration Management for Continue CLI Integration

Handles creation and management of CN config files for different models and providers.
"""

import logging
from pathlib import Path
import tempfile
from typing import Any, Dict, Optional

import yaml

logger = logging.getLogger(__name__)


class CNConfigManager:
    """Manages Continue CLI configuration files for different models."""

    def __init__(self):
        self.temp_configs = []  # Track temp files for cleanup

    def create_config(
        self,
        model_name: str,
        provider: str = "auto",
        custom_settings: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """Create a CN configuration file for the specified model.

        Args:
            model_name: Name of the model (e.g., "gpt-4", "ollama/llama2")
            provider: Provider type or "auto" to detect from model name
            custom_settings: Additional model settings

        Returns:
            Path to the created config file
        """
        # Auto-detect provider from model name
        if provider == "auto":
            provider = self._detect_provider(model_name)

        # Extract actual model name from prefixed formats
        actual_model_name = self._extract_model_name(model_name, provider)

        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, prefix=f"cn_config_{provider}_"
        )

        try:
            # Write proper YAML config
            yaml_content = self._build_yaml_content(actual_model_name, provider, custom_settings)
            temp_file.write(yaml_content)
            temp_file.flush()
            config_path = Path(temp_file.name)

            self.temp_configs.append(config_path)
            logger.debug(f"Created CN config: {config_path}")

            return config_path

        finally:
            temp_file.close()

    def _detect_provider(self, model_name: str) -> str:
        """Detect provider from model name."""
        model_lower = model_name.lower()

        # Check for Ollama models (including those with : notation)
        if model_lower.startswith("ollama/") or ":" in model_lower:
            return "ollama"
        # Check for OpenAI models (but not gpt-oss which is Ollama)
        elif any(x in model_lower for x in ["gpt-3", "gpt-4", "openai"]) and "gpt-oss" not in model_lower:
            return "openai"
        elif any(x in model_lower for x in ["claude", "anthropic"]):
            return "anthropic"
        elif any(x in model_lower for x in ["gemini", "palm"]):
            return "google"
        elif "mistral" in model_lower:
            return "mistral"
        elif "cohere" in model_lower:
            return "cohere"
        # Models like qwen, gpt-oss are typically Ollama
        elif any(x in model_lower for x in ["qwen", "gpt-oss", "llama", "codellama"]):
            return "ollama"
        else:
            return "ollama"  # Default to Ollama for unknown models

    def _extract_model_name(self, model_name: str, provider: str) -> str:
        """Extract the actual model name from prefixed formats."""
        if provider == "ollama" and model_name.startswith("ollama/"):
            return model_name[7:]  # Remove "ollama/" prefix
        return model_name

    def _build_yaml_content(
        self,
        model_name: str,
        provider: str,
        custom_settings: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build the YAML configuration content."""
        yaml_content = f"""name: vibe-check-assistant
version: 0.0.1
models:
  - name: {model_name}
    provider: {provider}
    model: {model_name}
    roles:
      - chat
      - edit
      - apply
"""
        
        # Add API key if needed
        if provider == "openai":
            yaml_content += f"    apiKey: ${{OPENAI_API_KEY}}\n"
        elif provider == "anthropic":
            yaml_content += f"    apiKey: ${{ANTHROPIC_API_KEY}}\n"
        
        # Add capabilities only for models that support tools
        if any(x in model_name.lower() for x in ["gpt-oss", "gpt-4", "gpt-3", "claude"]):
            yaml_content += "    capabilities:\n      - tool_use\n"
        
        # Add custom settings if provided
        if custom_settings:
            for key, value in custom_settings.items():
                if key not in ["provider", "model", "name"]:
                    yaml_content += f"    {key}: {value}\n"
        
        return yaml_content

    def _get_model_config(
        self,
        model_name: str,
        provider: str,
        custom_settings: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Get model-specific configuration."""
        base_config = {"model": model_name}

        # Provider-specific settings
        if provider == "ollama":
            base_config.update({"provider": "ollama"})
        elif provider == "openai":
            base_config.update({"provider": "openai", "apiKey": "${OPENAI_API_KEY}"})
        elif provider == "anthropic":
            base_config.update(
                {"provider": "anthropic", "apiKey": "${ANTHROPIC_API_KEY}"}
            )
        elif provider == "google":
            base_config.update({"provider": "google", "apiKey": "${GOOGLE_API_KEY}"})
        elif provider == "mistral":
            base_config.update({"provider": "mistral", "apiKey": "${MISTRAL_API_KEY}"})
        elif provider == "cohere":
            base_config.update({"provider": "cohere", "apiKey": "${COHERE_API_KEY}"})

        # Apply custom settings
        if custom_settings:
            base_config.update(custom_settings)

        return base_config

    def get_model_presets(self) -> Dict[str, Dict[str, Any]]:
        """Get predefined model configurations."""
        return {
            # OpenAI Models
            "gpt-4": {"provider": "openai", "temperature": 0.7, "max_tokens": 4096},
            "gpt-4-turbo": {
                "provider": "openai",
                "temperature": 0.7,
                "max_tokens": 4096,
            },
            "gpt-3.5-turbo": {
                "provider": "openai",
                "temperature": 0.7,
                "max_tokens": 2048,
            },
            # Anthropic Models
            "claude-3-opus": {
                "provider": "anthropic",
                "temperature": 0.7,
                "max_tokens": 4096,
            },
            "claude-3-sonnet": {
                "provider": "anthropic",
                "temperature": 0.7,
                "max_tokens": 4096,
            },
            "claude-3-haiku": {
                "provider": "anthropic",
                "temperature": 0.7,
                "max_tokens": 2048,
            },
            # Common Ollama Models
            "ollama/llama2": {"provider": "ollama", "temperature": 0.7},
            "ollama/codellama": {
                "provider": "ollama",
                "temperature": 0.1,  # Lower temp for code
            },
            "ollama/mistral": {"provider": "ollama", "temperature": 0.7},
            "ollama/qwen2.5-coder": {"provider": "ollama", "temperature": 0.1},
        }

    def create_preset_config(self, model_key: str) -> Path:
        """Create config using a preset model configuration.

        Args:
            model_key: Key from get_model_presets()

        Returns:
            Path to created config file
        """
        presets = self.get_model_presets()

        if model_key not in presets:
            raise ValueError(f"Unknown model preset: {model_key}")

        preset = presets[model_key]
        provider = preset["provider"]

        # Extract model name
        if model_key.startswith("ollama/"):
            model_name = model_key[7:]
        else:
            model_name = model_key

        # Remove provider from settings
        custom_settings = {k: v for k, v in preset.items() if k != "provider"}

        return self.create_config(model_name, provider, custom_settings)

    def cleanup_temp_configs(self):
        """Remove all temporary config files."""
        for config_path in self.temp_configs:
            try:
                if config_path.exists():
                    config_path.unlink()
                    logger.debug(f"Cleaned up temp config: {config_path}")
            except Exception as e:
                logger.warning(f"Could not remove temp config {config_path}: {e}")

        self.temp_configs.clear()

    def __del__(self):
        """Cleanup on destruction."""
        self.cleanup_temp_configs()


def test_config_manager():
    """Test the configuration manager."""
    manager = CNConfigManager()

    try:
        # Test various model types
        test_models = [
            ("gpt-4", "auto"),
            ("ollama/llama2", "auto"),
            ("claude-3-sonnet", "anthropic"),
        ]

        for model, provider in test_models:
            config_path = manager.create_config(model, provider)
            print(f"Created config for {model}: {config_path}")

            # Read and display the config
            with open(config_path) as f:
                content = f.read()
                print(f"Config content:\n{content}\n")

        # Test preset
        preset_config = manager.create_preset_config("gpt-3.5-turbo")
        print(f"Created preset config: {preset_config}")

    finally:
        manager.cleanup_temp_configs()


if __name__ == "__main__":
    test_config_manager()
