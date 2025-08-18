# Vibe CLI Documentation

The Vibe CLI is a powerful wrapper around Continue CLI that makes it easy to run benchmarks and test AI models on coding challenges.

## Installation

```bash
# From the vibe-check directory, run the install script
./install.sh

# Now you can use vibe directly from anywhere!
vibe --help
```

The install script creates a symlink to the vibe command, making it available system-wide. The script uses `uv run` internally to manage Python dependencies automatically.

## Quick Start

```bash
# List available challenges
vibe --list-challenges

# List available models
vibe --list-models

# Run a specific task
vibe --model qwen2.5-coder:7b --task fix_typo

# Run a random easy challenge
vibe --model gpt-oss:20b --challenge easy --random
```

## Command Reference

### Basic Options

| Option | Short | Description |
|--------|-------|-------------|
| `--model MODEL` | `-m` | Specify the model to use (e.g., `qwen2.5-coder:7b`) |
| `--challenge LEVEL` | `-c` | Select challenge difficulty: `smoke`, `easy`, `medium`, `hard` |
| `--task TASK` | `-t` | Run a specific task by name (e.g., `fix_typo`, `basic_todo_app`) |
| `--help` | `-h` | Show help message |

### Discovery Options

| Option | Short | Description |
|--------|-------|-------------|
| `--list-challenges` | `-lc` | List all available challenges organized by difficulty |
| `--list-models` | `-lm` | List all available Ollama models on your system |

### Execution Options

| Option | Description |
|--------|-------------|
| `--interactive` | Run in interactive mode (opens Continue CLI for manual interaction) |
| `--random` | Select a random challenge from the specified difficulty level |
| `--timeout SECONDS` | Set timeout for headless mode (default: 300 seconds) |

## Usage Examples

### Running Specific Tasks

```bash
# Run the basic todo app challenge
uv run ./vibe --model qwen2.5-coder:14b --task basic_todo_app

# Run the advanced todo app challenge
uv run ./vibe --model gpt-oss:20b --task advanced_todo_app

# Run a typo fixing task
uv run ./vibe --model codestral:22b --task fix_typo
```

### Running by Difficulty

```bash
# Run a smoke test (quick validation)
uv run ./vibe --model qwen2.5-coder:7b --challenge smoke

# Choose from easy challenges
uv run ./vibe --model gpt-oss:20b --challenge easy

# Run a random medium challenge
uv run ./vibe --model codestral:22b --challenge medium --random

# Run a hard challenge interactively
uv run ./vibe --model qwen2.5-coder:14b --challenge hard --interactive
```

### Interactive Mode

Interactive mode opens the Continue CLI, allowing you to interact with the model directly:

```bash
# Open interactive session for a medium challenge
uv run ./vibe --model gpt-oss:20b --challenge medium --interactive

# Interactive mode with specific task
uv run ./vibe --model qwen2.5-coder:7b --task refactor_metrics --interactive
```

### Discovery Commands

```bash
# See all available challenges
uv run ./vibe --list-challenges

# Output:
# 📋 Available Challenges:
# ========================================
# 
# 🎯 SMOKE:
#    • add_comment
# 
# 🎯 EASY:
#    • fix_typo
#    • fix_calculator_typos
#    • add_gitignore_entry
# 
# 🎯 MEDIUM:
#    • basic_todo_app
#    • add_validation
#    • add_export_feature
#    ...
# 
# 🎯 HARD:
#    • advanced_todo_app
#    • refactor_metrics
#    • implement_dashboard
#    ...

# See available models
uv run ./vibe --list-models

# Output:
# 🤖 Available Ollama Models:
# ========================================
#    • qwen2.5-coder:14b
#    • gpt-oss:20b
#    • codestral:22b
#    • llama3.2:3b
#    ...
```

## Challenge Difficulties

### Smoke Tests
- **Purpose**: Quick validation (< 30 seconds)
- **Example**: Add a simple comment to code
- **Use Case**: Verify setup is working

### Easy Challenges
- **Purpose**: Basic code modifications
- **Examples**: Fix typos, add gitignore entries
- **Time**: 2-5 minutes
- **Skills Tested**: Basic file editing, pattern matching

### Medium Challenges
- **Purpose**: Implement features or fix complex issues
- **Examples**: 
  - `basic_todo_app`: Create a simple todo application
  - `add_validation`: Add input validation to existing code
- **Time**: 10-20 minutes
- **Skills Tested**: Code organization, error handling, basic architecture

