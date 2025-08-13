# Automatic Git Tracking

## Overview

The Vibe Check framework now includes automatic git diff tracking that captures code changes during benchmarks without requiring manual input. This feature provides accurate, consistent metrics about file modifications, lines added/removed, and detailed per-file change information.

## How It Works

### 1. Initial State Capture

When a benchmark starts, the system automatically captures:
- Current git commit hash
- Whether there are uncommitted changes
- Timestamp of capture

```python
# Automatically called when benchmark starts
metrics.start_task()  # This triggers capture_initial_git_state()
```

### 2. Change Tracking During Task

While the AI coding agent works on the task, all file modifications are tracked by git. No manual intervention is required during this phase.

### 3. Final State Capture

When the task completes, the system automatically:
- Runs `git diff --stat` to get summary statistics
- Runs `git diff --numstat` to get detailed per-file changes
- Stores all information in the metrics

```python
# Automatically captures git changes
metrics.complete_task(success=True)  # This triggers capture_final_git_state()
```

## Data Captured

### Summary Statistics
- **files_modified**: Total number of files changed
- **lines_added**: Total lines added across all files
- **lines_removed**: Total lines removed across all files

### Detailed Information
- **initial_git_state**: Commit hash and uncommitted changes status at start
- **git_diff_details**: Array of per-file changes with:
  - filename
  - lines_added per file
  - lines_removed per file

## Implementation Details

### Core Methods in `benchmark/metrics.py`

#### `capture_initial_git_state()`
- Runs `git rev-parse HEAD` to get current commit
- Runs `git status --porcelain` to check for uncommitted changes
- Stores state with timestamp

#### `get_git_diff_stats()`
- Runs `git diff --stat` to get summary statistics
- Parses output to extract files/lines changed
- Returns tuple: (files_modified, lines_added, lines_removed)

#### `get_detailed_git_diff()`
- Runs `git diff --numstat` for detailed per-file stats
- Handles binary files (marked with `-` in output)
- Returns array of file change details

#### `capture_final_git_state()`
- Calls both stats methods above
- Updates metrics with all git information
- Logs the automatic capture event

## Usage Example

```python
from benchmark.metrics import BenchmarkMetrics

# Create metrics instance
metrics = BenchmarkMetrics("model_name", "task_name")

# Start benchmark (automatically captures initial git state)
metrics.start_task()

# ... AI agent modifies files here ...

# Complete benchmark (automatically captures final git state)
result_file = metrics.complete_task(success=True)

# Access captured git information
print(f"Files modified: {metrics.metrics['files_modified']}")
print(f"Lines added: {metrics.metrics['lines_added']}")
print(f"Lines removed: {metrics.metrics['lines_removed']}")

# Detailed per-file changes
for change in metrics.metrics['git_diff_details']:
    print(f"{change['filename']}: +{change['lines_added']}/-{change['lines_removed']}")
```

## Benefits

1. **Accuracy**: Eliminates human error in reporting changes
2. **Consistency**: Same metrics across all benchmarks
3. **Detail**: Captures per-file change information
4. **Automation**: No manual input required
5. **Transparency**: Shows exact code impact of AI assistance

## Error Handling

The system gracefully handles errors:
- Git command failures are logged but don't crash the benchmark
- Missing git installation returns zero values
- Non-git directories return zero values
- Binary files are handled specially (0 lines changed)

## Testing

Comprehensive test coverage includes:
- Mock git command outputs
- Error handling scenarios
- Integration tests
- Edge cases (binary files, no changes, etc.)

See `tests/test_metrics.py::TestGitTracking` for full test suite.

## Migration from Manual Tracking

Previous versions required manual input:
```python
# Old approach (deprecated)
files = input("How many files were modified?")
metrics.update_git_stats(files, lines_added, lines_removed)
```

New automatic approach:
```python
# New approach (automatic)
metrics.complete_task(success=True)  # Git stats captured automatically
```

## Requirements

- Git must be installed and accessible via command line
- Benchmark must run in a git repository
- Changes must be unstaged (not committed) to be tracked

## Limitations

- Only tracks unstaged changes (not committed changes)
- Requires git command-line tools
- Binary file changes show 0 lines (by design)
- Does not track file renames separately