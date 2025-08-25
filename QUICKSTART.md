# 🚀 Vibe Check Quick Start Guide

Get started with AI benchmarking in 10 minutes! This guide prioritizes the manual benchmarking workflow with Continue for immediate, realistic testing.

## Choose Your Path

### 🎯 Manual Benchmarking (Recommended)
**Best for**: Real-world testing, immediate feedback, natural AI interaction
→ Continue with this guide

### 🤖 Automated CLI Benchmarking
**Best for**: Batch testing, CI/CD, headless operation
→ See [CLI Benchmarking Guide](docs/cli-benchmarking.md)

## Prerequisites Checklist

### 📦 System Requirements

- [ ] **VS Code** installed
- [ ] **Python 3.8+** (uv will handle if needed)
- [ ] **Memory**: 8GB RAM minimum (16GB for larger models)
- [ ] **Storage**: 10GB free for models

## Step 1: Install Continue Extension

### Get VS Code Ready for AI Benchmarking

- [ ] Open VS Code

- [ ] Install Continue extension:
  - Press `Cmd+Shift+X` (Mac) or `Ctrl+Shift+X` (Windows/Linux)
  - Search for "Continue"
  - Install the extension by Continue.dev

- [ ] Configure your first AI model in Continue:
  - Open Continue settings (`Cmd+Shift+P` → "Continue: Open Settings")
  - Choose your model type:
    - **Cloud models** (OpenAI, Claude): Add API key
    - **Local models** (Ollama): See Step 3
    - **Free tier**: Use Continue's free tier

## Step 2: Project Setup

### Get Vibe Check

- [ ] Install uv (fast Python package manager):
  ```bash
  # macOS/Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh
  
  # Windows
  powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

- [ ] Clone and setup:
  ```bash
  git clone https://github.com/bdougie/vibe-check.git
  cd vibe-check
  uv pip sync requirements.txt
  ```

- [ ] Run interactive setup wizard:
  ```bash
  uv run setup_wizard.py
  ```
  Select "Manual with Continue" when prompted

## Step 3: AI Model Setup

### Option A: Use Cloud Models (Fastest)

If you have API keys for OpenAI, Anthropic, or other providers:

- [ ] Add to Continue config:
  ```json
  {
    "models": [{
      "title": "Claude 3.5",
      "provider": "anthropic",
      "model": "claude-3-5-sonnet-20241022",
      "apiKey": "YOUR_KEY"
    }]
  }
  ```

### Option B: Use Local Models with Ollama

For free, private, offline testing:

- [ ] Install Ollama:
  ```bash
  # macOS
  brew install ollama
  
  # Linux
  curl -fsSL https://ollama.com/install.sh | sh
  ```

- [ ] Start Ollama:
  ```bash
  ollama serve  # Keep this running
  ```

- [ ] Download a model:
  ```bash
  # Recommended for benchmarking
  ollama pull qwen2.5-coder:7b
  
  # Smaller option
  ollama pull deepseek-coder:1.3b
  ```

- [ ] Auto-configure Continue:
  ```bash
  uv run benchmark/continue_config_generator.py
  ```

## Step 4: Run Your First Manual Benchmark

### Manual Benchmarking Session

- [ ] Start session tracking:
  ```bash
  uv run benchmark/continue_session_tracker.py --start
  ```

- [ ] Open a task in VS Code:
  ```bash
  code benchmark/tasks/easy/fix_typo.md
  ```

- [ ] Solve with Continue:
  - Read the task requirements
  - Press `Cmd+L` (Mac) or `Ctrl+L` (Windows/Linux)
  - Ask Continue to help solve the task
  - Apply suggested changes

- [ ] Stop session when done:
  ```bash
  uv run benchmark/continue_session_tracker.py --stop
  ```

### Quick Smoke Test (Optional)

For automated validation:
```bash
uv run run_smoke_test.py
```

## Step 5: View Your Results

### Analyze Your Session

- [ ] View latest session results:
  ```bash
  uv run benchmark/analyze.py --session latest
  ```

- [ ] See all sessions:
  ```bash
  uv run benchmark/analyze.py
  ```

- [ ] Metrics captured:
  - Task completion status
  - Total duration and interaction count
  - Prompt/response patterns
  - Code changes (via git)
  - Model performance

## 🎉 Success Checklist

You've completed your first manual benchmark when:

- [ ] Continue extension is configured and working
- [ ] Session tracking captured your interactions
- [ ] Task was completed with AI assistance
- [ ] Results show in `uv run benchmark/analyze.py`
- [ ] Metrics include prompts, duration, and code changes

## 📊 Next Steps

### Continue Manual Benchmarking

1. **Try harder tasks:**
   - Easy: `benchmark/tasks/easy/`
   - Medium: `benchmark/tasks/medium/`
   - Hard: `benchmark/tasks/hard/`

2. **Compare models:**
   - Switch models in Continue settings
   - Run same task with different models
   - Compare metrics with `uv run benchmark/analyze.py`

3. **Advanced features:**
   - Create custom tasks
   - Export results to CSV
   - Set up automated workflows

### Try Automated Benchmarking

For batch testing without UI:
```bash
uv run benchmark/task_runner.py "model-name" "task.md"
```

See [CLI Benchmarking Guide](docs/cli-benchmarking.md) for details.

## 🐛 Troubleshooting

### Common Issues and Solutions

<details>
<summary>❌ Ollama: "command not found"</summary>

Make sure Ollama is in your PATH:
```bash
which ollama
```
If not found, add to your shell config:
```bash
echo 'export PATH=$PATH:/usr/local/bin' >> ~/.zshrc
source ~/.zshrc
```
</details>

<details>
<summary>❌ "Connection refused" when running benchmark</summary>

Ollama service isn't running. Start it:
```bash
ollama serve
```
Keep this running in a separate terminal!
</details>

<details>
<summary>❌ "Model not found" error</summary>

The model isn't downloaded. Pull it first:
```bash
ollama pull qwen2.5-coder:7b
```
</details>

<details>
<summary>❌ Continue extension not working</summary>

1. Check configuration exists:
   ```bash
   ls ~/.continue/config.yaml
   ```

2. Regenerate if needed:
   ```bash
   uv run benchmark/continue_config_generator.py
   ```

3. Restart VS Code completely
</details>

<details>
<summary>❌ Import errors when running scripts</summary>

Make sure dependencies are installed:
```bash
# Reinstall dependencies with uv
uv pip sync requirements.txt

