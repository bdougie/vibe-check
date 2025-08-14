# vibe-check
Vibe check or coding agents

# Simple Continue POC Setup for Human-in-the-Loop Agentic Programming Benchmark

This is a minimal setup to test human-in-the-loop agentic programming locally using Continue with multiple models.

## Quick Setup (15 minutes)

### 🔥 Quick Verification (30 seconds)

Before full setup, run a quick smoke test to verify the benchmark system works:

```bash
# Run automated smoke test (no model needed)
uv run run_smoke_test.py
```

This validates that the core benchmark infrastructure is working correctly.

### 1. Install Continue

- Install the [Continue VS Code extension](https://marketplace.visualstudio.com/items?itemName=Continue.continue)
- Install [Ollama](https://ollama.com/) for local models

### 2. Download Local Models

```bash
# Fast local models for testing
ollama pull qwen2.5-coder:7b    # Good coding model
ollama pull llama3.1:8b         # General purpose
ollama pull codestral:22b       # Mistral's code model (if you have enough RAM)

# Smaller models if RAM constrained
ollama pull qwen2.5-coder:1.5b  # Minimal coding model
ollama pull llama3.2:3b         # Lightweight general

```

### 3. Continue Configuration

Open Continue settings and replace your `config.yaml` with:

```yaml
models:
  # Commercial APIs (add your keys)
  - name: "Claude-4-Sonnet"
    provider: "anthropic"
    model: "claude-3-5-sonnet-20241022"
    apiKey: "your-api-key"
    roles: ["chat", "edit", "apply"]

  - name: "GPT-4o"
    provider: "openai"
    model: "gpt-4o"
    apiKey: "your-api-key"
    roles: ["chat", "edit", "apply"]

  # Local models via Ollama
  - name: "Qwen2.5-Coder-7B"
    provider: "ollama"
    model: "qwen2.5-coder:7b"
    roles: ["chat", "edit", "apply"]

  - name: "Llama3.1-8B"
    provider: "ollama"
    model: "llama3.1:8b"
    roles: ["chat", "edit", "apply"]

  - name: "Codestral-22B"
    provider: "ollama"
    model: "codestral:22b"
    roles: ["chat", "edit", "apply"]

# Context providers for better understanding
contextProviders:
  - name: "code"
    params: {}
  - name: "diff"
    params: {}
  - name: "terminal"
    params: {}
  - name: "problems"
    params: {}
  - name: "folder"
    params: {}

# Custom commands for benchmarking
slashCommands:
  - name: "benchmark-task"
    description: "Start a benchmarking task with metrics"
    run: "benchmark_task.py"

```

## POC Benchmark Framework

### 4. Create Benchmark Tasks

Create a `benchmark/` folder in your project:

```
benchmark/
├── tasks/
│   ├── easy/
│   ├── medium/
│   └── hard/
├── metrics.py
├── task_runner.py
└── results/

```

### 5. Simple Task Examples

**Easy Task** (`tasks/easy/fix_typo.md`):

```markdown
# Task: Fix Documentation Typo
**Repo**: Your current project
**Issue**: There's a typo in the README.md file where "recieve" should be "receive"
**Expected**: Fix the typo and ensure it doesn't appear elsewhere
**Time Estimate**: 2-5 minutes

```

**Medium Task** (`tasks/medium/add_validation.md`):

```markdown
# Task: Add Input Validation
**Repo**: Your current project
**Issue**: Add email validation to a user registration function
**Requirements**:
- Validate email format
- Return appropriate error messages
- Add unit tests
**Time Estimate**: 15-30 minutes

```

**Hard Task** (`tasks/hard/refactor_api.md`):

```markdown
# Task: Refactor API Response Structure
**Repo**: Your current project
**Issue**: Standardize API responses across endpoints
**Requirements**:
- Create consistent response wrapper
- Update all endpoints
- Maintain backward compatibility
**Time Estimate**: 1-2 hours

```

### 6. Simple Metrics Tracker

Create `benchmark/metrics.py`:

```python
import time
import json
from datetime import datetime

class BenchmarkMetrics:
    def __init__(self, model_name, task_name):
        self.model_name = model_name
        self.task_name = task_name
        self.start_time = None
        self.metrics = {
            'model': model_name,
            'task': task_name,
            'prompts_sent': 0,
            'chars_sent': 0,
            'chars_received': 0,
            'human_interventions': 0,
            'task_completed': False,
            'completion_time': 0,
            'files_modified': 0,
            'lines_added': 0,
            'lines_removed': 0,
            'session_log': []
        }

    def start_task(self):
        self.start_time = time.time()
        self.log_event('task_started')

    def log_prompt(self, prompt_text, response_text):
        self.metrics['prompts_sent'] += 1
        self.metrics['chars_sent'] += len(prompt_text)
        self.metrics['chars_received'] += len(response_text)
        self.log_event('prompt_sent', {
            'prompt_length': len(prompt_text),
            'response_length': len(response_text)
        })

    def log_human_intervention(self, intervention_type):
        self.metrics['human_interventions'] += 1
        self.log_event('human_intervention', {'type': intervention_type})

    def complete_task(self, success=True):
        if self.start_time:
            self.metrics['completion_time'] = time.time() - self.start_time
        self.metrics['task_completed'] = success
        self.log_event('task_completed', {'success': success})

        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"benchmark/results/{self.model_name}_{self.task_name}_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump(self.metrics, f, indent=2)

    def log_event(self, event_type, data=None):
        event = {
            'timestamp': time.time(),
            'event': event_type,
            'data': data or {}
        }
        self.metrics['session_log'].append(event)

```

### 7. Task Runner Script

Create `benchmark/task_runner.py`:

```python
#!/usr/bin/env python3
import os
import sys
from metrics import BenchmarkMetrics

def run_benchmark_task(model_name, task_file):
    """Simple POC task runner"""
    print(f"Starting benchmark: {model_name} on {task_file}")

    # Load task
    with open(task_file, 'r') as f:
        task_content = f.read()

    print(f"Task loaded:\n{task_content}")

    # Initialize metrics
    task_name = os.path.basename(task_file).replace('.md', '')
    metrics = BenchmarkMetrics(model_name, task_name)
    metrics.start_task()

    print(f"Metrics tracking started for {model_name}")
    print("Now go use Continue to solve this task!")
    print("Manual tracking points:")
    print("- Count each prompt you send")
    print("- Note when you manually edit code")
    print("- Track when you change the AI's suggestion")

    input("Press Enter when you complete the task...")

    success = input("Was the task completed successfully? (y/n): ").lower() == 'y'

    # Manual input for POC
    metrics.metrics['prompts_sent'] = int(input("How many prompts did you send? "))
    metrics.metrics['human_interventions'] = int(input("How many times did you manually intervene? "))
    metrics.metrics['files_modified'] = int(input("How many files were modified? "))

    metrics.complete_task(success)
    print(f"Benchmark completed! Results saved to benchmark/results/")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: uv run task_runner.py <model_name> <task_file>")
        sys.exit(1)

    run_benchmark_task(sys.argv[1], sys.argv[2])

```

## Running Your POC

### 8. Test Workflow

1. **Pick a "good first issue"** from a real repo or create synthetic ones
2. **Choose a model** in Continue
3. **Run the benchmark**:
    
    ```bash
    # First install dependencies with uv (10-100x faster than pip)
    uv pip install -r requirements.txt
    
    # Then run the benchmark
    uv run benchmark/task_runner.py "Claude-4-Sonnet" "benchmark/tasks/easy/fix_typo.md"
    ```
    
4. **Use Continue** to solve the task, noting:
    - How many prompts you send
    - When you manually edit code
    - When you reject AI suggestions
    - Overall collaboration quality
5. **Complete the task** and log results

### 9. Simple Analysis

Create `benchmark/analyze.py`:

```python
import json
import glob
import pandas as pd

def analyze_results():
    results = []

    for result_file in glob.glob("benchmark/results/*.json"):
        with open(result_file, 'r') as f:
            data = json.load(f)
            results.append(data)

    df = pd.DataFrame(results)

    # Basic analysis
    print("=== Benchmark Results ===")
    print(f"Total tasks: {len(df)}")
    print(f"Completion rate: {df['task_completed'].mean():.2%}")
    print("\nBy Model:")
    print(df.groupby('model')['task_completed'].agg(['count', 'mean', 'std']))
    print("\nAverage prompts by model:")
    print(df.groupby('model')['prompts_sent'].mean())
    print("\nAverage completion time by model:")
    print(df.groupby('model')['completion_time'].mean())

if __name__ == "__main__":
    analyze_results()

```

## Good First Issues to Try

### 10. Sample Tasks for Your POC

Create these tasks based on real GitHub "good first issues":

1. **Documentation fixes** (easy)
2. **Add error handling** (medium)
3. **Implement a small feature** (medium)
4. **Refactor duplicate code** (hard)
5. **Add comprehensive tests** (hard)

## Next Steps

Once your POC works:

1. **Automate metrics collection** by hooking into Continue's API
2. **Add more models** (Gemini, Claude variants, different local models)
3. **Create standardized tasks** from real repositories
4. **Build a simple dashboard** to visualize results
5. **Scale to multiple participants** for statistical significance

## Benefits of This Setup

- **Minimal setup time**: 15 minutes to start
- **Real models**: Mix of commercial and local
- **Actual workflow**: Using Continue as you normally would
- **Measurable**: Basic but meaningful metrics
- **Extensible**: Easy to add more sophistication later

This POC gives you the core structure to validate your benchmark concept before investing in the full implementation!
