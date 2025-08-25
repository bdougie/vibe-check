# CLI Benchmarking Guide (Advanced)

Automated, headless benchmarking for batch testing, CI/CD integration, and programmatic access.

## Overview

CLI benchmarking enables:
- **Automated Testing** - Run benchmarks without UI interaction
- **Batch Processing** - Test multiple models and tasks simultaneously
- **CI/CD Integration** - Add benchmarking to your pipeline
- **Reproducible Results** - Scripted, consistent testing

## Quick Start

### Single Task Benchmark

```bash
# Basic syntax
uv run benchmark/task_runner.py "MODEL_NAME" "TASK_PATH"

# Examples
uv run benchmark/task_runner.py "Claude-3.5-Sonnet" "benchmark/tasks/easy/fix_typo.md"
uv run benchmark/task_runner.py "ollama/qwen2.5-coder:7b" "benchmark/tasks/medium/add_validation.md"
uv run benchmark/task_runner.py "gpt-4-turbo" "benchmark/tasks/hard/refactor_metrics.md"
```

### Batch Processing

```bash
# Run multiple models on same task
uv run benchmark/batch_runner.py \
  --models "claude-3.5,gpt-4,ollama/qwen2.5-coder:7b" \
  --task "benchmark/tasks/easy/fix_typo.md"

# Run one model on multiple tasks
uv run benchmark/batch_runner.py \
  --model "claude-3.5" \
  --tasks "easy/*.md"

# Full matrix (all models × all tasks)
uv run benchmark/batch_runner.py \
  --models "model1,model2,model3" \
  --tasks "easy/*,medium/*"
```

## Model Configuration

### Commercial Models

#### OpenAI
```bash
export OPENAI_API_KEY="your-key"
uv run benchmark/task_runner.py "gpt-4-turbo" "task.md"
uv run benchmark/task_runner.py "gpt-3.5-turbo" "task.md"
```

#### Anthropic
```bash
export ANTHROPIC_API_KEY="your-key"
uv run benchmark/task_runner.py "claude-3-5-sonnet" "task.md"
uv run benchmark/task_runner.py "claude-3-haiku" "task.md"
```

#### Google
```bash
export GOOGLE_API_KEY="your-key"
uv run benchmark/task_runner.py "gemini-pro" "task.md"
```

### Local Models (Ollama)

```bash
# Ensure Ollama is running
ollama serve

# Run benchmarks
uv run benchmark/task_runner.py "ollama/qwen2.5-coder:7b" "task.md"
uv run benchmark/task_runner.py "ollama/deepseek-coder:6.7b" "task.md"
uv run benchmark/task_runner.py "ollama/codellama:13b" "task.md"
```

### Custom Endpoints

```bash
# Configure custom API endpoint
export CUSTOM_API_ENDPOINT="https://your-api.com"
export CUSTOM_API_KEY="your-key"

uv run benchmark/task_runner.py \
  --provider custom \
  --model "your-model" \
  --endpoint "$CUSTOM_API_ENDPOINT" \
  "task.md"
```

## Advanced Options

### Task Runner Options

```bash
uv run benchmark/task_runner.py --help

Options:
  --timeout SECONDS        Maximum time for task completion (default: 600)
  --max-prompts N         Maximum prompts allowed (default: 20)
  --temperature T         Model temperature 0.0-1.0 (default: 0.2)
  --skip-git-tracking     Don't track git changes
  --skip-ollama-check     Skip Ollama connectivity check
  --verbose               Show detailed output
  --json                  Output results as JSON
  --continue-on-error     Don't stop batch on failures
```

### Parallel Execution

```bash
# Run benchmarks in parallel (4 workers)
uv run benchmark/parallel_runner.py \
  --workers 4 \
  --models "model1,model2,model3,model4" \
  --tasks "tasks/*.md"

# Adaptive parallelism based on CPU cores
uv run benchmark/parallel_runner.py \
  --workers auto \
  --models "$(cat models.txt)" \
  --tasks "$(find tasks -name '*.md')"
```

### Custom Metrics Collection