# Run scripts with uv run to ensure correct environment
uv run benchmark/task_runner.py
```
</details>

## 📚 Additional Resources

### Manual Benchmarking
- **[Manual Benchmarking Guide](docs/manual-benchmarking-guide.md)** - Complete guide
- **[Continue Setup](docs/continue-setup.md)** - Advanced configuration
- **[Session Analysis](docs/session-analysis.md)** - Understanding metrics

### Advanced Topics
- **[CLI Benchmarking](docs/cli-benchmarking.md)** - Automated testing
- **[Task Creation](docs/task-creation.md)** - Custom benchmarks
- **[All Documentation](docs/README.md)** - Complete index

## 💡 Pro Tips

1. **Start with easy tasks** - Build confidence before tackling harder benchmarks
2. **Use smoke tests** - Quick 30-second tests to validate setup
3. **Monitor resource usage** - Check RAM with `ollama ps` while models run
4. **Save your results** - Results are timestamped and never overwritten
5. **Try multiple models** - Different models excel at different tasks

## 🤝 Getting Help

- **GitHub Issues**: [Report problems](https://github.com/bdougie/vibe-check/issues)
- **Documentation**: Check [docs/](docs/) folder for detailed guides
- **Quick Check**: Run `uv run benchmark/ollama_check.py` to diagnose Ollama issues

---

**Ready to benchmark more models?** Check out the [full task list](benchmark/tasks/) and [model recommendations](docs/models.md)!

**Having issues?** Most problems are covered in the troubleshooting section above or in the [detailed Ollama guide](docs/ollama.md).

---
*Estimated time to complete all steps: 15-20 minutes (depending on download speeds)*