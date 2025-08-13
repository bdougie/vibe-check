# Continue Session Tracking

The Vibe Check framework now automatically extracts metrics from Continue IDE extension session data, eliminating the need for manual input during benchmarks.

## Overview

When you use Continue to complete benchmark tasks, the framework automatically:
- Detects active Continue sessions
- Extracts prompts, responses, and tool calls
- Counts tokens from Continue's telemetry database
- Calculates human interventions
- Records session duration

## How It Works

### Automatic Detection

When you run a benchmark, the framework checks for Continue session data:

```bash
python benchmark/task_runner.py "model-name" "task.md"

# Output:
🔍 Checking for Continue session data...
✅ Found Continue session: abc123...
📊 Metrics will be extracted automatically from Continue
```

If no Continue session is found, it falls back to manual input.

### Data Sources

The Continue Session Tracker reads from multiple local data sources:

1. **Session Files** (`~/.continue/sessions/`)
   - Chat history and messages
   - Tool calls and responses
   - Model information
   - Timestamps

2. **Token Database** (`~/.continue/dev_data/devdata.sqlite`)
   - Prompt tokens consumed
   - Generated tokens
   - Model usage statistics
   - Request counts

3. **Event Logs** (`~/.continue/dev_data/0.2.0/*.jsonl`)
   - Quick edits
   - Autocomplete events
   - Chat feedback
   - Error logs

## Session Data Structure

Continue stores session data locally with the following structure:

```
~/.continue/
├── sessions/
│   ├── sessions.json          # List of all sessions with metadata
│   └── <sessionId>.json       # Individual session files
├── dev_data/
│   ├── devdata.sqlite         # Token usage database
│   └── 0.2.0/                 # Version-specific event logs
│       ├── tokensGenerated.jsonl
│       ├── chatFeedback.jsonl
│       ├── quickEdit.jsonl
│       └── autocomplete.jsonl
├── index/                     # Codebase indexing data
├── logs/                      # Continue logs
└── config.yaml               # User configuration
```

## Metrics Extracted

### From Session History
- **Prompts Sent**: Number of user messages
- **Messages**: Full conversation history
- **Tool Calls**: Function calls made by the model
- **Models Used**: Which models were active
- **Session Duration**: Time from first to last message

### From Token Database
- **Prompt Tokens**: Total tokens in prompts
- **Generated Tokens**: Total tokens generated
- **Token Usage by Model**: Breakdown per model

### From Event Logs
- **Quick Edits**: Manual code modifications
- **Autocompletes**: Tab completion usage
- **Human Interventions**: Estimated from user actions

## Usage

### Basic Usage

The automatic extraction happens transparently:

```python
from benchmark.metrics import BenchmarkMetrics

# Start benchmark
metrics = BenchmarkMetrics("model-name", "task-name")
metrics.start_task()

# ... complete task using Continue ...

# Complete benchmark - automatically imports Continue data
result_file = metrics.complete_task(success=True)
```

### Manual Session Import

You can also manually import a specific Continue session:

```python
from benchmark.continue_session_tracker import ContinueSessionTracker

tracker = ContinueSessionTracker()

# Find latest session
session_id = tracker.find_latest_session()

# Extract all metrics
metrics = tracker.extract_all_metrics(session_id)

# Export for benchmark
benchmark_metrics = tracker.export_metrics_for_benchmark()
```

### Standalone Usage

Extract metrics from Continue without running a benchmark:

```python
from benchmark.continue_session_tracker import extract_metrics_from_continue

# Get metrics from latest session
metrics = extract_metrics_from_continue()

# Or specify a session ID
metrics = extract_metrics_from_continue("session-id-123")

print(f"Prompts: {metrics['prompts_sent']}")
print(f"Tokens generated: {metrics['tokens_generated']}")
print(f"Tool calls: {metrics['tool_calls']}")
```

## Benefits

### No Manual Input Required

Before:
```
How many prompts did you send? 5
How many times did you manually intervene? 2
```

After:
```
✅ Continue session metrics captured:
   💬 5 prompts sent
   🤖 2473 tokens generated
   🔧 3 tool calls
   ✋ 2 interventions
```

### Accurate Metrics

