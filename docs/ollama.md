# Ollama Integration Guide

This guide covers how to use Ollama with the Vibe Check benchmark framework.

## Table of Contents
- [Installation](#installation)
- [Running with uv](#running-with-uv)
- [Ollama Health Check](#ollama-health-check)
- [Running Benchmarks](#running-benchmarks)
- [Troubleshooting](#troubleshooting)

## Installation

### 1. Install Ollama

Download and install Ollama for your platform:
- **macOS**: [Download from ollama.ai](https://ollama.ai/download/mac)
- **Linux**: `curl -fsSL https://ollama.ai/install.sh | sh`
- **Windows**: [Download from ollama.ai](https://ollama.ai/download/windows)

### 2. Start Ollama Service

```bash
# macOS: Ollama runs automatically after installation
# Or manually start with:
ollama serve

# Linux:
systemctl start ollama
# Or manually:
ollama serve

# Windows: Start from the system tray or run:
ollama serve
```

### 3. Pull Models

```bash
# Popular models for coding tasks
ollama pull llama2
ollama pull codellama
ollama pull mistral
ollama pull deepseek-coder
ollama pull qwen2.5-coder

# List available models
ollama list
```

## Running with uv

The `uv` package manager is recommended for running benchmarks as it handles dependencies automatically and is 10-100x faster than pip.

### Why use uv?
- **Fast**: Installs packages in milliseconds instead of seconds
- **Reliable**: Ensures all dependencies are installed
- **Simple**: No need to manage virtual environments manually
- **Consistent**: Same environment across different machines

### Basic Commands with uv

```bash
# Run Ollama health check
uv run -m benchmark.ollama_check

# Run task runner with Ollama model
uv run -m benchmark.task_runner "ollama/llama2" "benchmark/tasks/easy/fix_typo.md"

# Run analysis
uv run -m benchmark.analyze

# Run tests
uv run pytest tests/test_ollama_check.py
```

## Ollama Health Check

The framework includes a comprehensive Ollama health check system that runs automatically when using Ollama models.

### Standalone Health Check

```bash
# Full system check
uv run -m benchmark.ollama_check

# Check specific model
uv run -m benchmark.ollama_check --model llama2

# Quiet mode (less output)
uv run -m benchmark.ollama_check --quiet

# JSON output for automation
uv run -m benchmark.ollama_check --json

# Auto-pull missing models
uv run -m benchmark.ollama_check --model codellama --pull
```

### Integrated Health Check

When running benchmarks with Ollama models, the health check runs automatically:

```bash
# Automatic check when using ollama/ prefix
uv run -m benchmark.task_runner "ollama/llama2" "benchmark/tasks/easy/fix_typo.md"

# Manual check
uv run -m benchmark.task_runner --check-ollama

# Skip checks if you're confident everything is set up
uv run -m benchmark.task_runner "ollama/llama2" "task.md" --skip-ollama-check
```

### What Gets Checked?

1. **Ollama Installation**
   - Binary exists in PATH
   - Version information available

2. **Service Status**
   - Ollama service is running
   - Can communicate with the service

3. **Model Availability**
   - Lists all installed models
   - Verifies specific model if requested
   - Offers to pull missing models

4. **Platform-Specific Help**
   - Provides tailored instructions for macOS, Linux, and Windows
   - Shows exact commands to fix issues

## Running Benchmarks

### Model Naming Convention

When using Ollama models, use the `ollama/` prefix:

```bash
# Correct format
uv run -m benchmark.task_runner "ollama/llama2" "task.md"
uv run -m benchmark.task_runner "ollama/codellama" "task.md"
uv run -m benchmark.task_runner "ollama/mistral" "task.md"

# Alternative format (also supported)
uv run -m benchmark.task_runner "ollama-llama2" "task.md"
```

### Example Workflow

1. **Check your setup**:
   ```bash
   uv run -m benchmark.ollama_check
   ```

2. **Pull required models**:
   ```bash
   ollama pull llama2
   ollama pull codellama
   ```

3. **Run a benchmark**:
   ```bash
   uv run -m benchmark.task_runner "ollama/llama2" "benchmark/tasks/easy/fix_typo.md"
   ```

4. **Analyze results**:
   ```bash
   uv run -m benchmark.analyze
   ```

## Troubleshooting

### Common Issues and Solutions

#### 1. "Ollama is not installed"

**Solution**: Install Ollama from https://ollama.ai/download

#### 2. "Ollama service is not running"

**macOS**:
```bash
# Start from Applications or run:
ollama serve
```

**Linux**:
```bash
# With systemd:
sudo systemctl start ollama

# Or manually:
ollama serve
```

**Windows**:
- Check system tray for Ollama icon
- Or run `ollama serve` in terminal

#### 3. "No models found"

**Solution**: Pull at least one model:
```bash
ollama pull llama2
ollama pull codellama
ollama pull mistral
```

#### 4. "Model 'X' is not available"

**Solution**: Pull the specific model:
```bash
ollama pull <model-name>

# Or use auto-pull:
uv run -m benchmark.ollama_check --model <model-name> --pull
```

#### 5. "Connection refused" error

**Solution**: Ensure Ollama service is running:
```bash
# Check if running
curl http://localhost:11434/api/tags

# If not, start it:
ollama serve
```

### Getting Help

```bash
# Check Ollama version
ollama --version

# List running models
ollama list

# Check Ollama logs (Linux/macOS)
journalctl -u ollama -f  # Linux with systemd
tail -f ~/.ollama/logs/server.log  # macOS

# Test Ollama directly
ollama run llama2 "Hello, world!"
```

## Performance Tips

1. **Model Selection**:
   - Smaller models (7B) are faster but less capable
   - Larger models (13B, 70B) are more capable but slower
   - For coding tasks, specialized models like `codellama` perform better

2. **Resource Management**:
   - Ollama uses GPU when available (CUDA on Linux/Windows, Metal on macOS)
   - Close other applications to free up memory
   - Monitor resource usage with `ollama ps`

3. **Model Preloading**:
   ```bash
   # Keep model loaded in memory
   ollama run llama2 --keep-alive 60m
   ```

## Integration with CI/CD

For automated testing, use JSON output:

```bash
# Check if Ollama is ready
if uv run -m benchmark.ollama_check --json | jq -e '.ready'; then
    echo "Ollama is ready"
    uv run -m benchmark.task_runner "ollama/llama2" "task.md"
else
    echo "Ollama setup incomplete"
    exit 1
fi
```

## Security Considerations

- Ollama runs locally, keeping your code private
- No data is sent to external servers
- Models are stored in `~/.ollama/models/`
- Default API endpoint: `http://localhost:11434`

## Additional Resources

- [Ollama Documentation](https://github.com/jmorganca/ollama)
- [Ollama Model Library](https://ollama.ai/library)
- [Vibe Check Repository](https://github.com/bdougie/vibe-check)
- [uv Documentation](https://github.com/astral-sh/uv)