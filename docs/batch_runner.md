# Batch Benchmark Runner

The batch runner allows you to run the same benchmark task across multiple AI models automatically for comparison.

## Features

- **Automatic Model Detection**: Discovers all available Ollama models and configured commercial models
- **Beautiful Progress Tracking**: Real-time progress display with rich terminal UI
- **Comprehensive Reports**: Generates HTML, JSON, and CSV comparison reports
- **Resume Capability**: Can resume interrupted batch runs
- **Model Rankings**: Automatically ranks models by speed, efficiency, and autonomy

## Installation

Make sure you have the required dependencies:

```bash
uv pip install rich
```

## Basic Usage

### Run on all available models
```bash
uv run benchmark/batch_runner.py --task benchmark/tasks/easy/fix_typo.md
```

### Run on specific models
```bash
uv run benchmark/batch_runner.py --task benchmark/tasks/easy/fix_typo.md --models "llama3,mistral,codellama"
```

### Run with custom timeout
```bash
uv run benchmark/batch_runner.py --task benchmark/tasks/medium/add_validation.md --timeout 3600
```

### Resume an interrupted batch
```bash
uv run benchmark/batch_runner.py --task benchmark/tasks/hard/refactor_metrics.md --resume batch_20241213_143022
```

## Configuration

### Models Configuration

Edit `benchmark/models_config.yaml` to add commercial models:

```yaml
models:
  - name: "gpt-4"
    provider: "openai"
    display_name: "GPT-4"
    enabled: true
    api_key: "${OPENAI_API_KEY}"
    settings:
      temperature: 0.7
      max_tokens: 2048
```

### Model Categories

The config file also defines model categories for organized testing:

- **fast**: Quick models for rapid testing
- **balanced**: Good balance of speed and quality
- **powerful**: High-quality models (may be slower)
- **coding_specialized**: Models optimized for code generation

## Output

The batch runner creates a timestamped directory in `benchmark/results/` containing:

1. **Individual Results**: JSON file for each model's performance
2. **Comparison Report (JSON)**: Complete data for all models
3. **Comparison Report (HTML)**: Visual report for browser viewing
4. **Comparison Report (CSV)**: For data analysis in spreadsheets

### Example Output Structure
```
benchmark/results/batch_20241213_143022/
├── comparison_report.json      # Complete comparison data
├── comparison_report.html      # Visual HTML report
├── comparison_report.csv       # CSV for analysis
├── ollama_llama2_result.json  # Individual model result
├── ollama_mistral_result.json # Individual model result
└── gpt-4_result.json          # Individual model result
```

## Performance Metrics

The batch runner tracks and compares:

- **Completion Time**: How long each model takes
- **Success Rate**: Which models complete successfully
- **Prompts Sent**: Number of interactions with the AI
- **Human Interventions**: Manual corrections needed
- **Code Changes**: Files modified, lines added/removed

## Rankings

Models are automatically ranked by:

- 🏆 **Fastest**: Quickest completion time
- 💬 **Most Efficient**: Fewest prompts needed
- 🤖 **Most Autonomous**: Least human intervention

## Integration with Continue

The batch runner simulates benchmark runs in the current implementation. In production, it would integrate with Continue or other AI coding assistants to actually execute the tasks.

## Command-Line Options

```
--task TASK        Path to the task file (required)
--models MODELS    Comma-separated list or "all" (default: all)
--output OUTPUT    Custom output directory for results
--parallel         Run models in parallel (experimental)
--timeout TIMEOUT  Max time per model in seconds (default: 1800)
--resume RESUME    Resume from a previous batch ID
```

## Examples

### Quick Test
```bash
# Run smoke test on fast models
uv run benchmark/batch_runner.py --task benchmark/tasks/smoke/add_comment.md --models "mistral,llama3" --timeout 60
```

### Full Benchmark
```bash
# Run comprehensive benchmark on all models
uv run benchmark/batch_runner.py --task benchmark/tasks/medium/add_validation.md
```

### Production Run
```bash
# Run with specific models and extended timeout
uv run benchmark/batch_runner.py \
  --task benchmark/tasks/hard/refactor_metrics.md \
  --models "gpt-4,claude-3-opus,ollama/mixtral" \
  --timeout 7200 \
  --output ./my_results
```

## Troubleshooting

### No models detected
- Ensure Ollama is installed and running: `ollama list`
- Check `models_config.yaml` for commercial models
- Verify API keys are set as environment variables

### Timeout issues
- Increase timeout with `--timeout` flag
- Some complex tasks may need 60+ minutes

### Resume not working
- Ensure the batch ID exists in `benchmark/results/`
- Check that result files aren't corrupted