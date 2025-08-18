# Vibe Check Documentation

Welcome to the Vibe Check documentation! This directory contains comprehensive guides, references, and technical documentation for the AI coding agent benchmark framework.

## 📚 Table of Contents

### Getting Started
- [**Quick Start Checklist**](../QUICKSTART.md) - 15-minute setup with checkboxes ✅ **(Start Here!)**
- [**Vibe CLI Guide**](vibe-cli.md) - 🆕 Easy-to-use CLI wrapper for benchmarking
- [**Setup Guide**](setup.md) - Initial setup and configuration instructions
- [**Manual Guide**](manual-guide.md) - In-depth guide to run benchmarks

### Core Features
- [**Continue Session Tracking**](continue-session-tracking.md) - Automatic metrics extraction from Continue IDE ✨
- [**Automatic Git Tracking**](git-tracking.md) - How automatic code change tracking works
- [**Storage System**](storage.md) - Understanding the JSON storage format and structure

### Configuration
- [**Continue Config Generator**](continue-config.md) - Automatically generate Continue VS Code extension config
- [**Models Configuration**](models.md) - Supported AI models and setup instructions
- [**Ollama Setup**](ollama.md) - Local model setup with Ollama
- [**Pre-commit Hooks**](pre-commit-setup.md) - Code quality automation setup

## 📖 Documentation Overview

### For New Users

1. **Begin with the [Quick Start Checklist](../QUICKSTART.md)** - Interactive setup guide
2. **Try the [Vibe CLI](vibe-cli.md)** - Easiest way to run benchmarks
3. Review the [Setup Guide](setup.md) for detailed configuration options
4. Follow the [Manual Guide](manual-guide.md) for in-depth benchmarking
5. Use the [Continue Config Generator](continue-config.md) to set up VS Code integration
6. Review [Models Configuration](models.md) to set up your preferred AI models

### For Developers

1. Understand the [Git Tracking](git-tracking.md) system for automatic metrics
2. Learn about the [Storage System](storage.md) for data persistence
3. Set up [Pre-commit Hooks](pre-commit-setup.md) for code quality

### Key Features

#### 🤖 Continue Session Tracking
Automatically extracts from Continue IDE:
- Prompts and responses
- Token usage metrics
- Tool calls and arguments
- Human interventions

See [continue-session-tracking.md](continue-session-tracking.md) for details.

#### 🔄 Automatic Git Tracking
The framework automatically captures:
- Initial git state when benchmarks start
- File modifications during tasks
- Lines added/removed per file
- No manual input required

See [git-tracking.md](git-tracking.md) for details.

#### 💾 JSON Storage
Results are stored in timestamped JSON files:
- Human-readable format
- Complete session history
- Detailed metrics and git changes

See [storage.md](storage.md) for the complete schema.

#### 🤖 Multi-Model Support
Benchmark various AI models:
- Commercial APIs (Claude, GPT-4, etc.)
- Local models via Ollama
- Custom model integrations

See [models.md](models.md) for configuration.

## 🗂️ Documentation Structure

```
.
├── QUICKSTART.md                  # 15-minute interactive setup checklist ✅
└── docs/
    ├── README.md                   # This file - Table of contents
    ├── setup.md                   # Environment setup guide
    ├── manual-guide.md            # In-depth benchmark guide
    ├── continue-session-tracking.md # Automatic Continue metrics extraction
    ├── git-tracking.md            # Automatic git tracking documentation
    ├── storage.md                 # Storage system documentation
    ├── continue-config.md         # Continue VS Code extension configuration
    ├── models.md                  # AI models configuration
    ├── ollama.md                  # Ollama local models setup
    └── pre-commit-setup.md        # Pre-commit hooks configuration
```

## 🔍 Quick Reference

### Running a Benchmark
```bash
uv run benchmark/task_runner.py "ModelName" "benchmark/tasks/easy/fix_typo.md"
```

### Smoke Test (30 seconds)
```bash
uv run run_smoke_test.py
```

### Analyzing Results
```bash
uv run benchmark/analyze.py
```

### Test Suite
```bash
uv run pytest tests/
```

## 📝 Task Categories

The framework includes benchmark tasks in three difficulty levels:

- **Easy**: Simple fixes like typos and formatting
- **Medium**: Adding validation and features
- **Hard**: Complex refactoring and optimization
- **Smoke**: Quick 30-second validation tests

Tasks are located in `benchmark/tasks/`.

## 🤝 Contributing

When adding new documentation:
1. Use lowercase filenames (except this README.md)
2. Add entries to this table of contents
3. Follow the existing documentation style
4. Include code examples where appropriate

## 📊 Metrics Tracked

The framework automatically tracks:
- Prompts sent/received
- Character counts
- Human interventions
- Task completion status
- Execution time
- Files modified (automatic)
- Lines added/removed (automatic)
- Git state changes (automatic)

## 🔗 Additional Resources

- [GitHub Repository](https://github.com/bdougie/vibe-check)
- [Issue Tracker](https://github.com/bdougie/vibe-check/issues)
- [Sample Project](../sample_project/) - Test environment for benchmarks

## 📄 License

See the [LICENSE](../LICENSE) file in the repository root for details.

---

*Last updated: Documentation reorganized with automatic git tracking feature*