### Hard Challenges
- **Purpose**: Complex implementations requiring planning
- **Examples**:
  - `advanced_todo_app`: Full-featured todo app with persistence, CLI, and tests
  - `refactor_metrics`: Large-scale refactoring
  - `debug_race_condition`: Complex debugging
- **Time**: 30-60 minutes
- **Skills Tested**: Architecture, testing, performance optimization, design patterns

## Featured Challenges

### Todo App Challenges 🆕

Test model planning and implementation capabilities:

#### Basic Todo App (Medium)
```bash
uv run ./vibe --model qwen2.5-coder:14b --task basic_todo_app
```
Tests:
- Basic CRUD operations
- Class design
- Error handling
- Code organization

#### Advanced Todo App (Hard)
```bash
uv run ./vibe --model gpt-oss:20b --task advanced_todo_app
```
Tests:
- Data persistence with JSON
- Category and priority systems
- Tag-based organization
- Search functionality
- CLI interface
- Unit testing (>80% coverage)
- Performance with 1000+ todos
- Design patterns and best practices

## Output and Results

### Console Output

The CLI provides real-time feedback:
- 🚀 Task start notification
- 📝 Task description
- 📊 Difficulty level
- ⏱️ Execution time
- ✅/❌ Success/failure status
- 📁 Result file location

### Result Files

Results are saved as JSON files in `benchmark/results/`:

```json
{
  "model": "qwen2.5-coder:14b",
  "task": "basic_todo_app",
  "success": true,
  "execution_time": 45.2,
  "metrics": {
    "files_created": 1,
    "files_modified": 0,
    "tool_calls": 12,
    "prompts_sent": 1
  },
  "timestamp": "2024-01-20T10:30:00"
}
```

### Analyzing Results

View results using the analyze script:

```bash
# View all results
uv run benchmark/analyze.py

# Export to CSV
uv run benchmark/analyze.py --export

# With visualization
uv run benchmark/analyze.py --visualize
```

## Model Compatibility

### Models with Full Tool Support
- `gpt-oss:20b` ✅
- `codestral:22b` ✅
- GPT-3.5/4 models (with API key)
- Claude models (with API key)

### Models with Limited Tool Support
- `qwen3-coder:30b` ⚠️
- `qwen2.5-coder` series ⚠️
- Most base Ollama models

**Note**: Models without native tool support may not be able to complete file modification tasks in headless mode.

## Troubleshooting

### Common Issues

**"Model does not support tools" error**
- Some models don't have native tool calling support
- Try using models like `gpt-oss:20b` or `codestral:22b`
- Or use `--interactive` mode for manual interaction

**Timeout errors**
- Increase timeout: `--timeout 600` (10 minutes)
- Some complex tasks may need more time
- Consider using a faster model

**"No Ollama models found"**
- Ensure Ollama is running: `ollama serve`
- Pull a model: `ollama pull qwen2.5-coder:7b`
- Verify with: `ollama list`

### Best Practices

1. **Start Small**: Begin with smoke tests and easy challenges
2. **Model Selection**: Use `gpt-oss:20b` or `codestral:22b` for best compatibility
3. **Timeout Settings**: Increase timeout for hard challenges
4. **Interactive Mode**: Use for debugging or when models lack tool support
5. **Result Analysis**: Regularly analyze results to compare model performance

## Advanced Usage

### Batch Testing

Run multiple models on the same task:

```bash
# Create a simple batch script
for model in "qwen2.5-coder:7b" "gpt-oss:20b" "codestral:22b"; do
    echo "Testing $model..."
    uv run ./vibe --model "$model" --task basic_todo_app
done
```

### Custom Timeout for Complex Tasks

```bash
# Give more time for hard challenges
uv run ./vibe --model gpt-oss:20b --task advanced_todo_app --timeout 900
```

### Integration with CI/CD

```yaml
# Example GitHub Actions workflow
- name: Run Vibe Benchmark
  run: |
    uv run ./vibe --model qwen2.5-coder:7b --challenge easy --random
```

## Contributing

To add new challenges:

1. Create a markdown file in `benchmark/tasks/{difficulty}/`
2. Follow the existing format with Requirements and Success Criteria
3. Test with: `uv run ./vibe --model test_model --task your_new_task`

## See Also

- [Continue CLI Documentation](https://docs.continue.dev/reference/cli)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [Benchmark Task Guide](manual-guide.md)
- [Model Configuration](models.md)