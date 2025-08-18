# Vibe Check - AI Coding Agent Benchmark Framework

A benchmarking framework for evaluating human-in-the-loop AI coding agents. Test and compare how different AI models perform on real coding tasks with human collaboration.

## 🚀 New to Vibe Check?

### Interactive Setup (Recommended)
```bash
uv run setup_wizard.py
```
The interactive wizard will guide you through:
- Checking Python version and dependencies
- Installing Ollama for local models
- Downloading recommended models
- Configuring the Continue extension
- Running your first benchmark

### Manual Setup
**Start here → [QUICKSTART.md](QUICKSTART.md)** - Get from zero to running your first benchmark in 15 minutes!

## 📚 Documentation

For comprehensive documentation, see the [docs/](docs/) directory:
- [**Quick Start Checklist**](QUICKSTART.md) - Step-by-step setup with checkboxes ✅
- [**Setup Guide**](docs/setup.md) - Detailed setup instructions
- [**Manual Guide**](docs/manual-guide.md) - In-depth tutorial
- [**Git Tracking**](docs/git-tracking.md) - Automatic code change tracking
- [**Storage System**](docs/storage.md) - Data persistence and format
- [**All Documentation**](docs/README.md) - Complete documentation index

## Quick Start

### Prerequisites

- Python 3.8+ (uv will handle Python installation if needed)
- [uv](https://github.com/astral-sh/uv) - Fast Python package and environment manager
- Git (for tracking code changes)
- [Continue VS Code extension](https://marketplace.visualstudio.com/items?itemName=Continue.continue) (optional)
- [Ollama](https://ollama.com/) for local models (optional)

### Installation

```bash
# Install uv (fast Python package manager)
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or with Homebrew
brew install uv

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Clone the repository
git clone https://github.com/bdougie/vibe-check.git
cd vibe-check

# Install dependencies with uv (10-100x faster than pip)
uv pip sync requirements.txt
```

## Usage

### 🎯 NEW: Vibe CLI Wrapper

The easiest way to run benchmarks is with the new `vibe` CLI wrapper:

```bash
# List available challenges and models
uv run ./vibe --list-challenges
uv run ./vibe --list-models

# Run a specific task
uv run ./vibe --model qwen2.5-coder:7b --task basic_todo_app

# Run a random challenge by difficulty
uv run ./vibe --model gpt-oss:20b --challenge easy --random

# Interactive mode (opens Continue CLI)
uv run ./vibe --model codestral:22b --challenge medium --interactive

# Quick examples
uv run ./vibe -m gpt-oss:20b -c easy        # Choose from easy challenges
uv run ./vibe -m qwen2.5-coder:14b -t fix_typo  # Run specific task
```

See [docs/vibe-cli.md](docs/vibe-cli.md) for full CLI documentation.

### 🔥 Quick Smoke Test (30 seconds)

Before running full benchmarks, verify your setup with a quick smoke test:

```bash
# Using the vibe CLI
uv run ./vibe --model gpt-oss:20b --challenge smoke

# Or run the automated smoke test
uv run run_smoke_test.py
```

The smoke test:
- Takes less than 30 seconds
- Verifies all components work together
- Uses a simple "add a comment" task
- Requires no model setup

### 1. Run a Benchmark Task

```bash
# Using uv (recommended - handles dependencies automatically)
uv run benchmark/task_runner.py "ModelName" "benchmark/tasks/easy/fix_typo.md"

# Or using module syntax
uv run -m benchmark.task_runner "ModelName" "benchmark/tasks/easy/fix_typo.md"
```

Example with specific models:
```bash
# Commercial models (using uv)
uv run benchmark/task_runner.py "Claude-3.5-Sonnet" "benchmark/tasks/easy/fix_typo.md"
uv run benchmark/task_runner.py "GPT-4o" "benchmark/tasks/medium/add_validation.md"

# Local models via Ollama (automatic setup verification)
uv run benchmark/task_runner.py "ollama/llama2" "benchmark/tasks/easy/add_gitignore_entry.md"
uv run benchmark/task_runner.py "ollama/codellama" "benchmark/tasks/medium/add_validation.md"

# Skip Ollama checks if you're sure everything is set up
uv run benchmark/task_runner.py "ollama/mistral" "benchmark/tasks/easy/fix_typo.md" --skip-ollama-check
```

### 2. View Available Tasks

```bash
# Using uv (recommended)
uv run benchmark/task_runner.py

# Or using module syntax
uv run -m benchmark.task_runner
```

This will list all available benchmark tasks organized by difficulty:
- **Easy**: Simple fixes and additions (2-5 minutes)
- **Medium**: Feature additions and validations (15-30 minutes)  
- **Hard**: Refactoring and system design (1-3 hours)

### 3. Verify Models (Essential Step)

Check which AI models you have and what you need for benchmarking:

```bash
# Run comprehensive model verification
uv run -m benchmark.model_verifier

# Get download commands for missing models  
uv run -m benchmark.model_verifier --download

# Get model suggestions based on your system specs
uv run -m benchmark.model_verifier --suggest

# JSON output for automation
uv run -m benchmark.model_verifier --json
```

The model verifier will:
- ✅ Check your system resources (RAM, disk space)
- ✅ List installed vs missing models
- ✅ Recommend models based on your system
- ✅ Provide download commands
- ✅ Calculate disk space requirements

For Ollama-specific checks:

```bash
# Check Ollama installation and service
uv run -m benchmark.ollama_check

# Check specific model availability
uv run -m benchmark.ollama_check --model llama2

# Auto-pull missing models
uv run -m benchmark.ollama_check --model codellama --pull
```

### 4. Featured Challenges

#### 🆕 Todo App Challenges
Test model planning and implementation capabilities:

```bash
# Basic Todo App (Medium difficulty)
# Tests: Basic CRUD operations, class design, error handling
uv run ./vibe --model qwen2.5-coder:14b --task basic_todo_app

# Advanced Todo App (Hard difficulty)  
# Tests: Persistence, categories, CLI, testing, architecture
uv run ./vibe --model gpt-oss:20b --task advanced_todo_app
```

These challenges measure:
- Planning and architecture skills
- Code organization and design patterns
- Error handling and edge cases
- Test coverage and documentation
- Performance with complex requirements

### 5. Analyze Results

View aggregated benchmark results:
```bash
# Using vibe CLI (shows latest results)
uv run ./vibe --list-results

# Using analyze script for detailed analysis
uv run benchmark/analyze.py

# Export results to CSV for further analysis
uv run benchmark/analyze.py --export

# With pandas visualization support
uv run benchmark/analyze.py --visualize

# Get help on available options
uv run benchmark/analyze.py --help
```

### 5. Continue Integration (Optional)

If using Continue VS Code extension, start benchmarks with:
```bash
uv run benchmark_task.py --start
```

## Benchmark Workflow

1. **Start a task** - Run the task_runner with your chosen model and task
2. **Solve with AI** - Use your AI tool to complete the task
3. **Track metrics** - Note prompts sent and manual interventions
4. **Complete benchmark** - Record success and metrics
5. **Analyze results** - Compare performance across models and tasks

## Metrics Tracked

- **Task completion rate** - Success/failure ratio
- **Time to completion** - How long tasks take
- **Prompts sent** - Number of AI interactions
- **Human interventions** - Manual corrections needed
- **Code changes** - Files modified, lines added/removed
- **Model comparison** - Performance across different AI models

## Available Tasks

### Easy Tasks
- `fix_typo.md` - Fix documentation typos
- `add_gitignore_entry.md` - Update .gitignore file

### Medium Tasks  
- `add_validation.md` - Add input validation to functions
- `add_export_feature.md` - Implement JSON export functionality

### Hard Tasks
- `refactor_metrics.md` - Refactor the metrics system
- `implement_dashboard.md` - Build a web dashboard

## Next Steps

### For Users

1. **Run benchmarks** on your preferred AI models
2. **Create custom tasks** based on your real-world needs
3. **Share results** to contribute to community knowledge
4. **Compare models** to find the best fit for your workflow

### For Contributors

1. **Add new tasks** - Create realistic coding challenges in `benchmark/tasks/`
2. **Enhance metrics** - Add more sophisticated tracking (PR welcome!)
3. **Improve analysis** - Add visualizations and statistical tests
4. **Integration** - Add support for more AI tools and IDEs

### Planned Features

- [ ] Automatic prompt/response capture
- [ ] Web dashboard for results visualization  
- [ ] GitHub integration for real issue testing
- [ ] Multi-model parallel testing
- [ ] Difficulty auto-classification
- [ ] Performance regression detection
- [ ] Team leaderboards
- [ ] Task recommendation engine

## Creating Custom Tasks

Create a new task file in `benchmark/tasks/{difficulty}/` with this format:

```markdown
# Task: [Task Name]

**Difficulty**: [Easy/Medium/Hard]
**Issue**: [Problem description]

## Requirements
- [Requirement 1]
- [Requirement 2]

## Expected Outcome
- [Expected result]

**Time Estimate**: [X-Y minutes]

## Success Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]
```

## Advanced Setup

For full Continue integration and local model setup, see [setup.md](docs/setup.md).

## Data Privacy

All benchmark results are stored locally in `benchmark/results/`. No data is sent to external services unless you explicitly share it.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

MIT

## Acknowledgments

Built to evaluate and improve human-AI collaboration in software development. Special thanks to the Continue and Ollama projects for enabling local AI development.