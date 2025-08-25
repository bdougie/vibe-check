# Session Analysis Guide

Understanding and analyzing your benchmark session data to gain insights into AI model performance.

## Overview

Vibe Check captures comprehensive metrics during benchmarking sessions. This guide helps you understand, analyze, and derive insights from your session data.

## Session Metrics Explained

### Core Metrics

#### Task Completion
- **Success Rate**: Percentage of tasks completed successfully
- **Completion Time**: Total time from start to task completion
- **First Success Time**: Time to first working solution

#### Interaction Metrics
- **Prompt Count**: Number of prompts sent to AI
- **Response Count**: Number of AI responses received
- **Interaction Ratio**: Prompts per minute (interaction density)
- **Error Corrections**: Number of times AI output needed fixing

#### Code Quality Metrics
- **Lines Changed**: Total lines added/removed
- **Files Modified**: Number of files touched
- **Test Pass Rate**: If tests exist, percentage passing
- **Refactor Cycles**: Number of code revision iterations

#### Efficiency Metrics
- **Token Usage**: Total tokens consumed (if available)
- **Cost Estimate**: Approximate API costs for commercial models
- **Time per Token**: Response generation speed
- **Thinking Time**: Gaps between user prompts

## Viewing Session Results

### Quick Analysis

View the latest session:
```bash
uv run benchmark/analyze.py --session latest
```

Output example:
```
Session: session_20241125_143022
Model: Claude 3.5 Sonnet
Task: fix_typo.md
Status: SUCCESS
Duration: 4m 32s
Prompts: 3
Files Changed: 1
Lines Modified: +5 -3
```

### Detailed Analysis

Get comprehensive metrics:
```bash
uv run benchmark/analyze.py --session latest --detailed
```

Detailed output includes:
- Complete interaction timeline
- Token usage breakdown
- Response time distribution
- Error analysis
- Code change summary

## Comparing Sessions

### Model Comparison

Compare different models on the same task:
```bash
uv run benchmark/analyze.py --compare-models "claude-3.5" "gpt-4" --task "fix_typo"
```

Output:
```
Task: fix_typo.md

Claude 3.5 Sonnet:
  Avg Duration: 3m 45s
  Success Rate: 100%
  Avg Prompts: 2.5
  
GPT-4:
  Avg Duration: 4m 12s
  Success Rate: 95%
  Avg Prompts: 3.2

Winner: Claude 3.5 Sonnet (26% faster, 28% fewer prompts)
```

### Task Difficulty Analysis

Analyze performance across difficulty levels:
```bash
uv run benchmark/analyze.py --difficulty-analysis "claude-3.5"
```

## Understanding Patterns

### Success Indicators

Look for these patterns in successful sessions:
- **Low prompt count** - Model understood task quickly
- **Consistent response times** - Stable performance
- **Clean git diffs** - Precise, targeted changes
- **No error corrections** - Got it right first time

### Failure Patterns

Common failure indicators:
- **High prompt count** (>10 for simple tasks)
- **Multiple file reversions** - Model confused
- **Escalating response times** - Context overload
- **Repeated similar prompts** - Model not understanding

## Visualization

### Generate Charts

Create visual reports:
```bash
# Time series of response times
uv run benchmark/visualize.py --session latest --chart response-time

# Model comparison radar chart
uv run benchmark/visualize.py --compare-models --chart radar

# Success rate heatmap
uv run benchmark/visualize.py --heatmap success-rate
```

### Export for Analysis

Export to common formats:
```bash
# CSV for Excel/Sheets
uv run benchmark/analyze.py --export csv

# JSON for custom analysis
uv run benchmark/analyze.py --export json

# Markdown report
uv run benchmark/analyze.py --export markdown
```

## Key Metrics to Track

### For Model Selection

Focus on these metrics when choosing models:

