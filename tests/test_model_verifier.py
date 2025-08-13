#!/usr/bin/env python3
"""
Test suite for benchmark/model_verifier.py
"""

import json
import platform
from unittest.mock import MagicMock, Mock, patch

import pytest

from benchmark.model_verifier import (
    RECOMMENDED_MODELS,
    ModelInfo,
    ModelVerifier,
)


class TestModelInfo:
    """Test cases for ModelInfo dataclass."""
    
    def test_model_info_creation(self):
        """Test creating ModelInfo objects."""
        model = ModelInfo(
            name="test-model",
            size="1 GB",
            size_bytes=1_073_741_824,
            ram_required=4,
            description="Test model",
            priority="essential",
            provider="ollama",
            fallback="backup-model"
        )
        
        assert model.name == "test-model"
        assert model.size == "1 GB"
        assert model.size_bytes == 1_073_741_824
        assert model.ram_required == 4
        assert model.priority == "essential"
        assert model.fallback == "backup-model"
    
    def test_recommended_models_structure(self):
        """Test that RECOMMENDED_MODELS is properly structured."""
        assert len(RECOMMENDED_MODELS) > 0
        
        for name, model in RECOMMENDED_MODELS.items():
            assert isinstance(model, ModelInfo)
            assert model.name == name
            assert model.size_bytes > 0
            assert model.ram_required > 0
            assert model.priority in ["essential", "recommended", "optional"]
            assert model.provider == "ollama"


