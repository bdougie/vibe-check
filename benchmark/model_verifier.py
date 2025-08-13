#!/usr/bin/env python3
"""
Model download verification script for AI coding benchmarks.

This module helps users verify they have the correct models downloaded,
shows model sizes and download status, and provides guidance for
downloading missing models.
"""

from dataclasses import dataclass
import json
import logging
from pathlib import Path
import platform
import shlex
import shutil
import subprocess
import sys
from typing import Dict, List, Optional, Union

try:
    from benchmark.ollama_check import OllamaChecker
    from benchmark.validators import ValidationError, validate_model_name
except ImportError:
    # Fallback if modules are not available
    class OllamaChecker:
        def __init__(self, verbose=True):
            self.verbose = verbose
            self.available_models = []

        def list_available_models(self):
            return []

    def validate_model_name(name: str) -> str:
        return name.strip() if name else name

    class ValidationError(Exception):
        pass


# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class ModelInfo:
    """Information about a model."""

    name: str
    size: str  # Human-readable size
    size_bytes: int  # Size in bytes for calculations
    ram_required: int  # RAM required in GB
    description: str
    priority: str  # "essential", "recommended", "optional"
    provider: str  # "ollama", "openai", "anthropic", etc.
    fallback: Optional[str] = None  # Fallback model if this one is too large


# Recommended models for benchmarking
RECOMMENDED_MODELS = {
    # Essential models (small, fast, good for basic testing)
    "llama2": ModelInfo(
        name="llama2",
        size="3.8 GB",
        size_bytes=4_082_132_480,
        ram_required=8,
        description="Base Llama 2 model, good general-purpose model",
        priority="essential",
        provider="ollama",
        fallback=None,
    ),
    "codellama": ModelInfo(
        name="codellama",
        size="3.8 GB",
        size_bytes=4_082_132_480,
        ram_required=8,
        description="Code-specialized Llama model, excellent for coding tasks",
        priority="essential",
        provider="ollama",
        fallback="llama2",
    ),
    # Recommended models (better performance, moderate size)
    "mistral": ModelInfo(
        name="mistral",
        size="4.1 GB",
        size_bytes=4_404_019_200,
        ram_required=8,
        description="High-quality 7B model with good reasoning",
        priority="recommended",
        provider="ollama",
        fallback="llama2",
    ),
    "deepseek-coder": ModelInfo(
        name="deepseek-coder",
        size="4.0 GB",
        size_bytes=4_294_967_296,
        ram_required=8,
        description="Specialized coding model with strong performance",
        priority="recommended",
        provider="ollama",
        fallback="codellama",
    ),
    "qwen2.5-coder": ModelInfo(
        name="qwen2.5-coder",
        size="4.0 GB",
        size_bytes=4_294_967_296,
        ram_required=8,
        description="Latest Qwen coding model",
        priority="recommended",
        provider="ollama",
        fallback="codellama",
    ),
    # Optional models (larger, better quality)
    "codellama:13b": ModelInfo(
        name="codellama:13b",
        size="7.3 GB",
        size_bytes=7_836_348_416,
        ram_required=16,
        description="Larger CodeLlama with improved capabilities",
        priority="optional",
        provider="ollama",
        fallback="codellama",
    ),
    "mixtral": ModelInfo(
        name="mixtral",
        size="26 GB",
        size_bytes=27_917_287_424,
        ram_required=32,
        description="High-quality MoE model, excellent but resource-intensive",
        priority="optional",
        provider="ollama",
        fallback="mistral",
    ),
    "llama2:70b": ModelInfo(
        name="llama2:70b",
        size="40 GB",
        size_bytes=42_949_672_960,
        ram_required=64,
        description="Large Llama 2 model with superior capabilities",
        priority="optional",
        provider="ollama",
        fallback="llama2:13b",
    ),
}


