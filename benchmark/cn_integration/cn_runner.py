#!/usr/bin/env python3
"""
Continue CLI (cn) Integration for Vibe Check Benchmarking

This module provides automated task execution using the Continue CLI in headless mode.
It handles task preparation, execution, and metrics collection for benchmarking AI models.
"""

from datetime import datetime
import json
import logging
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple

from benchmark.validators import validate_task_file

logger = logging.getLogger(__name__)


class CNExecutionError(Exception):
    """Raised when CN CLI execution fails."""
    pass


class CNRunner:
    """Handles execution of coding tasks using Continue CLI (cn) in headless mode."""
    
    def __init__(self, working_dir: Optional[Path] = None, verbose: bool = False):
        """Initialize CN runner.
        
        Args:
            working_dir: Directory to run tasks in (defaults to current dir)
            verbose: Enable verbose logging
        """
        self.working_dir = Path(working_dir) if working_dir else Path.cwd()
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)
        
        if verbose:
            self.logger.setLevel(logging.DEBUG)
        
        # Check if cn is available
        if not self._check_cn_available():
            raise CNExecutionError("Continue CLI (cn) is not installed. Run: npm i -g @continuedev/cli")
    
    def _check_cn_available(self) -> bool:
        """Check if cn command is available."""
        try:
            result = subprocess.run(
                ["cn", "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _prepare_task_prompt(self, task_file: Path) -> str:
        """Convert a markdown task file into a CN prompt.
        
        Args:
            task_file: Path to the markdown task file
            
        Returns:
            Formatted prompt string for CN
        """
        with open(task_file, 'r') as f:
            content = f.read()
        
        # Extract key information from the markdown
        lines = content.split('\n')
        title = ""
        requirements = []
        success_criteria = []
        
        current_section = None
        for line in lines:
            line = line.strip()
            
            if line.startswith('# Task:'):
                title = line.replace('# Task:', '').strip()
            elif line.startswith('## Requirements'):
                current_section = "requirements"
            elif line.startswith('## Success Criteria'):
                current_section = "success_criteria"
            elif line.startswith('##'):
                current_section = None
            elif line.startswith('- ') and current_section == "requirements":
                requirements.append(line[2:])
            elif line.startswith('- [ ]') and current_section == "success_criteria":
                success_criteria.append(line[5:].strip())
        
        # Build the prompt
        prompt_parts = [f"Task: {title}"]
        
        if requirements:
            prompt_parts.append("\nRequirements:")
            for req in requirements:
                prompt_parts.append(f"- {req}")
        
        if success_criteria:
            prompt_parts.append("\nSuccess Criteria:")
            for criteria in success_criteria:
                prompt_parts.append(f"- {criteria}")
        
        prompt_parts.append(f"\nWorking directory: {self.working_dir}")
        prompt_parts.append("\nPlease complete this task by modifying the necessary files.")
        
        return "\n".join(prompt_parts)
    
    def _get_permission_flags(self, task_type: str = "default") -> List[str]:
        """Get appropriate CN permission flags for task type.
        
        Args:
            task_type: Type of task (code_modification, analysis, etc.)
            
        Returns:
            List of CN permission flags
        """
        if task_type == "analysis":
            return ["--allow", "Read()", "--exclude", "Write()"]
        elif task_type == "safe":
            return ["--allow", "Read()", "--allow", "Write()", "--exclude", "Bash()"]
        else:
            # Default permissions for most coding tasks
            return [
                "--allow", "Read()",
                "--allow", "Write()", 
                "--ask", "Bash(*)"  # Ask before running any bash commands
            ]
    
    def _create_temp_config(self, model_name: str, provider: str = "auto") -> Path:
        """Create a temporary CN configuration file.
        
        Args:
            model_name: Name of the model to use
            provider: Provider type (auto, ollama, openai, etc.)
            
        Returns:
            Path to temporary config file
        """
        # Basic config structure for CN
        config = {
            "models": {
                "chat": model_name
            }
        }
        
        # Handle different providers
        if provider == "auto":
            if model_name.startswith("ollama/"):
                provider = "ollama"
                model_name = model_name.replace("ollama/", "")
            elif "gpt" in model_name.lower():
                provider = "openai"
            elif "claude" in model_name.lower():
                provider = "anthropic"
        
        # Add provider-specific settings
        if provider == "ollama":
            config["models"]["chat"] = {
                "provider": "ollama",
                "model": model_name
            }
        elif provider == "openai":
            config["models"]["chat"] = {
                "provider": "openai",
                "model": model_name,
                "apiKey": "${OPENAI_API_KEY}"
            }
        elif provider == "anthropic":
            config["models"]["chat"] = {
                "provider": "anthropic",
                "model": model_name,
                "apiKey": "${ANTHROPIC_API_KEY}"
            }
        
        # Create temporary file
        temp_config = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.yaml',
            delete=False,
            prefix='cn_config_'
        )
        
        # Write YAML content (simple format)
        temp_config.write("models:\n")
        temp_config.write("  chat:\n")
        if isinstance(config["models"]["chat"], str):
            temp_config.write(f"    model: {config['models']['chat']}\n")
        else:
            for key, value in config["models"]["chat"].items():
                temp_config.write(f"    {key}: {value}\n")
        
        temp_config.flush()
        temp_config.close()
        
        return Path(temp_config.name)
    
    def _execute_cn_command(self, prompt: str, config_path: Optional[Path] = None, 
                          permissions: Optional[List[str]] = None, timeout: int = 600) -> Tuple[str, str, int]:
        """Execute CN command with given prompt and options.
        
        Args:
            prompt: The task prompt to send to CN
            config_path: Path to CN config file
            permissions: Permission flags to pass to CN
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (stdout, stderr, returncode)
        """
        cmd = ["cn", "-p", prompt]
        
        if config_path:
            cmd.extend(["--config", str(config_path)])
        
        if permissions:
            cmd.extend(permissions)
        
        self.logger.debug(f"Executing CN command: {' '.join(shlex.quote(arg) for arg in cmd)}")
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            self.logger.debug(f"CN return code: {result.returncode}")
            if result.stdout:
                self.logger.debug(f"CN stdout: {result.stdout[:500]}...")
            if result.stderr:
                self.logger.debug(f"CN stderr: {result.stderr[:500]}...")
            
            return result.stdout, result.stderr, result.returncode
            
        except subprocess.TimeoutExpired:
            raise CNExecutionError(f"CN command timed out after {timeout} seconds")
        except Exception as e:
            raise CNExecutionError(f"Failed to execute CN command: {e}")
    
    def _extract_metrics_from_output(self, stdout: str, stderr: str, execution_time: float) -> Dict[str, Any]:
        """Extract metrics from CN output.
        
        Args:
            stdout: Standard output from CN
            stderr: Standard error from CN
            execution_time: Time taken to execute
            
        Returns:
            Dictionary of extracted metrics
        """
        metrics = {
            "execution_time": execution_time,
            "prompts_sent": 1,  # Headless mode sends one prompt
            "tool_calls": 0,
            "files_read": 0,
            "files_written": 0,
            "success": False,
            "cn_output": stdout,
            "cn_errors": stderr
        }
        
        # Parse output for tool calls and actions
        output_text = stdout + "\n" + stderr
        
        # Count tool calls (this is heuristic, may need adjustment based on CN output format)
        tool_patterns = [
            (r"Reading file|Read file", "files_read"),
            (r"Writing to file|Wrote file|Modified file", "files_written"),
            (r"Running command|Executed", "bash_commands"),
        ]
        
        for pattern, metric_key in tool_patterns:
            matches = re.findall(pattern, output_text, re.IGNORECASE)
            if metric_key in metrics:
                metrics[metric_key] += len(matches)
            else:
                metrics[metric_key] = len(matches)
            metrics["tool_calls"] += len(matches)
        
        # Determine success based on output
        success_indicators = [
            "task completed",
            "successfully",
            "fixed",
            "done",
            "completed the task"
        ]
        
        metrics["success"] = any(
            indicator in output_text.lower() 
            for indicator in success_indicators
        )
        
        return metrics
    
    def _get_git_changes(self) -> Dict[str, int]:
        """Get git diff statistics for files changed.
        
        Returns:
            Dictionary with files_modified, lines_added, lines_removed
        """
        try:
            # Get list of modified files
            result = subprocess.run(
                ["git", "diff", "--name-only"],
                cwd=self.working_dir,
                capture_output=True,
                text=True
            )
            
            files_modified = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            
            # Get line statistics
            result = subprocess.run(
                ["git", "diff", "--numstat"],
                cwd=self.working_dir,
                capture_output=True,
                text=True
            )
            
            lines_added = 0
            lines_removed = 0
            
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                        lines_added += int(parts[0])
                        lines_removed += int(parts[1])
            
            return {
                "files_modified": files_modified,
                "lines_added": lines_added,
                "lines_removed": lines_removed
            }
        except Exception as e:
            self.logger.warning(f"Could not get git changes: {e}")
            return {"files_modified": 0, "lines_added": 0, "lines_removed": 0}
    
    def run_task(self, task_file: str, model_name: str, provider: str = "auto", 
                 timeout: int = 600, task_type: str = "default") -> Dict[str, Any]:
        """Run a benchmark task using Continue CLI.
        
        Args:
            task_file: Path to the task markdown file
            model_name: Name of the model to use
            provider: Model provider (auto, ollama, openai, etc.)
            timeout: Timeout in seconds
            task_type: Type of task for permission settings
            
        Returns:
            Dictionary with task results and metrics
        """
        start_time = time.time()
        task_path = validate_task_file(task_file)
        task_name = task_path.stem
        
        self.logger.info(f"Starting CN task: {task_name} with model: {model_name}")
        
        # Create temporary config
        config_path = None
        try:
            config_path = self._create_temp_config(model_name, provider)
            
            # Prepare task prompt
            prompt = self._prepare_task_prompt(task_path)
            self.logger.debug(f"Task prompt: {prompt[:200]}...")
            
            # Get appropriate permissions
            permissions = self._get_permission_flags(task_type)
            
            # Record initial git state
            self._get_git_changes()
            
            # Execute CN command
            stdout, stderr, returncode = self._execute_cn_command(
                prompt, config_path, permissions, timeout
            )
            
            execution_time = time.time() - start_time
            
            # Extract metrics from output
            metrics = self._extract_metrics_from_output(stdout, stderr, execution_time)
            
            # Get git changes
            git_changes = self._get_git_changes()
            metrics.update(git_changes)
            
            # Build result dictionary
            result = {
                "task_name": task_name,
                "model_name": model_name,
                "provider": provider,
                "success": returncode == 0 and metrics["success"],
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
                "metrics": metrics,
                "cn_returncode": returncode
            }
            
            self.logger.info(f"CN task completed: {task_name} - Success: {result['success']} - Time: {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.logger.error(f"CN task failed: {task_name} - Error: {e}")
            
            return {
                "task_name": task_name,
                "model_name": model_name,
                "provider": provider,
                "success": False,
                "execution_time": execution_time,
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "metrics": {"execution_time": execution_time, "success": False}
            }
        
        finally:
            # Clean up temporary config
            if config_path and config_path.exists():
                config_path.unlink()
    
    def run_multiple_tasks(self, task_files: List[str], model_name: str, 
                          provider: str = "auto", timeout: int = 600) -> List[Dict[str, Any]]:
        """Run multiple tasks sequentially.
        
        Args:
            task_files: List of task file paths
            model_name: Name of the model to use
            provider: Model provider
            timeout: Timeout per task in seconds
            
        Returns:
            List of task results
        """
        results = []
        
        for task_file in task_files:
            result = self.run_task(task_file, model_name, provider, timeout)
            results.append(result)
            
            # Brief pause between tasks
            time.sleep(1)
        
        return results


def test_cn_integration():
    """Test function to verify CN integration works."""
    runner = CNRunner(verbose=True)
    
    # Test with a simple task
    test_task = "benchmark/tasks/easy/fix_typo.md"
    if Path(test_task).exists():
        result = runner.run_task(test_task, "gpt-3.5-turbo", timeout=120)
        print(f"Test result: {json.dumps(result, indent=2)}")
        return result
    else:
        print(f"Test task not found: {test_task}")
        return None


if __name__ == "__main__":
    # Run test
    test_cn_integration()
