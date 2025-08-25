# Manual Benchmarking Guide with Continue

A complete guide to benchmarking AI coding assistants using VS Code and the Continue extension. This approach provides realistic testing scenarios and rich metrics through human-in-the-loop evaluation.

## Table of Contents
- [Overview](#overview)
- [Setup](#setup)
- [Running Your First Benchmark](#running-your-first-benchmark)
- [Understanding Sessions](#understanding-sessions)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

Manual benchmarking captures how AI assistants perform in real development workflows. Unlike automated testing, you interact with the AI naturally through Continue while Vibe Check tracks metrics in the background.

### Why Manual Benchmarking?

- **Realistic Scenarios** - Test AI performance in your actual development environment
- **Comprehensive Metrics** - Capture conversation flow, thinking time, and iteration patterns
- **Immediate Feedback** - See how different models handle your coding style
- **No Learning Curve** - Use your existing VS Code workflow

## Setup

### Prerequisites

1. **VS Code** with [Continue extension](https://marketplace.visualstudio.com/items?itemName=Continue.continue) installed
2. **Python 3.8+** and **uv** package manager
3. **Git** for tracking code changes
4. **AI Model Access** (Ollama, OpenAI, Claude, etc.)

### Step 1: Configure Continue

1. Open Continue settings (Cmd+Shift+P → "Continue: Open Settings")
2. Add your preferred model configuration:

```json
{
  "models": [
    {
      "title": "Claude 3.5 Sonnet",
      "provider": "anthropic",
      "model": "claude-3-5-sonnet-20241022",
      "apiKey": "YOUR_API_KEY"
    },
    {
      "title": "Local Qwen",
      "provider": "ollama",
      "model": "qwen2.5-coder:7b"
    }
  ]
}
```

### Step 2: Verify Setup

```bash
# Run the setup wizard
uv run setup_wizard.py

# Select "Manual with Continue" workflow
# Follow the prompts to verify your configuration
```

## Running Your First Benchmark

### 1. Choose a Task

Browse available tasks:
```bash
ls benchmark/tasks/easy/
ls benchmark/tasks/medium/
ls benchmark/tasks/hard/
```

Start with an easy task like `fix_typo.md`:
```bash
code benchmark/tasks/easy/fix_typo.md
```

### 2. Start Session Tracking

```bash
# Start tracking your session
uv run benchmark/continue_session_tracker.py --start

# You'll see:
# ✅ Session tracking started
# Session ID: session_20241125_143022
# Recording metrics for Continue interactions...
```

### 3. Solve the Task with Continue

1. Read the task requirements in VS Code
2. Open the target files mentioned in the task
3. Use Continue (Cmd+L / Ctrl+L) to solve the task
4. Iterate with the AI until the task is complete

Example interaction:
```
You: "Help me fix the typos in calculator.py as described in the task"
AI: "I'll help you fix the typos. Let me analyze the file..."
[AI provides solution]
You: "Apply the changes"
[Changes are made]
```

### 4. Stop Session Tracking

```bash
# Stop tracking when done
uv run benchmark/continue_session_tracker.py --stop

# You'll see:
# ✅ Session completed
# Duration: 4m 32s
# Interactions: 3
# Files changed: 1
# Success: Yes
```

### 5. Review Results

```bash
# View your session results
uv run benchmark/analyze.py --session latest

# Or view all sessions
uv run benchmark/analyze.py
```

## Understanding Sessions

### Session Metrics

Each session captures:

- **Timing Metrics**
  - Total duration
  - Time to first interaction
  - Average response time
  - Thinking time between prompts

- **Interaction Metrics**
  - Number of prompts sent
  - Number of AI responses
  - Conversation complexity
  - Error corrections needed

- **Code Metrics**
  - Files modified
  - Lines added/removed
  - Test results (if applicable)
  - Git diff statistics

### Session Files

Sessions are stored in `benchmark/results/sessions/`:
```
session_20241125_143022/
├── metadata.json       # Session info and config
├── interactions.jsonl  # All prompts and responses
├── metrics.json       # Calculated metrics
├── git_diff.txt      # Code changes
└── continue_log.json  # Raw Continue events
```

## Best Practices

### 1. Consistent Testing Environment

- Close unnecessary applications to reduce distractions
- Use the same VS Code workspace settings
- Maintain consistent Continue configurations
- Clear git changes between sessions

### 2. Task Approach

- Read the entire task before starting
- Don't pre-plan solutions - let the AI guide you
- Document any manual interventions
- Complete tasks in one session when possible

### 3. Fair Comparisons

When comparing models:
- Use the same task for each model
- Test at similar times (avoid fatigue bias)
- Run multiple sessions per model
- Note any model-specific issues

### 4. Session Hygiene

```bash
# Before starting a new session
git status  # Ensure clean working directory
git stash   # Save any uncommitted changes

# After completing a session
git diff    # Review changes made
git reset --hard  # Reset for next session
```

## Advanced Usage

### Batch Session Analysis

Compare multiple sessions:
```bash
# Compare models on the same task
uv run benchmark/analyze.py --compare "claude-3.5" "gpt-4" --task "fix_typo"

# Export session data for external analysis
uv run benchmark/analyze.py --export --format csv
```

### Custom Task Creation

Create tasks that match your workflow:
1. Copy an existing task as a template
2. Modify requirements for your use case
3. Include realistic acceptance criteria
4. Test with multiple models

### Integration with CI/CD

```yaml
# .github/workflows/benchmark.yml
name: Weekly Benchmark
on:
  schedule:
    - cron: '0 0 * * 0'
jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run benchmarks
        run: |
          uv run benchmark/continue_session_tracker.py --automated
          uv run benchmark/analyze.py --export
```

## Troubleshooting

### Session Not Recording

1. Verify Continue is running:
   ```bash
   ps aux | grep continue
   ```

2. Check session status:
   ```bash
   uv run benchmark/continue_session_tracker.py --status
   ```

3. Review logs:
   ```bash
   cat benchmark/results/sessions/latest/debug.log
   ```

### Metrics Not Captured

- Ensure git is initialized in the project
- Verify file changes are being tracked
- Check Continue console for errors
- Review session files for completeness

### Model Connection Issues

```bash
# Test model connectivity
uv run benchmark/model_verifier.py --test "your-model"

# For Ollama models
ollama list
ollama run your-model "test prompt"
```

## Tips for Better Benchmarks

1. **Be Natural** - Interact with the AI as you normally would
2. **Document Issues** - Note any problems in session notes
3. **Multiple Runs** - Run each task 3+ times for reliable data
4. **Vary Complexity** - Test easy through hard tasks
5. **Real Problems** - Create tasks from actual work scenarios

## Next Steps

- Review [Continue Setup Guide](continue-setup.md) for advanced configuration
- Explore [Session Analysis](session-analysis.md) for deeper insights
- Create custom tasks in `benchmark/tasks/`
- Share your results with the community

---

Questions? Check our [FAQ](faq.md) or open an [issue](https://github.com/bdougie/vibe-check/issues).