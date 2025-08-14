#!/usr/bin/env python3
"""
Machine Information Collector

Collects system details including CPU, RAM, GPU (if available), and other
relevant hardware/software information for benchmark context.
"""

import platform
import subprocess
import psutil
import json
from typing import Dict, Optional, Any
from datetime import datetime


class MachineInfoCollector:
    """Collects comprehensive machine information for benchmark context."""

    @staticmethod
    def get_cpu_info() -> Dict[str, Any]:
        """Get CPU information."""
        cpu_info = {
            "physical_cores": psutil.cpu_count(logical=False),
            "logical_cores": psutil.cpu_count(logical=True),
            "frequency_mhz": psutil.cpu_freq().current if psutil.cpu_freq() else None,
            "max_frequency_mhz": psutil.cpu_freq().max if psutil.cpu_freq() else None,
        }
        
        # Try to get CPU model on different platforms
        if platform.system() == "Darwin":
            try:
                result = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                cpu_info["model"] = result.stdout.strip()
            except:
                cpu_info["model"] = "Unknown"
        elif platform.system() == "Linux":
            try:
                with open("/proc/cpuinfo") as f:
                    for line in f:
                        if "model name" in line:
                            cpu_info["model"] = line.split(":")[1].strip()
                            break
            except:
                cpu_info["model"] = "Unknown"
        elif platform.system() == "Windows":
            try:
                result = subprocess.run(
                    ["wmic", "cpu", "get", "name"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:
                    cpu_info["model"] = lines[1].strip()
            except:
                cpu_info["model"] = "Unknown"
        else:
            cpu_info["model"] = platform.processor() or "Unknown"
            
        return cpu_info

    @staticmethod
    def get_memory_info() -> Dict[str, Any]:
        """Get memory information."""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            "total_gb": round(mem.total / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "used_gb": round(mem.used / (1024**3), 2),
            "percent_used": mem.percent,
            "swap_total_gb": round(swap.total / (1024**3), 2),
            "swap_used_gb": round(swap.used / (1024**3), 2),
        }

    @staticmethod
    def get_gpu_info() -> Optional[Dict[str, Any]]:
        """Get GPU information if available."""
        gpu_info = {}
        
        # Try NVIDIA GPUs
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                check=True
            )
            lines = result.stdout.strip().split("\n")
            if lines and lines[0]:
                parts = lines[0].split(",")
                gpu_info["nvidia"] = {
                    "model": parts[0].strip(),
                    "memory_mb": parts[1].strip() if len(parts) > 1 else "Unknown",
                    "driver": parts[2].strip() if len(parts) > 2 else "Unknown",
                }
        except:
            pass
        
        # Try to detect Apple Silicon GPU
        if platform.system() == "Darwin" and platform.processor() == "arm":
            try:
                result = subprocess.run(
                    ["system_profiler", "SPDisplaysDataType"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                if "Apple" in result.stdout or "M1" in result.stdout or "M2" in result.stdout or "M3" in result.stdout:
                    # Parse Apple Silicon GPU info
                    lines = result.stdout.split("\n")
                    for line in lines:
                        if "Chipset Model:" in line:
                            gpu_info["apple_silicon"] = {
                                "model": line.split(":")[1].strip()
                            }
                        elif "VRAM" in line or "Memory" in line:
                            if "apple_silicon" in gpu_info:
                                gpu_info["apple_silicon"]["memory"] = line.split(":")[1].strip()
            except:
                pass
        
        return gpu_info if gpu_info else None

    @staticmethod
    def get_disk_info() -> Dict[str, Any]:
        """Get disk information."""
        disk = psutil.disk_usage("/")
        
        return {
            "total_gb": round(disk.total / (1024**3), 2),
            "used_gb": round(disk.used / (1024**3), 2),
            "free_gb": round(disk.free / (1024**3), 2),
            "percent_used": disk.percent,
        }

    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get general system information."""
        return {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "hostname": platform.node(),
            "python_version": platform.python_version(),
        }

    @staticmethod
    def get_ollama_info() -> Optional[Dict[str, Any]]:
        """Get Ollama installation information if available."""
        try:
            # Check Ollama version
            result = subprocess.run(
                ["ollama", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            version = result.stdout.strip()
            
            # Get list of available models
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                check=True
            )
            models = []
            lines = result.stdout.strip().split("\n")[1:]  # Skip header
            for line in lines:
                if line:
                    parts = line.split()
                    if parts:
                        models.append(parts[0])
            
            return {
                "version": version,
                "models_count": len(models),
                "models": models[:10]  # Limit to first 10 models
            }
        except:
            return None

    @classmethod
    def collect_all(cls) -> Dict[str, Any]:
        """Collect all machine information."""
        return {
            "timestamp": datetime.now().isoformat(),
            "system": cls.get_system_info(),
            "cpu": cls.get_cpu_info(),
            "memory": cls.get_memory_info(),
            "disk": cls.get_disk_info(),
            "gpu": cls.get_gpu_info(),
            "ollama": cls.get_ollama_info(),
        }

    @classmethod
    def save_to_file(cls, filepath: str) -> None:
        """Save machine information to a JSON file."""
        info = cls.collect_all()
        with open(filepath, "w") as f:
            json.dump(info, f, indent=2)
        print(f"Machine information saved to {filepath}")

    @classmethod
    def print_summary(cls) -> None:
        """Print a summary of machine information."""
        info = cls.collect_all()
        
        print("\n🖥️  Machine Information Summary")
        print("=" * 50)
        
        print(f"System: {info['system']['platform']} {info['system']['platform_release']}")
        print(f"Architecture: {info['system']['architecture']}")
        print(f"Python: {info['system']['python_version']}")
        
        print(f"\nCPU: {info['cpu'].get('model', 'Unknown')}")
        print(f"  Cores: {info['cpu']['physical_cores']} physical, {info['cpu']['logical_cores']} logical")
        
        print(f"\nMemory: {info['memory']['total_gb']} GB total")
        print(f"  Available: {info['memory']['available_gb']} GB ({100 - info['memory']['percent_used']:.1f}%)")
        
        print(f"\nDisk: {info['disk']['total_gb']} GB total")
        print(f"  Free: {info['disk']['free_gb']} GB ({100 - info['disk']['percent_used']:.1f}%)")
        
        if info['gpu']:
            print("\nGPU:")
            for gpu_type, gpu_data in info['gpu'].items():
                print(f"  {gpu_type}: {gpu_data.get('model', 'Unknown')}")
        
        if info['ollama']:
            print(f"\nOllama: {info['ollama']['version']}")
            print(f"  Models available: {info['ollama']['models_count']}")
        
        print("=" * 50)


if __name__ == "__main__":
    # Test the collector
    collector = MachineInfoCollector()
    
    # Print summary
    collector.print_summary()
    
    # Save to file
    collector.save_to_file("machine_info.json")