#!/usr/bin/env python3
"""
Ollama installation and health check module.

This module provides functionality to verify Ollama is properly installed,
running, and has models available for benchmarking.
"""

import json
import logging
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Union

try:
    from benchmark.validators import sanitize_error_message, validate_model_name
except ImportError:
    # Fallback if validators module is not available
    def validate_model_name(name: str) -> str:
        return name.strip() if name else name

    def sanitize_error_message(error: Exception) -> str:
        return str(error)


# Set up logging
logger = logging.getLogger(__name__)


class OllamaChecker:
    """Check Ollama installation and status."""

    def __init__(self, verbose: bool = True):
        """Initialize the Ollama checker.

        Args:
            verbose: Whether to print detailed messages
        """
        self.verbose = verbose
        self.ollama_binary = None
        self.is_installed = False
        self.is_running = False
        self.available_models = []
        self.errors = []
        self.warnings = []

    def print_message(self, message: str, level: str = "info") -> None:
        """Print a message if verbose mode is enabled.

        Args:
            message: The message to print
            level: Message level (info, success, warning, error)
        """
        if not self.verbose:
            return

        symbols = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "checking": "🔍",
        }

        symbol = symbols.get(level, "•")
        print(f"{symbol}  {message}")

    def check_installation(self) -> bool:
        """Check if Ollama is installed on the system.

        Returns:
            True if Ollama is installed, False otherwise
        """
        self.print_message("Checking Ollama installation...", "checking")

        # Check if ollama binary exists in PATH
        self.ollama_binary = shutil.which("ollama")

        if self.ollama_binary:
            self.is_installed = True
            self.print_message(f"Ollama found at: {self.ollama_binary}", "success")

            # Try to get version information
            try:
                result = subprocess.run(
                    ["ollama", "--version"], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0 and result.stdout:
                    version = result.stdout.strip()
                    self.print_message(f"Ollama version: {version}", "info")
            except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
                logger.error(f"Ollama version check failed: {e}")
                self.warnings.append("Could not determine Ollama version")
                self.print_message("Could not determine Ollama version", "warning")
        else:
            self.is_installed = False
            self.errors.append("Ollama is not installed or not in PATH")
            self.print_message("Ollama is not installed", "error")
            self.print_message(
                "Please install Ollama from: https://ollama.ai/download", "info"
            )

        return self.is_installed

    def check_service_running(self) -> bool:
        """Check if Ollama service is running.

        Returns:
            True if service is running, False otherwise
        """
        if not self.is_installed:
            self.print_message(
                "Skipping service check (Ollama not installed)", "warning"
            )
            return False

        self.print_message("Checking if Ollama service is running...", "checking")

        # Try to list models as a way to check if service is running
        try:
            result = subprocess.run(
                ["ollama", "list"], capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0:
                self.is_running = True
                self.print_message("Ollama service is running", "success")
            else:
                self.is_running = False
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"

                if (
                    "connection refused" in error_msg.lower()
                    or "could not connect" in error_msg.lower()
                ):
                    self.errors.append("Ollama service is not running")
                    self.print_message("Ollama service is not running", "error")
                    self.print_message(
                        "Please start Ollama:\n"
                        "  - On macOS: Run 'ollama serve' or start from Applications\n"
                        "  - On Linux: Run 'systemctl start ollama' or 'ollama serve'\n"
                        "  - On Windows: Start Ollama from the Start Menu",
                        "info",
                    )
                else:
                    self.errors.append(f"Error checking Ollama service: {error_msg}")
                    self.print_message(f"Error checking service: {error_msg}", "error")

        except subprocess.TimeoutExpired:
            self.is_running = False
            self.errors.append("Timeout while checking Ollama service")
            self.print_message("Timeout while checking Ollama service", "error")

        except subprocess.SubprocessError as e:
            self.is_running = False
            logger.error(f"Ollama command error: {e}")
            error_msg = sanitize_error_message(e)
            self.errors.append(f"Error running ollama command: {error_msg}")
            self.print_message(f"Error running ollama command: {error_msg}", "error")

        return self.is_running

    def list_available_models(self) -> List[str]:
        """List available Ollama models.

        Returns:
            List of available model names
        """
        if not self.is_running:
            self.print_message("Skipping model list (service not running)", "warning")
            return []

        self.print_message("Checking available models...", "checking")

        try:
            result = subprocess.run(
                ["ollama", "list"], capture_output=True, text=True, timeout=10
            )

            if result.returncode == 0 and result.stdout:
                # Parse the output (skip header line)
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:  # Has header and at least one model
                    for line in lines[1:]:  # Skip header
                        # Format: NAME                           ID              SIZE      MODIFIED
                        parts = line.split()
                        if parts:
                            model_name = parts[0]
                            # Remove the tag if present (e.g., "llama2:latest" -> "llama2")
                            base_name = model_name.split(":")[0]
                            if base_name not in self.available_models:
                                self.available_models.append(base_name)

                    if self.available_models:
                        self.print_message(
                            f"Found {len(self.available_models)} model(s): {', '.join(self.available_models)}",
                            "success",
                        )
                    else:
                        self.warnings.append("No models found")
                        self.print_message("No models found", "warning")
                        self.print_message(
                            "Download a model with: ollama pull <model-name>\n"
                            "Example: ollama pull llama2",
                            "info",
                        )
                else:
                    self.warnings.append("No models installed")
                    self.print_message("No models installed", "warning")
                    self.print_message(
                        "Download a model with: ollama pull <model-name>\n"
                        "Popular models:\n"
                        "  - ollama pull llama2\n"
                        "  - ollama pull codellama\n"
                        "  - ollama pull mistral\n"
                        "  - ollama pull mixtral",
                        "info",
                    )
            else:
                error_msg = (
                    result.stderr.strip() if result.stderr else "Could not list models"
                )
                self.warnings.append(error_msg)
                self.print_message(f"Could not list models: {error_msg}", "warning")

        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            logger.error(f"Model listing error: {e}")
            error_msg = sanitize_error_message(e)
            self.warnings.append(f"Error listing models: {error_msg}")
            self.print_message(f"Error listing models: {error_msg}", "warning")

        return self.available_models

    def check_model_available(self, model_name: str) -> bool:
        """Check if a specific model is available.

        Args:
            model_name: Name of the model to check

        Returns:
            True if model is available, False otherwise
        """
        try:
            # Validate model name first
            model_name = validate_model_name(model_name)
        except Exception as e:
            logger.warning(f"Invalid model name: {e}")
            return False

        if not self.available_models:
            self.list_available_models()

        # Check both exact match and base name match
        model_base = model_name.split(":")[0]
        return (
            model_name in self.available_models or model_base in self.available_models
        )

    def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama registry.

        Args:
            model_name: Name of the model to pull

        Returns:
            True if successful, False otherwise
        """
        if not self.is_running:
            self.print_message("Cannot pull model (service not running)", "error")
            return False

        # Validate model name to prevent command injection
        try:
            model_name = validate_model_name(model_name)
        except Exception as e:
            self.print_message(f"Invalid model name: {e}", "error")
            return False

        self.print_message(f"Pulling model '{model_name}'...", "info")
        self.print_message(
            "This may take several minutes depending on model size", "info"
        )

        try:
            # Run with real-time output
            process = subprocess.Popen(
                ["ollama", "pull", model_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            # Stream output in real-time
            for line in process.stdout:
                if self.verbose:
                    print(f"  {line.rstrip()}")

            process.wait()

            if process.returncode == 0:
                self.print_message(
                    f"Successfully pulled model '{model_name}'", "success"
                )
                # Refresh model list
                self.list_available_models()
                return True
            else:
                self.print_message(f"Failed to pull model '{model_name}'", "error")
                return False

        except subprocess.SubprocessError as e:
            logger.error(f"Model pull error: {e}")
            error_msg = sanitize_error_message(e)
            self.print_message(f"Error pulling model: {error_msg}", "error")
            return False

    def run_full_check(self) -> Dict[str, Union[bool, List[str], Any]]:
        """Run complete Ollama health check.

        Returns:
            Dictionary with check results
        """
        self.print_message("Starting Ollama health check...\n", "info")

        # Run all checks
        self.check_installation()
        self.check_service_running()
        self.list_available_models()

        # Prepare summary
        results = {
            "installed": self.is_installed,
            "running": self.is_running,
            "models": self.available_models,
            "errors": self.errors,
            "warnings": self.warnings,
            "ready": self.is_installed
            and self.is_running
            and len(self.available_models) > 0,
        }

        # Print summary
        self.print_message("\n" + "=" * 50, "info")
        self.print_message("OLLAMA HEALTH CHECK SUMMARY", "info")
        self.print_message("=" * 50, "info")

        if results["ready"]:
            self.print_message("✅ Ollama is ready for benchmarking!", "success")
        else:
            self.print_message("❌ Ollama setup incomplete", "error")

            if not self.is_installed:
                self.print_message(
                    "\n1. Install Ollama from: https://ollama.ai/download", "info"
                )
            elif not self.is_running:
                self.print_message(
                    "\n2. Start Ollama service (run 'ollama serve')", "info"
                )
            elif not self.available_models:
                self.print_message(
                    "\n3. Pull a model (e.g., 'ollama pull llama2')", "info"
                )

        return results

    def ensure_model_available(self, model_name: str, auto_pull: bool = False) -> bool:
        """Ensure a specific model is available, optionally pulling it.

        Args:
            model_name: Name of the model to ensure
            auto_pull: Whether to automatically pull if not available

        Returns:
            True if model is available, False otherwise
        """
        # Validate model name first
        try:
            model_name = validate_model_name(model_name)
        except Exception as e:
            self.print_message(f"Invalid model name: {e}", "error")
            return False

        if self.check_model_available(model_name):
            self.print_message(f"Model '{model_name}' is available", "success")
            return True

        self.print_message(f"Model '{model_name}' is not available", "warning")

        if auto_pull:
            self.print_message(f"Attempting to pull model '{model_name}'...", "info")
            return self.pull_model(model_name)
        else:
            self.print_message(
                f"To download this model, run: ollama pull {model_name}", "info"
            )
            return False


def main():
    """Main entry point for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Check Ollama installation and health")
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress detailed output"
    )
    parser.add_argument("--model", "-m", help="Check if specific model is available")
    parser.add_argument(
        "--pull",
        action="store_true",
        help="Pull model if not available (requires --model)",
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")

    args = parser.parse_args()

    # Create checker
    checker = OllamaChecker(verbose=not args.quiet and not args.json)

    # Run checks
    if args.model:
        # Check specific model
        checker.check_installation()
        checker.check_service_running()
        available = checker.ensure_model_available(args.model, auto_pull=args.pull)

        if args.json:
            result = {
                "model": args.model,
                "available": available,
                "installed": checker.is_installed,
                "running": checker.is_running,
            }
            print(json.dumps(result, indent=2))

        sys.exit(0 if available else 1)
    else:
        # Run full check
        results = checker.run_full_check()

        if args.json:
            print(json.dumps(results, indent=2))

        sys.exit(0 if results["ready"] else 1)


if __name__ == "__main__":
    main()
