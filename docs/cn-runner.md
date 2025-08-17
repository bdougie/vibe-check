# CN Runner Documentation

## Overview

The `CNRunner` class provides automated task execution using the Continue CLI (`cn`) in headless mode. It enables running coding tasks without human intervention, making it perfect for automated benchmarking of AI models.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Permissions System](#permissions-system)
- [Metrics Collection](#metrics-collection)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Installation

### Prerequisites

1. **Continue CLI**: Install the Continue CLI globally:
   ```bash
   npm i -g @continuedev/cli
   ```

2. **Python Dependencies**: Install required Python packages:
   ```bash
   uv pip install pyyaml psutil
   ```

3. **API Keys**: Set up environment variables for your AI providers:
   ```bash
   export OPENAI_API_KEY="your-key-here"
   export ANTHROPIC_API_KEY="your-key-here"
   ```

## Quick Start

```python
from benchmark.cn_integration.cn_runner import CNRunner

# Initialize the runner
runner = CNRunner(verbose=True)

# Run a task
result = runner.run_task(
    task_file="benchmark/tasks/easy/fix_typo.md",
    model_name="gpt-3.5-turbo",
    timeout=300
)

# Check results
if result["success"]:
    print(f"Task completed in {result['execution_time']:.2f} seconds")
    print(f"Files modified: {result['metrics']['files_modified']}")
```

## Architecture

### Components

```
CNRunner
├── Task Processing
│   ├── _prepare_task_prompt()     # Convert markdown to prompt
│   └── validate_task_file()       # Validate task file path
├── Configuration
│   ├── _create_temp_config()      # Generate CN config files
│   └── _get_permission_flags()    # Set permission levels
├── Execution
│   ├── _execute_cn_command()      # Run CN CLI
│   └── run_task()                 # Main task execution
└── Metrics
    ├── _extract_metrics_from_output()  # Parse CN output
    └── _get_git_changes()              # Track file changes
```

### Workflow

1. **Validation**: Task file is validated for security
2. **Preparation**: Markdown task is converted to CN prompt
3. **Configuration**: Temporary config file is created for model
4. **Execution**: CN CLI runs the task in headless mode
5. **Collection**: Metrics are extracted from output and git
6. **Cleanup**: Temporary files are removed

## API Reference

### CNRunner Class

#### `__init__(working_dir: Optional[Path] = None, verbose: bool = False)`

Initialize the CN runner.

**Parameters:**
- `working_dir`: Directory to run tasks in (defaults to current directory)
- `verbose`: Enable verbose logging for debugging

**Raises:**
- `CNExecutionError`: If Continue CLI is not installed

#### `run_task(task_file: str, model_name: str, provider: str = "auto", timeout: int = 600, task_type: str = "default") -> Dict[str, Any]`

Run a benchmark task using Continue CLI.

**Parameters:**
- `task_file`: Path to the markdown task file
- `model_name`: Name of the AI model to use
- `provider`: Model provider ("auto", "ollama", "openai", "anthropic")
- `timeout`: Maximum execution time in seconds
- `task_type`: Permission level ("default", "safe", "analysis")

**Returns:**
```python
{
    "task_name": "fix_typo",
    "model_name": "gpt-3.5-turbo",
    "provider": "openai",
    "success": True,
    "execution_time": 45.2,
    "timestamp": "2024-01-15T10:30:00",
    "metrics": {
        "prompts_sent": 1,
        "tool_calls": 5,
        "files_read": 2,
        "files_written": 1,
        "files_modified": 1,
        "lines_added": 10,
        "lines_removed": 5,
        "success": True
    },
    "cn_returncode": 0
}
```

#### `run_multiple_tasks(task_files: List[str], model_name: str, provider: str = "auto", timeout: int = 600) -> List[Dict[str, Any]]`

Run multiple tasks sequentially.

**Parameters:**
- `task_files`: List of task file paths
- `model_name`: Name of the AI model to use
- `provider`: Model provider
- `timeout`: Timeout per task in seconds

**Returns:**
List of task results (same format as `run_task()`)

## Configuration

### Model Providers

The runner automatically detects providers based on model names:

| Model Pattern | Provider | Example |
|--------------|----------|---------|
| `ollama/*` | Ollama | `ollama/llama2` |
| `gpt*` | OpenAI | `gpt-3.5-turbo`, `gpt-4` |
| `claude*` | Anthropic | `claude-3-sonnet` |

### Custom Configuration

You can specify providers explicitly:

```python
# Use Ollama
result = runner.run_task(
    "task.md",
    model_name="llama2",
    provider="ollama"
)

# Use OpenAI
result = runner.run_task(
    "task.md", 
    model_name="gpt-4",
    provider="openai"
)
```

### Environment Variables

Configure API keys through environment variables:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Ollama (local, no key needed)
# Just ensure Ollama is running: ollama serve
```

## Permissions System

Control what actions the AI can perform:

### Permission Levels

| Task Type | Read | Write | Bash | Use Case |
|-----------|------|-------|------|----------|
| `default` | ✅ | ✅ | ⚠️ Ask | General coding tasks |
| `safe` | ✅ | ✅ | ❌ | No shell commands |
| `analysis` | ✅ | ❌ | ❌ | Read-only analysis |

### Setting Permissions

```python
# Read-only analysis
result = runner.run_task(
    "analyze.md",
    model_name="gpt-4",
    task_type="analysis"  # Can only read files
)

# Safe mode (no bash)
result = runner.run_task(
    "refactor.md",
    model_name="gpt-4",
    task_type="safe"  # Can read/write but no shell
)

# Default (ask for bash)
result = runner.run_task(
    "test.md",
    model_name="gpt-4",
    task_type="default"  # Will ask before running commands
)
```

## Metrics Collection

### Extracted Metrics

The runner collects comprehensive metrics:

1. **Execution Metrics**
   - `execution_time`: Total time in seconds
   - `prompts_sent`: Number of prompts (always 1 in headless mode)
   - `cn_returncode`: Exit code from CN CLI

2. **Tool Usage**
   - `tool_calls`: Total number of tool invocations
   - `files_read`: Number of files read
   - `files_written`: Number of files written
   - `bash_commands`: Number of shell commands run

3. **Git Changes**
   - `files_modified`: Number of files changed
   - `lines_added`: Total lines added
   - `lines_removed`: Total lines removed

4. **Success Indicators**
   - `success`: Boolean indicating task completion
   - `cn_output`: Full stdout from CN
   - `cn_errors`: Full stderr from CN

### Accessing Metrics

```python
result = runner.run_task("task.md", "gpt-4")

# Check success
if result["success"]:
    metrics = result["metrics"]
    print(f"Files modified: {metrics['files_modified']}")
    print(f"Lines changed: +{metrics['lines_added']} -{metrics['lines_removed']}")
    print(f"Tool calls: {metrics['tool_calls']}")
```

## Examples

### Basic Task Execution

```python
from benchmark.cn_integration.cn_runner import CNRunner
from pathlib import Path

# Initialize runner with custom working directory
runner = CNRunner(
    working_dir=Path("./sample_project"),
    verbose=True
)

# Run a simple task
result = runner.run_task(
    "benchmark/tasks/easy/fix_typo.md",
    "gpt-3.5-turbo"
)

print(f"Success: {result['success']}")
print(f"Time: {result['execution_time']:.2f}s")
```

### Batch Processing

```python
# Run multiple tasks
task_files = [
    "benchmark/tasks/easy/fix_typo.md",
    "benchmark/tasks/easy/add_comment.md",
    "benchmark/tasks/medium/add_validation.md"
]

results = runner.run_multiple_tasks(
    task_files,
    model_name="gpt-4",
    timeout=300  # 5 minutes per task
)

# Analyze results
successful = sum(1 for r in results if r["success"])
print(f"Completed {successful}/{len(results)} tasks")
```

### Error Handling

```python
from benchmark.cn_integration.cn_runner import CNRunner, CNExecutionError

try:
    runner = CNRunner()
    result = runner.run_task(
        "task.md",
        "gpt-4",
        timeout=60  # Short timeout
    )
except CNExecutionError as e:
    print(f"CN execution failed: {e}")
    # Handle CN not installed or other execution errors
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Custom Model Configuration

```python
# Use local Ollama model
result = runner.run_task(
    "task.md",
    model_name="codellama:13b",
    provider="ollama"
)

# Use specific OpenAI model
result = runner.run_task(
    "task.md",
    model_name="gpt-4-turbo-preview",
    provider="openai"
)

# Auto-detect provider
result = runner.run_task(
    "task.md",
    model_name="ollama/mistral"  # Auto-detects Ollama
)
```

## Task File Format

Task files should follow this markdown structure:

```markdown
# Task: Fix Calculator Typos

**Difficulty**: Easy
**Category**: Bug Fix

## Requirements
- Fix typo "paramter" to "parameter"
- Fix typo "reuslt" to "result"
- Ensure code still runs correctly

## Success Criteria
- [ ] All typos are fixed
- [ ] No syntax errors introduced
- [ ] File is saved properly

## Context
The calculator.py file has several typos that need fixing.
```

### Required Sections

1. **Task Title**: `# Task: <title>`
2. **Requirements**: List of specific requirements
3. **Success Criteria**: Checklist of completion criteria

## Troubleshooting

### Common Issues

#### CN CLI Not Found

**Error:** `CNExecutionError: Continue CLI (cn) is not installed`

**Solution:**
```bash
npm i -g @continuedev/cli
cn --version  # Verify installation
```

#### Model Not Available

**Error:** `Error: Model not available`

**Solutions:**
1. Check API key is set: `echo $OPENAI_API_KEY`
2. For Ollama, ensure model is pulled: `ollama pull llama2`
3. Verify Ollama is running: `ollama list`

#### Timeout Issues

**Error:** `CNExecutionError: CN command timed out after 600 seconds`

**Solutions:**
1. Increase timeout: `runner.run_task("task.md", "model", timeout=1200)`
2. Use simpler model for complex tasks
3. Break large tasks into smaller ones

#### Permission Denied

**Error:** `Permission denied` when writing files

**Solutions:**
1. Check file permissions in working directory
2. Run with appropriate user permissions
3. Use `task_type="analysis"` for read-only tasks

### Debug Mode

Enable verbose logging for debugging:

```python
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Create runner with verbose mode
runner = CNRunner(verbose=True)

# Run task - will show detailed debug output
result = runner.run_task("task.md", "gpt-4")
```

### Checking CN Installation

```python
from benchmark.cn_integration.cn_runner import CNRunner

runner = CNRunner()
if runner._check_cn_available():
    print("✅ CN CLI is installed and working")
else:
    print("❌ CN CLI is not available")
```

## Best Practices

1. **Start Small**: Test with simple tasks first
2. **Use Appropriate Models**: Match model capability to task complexity
3. **Set Reasonable Timeouts**: Allow enough time for complex tasks
4. **Monitor Resources**: Watch memory/CPU usage for large tasks
5. **Handle Errors Gracefully**: Always wrap in try-except blocks
6. **Clean Up**: Temporary configs are auto-cleaned, but check for leftover files
7. **Version Control**: Use git to track changes made by CN

## Integration with Vibe Check

The CN Runner integrates seamlessly with the Vibe Check benchmarking system:

```python
from benchmark.cn_integration.cn_batch_integration import CNBatchIntegration

# Run batch benchmark with CN
integration = CNBatchIntegration()
result = integration.run_batch_with_cn(
    task_files=["task1.md", "task2.md"],
    models=[
        {"name": "gpt-3.5-turbo"},
        {"name": "gpt-4"},
        {"name": "ollama/llama2"}
    ],
    timeout=300
)

print(f"Success rate: {result['success_rate']:.1f}%")
```

## Support

For issues or questions:
1. Check the [GitHub Issues](https://github.com/bdougie/vibe-check/issues)
2. Review the [Continue CLI docs](https://docs.continue.dev/cli)
3. Enable verbose mode for debugging
4. Check system requirements and permissions