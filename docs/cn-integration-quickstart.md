# Continue CLI Integration - Quick Start Guide

Get up and running with automated AI benchmarking in 5 minutes!

## 🚀 Quick Setup

### 1. Install Continue CLI

```bash
# Install globally via npm
npm i -g @continuedev/cli

# Verify installation
cn --version
```

### 2. Set Up API Keys

```bash
# For OpenAI models
export OPENAI_API_KEY="sk-..."

# For Anthropic models
export ANTHROPIC_API_KEY="sk-ant-..."

# For Ollama (local models)
ollama serve  # Run in separate terminal
```

### 3. Run Your First Benchmark

```bash
# Clone the repo
git clone https://github.com/bdougie/vibe-check.git
cd vibe-check

# Install Python dependencies
uv pip install -r requirements.txt

# Run a simple benchmark with CN
python -c "
from benchmark.cn_integration.cn_runner import CNRunner

runner = CNRunner(verbose=True)
result = runner.run_task(
    'benchmark/tasks/easy/fix_typo.md',
    'gpt-3.5-turbo',
    timeout=120
)

print(f'Success: {result[\"success\"]}')
print(f'Time: {result[\"execution_time\"]:.2f}s')
"
```

## 📊 Run Batch Benchmarks

Compare multiple models on the same task:

```python
from benchmark.cn_integration.cn_batch_integration import CNBatchIntegration

# Initialize batch runner
batch = CNBatchIntegration(verbose=True)

# Run benchmark across models
result = batch.run_batch_with_cn(
    task_files=["benchmark/tasks/easy/fix_typo.md"],
    models=[
        {"name": "gpt-3.5-turbo"},
        {"name": "gpt-4"},
        {"name": "ollama/llama2"}
    ],
    timeout=300
)

print(f"Success rate: {result['success_rate']:.1f}%")
print(f"Fastest model: {result['rankings']['fastest']}")
```

## 🎯 Example Tasks

### Easy Task - Fix Typos
```bash
python scripts/test_cn_integration.py \
    --task benchmark/tasks/easy/fix_calculator_typos.md \
    --model gpt-3.5-turbo
```

### Medium Task - Add Validation
```bash
python scripts/test_cn_integration.py \
    --task benchmark/tasks/medium/add_validation.md \
    --model gpt-4
```

### Run All Easy Tasks
```bash
for task in benchmark/tasks/easy/*.md; do
    python scripts/test_cn_integration.py \
        --task "$task" \
        --model gpt-3.5-turbo
done
```

## 🔧 Common Commands

### Test CN Installation
```bash
cn --help
```

### List Available Ollama Models
```bash
ollama list
```

### Pull New Ollama Model
```bash
ollama pull codellama:13b
```

### Run with Verbose Output
```python
runner = CNRunner(verbose=True)  # Shows detailed logs
```

### Set Custom Timeout
```python
result = runner.run_task(
    "task.md",
    "gpt-4",
    timeout=600  # 10 minutes
)
```

## 📈 View Results

Results are saved as JSON files:

```bash
# View latest result
cat benchmark/results/batch_*/cn_batch_summary.json | jq .

# Open HTML report
open benchmark/results/batch_*/cn_batch_report.html

# View CSV in Excel/Numbers
open benchmark/results/batch_*/cn_batch_results.csv
```

## 🐛 Troubleshooting

### CN Command Not Found
```bash
npm i -g @continuedev/cli
export PATH=$PATH:$(npm bin -g)
```

### API Key Issues
```bash
# Check if set
echo $OPENAI_API_KEY

# Set in .env file
echo "OPENAI_API_KEY=sk-..." >> .env
source .env
```

### Ollama Connection Error
```bash
# Start Ollama service
ollama serve

# Check if running
curl http://localhost:11434/api/tags
```

### Permission Errors
```bash
# Make scripts executable
chmod +x scripts/test_cn_integration.py

# Run with sudo if needed (not recommended)
sudo python scripts/test_cn_integration.py ...
```

## 🎮 Interactive Demo

Run the interactive demo to see CN in action:

```bash
# Run demo with default model (gpt-3.5-turbo)
./scripts/run_cn_demo

# Run with specific model
./scripts/run_cn_demo --model gpt-4

# Run with Ollama
./scripts/run_cn_demo --model ollama/llama2
```

## 📚 Next Steps

1. **Read Full Documentation**: [CN Runner Docs](./cn-runner.md)
2. **Explore Task Types**: Check `benchmark/tasks/` directory
3. **Create Custom Tasks**: Follow the task format in existing files
4. **Contribute**: Submit PRs with new tasks or improvements

## 💡 Tips

- Start with easy tasks to verify setup
- Use Ollama for local testing (no API costs)
- Set reasonable timeouts (easy: 2min, medium: 5min, hard: 10min)
- Monitor git changes to see what CN modified
- Use `task_type="analysis"` for read-only exploration

## 🔗 Resources

- [Continue CLI Docs](https://docs.continue.dev/cli)
- [Vibe Check Repo](https://github.com/bdougie/vibe-check)
- [OpenAI API Keys](https://platform.openai.com/api-keys)
- [Ollama Models](https://ollama.ai/library)

---

**Ready to benchmark?** Start with the easy tasks and work your way up! 🚀