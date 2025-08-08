# Task: Add JSON Export Feature

**Difficulty**: Medium  
**Repo**: Your current project  
**Issue**: Add ability to export aggregated benchmark results to a single JSON file  

## Requirements
- Create a function to aggregate all results
- Include summary statistics in the export
- Add command line option to trigger export
- Format JSON output for readability

## Implementation Details
- Add `--export-json` flag to analyze.py
- Aggregate results by model and task
- Calculate statistics (mean, median, std dev)
- Include timestamp and version info
- Pretty-print JSON with proper indentation

## Expected Outcome
- New export functionality works correctly
- JSON output is well-structured and readable
- Statistics are accurately calculated
- Command line interface is intuitive

**Time Estimate**: 20-40 minutes

## Success Criteria
- [ ] Export function implemented
- [ ] Statistics calculation correct
- [ ] JSON format is clean and readable
- [ ] Command line flag works properly
- [ ] Error handling for edge cases
- [ ] Documentation updated if needed