class TestModelVerifier:
    """Test cases for ModelVerifier class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        with patch("benchmark.model_verifier.OllamaChecker"):
            self.verifier = ModelVerifier(verbose=False)
    
    @patch("platform.system")
    @patch("subprocess.run")
    def test_get_total_ram_macos(self, mock_run, mock_system):
        """Test RAM detection on macOS."""
        mock_system.return_value = "Darwin"
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="17179869184"  # 16 GB in bytes
        )
        
        ram = self.verifier._get_total_ram()
        assert ram == 16
    
    @patch("platform.system")
    @patch("builtins.open", create=True)
    def test_get_total_ram_linux(self, mock_open, mock_system):
        """Test RAM detection on Linux."""
        mock_system.return_value = "Linux"
        mock_open.return_value.__enter__.return_value = [
            "MemTotal:       16777216 kB\n",
            "MemFree:        1234567 kB\n"
        ]
        
        ram = self.verifier._get_total_ram()
        assert ram == 16
    
    @patch("platform.system")
    def test_get_total_ram_fallback(self, mock_system):
        """Test RAM detection fallback."""
        mock_system.return_value = "Unknown"
        
        ram = self.verifier._get_total_ram()
        assert ram == 8  # Default fallback value
    
    @patch("shutil.disk_usage")
    def test_get_free_disk_space(self, mock_disk_usage):
        """Test disk space detection."""
        mock_disk_usage.return_value = MagicMock(
            free=107_374_182_400  # 100 GB in bytes
        )
        
        disk = self.verifier._get_free_disk_space()
        assert disk == 100
    
    @patch("shutil.disk_usage")
    def test_get_free_disk_space_error(self, mock_disk_usage):
        """Test disk space detection with error."""
        mock_disk_usage.side_effect = Exception("Disk error")
        
        disk = self.verifier._get_free_disk_space()
        assert disk == 50  # Default fallback
    
    def test_format_bytes(self):
        """Test byte formatting."""
        assert self.verifier._format_bytes(512) == "512.0 B"
        assert self.verifier._format_bytes(1024) == "1.0 KB"
        assert self.verifier._format_bytes(1_048_576) == "1.0 MB"
        assert self.verifier._format_bytes(1_073_741_824) == "1.0 GB"
        assert self.verifier._format_bytes(1_099_511_627_776) == "1.0 TB"
    
    @patch.object(ModelVerifier, "_get_total_ram", return_value=16)
    @patch.object(ModelVerifier, "_get_free_disk_space", return_value=100)
    def test_get_system_info(self, mock_disk, mock_ram):
        """Test system info gathering."""
        with patch("benchmark.model_verifier.OllamaChecker") as mock_checker:
            mock_instance = MagicMock()
            mock_instance.check_installation.return_value = True
            mock_instance.check_service_running.return_value = True
            mock_checker.return_value = mock_instance
            
            verifier = ModelVerifier(verbose=False)
            info = verifier.system_info
            
            assert info["ram_gb"] == 16
            assert info["disk_free_gb"] == 100
            assert info["ollama_installed"] is True
            assert info["ollama_running"] is True
    
    def test_check_installed_models(self):
        """Test checking installed models."""
        self.verifier.system_info["ollama_running"] = True
        self.verifier.ollama_checker.list_available_models = MagicMock(
            return_value=["llama2", "codellama", "mistral"]
        )
        
        models = self.verifier.check_installed_models()
        
        assert len(models) == 3
        assert "llama2" in models
        assert "codellama" in models
        assert "mistral" in models
    
    def test_check_installed_models_not_running(self):
        """Test checking models when Ollama is not running."""
        self.verifier.system_info["ollama_running"] = False
        
        models = self.verifier.check_installed_models()
        
        assert models == []
    
    def test_get_missing_models_all(self):
        """Test getting all missing models."""
        self.verifier.installed_models = ["llama2"]
        
        missing = self.verifier.get_missing_models()
        
        # Should include all models except llama2
        model_names = [m.name for m in missing]
        assert "llama2" not in model_names
        assert "codellama" in model_names
        assert "mistral" in model_names
    
    def test_get_missing_models_by_priority(self):
        """Test getting missing models filtered by priority."""
        self.verifier.installed_models = []
        
        # Get only essential models
        essential = self.verifier.get_missing_models("essential")
        for model in essential:
            assert model.priority == "essential"
        
        # Get only recommended models
        recommended = self.verifier.get_missing_models("recommended")
        for model in recommended:
            assert model.priority == "recommended"
    
    def test_calculate_download_requirements(self):
        """Test calculating download requirements."""
        models = [
            ModelInfo("model1", "1 GB", 1_073_741_824, 4, "Test 1", "essential", "ollama"),
            ModelInfo("model2", "2 GB", 2_147_483_648, 8, "Test 2", "essential", "ollama"),
        ]
        
        self.verifier.system_info["disk_free_gb"] = 50
        self.verifier.system_info["ram_gb"] = 16
        
        reqs = self.verifier.calculate_download_requirements(models)
        
        assert reqs["total_size_gb"] == 3.0
        assert reqs["max_ram_gb"] == 8
        assert reqs["models_count"] == 2
        assert reqs["can_download"] is True
        assert reqs["can_run"] is True
    
    def test_calculate_download_requirements_insufficient(self):
        """Test requirements with insufficient resources."""
        models = [
            ModelInfo("model1", "40 GB", 42_949_672_960, 64, "Test", "optional", "ollama"),
        ]
        
        self.verifier.system_info["disk_free_gb"] = 30
        self.verifier.system_info["ram_gb"] = 8
        
        reqs = self.verifier.calculate_download_requirements(models)
        
        assert reqs["can_download"] is False
        assert reqs["can_run"] is False
    
    def test_suggest_models_for_system_high_end(self):
        """Test model suggestions for high-end system."""
        self.verifier.system_info["ram_gb"] = 64
        self.verifier.system_info["disk_free_gb"] = 500
        
        suggested = self.verifier.suggest_models_for_system()
        
        # Should include large models
        model_names = [m.name for m in suggested]
        # High-end system can handle any model
        assert len(suggested) > 0
    
    def test_suggest_models_for_system_low_end(self):
        """Test model suggestions for low-end system."""
        self.verifier.system_info["ram_gb"] = 4
        self.verifier.system_info["disk_free_gb"] = 20
        
        suggested = self.verifier.suggest_models_for_system()
        
        # Should only suggest small models
        for model in suggested:
            assert model.ram_required <= 8
    
    def test_suggest_models_for_system_moderate(self):
        """Test model suggestions for moderate system."""
        self.verifier.system_info["ram_gb"] = 16
        self.verifier.system_info["disk_free_gb"] = 100
        
        suggested = self.verifier.suggest_models_for_system()
        
        # Should exclude very large models
        for model in suggested:
            assert model.ram_required <= 16
    
    @patch("builtins.print")
    def test_print_model_status_no_ollama(self, mock_print):
        """Test status printing when Ollama is not installed."""
        self.verifier.verbose = True
        self.verifier.system_info["ollama_installed"] = False
        
        self.verifier.print_model_status()
        
        # Check that appropriate messages were printed
        printed = " ".join(str(call.args[0]) if call.args else "" 
                          for call in mock_print.call_args_list)
        assert "Ollama is not installed" in printed
    
    @patch("builtins.print")
    def test_print_model_status_not_running(self, mock_print):
        """Test status printing when Ollama is not running."""
        self.verifier.verbose = True
        self.verifier.system_info["ollama_installed"] = True
        self.verifier.system_info["ollama_running"] = False
        
        self.verifier.print_model_status()
        
        printed = " ".join(str(call.args[0]) if call.args else "" 
                          for call in mock_print.call_args_list)
        assert "Ollama service is not running" in printed
    
    @patch("builtins.print")
    def test_print_model_status_with_models(self, mock_print):
        """Test status printing with installed models."""
        self.verifier.verbose = True
        self.verifier.system_info["ollama_installed"] = True
        self.verifier.system_info["ollama_running"] = True
        self.verifier.ollama_checker.list_available_models = MagicMock(
            return_value=["llama2", "codellama"]
        )
        
        self.verifier.print_model_status()
        
        printed = " ".join(str(call.args[0]) if call.args else "" 
                          for call in mock_print.call_args_list)
        assert "Installed Models" in printed
        assert "llama2" in printed
        assert "codellama" in printed
    
    @patch("builtins.print")
    def test_print_download_commands(self, mock_print):
        """Test printing download commands."""
        self.verifier.verbose = True
        self.verifier.installed_models = []
        self.verifier.system_info["disk_free_gb"] = 100
        
        self.verifier.print_download_commands()
        
        printed = " ".join(str(call.args[0]) if call.args else "" 
                          for call in mock_print.call_args_list)
        assert "ollama pull" in printed
        assert "DOWNLOAD COMMANDS" in printed
    
    @patch("builtins.print")
    def test_print_download_commands_all_installed(self, mock_print):
        """Test download commands when all models are installed."""
        self.verifier.verbose = True
        # Mark all essential and recommended as installed
        self.verifier.installed_models = [
            m.name for m in RECOMMENDED_MODELS.values() 
            if m.priority in ["essential", "recommended"]
        ]
        
        self.verifier.print_download_commands()
        
        printed = " ".join(str(call.args[0]) if call.args else "" 
                          for call in mock_print.call_args_list)
        assert "All essential and recommended models are installed" in printed
    
    @patch("builtins.print")
    def test_suggest_fallbacks_low_ram(self, mock_print):
        """Test fallback suggestions for low RAM."""
        self.verifier.verbose = True
        self.verifier.system_info["ram_gb"] = 4
        
        self.verifier.suggest_fallbacks()
        
        printed = " ".join(str(call.args[0]) if call.args else "" 
                          for call in mock_print.call_args_list)
        assert "RECOMMENDED MODELS FOR YOUR SYSTEM" in printed
        assert "limited RAM" in printed
    
    @patch("builtins.print")
    def test_suggest_fallbacks_sufficient_ram(self, mock_print):
        """Test no fallbacks needed for sufficient RAM."""
        self.verifier.verbose = True
        self.verifier.system_info["ram_gb"] = 32
        
        self.verifier.suggest_fallbacks()
        
        # Should not print anything for high-RAM systems
        assert mock_print.call_count == 0
    
    def test_run_verification_not_installed(self):
        """Test verification when Ollama is not installed."""
        self.verifier.system_info["ollama_installed"] = False
        
        results = self.verifier.run_verification()
        
        assert results["ready"] is False
        assert results["installed"] == []
    
    def test_run_verification_not_running(self):
        """Test verification when Ollama is not running."""
        self.verifier.system_info["ollama_installed"] = True
        self.verifier.system_info["ollama_running"] = False
        
        results = self.verifier.run_verification()
        
        assert results["ready"] is False
        assert results["installed"] == []
    
    def test_run_verification_ready(self):
        """Test verification when ready for benchmarking."""
        self.verifier.system_info["ollama_installed"] = True
        self.verifier.system_info["ollama_running"] = True
        self.verifier.ollama_checker.list_available_models = MagicMock(
            return_value=["llama2", "codellama"]
        )
        
        results = self.verifier.run_verification()
        
        assert results["ready"] is True
        assert "llama2" in results["installed"]
        assert len(results["missing_essential"]) == 0
    
    def test_run_verification_missing_essential(self):
        """Test verification with missing essential models."""
        self.verifier.system_info["ollama_installed"] = True
        self.verifier.system_info["ollama_running"] = True
        self.verifier.ollama_checker.list_available_models = MagicMock(
            return_value=["mistral"]  # Not an essential model
        )
        
        results = self.verifier.run_verification()
        
        # Should not be ready without essential models
        assert results["ready"] is False
        assert "llama2" in results["missing_essential"]
        assert "codellama" in results["missing_essential"]


class TestMainFunction:
    """Test cases for main function."""
    
    @patch("sys.argv", ["model_verifier.py"])
    @patch("benchmark.model_verifier.ModelVerifier")
    def test_main_default(self, mock_verifier_class):
        """Test main function with default arguments."""
        mock_verifier = MagicMock()
        mock_verifier.run_verification.return_value = {"ready": True}
        mock_verifier.installed_models = ["llama2"]
        mock_verifier.system_info = {"ram_gb": 16}
        mock_verifier_class.return_value = mock_verifier
        
        with patch("sys.exit") as mock_exit:
            from benchmark.model_verifier import main
            main()
            
            mock_verifier.print_model_status.assert_called_once()
            mock_exit.assert_called_once_with(0)
    
    @patch("sys.argv", ["model_verifier.py", "--json"])
    @patch("benchmark.model_verifier.ModelVerifier")
    @patch("builtins.print")
    def test_main_json_output(self, mock_print, mock_verifier_class):
        """Test main function with JSON output."""
        mock_verifier = MagicMock()
        mock_verifier.run_verification.return_value = {
            "ready": True,
            "installed": ["llama2"]
        }
        mock_verifier_class.return_value = mock_verifier
        
        with patch("sys.exit"):
            from benchmark.model_verifier import main
            main()
            
            # Check that JSON was printed
            mock_print.assert_called_once()
            output = mock_print.call_args[0][0]
            data = json.loads(output)
            assert data["ready"] is True
            assert "llama2" in data["installed"]
    
    @patch("sys.argv", ["model_verifier.py", "--download"])
    @patch("benchmark.model_verifier.ModelVerifier")
    def test_main_download_flag(self, mock_verifier_class):
        """Test main function with download flag."""
        mock_verifier = MagicMock()
        mock_verifier.run_verification.return_value = {"ready": False}
        mock_verifier.installed_models = []
        mock_verifier.system_info = {"ram_gb": 16}
        mock_verifier_class.return_value = mock_verifier
        
        with patch("sys.exit"):
            from benchmark.model_verifier import main
            main()
            
            mock_verifier.print_download_commands.assert_called_once()
    
    @patch("sys.argv", ["model_verifier.py", "--suggest"])
    @patch("benchmark.model_verifier.ModelVerifier")
    def test_main_suggest_flag(self, mock_verifier_class):
        """Test main function with suggest flag."""
        mock_verifier = MagicMock()
        mock_verifier.run_verification.return_value = {"ready": True}
        mock_verifier.installed_models = ["llama2"]
        mock_verifier.system_info = {"ram_gb": 16}
        mock_verifier_class.return_value = mock_verifier
        
        with patch("sys.exit"):
            from benchmark.model_verifier import main
            main()
            
            mock_verifier.suggest_fallbacks.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])