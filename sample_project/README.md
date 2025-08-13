# Sample Project for AI Benchmarking

This is a test project with intentional issues for benchmarking AI coding agents.

## Purpose

This project contains various types of coding issues to test AI agents' ability to:
- Fix simple typos and formatting issues
- Add validation and error handling
- Refactor complex code
- Optimize performance

## Structure

```
sample_project/
├── src/
│   ├── __init__.py
│   ├── calculator.py      # Easy: Contains typos
│   ├── data_processor.py  # Medium: Needs validation
│   ├── user_manager.py    # Hard: Needs refactoring (god class)
│   └── analytics.py       # Hard: Performance issues
├── tests/
│   └── (test files would go here)
├── docs/
│   └── (documentation)
├── requirements.txt
└── README.md
```

## Planted Issues

See `ISSUES.md` for a complete list of all intentional issues and their locations.

## Usage

This project is used by the benchmark tasks in `../benchmark/tasks/`.

To reset the project to its original state (with all issues intact):
```bash
python reset_sample_project.py
```

## Warning

**DO NOT FIX** the issues in this project directly! They are intentionally placed for benchmarking purposes. Any fixes should be done as part of a benchmark test run.