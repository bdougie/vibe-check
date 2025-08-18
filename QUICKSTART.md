# 🚀 Vibe Check Quick Start Guide

Welcome! This step-by-step checklist will get you from zero to running your first local model benchmark in about 15 minutes.

## Prerequisites Checklist

### 📦 System Requirements

- [ ] **Operating System**: macOS, Linux, or Windows with WSL2
- [ ] **Memory**: At least 8GB RAM (16GB recommended for larger models)
- [ ] **Storage**: 10GB free disk space for models

## Step 1: Install uv

### Install uv Package Manager

uv handles Python installation and package management automatically.

- [ ] Install uv:
  ```bash
  # macOS/Linux
  curl -LsSf https://astral.sh/uv/install.sh | sh
  
  # Or with Homebrew (macOS)
  brew install uv
  
  # Windows
  powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
  ```

- [ ] Verify uv is installed:
  ```bash
  uv --version
  ```

## Step 2: Project Setup

### Clone and Install

- [ ] Clone the repository:
  ```bash
  git clone https://github.com/bdougie/vibe-check.git
  cd vibe-check
  ```

- [ ] Set up environment and install dependencies:
  ```bash
  # Create virtual environment and install dependencies
  uv venv
  uv pip sync requirements.txt
  ```

- [ ] Verify installation:
  ```bash
  uv run python -c "import pandas, yaml, pytest; print('✅ Dependencies installed')"
  ```

## Step 3: Quick Test with Vibe CLI 🆕

### Test Setup with the Vibe CLI Wrapper

- [ ] Run a quick smoke test:
  ```bash
  # List available challenges
  uv run ./vibe --list-challenges
  
  # Run smoke test (no model needed)
  uv run ./vibe --model test_model --challenge smoke
  ```

## Step 4: Ollama Setup (for Local Models)

### Install and Configure Ollama

- [ ] Install Ollama:
  - **macOS**: 
    ```bash
    brew install ollama
    ```
  - **Linux**: 
    ```bash
    curl -fsSL https://ollama.com/install.sh | sh
    ```
  - **Windows**: Download from [ollama.com](https://ollama.com/download)

- [ ] Start Ollama service:
  ```bash
  ollama serve
  ```
  Keep this terminal window open!

- [ ] Verify Ollama is running (in a new terminal):
  ```bash
  ollama list
  ```

## Step 5: Download a Model

### Get Your First Model

- [ ] Download recommended model (qwen2.5-coder:7b - good balance of speed and quality):
  ```bash
  ollama pull qwen2.5-coder:7b
  ```
  This will take 5-10 minutes depending on your internet speed.

- [ ] Alternative models:
  ```bash
  # Larger, more capable (20GB)
  ollama pull gpt-oss:20b
  
  # Code-focused model (22GB)
  ollama pull codestral:22b
  
  # Smaller, faster option (3.8GB)
  ollama pull deepseek-coder:1.3b
  ```

- [ ] Verify model is downloaded:
  ```bash
  # Using vibe CLI
  uv run ./vibe --list-models
  
  # Or directly with ollama
  ollama list
  ```
  You should see your model listed!

## Step 5: VS Code and Continue Setup

### Install Continue Extension

- [ ] Open VS Code

- [ ] Install Continue extension:
  - Press `Cmd+Shift+X` (Mac) or `Ctrl+Shift+X` (Windows/Linux)
  - Search for "Continue"
  - Install the extension by Continue.dev

- [ ] Generate Continue configuration:
  ```bash
  uv run benchmark/continue_config_generator.py
  ```
  - Answer `n` for OpenAI and Anthropic keys (unless you have them)
  - The script will auto-detect your Ollama models

- [ ] Restart VS Code to load the configuration

- [ ] Test Continue:
  - Open any code file
  - Press `Cmd+L` (Mac) or `Ctrl+L` (Windows/Linux)
  - Type "Hello" and see if the model responds

## Step 6: Run Your First Benchmark

### Using the Vibe CLI (Recommended) 🆕

- [ ] Run your first benchmark with the Vibe CLI:
  ```bash
  # Run an easy challenge
  uv run ./vibe --model qwen2.5-coder:7b --challenge easy
  
  # Or run a specific task
  uv run ./vibe --model qwen2.5-coder:7b --task fix_typo
  
  # Try the new Todo App challenge
  uv run ./vibe --model gpt-oss:20b --task basic_todo_app
  ```

- [ ] Alternative: Run the automated smoke test:
  ```bash
  uv run run_smoke_test.py
  ```
  
  This will:
  - Create a sample project
  - Run a simple task (fix a typo)
  - Complete in about 30 seconds
  - Save results automatically

## Step 7: View Your Results

### Analyze Benchmark Results

- [ ] View results summary:
  ```bash
  uv run benchmark/analyze.py
  ```

- [ ] Check the results file:
  ```bash
  ls -la benchmark/results/
  ```
  Your results are saved as JSON files with timestamps

- [ ] Review metrics:
  - Task completion status
  - Time taken
  - Number of prompts
  - Files modified (automatically tracked)
  - Lines added/removed

## 🎉 Success Checklist

You've successfully completed your first benchmark when:

- [ ] Ollama is running with at least one model
- [ ] Continue extension is working in VS Code
- [ ] Smoke test completed successfully
- [ ] Results file was generated in `benchmark/results/`
- [ ] You can see metrics with `uv run benchmark/analyze.py`

## 📊 Next Steps

### Run More Benchmarks

1. **Try different difficulty levels:**
   ```bash
   # Easy task
   uv run benchmark/task_runner.py "ollama/qwen2.5-coder:7b" "benchmark/tasks/easy/add_gitignore_entry.md"
   
   # Medium task
   uv run benchmark/task_runner.py "ollama/qwen2.5-coder:7b" "benchmark/tasks/medium/add_validation.md"
   ```

2. **Compare different models:**
   ```bash
   # Download another model
   ollama pull codestral:latest
   
   # Run same task with different model
   uv run benchmark/task_runner.py "ollama/codestral" "benchmark/tasks/easy/fix_typo.md"
   ```

3. **Analyze and compare results:**
   ```bash
   # View all results
   uv run benchmark/analyze.py
   
   # Export to CSV for analysis
   uv run benchmark/analyze.py --export
   ```

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

- **[Full Documentation](docs/README.md)** - Comprehensive guides
- **[Model Setup Guide](docs/models.md)** - Configure different AI models  
- **[Task Creation](docs/manual-guide.md)** - Create custom benchmark tasks
- **[Troubleshooting Guide](docs/ollama.md)** - Detailed Ollama troubleshooting
- **[Continue Docs](https://docs.continue.dev)** - Continue extension documentation

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