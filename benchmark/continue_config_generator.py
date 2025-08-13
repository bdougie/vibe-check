#!/usr/bin/env python3
"""
Continue Configuration Generator

Automatically generates Continue config.yaml based on available models
and user preferences.
"""

from pathlib import Path
import subprocess
import sys
from typing import List

import yaml


class ContinueConfigGenerator:
    """Generates Continue configuration files for AI-powered coding assistants."""

    def __init__(self):
        self.continue_dir = Path.home() / ".continue"
        self.config_path = self.continue_dir / "config.yaml"
        self.ollama_models = []
        self.config = {
            "name": "Continue Configuration",
            "version": "1.0",
            "schema": "1.0.0",
            "models": [],
            "tabAutocompleteModel": None,
            "embeddingsProvider": {"provider": "transformers.js"},
            "reranker": {"name": "voyage", "params": {"model": "rerank-lite-1"}},
        }

    def detect_ollama_models(self) -> List[str]:
        """Detect available Ollama models on the system."""
        try:
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )

            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split("\n")
                # Skip header line
                models = []
                for line in lines[1:]:
                    if line.strip():
                        # Model name is the first column
                        model_name = line.split()[0]
                        # Remove the tag if present (e.g., "llama2:latest" -> "llama2")
                        base_name = model_name.split(":")[0]
                        models.append(base_name)

                self.ollama_models = models
                return models

        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("⚠️  Ollama not found or not responding")

        return []

    def add_ollama_models(self):
        """Add detected Ollama models to configuration."""
        if not self.ollama_models:
            return

        print(f"\n✅ Found {len(self.ollama_models)} Ollama models:")

        for model in self.ollama_models:
            print(f"   • {model}")

            # Determine appropriate roles based on model type
            roles = []
            if (
                "code" in model.lower()
                or "codestral" in model.lower()
                or "deepseek" in model.lower()
            ):
                roles = ["chat", "autocomplete", "edit"]
            elif "llama" in model.lower() or "mistral" in model.lower():
                roles = ["chat", "edit"]
            else:
                roles = ["chat"]

            model_config = {
                "name": f"Ollama {model}",
                "provider": "ollama",
                "model": model,
                "roles": roles,
            }

            # Add model-specific settings
            if "autocomplete" in roles:
                model_config["autocompleteOptions"] = {
                    "debounceDelay": 250,
                    "maxPromptTokens": 2048,
                    "prefixPercentage": 0.5,
                }

                # Set as default autocomplete model if it's code-focused
                if not self.config["tabAutocompleteModel"] and "code" in model.lower():
                    self.config["tabAutocompleteModel"] = {
                        "title": f"Ollama {model}",
                        "provider": "ollama",
                        "model": model,
                    }

            self.config["models"].append(model_config)

    def add_commercial_models(self):
        """Add commercial model configurations with placeholder API keys."""
        print("\n📝 Adding commercial model templates...")

        # OpenAI configuration
        openai_config = {
            "name": "GPT-4",
            "provider": "openai",
            "model": "gpt-4",
            "apiKey": "YOUR_OPENAI_API_KEY",
            "roles": ["chat", "edit"],
            "defaultCompletionOptions": {"temperature": 0.7, "maxTokens": 2048},
        }

        # Anthropic configuration
        anthropic_config = {
            "name": "Claude 3.5 Sonnet",
            "provider": "anthropic",
            "model": "claude-3-5-sonnet-20241022",
            "apiKey": "YOUR_ANTHROPIC_API_KEY",
            "roles": ["chat", "edit"],
            "defaultCompletionOptions": {"temperature": 0.7, "maxTokens": 4096},
        }

        # Ask user if they want to configure API keys now
        configure_openai = (
            input("\nDo you have an OpenAI API key to configure? (y/n): ")
            .strip()
            .lower()
        )
        if configure_openai == "y":
            api_key = input("Enter your OpenAI API key: ").strip()
            if api_key:
                openai_config["apiKey"] = api_key
                self.config["models"].append(openai_config)
                print("✅ OpenAI configuration added")
        else:
            self.config["models"].append(openai_config)
            print("📝 OpenAI template added (update API key later)")

        configure_anthropic = (
            input("\nDo you have an Anthropic API key to configure? (y/n): ")
            .strip()
            .lower()
        )
        if configure_anthropic == "y":
            api_key = input("Enter your Anthropic API key: ").strip()
            if api_key:
                anthropic_config["apiKey"] = api_key
                self.config["models"].append(anthropic_config)
                print("✅ Anthropic configuration added")
        else:
            self.config["models"].append(anthropic_config)
            print("📝 Anthropic template added (update API key later)")

    def add_context_providers(self):
        """Add context providers configuration."""
        self.config["contextProviders"] = [
            {"name": "code", "params": {}},
            {"name": "docs", "params": {}},
            {"name": "diff", "params": {}},
            {"name": "terminal", "params": {}},
            {"name": "problems", "params": {}},
            {"name": "folder", "params": {}},
            {"name": "codebase", "params": {}},
        ]

    def add_slash_commands(self):
        """Add useful slash commands."""
        self.config["slashCommands"] = [
            {"name": "edit", "description": "Edit selected code"},
            {"name": "comment", "description": "Write comments for the selected code"},
            {
                "name": "share",
                "description": "Export the current chat session to markdown",
            },
            {"name": "cmd", "description": "Generate a shell command"},
            {"name": "commit", "description": "Generate a git commit message"},
        ]

    def add_custom_commands(self):
        """Add custom commands for common tasks."""
        self.config["customCommands"] = [
            {
                "name": "test",
                "prompt": "Write comprehensive unit tests for the selected code",
                "description": "Generate unit tests",
            },
            {
                "name": "check",
                "prompt": "Review the selected code for potential bugs, security issues, and improvements",
                "description": "Perform code review",
            },
            {
                "name": "benchmark",
                "prompt": "Analyze the performance of the selected code and suggest optimizations",
                "description": "Performance analysis",
            },
        ]

    def save_configuration(self, backup=True):
        """Save the configuration to ~/.continue/config.yaml."""
        # Create .continue directory if it doesn't exist
        self.continue_dir.mkdir(parents=True, exist_ok=True)

        # Backup existing configuration if requested
        if backup and self.config_path.exists():
            backup_path = self.config_path.with_suffix(".yaml.backup")
            import shutil

            shutil.copy(self.config_path, backup_path)
            print(f"\n📁 Backed up existing config to: {backup_path}")

        # Save the new configuration
        with open(self.config_path, "w") as f:
            yaml.dump(self.config, f, default_flow_style=False, sort_keys=False)

        print(f"\n✅ Configuration saved to: {self.config_path}")

    def print_instructions(self):
        """Print instructions for manual configuration."""
        print("\n" + "=" * 60)
        print("📚 MANUAL CONFIGURATION INSTRUCTIONS")
        print("=" * 60)

        print("\n1. Configuration file location:")
        print(f"   {self.config_path}")

        print("\n2. To add/modify API keys:")
        print("   Edit the config.yaml file and replace:")
        print("   - YOUR_OPENAI_API_KEY with your OpenAI key")
        print("   - YOUR_ANTHROPIC_API_KEY with your Anthropic key")

        print("\n3. To add more models:")
        print("   Add entries to the 'models' section following the existing format")

        print("\n4. To change autocomplete model:")
        print("   Modify the 'tabAutocompleteModel' section")

        print("\n5. Continue documentation:")
        print("   https://docs.continue.dev/reference")

        print("\n6. After making changes:")
        print("   Restart VS Code or reload the Continue extension")

        print("\n" + "=" * 60)

    def generate_config(self):
        """Main method to generate the complete configuration."""
        print("🚀 Continue Configuration Generator")
        print("=" * 60)

        # Check for existing configuration
        if self.config_path.exists():
            overwrite = (
                input(
                    f"\n⚠️  Configuration already exists at {self.config_path}\n   Overwrite? (y/n): "
                )
                .strip()
                .lower()
            )
            if overwrite != "y":
                print("❌ Configuration generation cancelled")
                return False

        # Detect and add Ollama models
        print("\n🔍 Detecting Ollama models...")
        self.detect_ollama_models()
        self.add_ollama_models()

        # Add commercial models
        self.add_commercial_models()

        # Add context providers
        self.add_context_providers()

        # Add slash commands
        self.add_slash_commands()

        # Add custom commands
        self.add_custom_commands()

        # Save configuration
        self.save_configuration()

        # Print instructions
        self.print_instructions()

        return True


def main():
    """Main entry point for the configuration generator."""
    generator = ContinueConfigGenerator()

    try:
        success = generator.generate_config()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Configuration generation cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error generating configuration: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
