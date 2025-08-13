#!/usr/bin/env python3
"""
Security validators for benchmark framework.

Provides input validation and sanitization to prevent security vulnerabilities.
"""

from pathlib import Path
import re
from typing import Union


class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass


def validate_model_name(name: str) -> str:
    """Validate and sanitize model name to prevent command injection.

    Args:
        name: Model name to validate

    Returns:
        Sanitized model name

    Raises:
        ValidationError: If model name is invalid or potentially malicious
    """
    if not isinstance(name, str) or not name.strip():
        raise ValidationError("Model name must be a non-empty string")

    # Strip whitespace
    name = name.strip()

    # Allow only safe characters: alphanumeric, dots, hyphens, underscores, colons, forward slashes
    # This covers patterns like "llama2", "codellama:13b", "mistral", "ollama/llama2"
    if not re.match(r"^[a-zA-Z0-9._:/-]+$", name):
        raise ValidationError(
            f"Invalid model name format: {name}. "
            "Only alphanumeric characters, dots, hyphens, underscores, colons, and slashes are allowed."
        )

    # Check for suspicious patterns
    suspicious_patterns = [
        "..",  # Directory traversal
        "~",  # Home directory access
        ";",  # Command separator
        "&&",  # Command chaining
        "||",  # Command chaining
        "`",  # Command substitution
        "$",  # Variable expansion
        "|",  # Pipe
        ">",  # Redirect
        "<",  # Redirect
        "&",  # Background
        "\n",  # Newline
        "\r",  # Carriage return
        "\0",  # Null byte
    ]

    for pattern in suspicious_patterns:
        if pattern in name:
            raise ValidationError(f"Model name contains suspicious pattern: {pattern}")

    # Limit length to prevent buffer overflow attacks
    if len(name) > 256:
        raise ValidationError("Model name is too long (max 256 characters)")

    return name


def validate_task_file(path: Union[str, Path]) -> Path:
    """Validate task file path to prevent directory traversal.

    Args:
        path: Path to task file

    Returns:
        Validated Path object

    Raises:
        ValidationError: If path is invalid or potentially malicious
    """
    if not path:
        raise ValidationError("Task file path cannot be empty")

    # Convert to Path and resolve to absolute path
    task_path = Path(path).resolve()

    # Get the expected base directory for tasks
    base_dir = (Path.cwd() / "benchmark" / "tasks").resolve()

    # Check if the resolved path is within the allowed directory
    try:
        # This will raise ValueError if task_path is not relative to base_dir
        task_path.relative_to(base_dir)
    except ValueError:
        raise ValidationError(
            f"Task file must be within benchmark/tasks directory. Got: {path}"
        )

    # Check if file exists
    if not task_path.exists():
        raise ValidationError(f"Task file does not exist: {path}")

    # Check if it's actually a file (not a directory)
    if not task_path.is_file():
        raise ValidationError(f"Task path is not a file: {path}")

    # Check file extension
    if task_path.suffix not in [".md", ".txt", ".markdown"]:
        raise ValidationError(
            f"Invalid task file extension: {task_path.suffix}. "
            "Only .md, .txt, and .markdown files are allowed."
        )

    # Check file size (prevent loading huge files)
    max_size = 10 * 1024 * 1024  # 10 MB
    if task_path.stat().st_size > max_size:
        raise ValidationError(f"Task file is too large (max 10 MB): {path}")

    return task_path


def get_safe_user_input(prompt: str, valid_options: list) -> str:
    """Get user input with validation.

    Args:
        prompt: Prompt to display to user
        valid_options: List of valid input options

    Returns:
        Validated user input
    """
    if not valid_options:
        raise ValueError("valid_options cannot be empty")

    max_attempts = 5
    attempts = 0

    while attempts < max_attempts:
        attempts += 1
        response = input(prompt).strip().lower()

        if response in valid_options:
            return response

        print(f"Invalid input. Please enter one of: {', '.join(valid_options)}")

    raise ValidationError(f"Max input attempts ({max_attempts}) exceeded")


def sanitize_error_message(error: Exception) -> str:
    """Sanitize error messages to prevent information disclosure.

    Args:
        error: Exception to sanitize

    Returns:
        Safe error message for display
    """
    # Map specific error types to generic messages
    safe_messages = {
        FileNotFoundError: "File not found",
        PermissionError: "Permission denied",
        ConnectionError: "Connection failed",
        TimeoutError: "Operation timed out",
        ValueError: "Invalid value provided",
        KeyError: "Required key not found",
    }

    # Return generic message for known error types
    for error_type, message in safe_messages.items():
        if isinstance(error, error_type):
            return message

    # For unknown errors, return a generic message
    return "An error occurred during operation"
