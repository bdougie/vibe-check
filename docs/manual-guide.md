# Vibe Check - Complete Benchmarking Guide

This guide walks you through benchmarking AI coding agents from start to finish.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Understanding the Framework](#understanding-the-framework)
3. [Running Your First Benchmark](#running-your-first-benchmark)
4. [Using the Sample Project](#using-the-sample-project)
5. [Interpreting Results](#interpreting-results)
6. [Advanced Usage](#advanced-usage)
7. [Best Practices](#best-practices)

## Quick Start

### Prerequisites

1. **Install uv (fast Python package manager)**:
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

2. **Install dependencies**:
```bash
uv pip install -r requirements.txt
```

3. **For local models, install Ollama**:
```bash
# Download from https://ollama.com/
# Then pull models:
ollama pull qwen2.5-coder:7b
ollama pull llama3.1:8b
```

### Your First Benchmark in 3 Steps

```bash
# 1. Check available tasks
uv run -m benchmark.task_runner

# 2. Run a simple benchmark
uv run -m benchmark.task_runner "YourModelName" "benchmark/tasks/easy/fix_calculator_typos.md"

# 3. View results
uv run -m benchmark.analyze
```

## Understanding the Framework

### What is Vibe Check?

Vibe Check measures how well AI coding agents collaborate with humans on real coding tasks. It tracks:
- Task completion success rate
- Time to completion
- Number of prompts needed
- Manual interventions required
- Code quality metrics

### Framework Structure

```
vibe-check/
├── benchmark/
│   ├── tasks/          # Benchmark task definitions
│   │   ├── easy/       # 2-5 minute tasks
│   │   ├── medium/     # 15-30 minute tasks
│   │   └── hard/       # 1-3 hour tasks
│   ├── results/        # JSON results from each run
│   ├── task_runner.py  # Main benchmark executor
│   └── analyze.py      # Results analysis tool
├── sample_project/     # Test project with planted issues
│   ├── src/           # Python modules with bugs
│   ├── ISSUES.md      # Documentation of all issues
│   └── README.md      # Project documentation
└── reset_sample_project.py  # Reset tool for repeated testing
```

## Running Your First Benchmark

### Step 1: Choose a Task

List all available tasks:
```bash
uv run -m benchmark.task_runner
```

Tasks are categorized by difficulty:
- **Easy**: Simple fixes (typos, formatting)
- **Medium**: Add validation, error handling
- **Hard**: Refactoring, optimization

### Step 2: Select Your AI Model

The framework supports any AI coding tool:
- **Claude (Anthropic)**
- **GPT-4 (OpenAI)**
- **Local models via Ollama**
- **Continue extension**
- **Cursor**
- **Any other AI coding assistant**

### Step 3: Run the Benchmark

Start a benchmark session:
```bash
# Example with Claude
uv run -m benchmark.task_runner "Claude-3.5-Sonnet" "benchmark/tasks/easy/fix_calculator_typos.md"
```

The runner will:
1. Display the task requirements
2. Start tracking time
3. Wait for you to complete the task
4. Prompt for metrics when done

### Step 4: Complete the Task

1. **Read the task** displayed by the runner
2. **Use your AI tool** to solve the problem
3. **Track your interactions**:
   - Count prompts sent
   - Note manual edits
   - Record when you override AI suggestions

### Step 5: Record Results

When finished, the runner will ask:
- Was the task completed successfully?
- How many prompts did you send?
- How many manual interventions?
- How many files were modified?

Results are automatically saved to `benchmark/results/`.

## Using the Sample Project

The `sample_project/` directory contains a Python project with intentional issues for consistent benchmarking.

### Available Issues

#### Easy Tasks (2-5 minutes)
- **Fix typos** in calculator.py
  - "paramter" → "parameter"
  - "reuslt" → "result"
  - "Divsion" → "Division"

#### Medium Tasks (15-30 minutes)
- **Add validation** to calculator.py
  - Division by zero checking
  - Power function validation
- **Add error handling** to data_processor.py
  - File operation try/except
  - Input validation
  - Bounds checking

#### Hard Tasks (1-3 hours)
- **Refactor god class** in user_manager.py
  - Split into focused classes
  - Remove code duplication
  - Implement SOLID principles
- **Optimize algorithms** in analytics.py
  - Improve O(n²) to O(n) complexity
  - Implement efficient algorithms
  - Fix exponential recursion

### Resetting the Sample Project

After each benchmark, reset to original state:
```bash
# Reset to original (buggy) state
uv run reset_sample_project.py

# Create a backup
uv run reset_sample_project.py --backup
```

### Example Workflow

```bash
# 1. Start with the typo fix task
uv run -m benchmark.task_runner "YourModel" "benchmark/tasks/easy/fix_calculator_typos.md"

# 2. Open sample_project/src/calculator.py in your AI tool

# 3. Ask AI to fix the typos mentioned in the task

# 4. Verify the fixes

# 5. Complete the benchmark and record metrics

# 6. Reset for next test
uv run reset_sample_project.py
```

## Interpreting Results

### View Results

Analyze all benchmark results:
```bash
# Basic analysis
uv run -m benchmark.analyze

# Export to CSV
uv run -m benchmark.analyze --export

# With visualization (requires pandas)
uv run -m benchmark.analyze --visualize
```

### Key Metrics

1. **Completion Rate**: Percentage of tasks successfully completed
2. **Average Prompts**: Number of interactions needed
3. **Time to Complete**: How long tasks take
4. **Human Interventions**: Manual corrections required
5. **Model Comparison**: Performance across different AI models

### Sample Analysis Output

```
=== Benchmark Results Summary ===
Total runs: 24
Models tested: 4
Overall completion rate: 87.5%

By Model Performance:
Model               Tasks  Success Rate  Avg Prompts  Avg Time (min)
Claude-3.5-Sonnet    6      100.0%         3.2          8.5
GPT-4o               6       83.3%         4.5         10.2
Qwen2.5-Coder-7B     6       83.3%         5.8         12.3
Llama3.1-8B          6       66.7%         7.2         15.7

By Task Difficulty:
Difficulty  Success Rate  Avg Prompts  Avg Time (min)
Easy           95.0%         2.1          3.5
Medium         85.0%         4.8         18.2
Hard           70.0%         8.3         67.4
```

## Advanced Usage

### Custom Tasks

Create your own benchmark tasks:

1. **Create a task file** in `benchmark/tasks/{difficulty}/`:
```markdown
# Task: [Clear Title]

**Difficulty**: [Easy/Medium/Hard]
**Issue**: [Problem description]

## Requirements
- [Specific requirement 1]
- [Specific requirement 2]

## File Location
`path/to/file.py`

## Expected Outcome
- [What should be achieved]

**Time Estimate**: [X-Y minutes]

## Success Criteria
- [ ] [Measurable criterion 1]
- [ ] [Measurable criterion 2]
```

2. **Add corresponding issues** to your test project

3. **Document the issues** for consistency

### Batch Testing

Run multiple benchmarks sequentially:
```bash
# Create a batch script
for task in benchmark/tasks/easy/*.md; do
    uv run -m benchmark.task_runner "YourModel" "$task"
    uv run reset_sample_project.py
done
```

### Model Verification

Before benchmarking, verify model availability:
```bash
# Check all models
uv run -m benchmark.model_verifier

# Get missing model download commands
uv run -m benchmark.model_verifier --download

# Check Ollama specifically
uv run -m benchmark.ollama_check
```

## Best Practices

### For Consistent Results

1. **Always reset** the sample project between tests
2. **Use the same starting state** for all models
3. **Run tasks in the same order** across models
4. **Document your process** for reproducibility

### For Fair Comparison

1. **Test multiple times** - Run each task 3+ times per model
2. **Vary task order** - Avoid learning effects
3. **Use fresh sessions** - Clear context between tasks
4. **Track all metrics** - Don't skip the intervention count

### For Meaningful Insights

1. **Focus on patterns** - Look for consistent strengths/weaknesses
2. **Consider task types** - Some models excel at certain tasks
3. **Note quality differences** - Not just completion, but code quality
4. **Document edge cases** - When models fail or excel unexpectedly

## Troubleshooting

### Common Issues

**Problem**: "Module not found" errors
```bash
# Solution: Ensure you're using uv to run commands
uv run -m benchmark.task_runner
```

**Problem**: Sample project changes persist
```bash
# Solution: Reset the project
uv run reset_sample_project.py
```

**Problem**: Ollama models not working
```bash
# Solution: Check Ollama is running
ollama list  # Should show available models
uv run -m benchmark.ollama_check
```

**Problem**: Results not saving
```bash
# Solution: Check results directory exists
mkdir -p benchmark/results
```

## Next Steps

1. **Run a complete benchmark suite** - Test all easy tasks with one model
2. **Compare models** - Run same tasks with different AI assistants
3. **Create custom tasks** - Add tasks specific to your workflow
4. **Share results** - Contribute findings to improve AI coding tools
5. **Automate testing** - Set up CI/CD for continuous benchmarking

## Contributing

Found an issue or want to add features? Contributions welcome!

1. Create new benchmark tasks
2. Improve metrics collection
3. Add visualization tools
4. Share benchmark results
5. Report bugs or suggestions

## Summary

Vibe Check provides a structured way to evaluate AI coding assistants on real tasks. Start with easy tasks to understand the workflow, then progress to more complex challenges. The sample project ensures consistent, repeatable testing across different models and sessions.

Remember: The goal is not just to complete tasks, but to understand how different AI models collaborate with humans and where they excel or struggle.