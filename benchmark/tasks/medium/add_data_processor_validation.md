# Task: Add Data Processor Validation

**Difficulty**: Medium
**Issue**: The DataProcessor class lacks input validation and error handling.

## Requirements
- Add validation to `process_data()` to check data type and structure
- Add error handling to `load_csv()` for file operations
- Add validation to `filter_data()` to check if key exists
- Add bounds checking to `get_percentile()` for percentile value

## File Location
`sample_project/src/data_processor.py`

## Expected Outcome
- All functions properly validate their inputs
- Appropriate exceptions are raised for invalid inputs
- File operations are wrapped in try/except blocks
- Functions provide helpful error messages

**Time Estimate**: 20-30 minutes

## Success Criteria
- [ ] `process_data()` validates input is a list
- [ ] `load_csv()` handles file not found and parsing errors
- [ ] `filter_data()` checks if key exists before filtering
- [ ] `get_percentile()` validates percentile is between 0-100
- [ ] All validations raise appropriate exceptions
- [ ] Error messages are descriptive and helpful