# Makefile for vibe-check development

.PHONY: help install test coverage clean lint format type-check security all

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install dependencies
	python3 -m pip install --user -r requirements.txt

test:  ## Run basic test suite
	python3 run_tests.py

coverage:  ## Run tests with coverage (requires pytest)
	python3 -m pytest --cov=benchmark --cov=. --cov-report=html:htmlcov --cov-report=xml:coverage.xml --cov-report=term-missing --cov-fail-under=80 -v || echo "Install pytest-cov to run full coverage tests"

quick-test:  ## Run quick smoke tests
	@echo "🧪 Running quick smoke tests..."
	@python3 -c "import benchmark.metrics; print('✅ Imports work')"
	@python3 -c "from benchmark.metrics import BenchmarkMetrics; m = BenchmarkMetrics('test', 'test'); m.start_task(); print('✅ Basic functionality works')"
	@echo "✅ Quick tests passed!"

lint:  ## Run linting (requires flake8)
	python3 -m flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || echo "Install flake8 to run linting"
	python3 -m flake8 . --count --exit-zero --max-complexity=10 --max-line-length=88 --statistics || echo "Install flake8 to run linting"

format:  ## Format code (requires black)
	python3 -m black . || echo "Install black to format code"

type-check:  ## Run type checking (requires mypy)
	python3 -m mypy benchmark/ --ignore-missing-imports || echo "Install mypy to run type checking"
	python3 -m mypy benchmark_task.py --ignore-missing-imports || echo "Install mypy to run type checking"

security:  ## Run security checks (requires bandit)
	python3 -m bandit -r . || echo "Install bandit to run security checks"

clean:  ## Clean up generated files
	rm -rf __pycache__ benchmark/__pycache__ tests/__pycache__
	rm -rf .pytest_cache .coverage htmlcov coverage.xml
	rm -rf .mypy_cache
	rm -f .benchmark_session_*.json
	rm -f bandit-report.json
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete

benchmark-easy:  ## Run an easy benchmark task
	python3 benchmark/task_runner.py "test_model" "benchmark/tasks/easy/fix_typo.md"

benchmark-medium:  ## Run a medium benchmark task  
	python3 benchmark/task_runner.py "test_model" "benchmark/tasks/medium/add_validation.md"

benchmark-hard:  ## Run a hard benchmark task
	python3 benchmark/task_runner.py "test_model" "benchmark/tasks/hard/refactor_metrics.md"

analyze:  ## Analyze benchmark results
	python3 benchmark/analyze.py || echo "No results to analyze yet"

all: clean quick-test lint format type-check security  ## Run all checks

dev-setup:  ## Set up development environment
	@echo "🔧 Setting up development environment..."
	@echo "1. Installing dependencies..."
	make install || echo "Warning: Could not install all dependencies"
	@echo "2. Running initial tests..."
	make quick-test
	@echo "3. Creating benchmark results directory..."
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