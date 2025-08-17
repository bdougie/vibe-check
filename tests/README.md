# Tests Directory

This directory contains all test files for the vibe-check benchmark suite.

## Test Files

### Core Tests

#### `test_benchmark_task.py`
Tests for the core benchmark task execution functionality, including:
- Task loading and validation
- Execution flow
- Result collection

#### `test_end_to_end.py`
End-to-end integration tests that verify the complete benchmark workflow from task loading to result generation.

#### `test_validators.py`
Tests for the validation system that checks whether tasks have been completed successfully.

### Component Tests

#### `test_analyze.py`
Tests for the results analysis module that processes and summarizes benchmark outcomes.

#### `test_batch_runner.py`
Tests for the batch runner that executes multiple benchmark tasks in sequence.

#### `test_continue_config_generator.py`
Tests for the Continue CLI configuration generator that creates appropriate configs for different models.

#### `test_continue_session_tracker.py` & `test_continue_session_tracker_fix.py`
Tests for the session tracking system that monitors Continue CLI sessions during benchmark execution.

#### `test_metrics.py`
Tests for the metrics collection and calculation system.

#### `test_model_verifier.py`
Tests for the model verification system that ensures models are properly configured and accessible.

#### `test_ollama_check.py`
Tests for Ollama integration and model availability checking.

#### `test_task_runner.py`
Tests for the individual task runner component.

### Utility Tests

#### `test_setup_wizard.py`
Tests for the interactive setup wizard functionality.

#### `test_precommit.py`
Tests for pre-commit hook functionality.

#### `test_complete_function.py`
Tests for function completion utilities.

## Running Tests

To run all tests:
```bash
python scripts/run_tests.py
```

To run a specific test file:
```bash
pytest tests/test_benchmark_task.py
```

To run with coverage:
```bash
pytest --cov=benchmark tests/
```