class ModelVerifier:
    """Verify and manage AI models for benchmarking."""

    def __init__(self, verbose: bool = True):
        """Initialize the model verifier.

        Args:
            verbose: Whether to print detailed messages
        """
        self.verbose = verbose
        self.ollama_checker = OllamaChecker(verbose=False)
        self.installed_models: List[str] = []
        self.system_info = self._get_system_info()

    def _get_system_info(self) -> Dict[str, Union[str, int, bool]]:
        """Get system information for resource checks."""
        info = {
            "platform": platform.system(),
            "machine": platform.machine(),
            "ram_gb": self._get_total_ram(),
            "disk_free_gb": self._get_free_disk_space(),
            "ollama_installed": False,
            "ollama_running": False,
        }

        # Check Ollama status
        if self.ollama_checker.check_installation():
            info["ollama_installed"] = True
            if self.ollama_checker.check_service_running():
                info["ollama_running"] = True

        return info

    def _get_total_ram(self) -> int:
        """Get total system RAM in GB."""
        try:
            if platform.system() == "Darwin":  # macOS
                result = subprocess.run(
                    ["sysctl", "-n", "hw.memsize"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0:
                    bytes_ram = int(result.stdout.strip())
                    return bytes_ram // (1024**3)
            elif platform.system() == "Linux":
                with open("/proc/meminfo") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            kb_ram = int(line.split()[1])
                            return kb_ram // (1024**2)
            elif platform.system() == "Windows":
                import ctypes

                kernel32 = ctypes.windll.kernel32
                c_ulong = ctypes.c_ulong

                class MEMORYSTATUS(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", c_ulong),
                        ("dwMemoryLoad", c_ulong),
                        ("dwTotalPhys", c_ulong),
                        ("dwAvailPhys", c_ulong),
                        ("dwTotalPageFile", c_ulong),
                        ("dwAvailPageFile", c_ulong),
                        ("dwTotalVirtual", c_ulong),
                        ("dwAvailVirtual", c_ulong),
                    ]

                memory_status = MEMORYSTATUS()
                memory_status.dwLength = ctypes.sizeof(MEMORYSTATUS)
                kernel32.GlobalMemoryStatus(ctypes.byref(memory_status))
                return memory_status.dwTotalPhys // (1024**3)
        except Exception as e:
            logger.warning("Could not determine RAM due to system error")
            logger.debug(f"RAM detection error details: {e}")

        return 8  # Default assumption

    def _get_free_disk_space(self) -> int:
        """Get free disk space in GB."""
        try:
            # Get Ollama models directory with path validation
            models_dir = Path.home() / ".ollama" / "models"
            models_dir = models_dir.resolve()

            # Validate path is within user home directory
            if not str(models_dir).startswith(str(Path.home())):
                logger.warning("Models directory path outside home directory")
                models_dir = Path.home()

            if not models_dir.exists():
                models_dir = Path.home()

            stat = shutil.disk_usage(models_dir)
            return stat.free // (1024**3)
        except Exception as e:
            logger.warning("Could not determine disk space")
            logger.debug(f"Disk space detection error details: {e}")
            return 50  # Default assumption

    def print_message(self, message: str, level: str = "info") -> None:
        """Print a message if verbose mode is enabled."""
        if not self.verbose:
            return

        symbols = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "checking": "🔍",
            "download": "⬇️",
            "disk": "💾",
            "ram": "🧠",
        }

        symbol = symbols.get(level, "•")
        print(f"{symbol}  {message}")

    def check_installed_models(self) -> List[str]:
        """Check which recommended models are installed."""
        if not self.system_info["ollama_running"]:
            self.print_message(
                "Ollama is not running. Starting Ollama check...", "warning"
            )
            return []

        self.installed_models = self.ollama_checker.list_available_models()
        return self.installed_models

    def get_missing_models(self, priority: Optional[str] = None) -> List[ModelInfo]:
        """Get list of missing models.

        Args:
            priority: Filter by priority ("essential", "recommended", "optional")

        Returns:
            List of missing ModelInfo objects
        """
        missing = []
        for model_name, model_info in RECOMMENDED_MODELS.items():
            if priority and model_info.priority != priority:
                continue

            # Check if model is installed
            base_name = model_name.split(":")[0]
            if (
                base_name not in self.installed_models
                and model_name not in self.installed_models
            ):
                missing.append(model_info)

        return missing

    def calculate_download_requirements(
        self, models: List[ModelInfo]
    ) -> Dict[str, Union[int, float, str, bool]]:
        """Calculate disk space and RAM requirements for models.

        Args:
            models: List of models to analyze

        Returns:
            Dictionary with requirement information
        """
        total_size_bytes = sum(m.size_bytes for m in models)
        max_ram_required = max((m.ram_required for m in models), default=0)

        return {
            "total_size_gb": total_size_bytes / (1024**3),
            "total_size_human": self._format_bytes(total_size_bytes),
            "max_ram_gb": max_ram_required,
            "models_count": len(models),
            "disk_available_gb": self.system_info["disk_free_gb"],
            "ram_available_gb": self.system_info["ram_gb"],
            "can_download": self.system_info["disk_free_gb"]
            > (total_size_bytes / (1024**3) + 5),
            "can_run": self.system_info["ram_gb"] >= max_ram_required,
        }

    def _format_bytes(self, bytes_val: int) -> str:
        """Format bytes to human-readable string."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f} {unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f} PB"

    def suggest_models_for_system(self) -> List[ModelInfo]:
        """Suggest models based on system resources."""
        ram_gb = self.system_info["ram_gb"]
        disk_gb = self.system_info["disk_free_gb"]

        suggested = []

        # Categorize based on RAM
        if ram_gb >= 64:
            # High-end system - can run everything
            suggested = list(RECOMMENDED_MODELS.values())
        elif ram_gb >= 32:
            # Good system - skip the largest models
            suggested = [m for m in RECOMMENDED_MODELS.values() if m.ram_required <= 32]
        elif ram_gb >= 16:
            # Moderate system - focus on medium models
            suggested = [m for m in RECOMMENDED_MODELS.values() if m.ram_required <= 16]
        else:
            # Low-end system - only small models
            suggested = [m for m in RECOMMENDED_MODELS.values() if m.ram_required <= 8]

        # Filter by available disk space
        available_models = []
        total_size = 0
        for model in suggested:
            if (
                total_size + (model.size_bytes / (1024**3)) < disk_gb - 5
            ):  # Keep 5GB free
                available_models.append(model)
                total_size += model.size_bytes / (1024**3)

        return (
            available_models
            if available_models
            else [m for m in RECOMMENDED_MODELS.values() if m.priority == "essential"][
                :2
            ]
        )  # At least return 2 essential models

    def print_model_status(self) -> None:
        """Print comprehensive model status."""
        self.print_message("\n" + "=" * 60, "info")
        self.print_message("MODEL VERIFICATION REPORT", "info")
        self.print_message("=" * 60, "info")

        # System info
        self.print_message("\nSystem Information:", "info")
        self.print_message(
            f"  Platform: {self.system_info['platform']} ({self.system_info['machine']})",
            "info",
        )
        self.print_message(f"  RAM: {self.system_info['ram_gb']} GB", "ram")
        self.print_message(
            f"  Free Disk: {self.system_info['disk_free_gb']} GB", "disk"
        )

        # Ollama status
        if not self.system_info["ollama_installed"]:
            self.print_message("\n⚠️  Ollama is not installed!", "error")
            self.print_message("  Install from: https://ollama.ai/download", "info")
            return

        if not self.system_info["ollama_running"]:
            self.print_message("\n⚠️  Ollama service is not running!", "warning")
            self.print_message("  Start with: ollama serve", "info")
            return

        # Check installed models
        self.check_installed_models()

        # Installed models
        if self.installed_models:
            self.print_message(
                f"\n✅ Installed Models ({len(self.installed_models)}):", "success"
            )
            for model in self.installed_models:
                status = "✓"
                if model in RECOMMENDED_MODELS:
                    info = RECOMMENDED_MODELS[model]
                    self.print_message(
                        f"  {status} {model} - {info.description}", "info"
                    )
                else:
                    self.print_message(f"  {status} {model}", "info")
        else:
            self.print_message("\n⚠️  No models installed", "warning")

        # Missing essential models
        missing_essential = self.get_missing_models("essential")
        if missing_essential:
            self.print_message(
                f"\n❌ Missing Essential Models ({len(missing_essential)}):", "error"
            )
            for model in missing_essential:
                self.print_message(
                    f"  • {model.name} ({model.size}) - {model.description}", "info"
                )

        # Missing recommended models
        missing_recommended = self.get_missing_models("recommended")
        if missing_recommended:
            self.print_message(
                f"\n⚠️  Missing Recommended Models ({len(missing_recommended)}):",
                "warning",
            )
            for model in missing_recommended:
                self.print_message(
                    f"  • {model.name} ({model.size}) - {model.description}", "info"
                )

        # Optional models
        missing_optional = self.get_missing_models("optional")
        if missing_optional and self.system_info["ram_gb"] >= 16:
            self.print_message("\nℹ️  Optional Models (not installed):", "info")
            for model in missing_optional[:3]:  # Show max 3
                self.print_message(
                    f"  • {model.name} ({model.size}) - {model.description}", "info"
                )

    def print_download_commands(self) -> None:
        """Print commands to download missing models."""
        missing_essential = self.get_missing_models("essential")
        missing_recommended = self.get_missing_models("recommended")

        if not missing_essential and not missing_recommended:
            self.print_message(
                "\n✅ All essential and recommended models are installed!", "success"
            )
            return

        self.print_message("\n" + "=" * 60, "info")
        self.print_message("DOWNLOAD COMMANDS", "download")
        self.print_message("=" * 60, "info")

        # Essential models
        if missing_essential:
            self.print_message("\n🔴 Essential Models (install these first):", "error")
            for model in missing_essential:
                self.print_message(f"  ollama pull {model.name}", "info")

        # Check disk space for all missing
        all_missing = missing_essential + missing_recommended
        requirements = self.calculate_download_requirements(all_missing)

        self.print_message("\n💾 Disk Space Requirements:", "disk")
        self.print_message(
            f"  Total download size: {requirements['total_size_human']}", "info"
        )
        self.print_message(
            f"  Available disk space: {requirements['disk_available_gb']} GB", "info"
        )

        if not requirements["can_download"]:
            self.print_message(
                f"  ⚠️  Insufficient disk space! Need at least {requirements['total_size_gb']:.1f} GB",
                "warning",
            )

        # Recommended models
        if missing_recommended and requirements["can_download"]:
            self.print_message(
                "\n🟡 Recommended Models (better performance):", "warning"
            )
            for model in missing_recommended:
                self.print_message(f"  ollama pull {model.name}", "info")

        # Batch download command
        if len(all_missing) > 1:
            self.print_message("\n📦 Download all at once:", "info")
            # Validate and quote model names to prevent command injection
            safe_models = []
            for model in all_missing[:3]:  # Max 3 at once
                try:
                    validated_name = validate_model_name(model.name)
                    safe_models.append(shlex.quote(validated_name))
                except (ValidationError, Exception):
                    logger.warning(f"Skipping invalid model name: {model.name}")

            if safe_models:
                model_names = " ".join(safe_models)
                self.print_message(
                    f"  for model in {model_names}; do ollama pull $model; done", "info"
                )

    def suggest_fallbacks(self) -> None:
        """Suggest fallback models for resource-constrained systems."""
        if self.system_info["ram_gb"] >= 16:
            return  # No need for fallbacks

        self.print_message("\n" + "=" * 60, "info")
        self.print_message("RECOMMENDED MODELS FOR YOUR SYSTEM", "ram")
        self.print_message("=" * 60, "info")

        suggested = self.suggest_models_for_system()

        self.print_message(
            f"\nBased on your {self.system_info['ram_gb']} GB RAM:", "info"
        )
        for model in suggested[:5]:  # Show top 5
            installed = "✅" if model.name in self.installed_models else "⬇️"
            self.print_message(
                f"  {installed} {model.name} ({model.size}, needs {model.ram_required}GB RAM)",
                "info",
            )

        if self.system_info["ram_gb"] < 8:
            self.print_message("\n⚠️  Your system has limited RAM. Consider:", "warning")
            self.print_message(
                "  • Using cloud-based models (OpenAI, Anthropic)", "info"
            )
            self.print_message("  • Upgrading RAM to at least 8GB", "info")
            self.print_message(
                "  • Using quantized models (e.g., llama2:7b-q4_0)", "info"
            )

    def run_verification(self) -> Dict[str, Union[Dict, List, bool]]:
        """Run complete model verification.

        Returns:
            Dictionary with verification results
        """
        results = {
            "system": self.system_info,
            "installed": [],
            "missing_essential": [],
            "missing_recommended": [],
            "missing_optional": [],
            "suggested": [],
            "ready": False,
        }

        if not self.system_info["ollama_installed"]:
            self.print_message("Ollama is not installed", "error")
            return results

        if not self.system_info["ollama_running"]:
            self.print_message("Ollama service is not running", "warning")
            return results

        # Check models
        results["installed"] = self.check_installed_models()
        results["missing_essential"] = [
            m.name for m in self.get_missing_models("essential")
        ]
        results["missing_recommended"] = [
            m.name for m in self.get_missing_models("recommended")
        ]
        results["missing_optional"] = [
            m.name for m in self.get_missing_models("optional")
        ]
        results["suggested"] = [m.name for m in self.suggest_models_for_system()]

        # Ready if at least one essential model is installed
        essential_models = [
            m.name for m in RECOMMENDED_MODELS.values() if m.priority == "essential"
        ]
        results["ready"] = any(
            model in results["installed"] for model in essential_models
        )

        return results


def main():
    """Main entry point for model verification."""
    import argparse

    parser = argparse.ArgumentParser(description="Verify AI models for benchmarking")
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress detailed output"
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    parser.add_argument(
        "--download", "-d", action="store_true", help="Show download commands"
    )
    parser.add_argument(
        "--suggest", "-s", action="store_true", help="Suggest models for your system"
    )

    args = parser.parse_args()

    verifier = ModelVerifier(verbose=not args.quiet and not args.json)

    if args.json:
        results = verifier.run_verification()
        print(json.dumps(results, indent=2))
    else:
        # Run full verification
        verifier.print_model_status()

        if args.download or not verifier.installed_models:
            verifier.print_download_commands()

        if args.suggest or verifier.system_info["ram_gb"] < 16:
            verifier.suggest_fallbacks()

        # Final summary
        results = verifier.run_verification()
        if results["ready"]:
            verifier.print_message("\n✅ Ready for benchmarking!", "success")
        else:
            verifier.print_message(
                "\n❌ Not ready - install essential models first", "error"
            )

        sys.exit(0 if results["ready"] else 1)


if __name__ == "__main__":
    main()
