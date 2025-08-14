# Makefile for vibe-check development

.PHONY: help install test coverage clean lint format type-check security all

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	uv pip sync requirements.txt

test:  ## Run basic test suite
	uv run run_tests.py

coverage:  ## Run tests with coverage (requires pytest)
	uv run pytest --cov=benchmark --cov=. --cov-report=html:htmlcov --cov-report=xml:coverage.xml --cov-report=term-missing --cov-fail-under=80 -v || echo "Install pytest-cov to run full coverage tests"

quick-test:  ## Run quick smoke tests
	@echo "🧪 Running quick smoke tests..."
	@uv run python -c "import benchmark.metrics; print('✅ Imports work')"
	@uv run python -c "from benchmark.metrics import BenchmarkMetrics; m = BenchmarkMetrics('test', 'test'); m.start_task(); print('✅ Basic functionality works')"
	@echo "✅ Quick tests passed!"

lint:  ## Run linting with ruff (fast!)
	uv run ruff check . || echo "Install ruff to run linting"

lint-fix:  ## Run linting with ruff and auto-fix issues
	uv run ruff check . --fix || echo "Install ruff to run linting"

format:  ## Format code with ruff (fast!)
	uv run ruff format . || echo "Install ruff to format code"

format-check:  ## Check code formatting with ruff
	uv run ruff format . --check --diff || echo "Install ruff to check formatting"

black-format:  ## Format code with black (backup)
	uv run black . || echo "Install black to format code"

type-check:  ## Run type checking (requires mypy)
	uv run mypy benchmark/ --ignore-missing-imports || echo "Install mypy to run type checking"
	uv run mypy benchmark_task.py --ignore-missing-imports || echo "Install mypy to run type checking"

security:  ## Run security checks (requires bandit)
	uv run bandit -r . || echo "Install bandit to run security checks"

pre-commit-install:  ## Install pre-commit hooks
	uv run pre-commit install || echo "Install pre-commit to set up hooks"

pre-commit-run:  ## Run pre-commit hooks on all files
	uv run pre-commit run --all-files || echo "Install pre-commit to run hooks"

pre-commit-update:  ## Update pre-commit hooks
	uv run pre-commit autoupdate || echo "Install pre-commit to update hooks"

clean:  ## Clean up generated files
	rm -rf __pycache__ benchmark/__pycache__ tests/__pycache__
	rm -rf .pytest_cache .coverage htmlcov coverage.xml
	rm -rf .mypy_cache .ruff_cache
	rm -f .benchmark_session_*.json
	rm -f bandit-report.json
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete

benchmark-easy:  ## Run an easy benchmark task
	uv run benchmark/task_runner.py "test_model" "benchmark/tasks/easy/fix_typo.md"

benchmark-medium:  ## Run a medium benchmark task  
	uv run benchmark/task_runner.py "test_model" "benchmark/tasks/medium/add_validation.md"

benchmark-hard:  ## Run a hard benchmark task
	uv run benchmark/task_runner.py "test_model" "benchmark/tasks/hard/refactor_metrics.md"

analyze:  ## Analyze benchmark results
	uv run benchmark/analyze.py || echo "No results to analyze yet"

all: clean quick-test lint format-check type-check security pre-commit-run  ## Run all checks

dev-setup:  ## Set up development environment
	@echo "🔧 Setting up development environment..."
	@echo "1. Installing dependencies..."
	make install || echo "Warning: Could not install all dependencies"
	@echo "2. Installing pre-commit hooks..."
	make pre-commit-install || echo "Warning: Could not install pre-commit hooks"
	@echo "3. Running initial tests..."
	make quick-test
	@echo "4. Creating benchmark results directory..."
	mkdir -p benchmark/results
	@echo "✅ Development setup complete!"
	@echo ""
	@echo "📋 Available commands:"
	make help

ci-local:  ## Run CI-like tests locally
	@echo "🤖 Running CI-like tests locally..."
	make clean
	make quick-test
	make test
	@echo "✅ Local CI simulation complete!"