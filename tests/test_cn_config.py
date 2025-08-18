#!/usr/bin/env python3
"""
Test suite for Continue CLI Configuration Manager

Tests the CNConfigManager class and its configuration generation functionality.
"""

from pathlib import Path
import tempfile
import unittest

import yaml

from benchmark.cn_integration.cn_config import CNConfigManager


class TestCNConfigManager(unittest.TestCase):
    """Test cases for CNConfigManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.config_manager = CNConfigManager()
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        self.config_manager.cleanup_temp_configs()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_detect_provider_ollama(self):
        """Test provider detection for Ollama models."""
        test_cases = [
            "ollama/llama2",
            "ollama/mistral",
            "ollama/qwen2.5-coder"
        ]
        
        for model_name in test_cases:
            provider = self.config_manager._detect_provider(model_name)
            self.assertEqual(provider, "ollama")
    
    def test_detect_provider_openai(self):
        """Test provider detection for OpenAI models."""
        test_cases = [
            "gpt-4",
            "gpt-3.5-turbo",
            "openai/gpt-4"
        ]
        
        for model_name in test_cases:
            provider = self.config_manager._detect_provider(model_name)
            self.assertEqual(provider, "openai")
    
    def test_detect_provider_anthropic(self):
        """Test provider detection for Anthropic models."""
        test_cases = [
            "claude-3-opus",
            "claude-3-sonnet",
            "anthropic/claude-2"
        ]
        
        for model_name in test_cases:
            provider = self.config_manager._detect_provider(model_name)
            self.assertEqual(provider, "anthropic")
    
    def test_detect_provider_google(self):
        """Test provider detection for Google models."""
        test_cases = [
            "gemini-pro",
            "palm-2"
        ]
        
        for model_name in test_cases:
            provider = self.config_manager._detect_provider(model_name)
            self.assertEqual(provider, "google")
    
    def test_detect_provider_fallback(self):
        """Test provider detection fallback."""
        unknown_model = "unknown-model-name"
        provider = self.config_manager._detect_provider(unknown_model)
        self.assertEqual(provider, "openai")  # Default fallback
    
    def test_extract_model_name_ollama(self):
        """Test model name extraction for Ollama."""
        model_name = "ollama/llama2:7b"
        extracted = self.config_manager._extract_model_name(model_name, "ollama")
        self.assertEqual(extracted, "llama2:7b")
    
    def test_extract_model_name_no_prefix(self):
        """Test model name extraction without prefix."""
        model_name = "gpt-4"
        extracted = self.config_manager._extract_model_name(model_name, "openai")
        self.assertEqual(extracted, "gpt-4")
    
    def test_get_model_config_ollama(self):
        """Test model configuration for Ollama."""
        config = self.config_manager._get_model_config("llama2", "ollama")
        
        expected = {
            "model": "llama2",
            "provider": "ollama"
        }
        self.assertEqual(config, expected)
    
    def test_get_model_config_openai(self):
        """Test model configuration for OpenAI."""
        config = self.config_manager._get_model_config("gpt-4", "openai")
        
        expected = {
            "model": "gpt-4",
            "provider": "openai",
            "apiKey": "${OPENAI_API_KEY}"
        }
        self.assertEqual(config, expected)
    
    def test_get_model_config_anthropic(self):
        """Test model configuration for Anthropic."""
        config = self.config_manager._get_model_config("claude-3-sonnet", "anthropic")
        
        expected = {
            "model": "claude-3-sonnet",
            "provider": "anthropic",
            "apiKey": "${ANTHROPIC_API_KEY}"
        }
        self.assertEqual(config, expected)
    
    def test_get_model_config_with_custom_settings(self):
        """Test model configuration with custom settings."""
        custom_settings = {
            "temperature": 0.5,
            "max_tokens": 1000
        }
        
        config = self.config_manager._get_model_config(
            "gpt-4", "openai", custom_settings
        )
        
        self.assertEqual(config["temperature"], 0.5)
        self.assertEqual(config["max_tokens"], 1000)
        self.assertEqual(config["provider"], "openai")
        self.assertEqual(config["model"], "gpt-4")
    
    def test_build_config_basic(self):
        """Test basic configuration building."""
        config = self.config_manager._build_config("llama2", "ollama")
        
        self.assertIn("models", config)
        self.assertIn("chat", config["models"])
        self.assertEqual(config["models"]["chat"]["model"], "llama2")
        self.assertEqual(config["models"]["chat"]["provider"], "ollama")
    
    def test_create_config_ollama(self):
        """Test configuration creation for Ollama model."""
        config_path = self.config_manager.create_config("ollama/llama2", "auto")
        
        # Verify file exists
        self.assertTrue(config_path.exists())
        
        # Verify content
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        self.assertIn("models", config)
        self.assertEqual(config["models"]["chat"]["model"], "llama2")
        self.assertEqual(config["models"]["chat"]["provider"], "ollama")
    
    def test_create_config_openai(self):
        """Test configuration creation for OpenAI model."""
        config_path = self.config_manager.create_config("gpt-4", "openai")
        
        # Verify file exists
        self.assertTrue(config_path.exists())
        
        # Verify content
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        self.assertEqual(config["models"]["chat"]["model"], "gpt-4")
        self.assertEqual(config["models"]["chat"]["provider"], "openai")
        self.assertEqual(config["models"]["chat"]["apiKey"], "${OPENAI_API_KEY}")
    
    def test_create_config_with_custom_settings(self):
        """Test configuration creation with custom settings."""
        custom_settings = {
            "temperature": 0.1,
            "max_tokens": 2048
        }
        
        config_path = self.config_manager.create_config(
            "gpt-3.5-turbo", "openai", custom_settings
        )
        
        # Verify content includes custom settings
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        self.assertEqual(config["models"]["chat"]["temperature"], 0.1)
        self.assertEqual(config["models"]["chat"]["max_tokens"], 2048)
    
    def test_get_model_presets(self):
        """Test model presets retrieval."""
        presets = self.config_manager.get_model_presets()
        
        # Verify structure
        self.assertIsInstance(presets, dict)
        self.assertGreater(len(presets), 0)
        
        # Check some expected presets
        self.assertIn("gpt-4", presets)
        self.assertIn("claude-3-opus", presets)
        self.assertIn("ollama/llama2", presets)
        
        # Verify preset structure
        gpt4_preset = presets["gpt-4"]
        self.assertEqual(gpt4_preset["provider"], "openai")
        self.assertIn("temperature", gpt4_preset)
        self.assertIn("max_tokens", gpt4_preset)
    
    def test_create_preset_config_gpt4(self):
        """Test creating config from GPT-4 preset."""
        config_path = self.config_manager.create_preset_config("gpt-4")
        
        # Verify file exists
        self.assertTrue(config_path.exists())
        
        # Verify content matches preset
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        presets = self.config_manager.get_model_presets()
        expected_preset = presets["gpt-4"]
        
        self.assertEqual(config["models"]["chat"]["model"], "gpt-4")
        self.assertEqual(config["models"]["chat"]["provider"], "openai")
        self.assertEqual(
            config["models"]["chat"]["temperature"], 
            expected_preset["temperature"]
        )
    
    def test_create_preset_config_ollama(self):
        """Test creating config from Ollama preset."""
        config_path = self.config_manager.create_preset_config("ollama/llama2")
        
        # Verify file exists
        self.assertTrue(config_path.exists())
        
        # Verify content
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        self.assertEqual(config["models"]["chat"]["model"], "llama2")
        self.assertEqual(config["models"]["chat"]["provider"], "ollama")
    
    def test_create_preset_config_unknown(self):
        """Test creating config from unknown preset."""
        with self.assertRaises(ValueError) as cm:
            self.config_manager.create_preset_config("unknown-model")
        
        self.assertIn("Unknown model preset", str(cm.exception))
    
    def test_cleanup_temp_configs(self):
        """Test cleanup of temporary configuration files."""
        # Create a few configs
        config1 = self.config_manager.create_config("gpt-4", "openai")
        config2 = self.config_manager.create_config("ollama/llama2", "auto")
        
        # Verify they exist
        self.assertTrue(config1.exists())
        self.assertTrue(config2.exists())
        
        # Cleanup
        self.config_manager.cleanup_temp_configs()
        
        # Verify they're gone
        self.assertFalse(config1.exists())
        self.assertFalse(config2.exists())
        
        # Verify tracking list is empty
        self.assertEqual(len(self.config_manager.temp_configs), 0)
    
    def test_config_manager_destructor(self):
        """Test that destructor cleans up temp configs."""
        # Create a config
        config_path = self.config_manager.create_config("gpt-4", "openai")
        self.assertTrue(config_path.exists())
        
        # Manually call destructor
        self.config_manager.__del__()
        
        # Config should be cleaned up
        self.assertFalse(config_path.exists())
    
    def test_config_file_format(self):
        """Test that generated config files are valid YAML."""
        config_path = self.config_manager.create_config("gpt-4", "openai")
        
        # Should be able to load as YAML without errors
        with open(config_path) as f:
            config = yaml.safe_load(f)
        
        # Verify basic structure
        self.assertIsInstance(config, dict)
        self.assertIn("models", config)
        self.assertIn("chat", config["models"])
    
    def test_multiple_config_creation(self):
        """Test creating multiple configurations."""
        models = [
            ("gpt-4", "openai"),
            ("claude-3-sonnet", "anthropic"),
            ("ollama/llama2", "auto")
        ]
        
        config_paths = []
        for model, provider in models:
            path = self.config_manager.create_config(model, provider)
            config_paths.append(path)
            self.assertTrue(path.exists())
        
        # All should be tracked
        self.assertEqual(len(self.config_manager.temp_configs), 3)
        
        # All should be unique files
        self.assertEqual(len(set(config_paths)), 3)


if __name__ == "__main__":
    unittest.main()
