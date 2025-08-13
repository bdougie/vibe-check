# Model Setup Guide

This guide helps you select and download the right AI models for benchmarking based on your system resources.

## Quick Start

### 1. Check Your System and Models

Run the model verification script to see what models you have and what you need:

```bash
# Full verification report
uv run python -m benchmark.model_verifier

# Get download commands for missing models
uv run python -m benchmark.model_verifier --download

# Get model suggestions based on your system
uv run python -m benchmark.model_verifier --suggest

# JSON output for automation
uv run python -m benchmark.model_verifier --json
```

### 2. Download Essential Models

At minimum, you need one of these essential models:

```bash
# Base models for general coding tasks
ollama pull llama2       # 3.8 GB, needs 8GB RAM
ollama pull codellama    # 3.8 GB, needs 8GB RAM (recommended for coding)
```

### 3. Download Recommended Models (Optional)

For better benchmark results:

```bash
# Better performance models
ollama pull mistral         # 4.1 GB, needs 8GB RAM
ollama pull deepseek-coder  # 4.0 GB, needs 8GB RAM
ollama pull qwen2.5-coder   # 4.0 GB, needs 8GB RAM
```

## Model Categories

### Essential Models (Start Here)
These models provide good baseline performance and work on most systems:

| Model | Size | RAM Required | Description |
|-------|------|--------------|-------------|
| `llama2` | 3.8 GB | 8 GB | Base Llama 2 model, good general-purpose |
| `codellama` | 3.8 GB | 8 GB | Code-specialized, excellent for coding tasks |

### Recommended Models (Better Performance)
These models offer improved capabilities with moderate resource requirements:

| Model | Size | RAM Required | Description |
|-------|------|--------------|-------------|
| `mistral` | 4.1 GB | 8 GB | High-quality 7B model with good reasoning |
| `deepseek-coder` | 4.0 GB | 8 GB | Specialized coding model with strong performance |
| `qwen2.5-coder` | 4.0 GB | 8 GB | Latest Qwen coding model |

### Optional Models (Advanced)
For systems with more resources:

| Model | Size | RAM Required | Description |
|-------|------|--------------|-------------|
| `codellama:13b` | 7.3 GB | 16 GB | Larger CodeLlama with improved capabilities |
| `mixtral` | 26 GB | 32 GB | High-quality MoE model, excellent but resource-intensive |
| `llama2:70b` | 40 GB | 64 GB | Large Llama 2 model with superior capabilities |

## System Requirements

### Minimum Requirements
- **RAM**: 8 GB (for essential models)
- **Disk Space**: 10 GB free
- **OS**: macOS, Linux, or Windows
- **Ollama**: Installed and running

### Recommended Requirements
- **RAM**: 16 GB (for better models)
- **Disk Space**: 50 GB free
- **GPU**: Optional but improves performance

### High-Performance Setup
- **RAM**: 32+ GB
- **Disk Space**: 100+ GB free
- **GPU**: NVIDIA GPU with CUDA support

## Checking Your System

The model verifier automatically checks your system and recommends appropriate models:

```bash
# See what your system can handle
uv run python -m benchmark.model_verifier --suggest
```

Example output for different systems:

### Low-End System (8GB RAM)
```
Recommended models:
  ✅ llama2 (3.8 GB, needs 8GB RAM)
  ✅ codellama (3.8 GB, needs 8GB RAM)
  ⬇️ mistral (4.1 GB, needs 8GB RAM)
```

### Mid-Range System (16GB RAM)
```
Recommended models:
  ✅ codellama (3.8 GB, needs 8GB RAM)
  ✅ mistral (4.1 GB, needs 8GB RAM)
  ⬇️ codellama:13b (7.3 GB, needs 16GB RAM)
  ⬇️ deepseek-coder (4.0 GB, needs 8GB RAM)
```

### High-End System (32GB+ RAM)
```
Recommended models:
  ✅ codellama:13b (7.3 GB, needs 16GB RAM)
  ✅ mixtral (26 GB, needs 32GB RAM)
  ⬇️ llama2:70b (40 GB, needs 64GB RAM)
```

## Download Strategies

### 1. Space-Conscious Installation
If you have limited disk space:

```bash
# Start with just one small model
ollama pull codellama

# Test it works
ollama run codellama "Hello, world!"

# Then add more as needed
```