```bash
# Add custom metrics collector
uv run benchmark/task_runner.py \
  --metrics-plugin "my_metrics.py" \
  --collect "token_efficiency,cost_per_line" \
  "model" "task.md"
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Benchmark Suite
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  pull_request:
    paths:
      - 'src/**'
      - 'benchmark/**'

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python with uv
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          echo "$HOME/.cargo/bin" >> $GITHUB_PATH
      
      - name: Install dependencies
        run: uv pip sync requirements.txt
      
      - name: Run benchmarks
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
        run: |
          uv run benchmark/batch_runner.py \
            --models "gpt-4,claude-3.5" \
            --tasks "easy/*,medium/*" \
            --json > results.json
      
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: benchmark-results
          path: results.json
      
      - name: Comment on PR
        if: github.event_name == 'pull_request'
        run: |
          uv run benchmark/format_pr_comment.py results.json
```

### GitLab CI

```yaml
benchmark:
  stage: test
  image: python:3.11
  before_script:
    - curl -LsSf https://astral.sh/uv/install.sh | sh
    - export PATH="$HOME/.cargo/bin:$PATH"
    - uv pip sync requirements.txt
  script:
    - uv run benchmark/batch_runner.py --models "$MODELS" --tasks "tasks/*"
  artifacts:
    reports:
      junit: benchmark-results.xml
    paths:
      - benchmark/results/
  only:
    - schedules
    - merge_requests
```

### Jenkins

```groovy
pipeline {
    agent any
    
    environment {
        OPENAI_API_KEY = credentials('openai-api-key')
    }
    
    stages {
        stage('Setup') {
            steps {
                sh 'curl -LsSf https://astral.sh/uv/install.sh | sh'
                sh 'uv pip sync requirements.txt'
            }
        }
        
        stage('Benchmark') {
            parallel {
                stage('GPT-4') {
                    steps {
                        sh 'uv run benchmark/task_runner.py "gpt-4" "tasks/easy/*.md"'
                    }
                }
                stage('Claude') {
                    steps {
                        sh 'uv run benchmark/task_runner.py "claude-3.5" "tasks/easy/*.md"'
                    }
                }
            }
        }
        
        stage('Report') {
            steps {
                sh 'uv run benchmark/analyze.py --export html'
                publishHTML(target: [
                    reportName: 'Benchmark Report',
                    reportDir: 'benchmark/results',
                    reportFiles: 'report.html'
                ])
            }
        }
    }
}
```

## Programmatic Usage

### Python API

```python
from benchmark import TaskRunner, BatchProcessor
from benchmark.models import ModelConfig

# Single task
runner = TaskRunner(
    model=ModelConfig("gpt-4", temperature=0.2),
    task_path="benchmark/tasks/easy/fix_typo.md"
)
result = runner.run()
print(f"Success: {result.success}, Duration: {result.duration}")

# Batch processing
processor = BatchProcessor()
results = processor.run_matrix(
    models=["gpt-4", "claude-3.5"],
    tasks=["task1.md", "task2.md"],
    parallel=True
)

# Custom analysis
for result in results:
    print(f"{result.model} on {result.task}: {result.metrics}")
```

### REST API Server

```bash
# Start benchmark server
uv run benchmark/server.py --port 8080

# Submit benchmark job
curl -X POST http://localhost:8080/benchmark \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "task": "fix_typo.md",
    "options": {"timeout": 300}
  }'

# Check status
curl http://localhost:8080/status/job_123

# Get results
curl http://localhost:8080/results/job_123
```

## Performance Optimization

### Resource Management

```bash
# Limit resource usage
uv run benchmark/task_runner.py \
  --max-memory 4G \
  --max-cpu 2 \
  --rate-limit 10/min \
  "model" "task.md"
```

### Caching

```bash
# Enable response caching
export BENCHMARK_CACHE_DIR="/tmp/benchmark_cache"
uv run benchmark/task_runner.py \
  --cache-responses \
  --cache-ttl 3600 \
  "model" "task.md"
```

### Batch Optimization