- **Exact token counts** from Continue's telemetry
- **Precise timestamps** for duration calculation
- **Complete tool call history** with arguments
- **Automatic intervention detection** from user actions

### Tool Call Tracking

The tracker captures detailed tool usage:

```json
{
  "tool_calls": [
    {
      "name": "writeFile",
      "arguments": {
        "path": "test.py",
        "content": "def test_function()..."
      },
      "id": "call_123"
    },
    {
      "name": "runCommand",
      "arguments": {
        "command": "python test.py"
      },
      "id": "call_124"
    }
  ]
}
```

## Configuration

### Enable/Disable Automatic Import

You can control automatic Continue import:

```python
# Disable automatic import
metrics.complete_task(success=True, auto_import_continue=False)

# Or set globally in your benchmark
class CustomBenchmark:
    def __init__(self):
        self.auto_import_continue = False
```

### Privacy Settings

The tracker only reads local Continue data. No data is sent to external services. The following data is accessed:

- Local session files in `~/.continue/sessions/`
- Local SQLite database in `~/.continue/dev_data/`
- Local event logs in `~/.continue/dev_data/0.2.0/`

## Troubleshooting

### Continue Session Not Found

If the tracker can't find Continue sessions:

1. **Check Continue is installed**: Ensure the Continue extension is installed in VS Code
2. **Check session exists**: Look for files in `~/.continue/sessions/`
3. **Use Continue first**: Complete at least one chat session with Continue
4. **Check permissions**: Ensure read access to `~/.continue/` directory

### Missing Metrics

If some metrics are missing:

- **No tokens**: Continue's telemetry may be disabled
- **No tool calls**: The model may not have used tools
- **No interventions**: May indicate a fully automated session

### Manual Override

You can always fall back to manual input:

```python
# Force manual input
metrics.metrics["prompts_sent"] = 5
metrics.metrics["human_interventions"] = 2
```

## Integration with Git Tracking

The Continue session tracking works alongside automatic git tracking:

```python
# Both Continue metrics and git changes are captured
metrics.complete_task(success=True)

# Results include:
# - Continue session metrics (prompts, tokens, tools)
# - Git changes (files modified, lines added/removed)
# - Combined duration and intervention tracking
```

## Example Output

When running a benchmark with Continue integration:

```
🔍 Checking for Continue session data...
✅ Found Continue session: abc123...
📊 Metrics will be extracted automatically from Continue

📊 Automatically capturing metrics...

✅ Continue session metrics captured:
   💬 8 prompts sent
   🤖 3542 tokens generated
   🔧 5 tool calls
   ✋ 3 interventions

📝 Git changes captured:
   📁 3 files modified
   ➕ 125 lines added
   ➖ 42 lines removed

✅ Benchmark completed!
📁 Results saved to: benchmark/results/model_task_20240113_123456_abc123.json
```

## API Reference

### ContinueSessionTracker

Main class for extracting Continue metrics:

```python
class ContinueSessionTracker:
    def find_latest_session() -> Optional[str]
    def load_session(session_id: str) -> bool
    def parse_session_messages() -> Dict
    def get_token_usage_from_db() -> Dict
    def extract_all_metrics(session_id: str) -> Dict
    def export_metrics_for_benchmark() -> Dict
```

### Helper Functions

```python
# Find the most recent Continue session
find_active_continue_session() -> Optional[str]

# Extract metrics from Continue (high-level API)
extract_metrics_from_continue(session_id: Optional[str]) -> Dict
```

## Future Enhancements

Planned improvements for Continue integration:

1. **Real-time tracking**: Monitor sessions as they happen
2. **Multi-session support**: Aggregate metrics across multiple sessions
3. **Advanced tool analysis**: Categorize and analyze tool usage patterns
4. **Model comparison**: Compare tool usage across different models
5. **Export formats**: Support for CSV, JSON, and visualization exports

## Related Documentation

- [Automatic Git Tracking](git-tracking.md) - Git change tracking
- [Storage System](storage.md) - How metrics are stored
- [Continue Configuration](continue-config.md) - Setting up Continue
- [Benchmark Metrics](../benchmark/metrics.py) - Core metrics system