### 2. Batch Download
Download multiple models at once:

```bash
# Download all essential models
for model in llama2 codellama mistral; do
  ollama pull $model
done
```

### 3. Progressive Download
Start small and upgrade:

```bash
# Start with base model
ollama pull codellama

# If that works well, get the larger version
ollama pull codellama:13b

# Remove the smaller one if needed
ollama rm codellama
```

## Disk Space Management

### Check Model Sizes
```bash
# List installed models with sizes
ollama list

# Check total disk usage
du -sh ~/.ollama/models
```

### Remove Unused Models
```bash
# Remove a specific model
ollama rm model_name

# Example: Remove large model to free space
ollama rm llama2:70b
```

### Model Storage Location
Models are stored in:
- **macOS/Linux**: `~/.ollama/models/`
- **Windows**: `%USERPROFILE%\.ollama\models\`

## Troubleshooting

### "Insufficient Disk Space"
```bash
# Check available space
df -h ~/.ollama

# Remove unused models
ollama list  # See what you have
ollama rm unwanted_model

# Consider external storage
# You can symlink the models directory to external drive
```

### "Out of Memory" Errors
```bash
# Use smaller models
ollama pull llama2  # Instead of llama2:13b

# Or use quantized versions
ollama pull llama2:7b-q4_0  # Smaller, quantized version
```

### "Model Not Found"
```bash
# Check exact model name
ollama search codellama

# Pull with specific tag
ollama pull codellama:latest
ollama pull codellama:13b
```

## Cloud Alternatives

If your system can't run local models, consider cloud alternatives:

### Using Cloud Models with Benchmarks
```bash
# Use OpenAI models
python -m benchmark.task_runner "gpt-4" "benchmark/tasks/easy/fix_typo.md"

# Use Anthropic models
python -m benchmark.task_runner "claude-3-opus" "benchmark/tasks/easy/fix_typo.md"
```

### Hybrid Approach
Use small local models for testing, cloud models for production:

```bash
# Test locally with small model
python -m benchmark.task_runner "ollama/llama2" "task.md"

# Run same test with cloud model
python -m benchmark.task_runner "gpt-4" "task.md"
```

## Performance Tips

### 1. Model Loading
Keep frequently used models in memory:

```bash
# Keep model loaded for 30 minutes
ollama run codellama --keep-alive 30m
```

### 2. GPU Acceleration
- **macOS**: Metal acceleration is automatic
- **Linux/Windows**: Install CUDA for NVIDIA GPUs
- Check GPU usage: `ollama ps`

### 3. Concurrent Models
Running multiple models requires more RAM:

```bash
# Check current memory usage
ollama ps

# Stop unused models
ollama stop model_name
```

## Automation

### Pre-flight Check Script
Create a script to verify models before benchmarking:

```bash
#!/bin/bash
# check_models.sh

echo "Checking Ollama setup..."
if ! ollama list > /dev/null 2>&1; then
    echo "ERROR: Ollama is not running"
    echo "Start with: ollama serve"
    exit 1
fi

# Check for essential models
REQUIRED_MODELS="llama2 codellama"
MISSING=""

for model in $REQUIRED_MODELS; do
    if ! ollama list | grep -q "$model"; then
        MISSING="$MISSING $model"
    fi
done

if [ -n "$MISSING" ]; then
    echo "Missing models:$MISSING"
    echo "Install with: ollama pull$MISSING"
    exit 1
fi

echo "✅ All required models are installed"
```

### CI/CD Integration
```yaml
# .github/workflows/benchmark.yml
- name: Check Models
  run: |
    python -m benchmark.model_verifier --json > model_check.json
    if ! jq -e '.ready' model_check.json; then
      echo "Models not ready"
      exit 1
    fi
```

## Next Steps

1. **Run the verifier**: `uv run python -m benchmark.model_verifier`
2. **Download essential models**: Follow the download commands provided
3. **Test a model**: `ollama run codellama "Write a Python hello world"`
4. **Start benchmarking**: `uv run python -m benchmark.task_runner "ollama/codellama" "benchmark/tasks/easy/fix_typo.md"`

## Related Documentation

- [Ollama Integration Guide](OLLAMA.md) - Complete Ollama setup
- [README](../README.md) - Main documentation
- [Benchmark Tasks](../benchmark/tasks/) - Available benchmark tasks