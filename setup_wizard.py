#!/usr/bin/env python3
"""
Interactive Setup Wizard for Vibe Check

This wizard guides new users through the complete setup process including:
- Python version and dependency checks
- Ollama installation guidance
- Model downloads
- Continue extension configuration
- Running a test benchmark
"""

import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
from typing import Optional

# Check for rich library for better UI
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.prompt import Confirm, Prompt
    from rich.table import Table

    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None


# ANSI color codes for fallback
class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


def print_header(text: str) -> None:
    """Print a formatted header."""
    if RICH_AVAILABLE:
        console.print(Panel(text, style="bold cyan"))
    else:
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
        print(f"{Colors.CYAN}{Colors.BOLD}{text}{Colors.ENDC}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


def print_success(text: str) -> None:
    """Print a success message."""
    if RICH_AVAILABLE:
        console.print(f"[green]✅ {text}[/green]")
    else:
        print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")


def print_warning(text: str) -> None:
    """Print a warning message."""
    if RICH_AVAILABLE:
        console.print(f"[yellow]⚠️  {text}[/yellow]")
    else:
        print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")


def print_error(text: str) -> None:
    """Print an error message."""
    if RICH_AVAILABLE:
        console.print(f"[red]❌ {text}[/red]")
    else:
        print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")


def print_info(text: str) -> None:
    """Print an info message."""
    if RICH_AVAILABLE:
        console.print(f"[blue]ℹ️  {text}[/blue]")
    else:
        print(f"{Colors.BLUE}ℹ️  {text}{Colors.ENDC}")


def ask_yes_no(question: str, default: bool = True) -> bool:
    """Ask a yes/no question."""
    if RICH_AVAILABLE:
        return Confirm.ask(question, default=default)
    else:
        default_str = "Y/n" if default else "y/N"
        while True:
            response = input(f"{question} [{default_str}]: ").strip().lower()
            if not response:
                return default
            if response in ["y", "yes"]:
                return True
            if response in ["n", "no"]:
                return False
            print("Please answer 'yes' or 'no'")


def ask_input(prompt: str, default: Optional[str] = None) -> str:
    """Ask for user input."""
    if RICH_AVAILABLE:
        return Prompt.ask(prompt, default=default)
    else:
        if default:
            response = input(f"{prompt} [{default}]: ").strip()
            return response if response else default
        else:
            return input(f"{prompt}: ").strip()


class SetupWizard:
    """Interactive setup wizard for Vibe Check."""

    def __init__(self):
        """Initialize the setup wizard."""
        self.python_version = sys.version_info
        self.os_type = platform.system()
        self.has_uv = False
        self.has_ollama = False
        self.ollama_models = []
        self.continue_installed = False
        self.setup_complete = False

    def run(self) -> None:
        """Run the complete setup wizard."""
        print_header("🚀 Welcome to Vibe Check Setup Wizard")
        print_info(
            f"This wizard will guide you through setting up Vibe Check on {self.os_type}"
        )
        print()

        # Step 1: Check Python version
        if not self.check_python_version():
            return

        # Step 2: Check and install dependencies
        if not self.check_dependencies():
            return

        # Step 3: Check/Install Ollama
        if not self.setup_ollama():
            print_warning("Ollama setup skipped. You can still use commercial models.")

        # Step 4: Download models
        if self.has_ollama:
            self.download_models()

        # Step 5: Configure Continue (optional)
        self.configure_continue()

        # Step 6: Run test benchmark
        if ask_yes_no("\nWould you like to run a test benchmark?"):
            self.run_test_benchmark()

        # Complete!
        self.setup_complete = True
        self.print_completion_message()

    def check_python_version(self) -> bool:
        """Check if Python version meets requirements."""
        print_header("Step 1: Checking Python Version")

        min_version = (3, 8)
        current = f"{self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}"

        if self.python_version >= min_version:
            print_success(f"Python {current} is installed (minimum required: 3.8)")
            return True
        else:
            print_error(
                f"Python {current} is too old. Please install Python 3.8 or higher."
            )
            print_info(
                "Visit https://www.python.org/downloads/ to download the latest version."
            )
            return False

    def check_dependencies(self) -> bool:
        """Check and install project dependencies."""
        print_header("Step 2: Checking Dependencies")

        # Check for uv
        if shutil.which("uv"):
            self.has_uv = True
            print_success("uv (fast package manager) is installed")
        else:
            print_info(
                "uv is not installed (optional but recommended for faster installs)"
            )
            if ask_yes_no(
                "Would you like to install uv for faster package management?"
            ):
                if self.install_uv():
                    self.has_uv = True

        # Check for Git
        if not shutil.which("git"):
            print_error("Git is not installed. Please install Git first.")
            self.print_git_install_instructions()
            return False
        else:
            print_success("Git is installed")

        # Install Python dependencies
        print_info("Installing Python dependencies...")
        return self.install_python_dependencies()

    def install_uv(self) -> bool:
        """Install uv package manager."""
        print_info("Installing uv...")

        if self.os_type == "Windows":
            cmd = 'powershell -c "irm https://astral.sh/uv/install.ps1 | iex"'
        else:
            cmd = "curl -LsSf https://astral.sh/uv/install.sh | sh"

        try:
            subprocess.run(cmd, shell=True, check=True)
            print_success("uv installed successfully")
            return True
        except subprocess.CalledProcessError:
            print_warning("Failed to install uv. Falling back to pip.")
            return False

    def install_python_dependencies(self) -> bool:
        """Install Python dependencies from requirements.txt."""
        if not Path("requirements.txt").exists():
            print_error(
                "requirements.txt not found. Are you in the vibe-check directory?"
            )
            return False

        try:
            if self.has_uv:
                cmd = ["uv", "pip", "install", "-r", "requirements.txt"]
            else:
                cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]

            subprocess.run(cmd, check=True)
            print_success("Python dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print_error(f"Failed to install dependencies: {e}")
            return False

    def setup_ollama(self) -> bool:
        """Check and setup Ollama for local models."""
        print_header("Step 3: Setting up Ollama (for local models)")

        if shutil.which("ollama"):
            self.has_ollama = True
            print_success("Ollama is installed")

            # Check if Ollama is running
            try:
                result = subprocess.run(
                    ["ollama", "list"], capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    print_success("Ollama service is running")
                    self.parse_ollama_models(result.stdout)
                else:
                    print_warning("Ollama is installed but not running")
                    if ask_yes_no("Would you like to start Ollama?"):
                        self.start_ollama()
            except subprocess.TimeoutExpired:
                print_warning("Ollama is not responding. Please start it manually.")
            except Exception as e:
                print_warning(f"Could not check Ollama status: {e}")
        else:
            print_info("Ollama is not installed (required for local models)")
            if ask_yes_no("Would you like instructions for installing Ollama?"):
                self.print_ollama_install_instructions()

                # Wait for user to install
                if ask_yes_no("Have you installed Ollama?"):
                    return self.setup_ollama()  # Recursive check
            return False

        return self.has_ollama

    def parse_ollama_models(self, output: str) -> None:
        """Parse the output of 'ollama list' to get available models."""
        lines = output.strip().split("\n")
        if len(lines) > 1:  # Skip header
            for line in lines[1:]:
                parts = line.split()
                if parts:
                    model_name = parts[0].split(":")[0]  # Get base name without tag
                    if model_name not in self.ollama_models:
                        self.ollama_models.append(model_name)

        if self.ollama_models:
            print_success(
                f"Found {len(self.ollama_models)} Ollama models: {', '.join(self.ollama_models)}"
            )

    def start_ollama(self) -> bool:
        """Try to start the Ollama service."""
        print_info("Starting Ollama service...")

        if self.os_type == "Darwin":  # macOS
            try:
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                time.sleep(3)  # Give it time to start
                print_success("Ollama service started")
                return True
            except Exception as e:
                print_error(f"Failed to start Ollama: {e}")
                return False
        else:
            print_info(
                "Please start Ollama manually in another terminal: 'ollama serve'"
            )
            return ask_yes_no("Is Ollama running now?")

    def download_models(self) -> None:
        """Guide user through downloading Ollama models."""
        print_header("Step 4: Downloading Models")

        recommended_models = [
            ("qwen2.5-coder:1.5b", "Minimal coding model (1GB)"),
            ("qwen2.5-coder:7b", "Good coding model (4GB)"),
            ("llama3.2:3b", "Lightweight general (2GB)"),
            ("codestral:22b", "Mistral's code model (13GB, needs 16GB+ RAM)"),
        ]

        print_info("Recommended models for benchmarking:")
        if RICH_AVAILABLE:
            table = Table()
            table.add_column("Model", style="cyan")
            table.add_column("Description", style="white")
            for model, desc in recommended_models:
                table.add_row(model, desc)
            console.print(table)
        else:
            for model, desc in recommended_models:
                print(f"  • {model}: {desc}")

        print()
        if not self.ollama_models:
            print_warning("No models currently installed")
            if ask_yes_no("Would you like to download a model now?"):
                model = ask_input("Enter model name (e.g., qwen2.5-coder:1.5b)")
                self.download_model(model)
        else:
            if ask_yes_no("Would you like to download additional models?"):
                model = ask_input("Enter model name")
                self.download_model(model)

    def download_model(self, model_name: str) -> bool:
        """Download a specific Ollama model."""
        print_info(f"Downloading {model_name}... (this may take a few minutes)")

        try:
            subprocess.run(["ollama", "pull", model_name], check=True)
            print_success(f"Model {model_name} downloaded successfully")
            self.ollama_models.append(model_name.split(":")[0])
            return True
        except subprocess.CalledProcessError:
            print_error(f"Failed to download {model_name}")
            return False
        except KeyboardInterrupt:
            print_warning("Download cancelled")
            return False

    def configure_continue(self) -> None:
        """Guide user through Continue extension configuration."""
        print_header("Step 5: Continue Extension Configuration (Optional)")

        print_info("Continue is a VS Code extension for AI-assisted coding")
        print_info("It's optional but recommended for the best experience")

        if ask_yes_no("Would you like help configuring Continue?"):
            print_info("\n1. Install the Continue extension in VS Code:")
            print_info(
                "   https://marketplace.visualstudio.com/items?itemName=Continue.continue"
            )
            print_info(
                "\n2. Open Continue settings (Cmd/Ctrl + Shift + P -> 'Continue: Open Settings')"
            )
            print_info("\n3. Add your models to the configuration")

            if self.ollama_models:
                print_info(
                    "\nFor your Ollama models, add this to your Continue config:"
                )
                config_snippet = self.generate_continue_config()
                if RICH_AVAILABLE:
                    console.print(
                        Panel(config_snippet, title="Continue Config", language="yaml")
                    )
                else:
                    print("\n" + config_snippet + "\n")

            self.continue_installed = ask_yes_no("Have you configured Continue?")

    def generate_continue_config(self) -> str:
        """Generate a Continue configuration snippet."""
        config = "models:\n"
        for model in self.ollama_models:
            config += f"""  - name: "{model}"
    provider: "ollama"
    model: "{model}"
"""
        return config

    def run_test_benchmark(self) -> None:
        """Run a test benchmark to verify setup."""
        print_header("Step 6: Running Test Benchmark")

        print_info("Running a simple smoke test to verify everything works...")

        # First try the smoke test script
        if Path("run_smoke_test.py").exists():
            try:
                result = subprocess.run(
                    [sys.executable, "run_smoke_test.py"],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )
                if result.returncode == 0:
                    print_success("Smoke test passed! Your setup is working correctly.")
                else:
                    print_warning("Smoke test had issues. Checking output...")
                    if result.stderr:
                        print(result.stderr)
            except subprocess.TimeoutExpired:
                print_warning("Smoke test timed out")
            except Exception as e:
                print_warning(f"Could not run smoke test: {e}")

        # Offer to run a real benchmark
        if self.ollama_models and ask_yes_no(
            "\nWould you like to run a real benchmark with a local model?"
        ):
            model = self.ollama_models[0]
            print_info(f"Running benchmark with {model}...")

            try:
                cmd = [
                    sys.executable,
                    "benchmark/task_runner.py",
                    f"ollama/{model}",
                    "benchmark/tasks/easy/fix_typo.md",
                    "--skip-ollama-check",
                ]
                subprocess.run(cmd, check=True)
                print_success("Benchmark completed successfully!")
            except subprocess.CalledProcessError:
                print_error("Benchmark failed. Please check the error messages above.")
            except Exception as e:
                print_error(f"Could not run benchmark: {e}")

    def print_git_install_instructions(self) -> None:
        """Print Git installation instructions for different platforms."""
        print_info("\nGit Installation Instructions:")

        if self.os_type == "Darwin":  # macOS
            print_info("  macOS: brew install git")
            print_info("  Or download from: https://git-scm.com/download/mac")
        elif self.os_type == "Linux":
            print_info("  Ubuntu/Debian: sudo apt install git")
            print_info("  Fedora: sudo dnf install git")
            print_info("  Arch: sudo pacman -S git")
        elif self.os_type == "Windows":
            print_info("  Download from: https://git-scm.com/download/win")
            print_info("  Or use: winget install --id Git.Git")

    def print_ollama_install_instructions(self) -> None:
        """Print Ollama installation instructions."""
        print_info("\nOllama Installation Instructions:")

        if self.os_type == "Darwin":  # macOS
            print_info("  1. Download from: https://ollama.com/download/mac")
            print_info("  2. Or use Homebrew: brew install ollama")
        elif self.os_type == "Linux":
            print_info("  Run: curl -fsSL https://ollama.com/install.sh | sh")
        elif self.os_type == "Windows":
            print_info("  Download from: https://ollama.com/download/windows")

        print_info("\nAfter installation, start Ollama with: ollama serve")

    def print_completion_message(self) -> None:
        """Print the completion message with next steps."""
        print_header("🎉 Setup Complete!")

        print_success("Vibe Check is ready to use!")

        print_info("\n📚 Next Steps:")
        print_info("1. View available tasks: python benchmark/task_runner.py")
        print_info("2. Run a benchmark: python benchmark/task_runner.py <model> <task>")

        if self.ollama_models:
            model = self.ollama_models[0]
            print_info("\n💡 Example with your local model:")
            print_info(
                f"   python benchmark/task_runner.py ollama/{model} benchmark/tasks/easy/fix_typo.md"
            )

        print_info("\n📖 Documentation:")
        print_info("   • Quick Start: QUICKSTART.md")
        print_info("   • Full Guide: docs/setup.md")
        print_info("   • Manual Guide: docs/manual-guide.md")

        print_info("\n🤝 Get Help:")
        print_info("   • GitHub Issues: https://github.com/bdougie/vibe-check/issues")

        # Save setup status
        self.save_setup_status()

    def save_setup_status(self) -> None:
        """Save the setup status to a file for future reference."""
        status = {
            "setup_complete": self.setup_complete,
            "python_version": f"{self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}",
            "os_type": self.os_type,
            "has_uv": self.has_uv,
            "has_ollama": self.has_ollama,
            "ollama_models": self.ollama_models,
            "continue_configured": self.continue_installed,
            "setup_date": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        setup_file = Path(".vibe_check_setup.json")
        try:
            with open(setup_file, "w") as f:
                json.dump(status, f, indent=2)
            print_info(f"\nSetup status saved to {setup_file}")
        except Exception as e:
            print_warning(f"Could not save setup status: {e}")


def main():
    """Main entry point for the setup wizard."""
    wizard = SetupWizard()

    try:
        wizard.run()
    except KeyboardInterrupt:
        print_warning("\n\nSetup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        print_info(
            "Please report this issue at: https://github.com/bdougie/vibe-check/issues"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