1. **Success Rate** - Can it complete tasks?
2. **Average Duration** - How fast?
3. **Prompt Efficiency** - Prompts per task
4. **Cost per Task** - For commercial models

### For Workflow Optimization

Track these to improve your process:

1. **Thinking Time** - Are you clear in prompts?
2. **Error Patterns** - Common failure modes
3. **Context Usage** - Are you providing enough info?
4. **Iteration Count** - How many attempts needed?

## Advanced Analysis

### Statistical Analysis

Run statistical tests:
```bash
# Confidence intervals for metrics
uv run benchmark/analyze.py --statistics confidence

# Hypothesis testing between models
uv run benchmark/analyze.py --statistics t-test --models "claude" "gpt-4"

# Regression analysis on factors
uv run benchmark/analyze.py --statistics regression
```

### Custom Queries

Query session data directly:
```python
from benchmark.analysis import SessionAnalyzer

analyzer = SessionAnalyzer()

# Get all sessions for a model
sessions = analyzer.query(model="claude-3.5")

# Filter by success and duration
fast_success = analyzer.query(
    success=True,
    max_duration=300  # 5 minutes
)

# Complex queries
results = analyzer.query_raw("""
    SELECT * FROM sessions 
    WHERE model LIKE 'claude%' 
    AND prompts < 5 
    AND success = true
""")
```

### Correlation Analysis

Find what affects performance:
```bash
# Correlate metrics
uv run benchmark/analyze.py --correlate "prompts" "duration"

# Factor analysis
uv run benchmark/analyze.py --factors
```

## Creating Reports

### Automated Reports

Generate comprehensive reports:
```bash
# Weekly summary
uv run benchmark/report.py --period week

# Model comparison report
uv run benchmark/report.py --type comparison

# Executive summary
uv run benchmark/report.py --type executive
```

### Custom Dashboards

Build your own dashboard:
```bash
# Start web dashboard
uv run benchmark/dashboard.py

# Access at http://localhost:8080
```

Dashboard features:
- Real-time session monitoring
- Interactive charts
- Model leaderboards
- Task completion matrix

## Interpreting Results

### What Good Looks Like

High-performing sessions typically show:
- **Duration**: Within estimated time
- **Prompts**: 1-3 for easy, 3-7 for medium
- **Code Quality**: Clean, minimal diffs
- **No Reversions**: Gets it right progressively

### Red Flags

Watch for these warning signs:
- **Timeout**: Session exceeds 3x estimate
- **Thrashing**: Multiple file edits/reversions
- **Context Loss**: Repeating same mistakes
- **Hallucination**: Creating unnecessary files

## Best Practices

### 1. Regular Analysis

- Review sessions daily during active testing
- Compare weekly aggregates
- Track improvement trends

### 2. Consistent Baselines

- Run same tasks periodically
- Use control tasks for calibration
- Document environment changes

### 3. Statistical Significance

- Collect 5+ sessions per model/task
- Use confidence intervals
- Account for variance

### 4. Context Awareness

Consider external factors:
- Time of day (API load)
- Network conditions
- Model updates
- Task familiarity

## Troubleshooting Metrics

### Missing Metrics

If metrics are incomplete:
```bash
# Verify session integrity
uv run benchmark/verify_session.py --session SESSION_ID

# Reconstruct from logs
uv run benchmark/reconstruct.py --session SESSION_ID

# Fill missing data
uv run benchmark/analyze.py --repair SESSION_ID
```

### Outlier Detection

Identify anomalous sessions:
```bash
# Automatic outlier detection
uv run benchmark/analyze.py --outliers

# Manual threshold
uv run benchmark/analyze.py --flag-if "duration > 600"
```

## Next Steps

1. Run multiple sessions for statistical significance
2. Create custom analysis scripts for your needs
3. Set up automated reporting
4. Share insights with the community

---

Questions? See our [FAQ](faq.md) or open an [issue](https://github.com/bdougie/vibe-check/issues).