```bash
# Optimize batch size for throughput
uv run benchmark/optimize_batch.py \
  --models "model1,model2,model3" \
  --target-duration 3600 \
  --recommend-batch-size
```

## Output Formats

### JSON Output

```bash
uv run benchmark/task_runner.py \
  --json \
  "model" "task.md" > result.json
```

### CSV Export

```bash
uv run benchmark/batch_runner.py \
  --export csv \
  --output results.csv \
  --models "model1,model2" \
  --tasks "tasks/*.md"
```

### Markdown Report

```bash
uv run benchmark/task_runner.py \
  --format markdown \
  "model" "task.md" > report.md
```

### JUnit XML (for CI)

```bash
uv run benchmark/task_runner.py \
  --format junit \
  --output test-results.xml \
  "model" "task.md"
```

## Error Handling

### Retry Logic

```bash
# Automatic retries on failure
uv run benchmark/task_runner.py \
  --max-retries 3 \
  --retry-delay 30 \
  "model" "task.md"
```

### Failure Recovery

```bash
# Resume interrupted batch
uv run benchmark/batch_runner.py \
  --resume-from checkpoint.json \
  --models "model1,model2,model3" \
  --tasks "tasks/*.md"
```

### Debug Mode

```bash
# Verbose debugging output
uv run benchmark/task_runner.py \
  --debug \
  --log-level DEBUG \
  --save-traces \
  "model" "task.md"
```

## Custom Task Creation

### Task Template

```markdown
# Task: [Name]
**Difficulty**: [easy|medium|hard]
**Estimated Time**: [X-Y minutes]

## Description
[What needs to be done]

## Requirements
- [Requirement 1]
- [Requirement 2]

## Success Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]

## Test Command
```bash
[Command to verify success]
```
```

### Automated Task Generation

```bash
# Generate task from GitHub issue
uv run benchmark/generate_task.py \
  --from-issue "https://github.com/owner/repo/issues/123" \
  --difficulty auto \
  --output "benchmark/tasks/generated/"

# Generate from code snippet
uv run benchmark/generate_task.py \
  --from-code "buggy_function.py" \
  --type "fix-bug" \
  --output "task.md"
```

## Monitoring & Alerts

### Real-time Monitoring

```bash
# Monitor running benchmarks
uv run benchmark/monitor.py --follow

# Dashboard view
uv run benchmark/dashboard.py --realtime
```

### Alerting

```bash
# Set up alerts for failures
uv run benchmark/batch_runner.py \
  --alert-on-failure \
  --webhook "https://hooks.slack.com/..." \
  --models "production-models.txt" \
  --tasks "critical/*.md"
```

## Best Practices

### 1. Consistent Environment
- Use Docker for reproducible environments
- Pin model versions when possible
- Document system specifications

### 2. Statistical Significance
- Run each benchmark 3-5 times
- Calculate confidence intervals
- Account for variance in results

### 3. Cost Management
- Set spending limits for API calls
- Use local models for development
- Cache responses when appropriate

### 4. Security
- Never commit API keys
- Use environment variables or secrets management
- Sanitize task outputs

## Troubleshooting

### Common Issues

**Model timeout**
```bash
# Increase timeout
uv run benchmark/task_runner.py --timeout 1200 "model" "task.md"
```

**Rate limiting**
```bash
# Add rate limit handling
uv run benchmark/task_runner.py \
  --rate-limit 10/min \
  --retry-on-rate-limit \
  "model" "task.md"
```

**Memory issues**
```bash
# Limit memory usage
ulimit -v 4194304  # 4GB limit
uv run benchmark/task_runner.py "model" "task.md"
```

## Next Steps

- Review [Manual Benchmarking Guide](manual-benchmarking-guide.md) for interactive testing
- Explore [Session Analysis](session-analysis.md) for result interpretation
- Check [Task Creation Guide](task-creation.md) for custom benchmarks
- Join our [Discord](https://discord.gg/vibecheck) for community support

---

Need help? Open an [issue](https://github.com/bdougie/vibe-check/issues) or check our [FAQ](faq.md).