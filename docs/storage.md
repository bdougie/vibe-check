# Storage System

## Overview

Vibe Check uses a simple, file-based JSON storage system for benchmark results. This approach prioritizes simplicity, portability, and human readability while providing all necessary data for analysis.

## Storage Location

All benchmark results are stored in the local filesystem:

```
benchmark/
  results/
    ├── model1_task1_20250813_071359.json
    ├── model2_task1_20250813_072145.json
    └── model3_task2_20250813_081523.json
```

## File Naming Convention

Files follow a consistent naming pattern:

```
{model_name}_{task_name}_{timestamp}.json
```

- **model_name**: The AI model being benchmarked (e.g., "Claude-3-Sonnet", "GPT-4", "Llama3")
- **task_name**: The benchmark task name (e.g., "fix_typo", "add_validation")
- **timestamp**: Format `YYYYMMDD_HHMMSS` in local time

### Examples
- `Claude-3-Sonnet_fix_typo_20250813_143022.json`
- `GPT-4_add_validation_20250813_150135.json`
- `test_model_smoke_test_20250813_152301.json`

## JSON Structure

Each result file contains a complete record of the benchmark session:

```json
{
  // Model and Task Information
  "model": "Claude-3-Sonnet",
  "task": "fix_typo",
  
  // Performance Metrics
  "prompts_sent": 3,
  "chars_sent": 1523,
  "chars_received": 4892,
  "human_interventions": 1,
  
  // Task Outcome
  "task_completed": true,
  "completion_time": 45.23,
  "duration_seconds": 45.23,
  
  // Git Tracking (Automatic)
  "files_modified": 2,
  "lines_added": 15,
  "lines_removed": 8,
  
  // Initial Git State
  "initial_git_state": {
    "commit": "abc123def456789",
    "has_uncommitted_changes": false,
    "timestamp": 1755083368.192
  },
  
  // Detailed Git Changes
  "git_diff_details": [
    {
      "filename": "src/main.py",
      "lines_added": 10,
      "lines_removed": 5
    },
    {
      "filename": "tests/test_main.py",
      "lines_added": 5,
      "lines_removed": 3
    }
  ],
  
  // Session Event Log
  "session_log": [
    {
      "timestamp": 1755083368.192,
      "event": "git_state_captured",
      "data": {...}
    },
    {
      "timestamp": 1755083368.193,
      "event": "task_started",
      "data": {}
    },
    {
      "timestamp": 1755083413.415,
      "event": "task_completed",
      "data": {"success": true}
    }
  ],
  
  // Optional: Smoke Test Flag
  "smoke_test": false
}
```

## Field Descriptions

### Core Metrics
| Field | Type | Description |
|-------|------|-------------|
| model | string | Name of the AI model |
| task | string | Name of the benchmark task |
| prompts_sent | integer | Number of prompts sent to the AI |
| chars_sent | integer | Total characters sent to the AI |
| chars_received | integer | Total characters received from the AI |
| human_interventions | integer | Number of manual corrections/edits |
| task_completed | boolean | Whether the task was successfully completed |
| completion_time | float | Time in seconds to complete the task |
| duration_seconds | float | Same as completion_time (for compatibility) |

### Git Tracking Fields
| Field | Type | Description |
|-------|------|-------------|
| files_modified | integer | Total files changed |
| lines_added | integer | Total lines added |
| lines_removed | integer | Total lines removed |
| initial_git_state | object | Git state at benchmark start |
| git_diff_details | array | Per-file change details |

### Session Log
Each event in the session_log contains:
- **timestamp**: Unix timestamp of the event
- **event**: Event type (e.g., "task_started", "prompt_sent")
- **data**: Event-specific data

## Storage Implementation

The storage system is implemented in `benchmark/metrics.py`:

```python
def complete_task(self, success=True):
    # ... capture metrics ...
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path("benchmark/results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    filename = results_dir / f"{self.model_name}_{self.task_name}_{timestamp}.json"
    
    with filename.open("w") as f:
        json.dump(self.metrics, f, indent=2)
    
    return filename
```

## Accessing Stored Data

### Reading Individual Files

```python
import json
from pathlib import Path

# Read a specific result file
result_file = Path("benchmark/results/model_task_timestamp.json")
with open(result_file) as f:
    data = json.load(f)

print(f"Model: {data['model']}")
print(f"Task completed: {data['task_completed']}")
print(f"Files modified: {data['files_modified']}")
```

### Analyzing Multiple Results

```python
from pathlib import Path
import json

# Load all results
results_dir = Path("benchmark/results")
all_results = []

for result_file in results_dir.glob("*.json"):
    with open(result_file) as f:
        all_results.append(json.load(f))

# Analyze by model
from collections import defaultdict
by_model = defaultdict(list)
for result in all_results:
    by_model[result['model']].append(result)

# Calculate averages
for model, results in by_model.items():
    avg_time = sum(r['completion_time'] for r in results) / len(results)
    success_rate = sum(1 for r in results if r['task_completed']) / len(results)
    print(f"{model}: {avg_time:.1f}s average, {success_rate:.1%} success rate")
```

## Backup and Version Control

### Recommended Practices

1. **Include in .gitignore**: Add `benchmark/results/` to avoid committing result files
2. **Regular backups**: Copy important results to a backup location
3. **Export summaries**: Use the analyze.py script to create CSV summaries
4. **Archive old results**: Move old results to an archive directory

### Example .gitignore entry
```
# Benchmark results
benchmark/results/*.json
```

## Data Privacy

Result files may contain:
- Code snippets from tasks
- File paths from your project
- Git commit hashes
- Timestamps

**Note**: Be cautious when sharing result files, as they may contain sensitive information about your codebase.

## Storage Advantages

1. **Simplicity**: No database setup required
2. **Portability**: Files can be easily copied/moved
3. **Human-readable**: JSON format can be opened in any text editor
4. **Version control friendly**: Can be committed if needed
5. **Tool compatibility**: JSON works with any analysis tool
6. **No dependencies**: Uses only Python standard library

## Storage Limitations

1. **No concurrent access**: Files may conflict if multiple benchmarks run simultaneously
2. **No query engine**: Must load files to search/filter
3. **Disk space**: Each benchmark creates a new file
4. **No automatic cleanup**: Old files must be manually deleted

## Future Enhancements

Potential improvements (not yet implemented):
- SQLite database option for larger datasets
- Automatic archiving of old results
- Result compression for large files
- Cloud storage integration
- Real-time result streaming