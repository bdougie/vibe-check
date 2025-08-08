# Task: Add Input Validation

**Difficulty**: Medium  
**Repo**: Your current project  
**Issue**: Add validation to the task_runner.py to ensure proper inputs  

## Requirements
- Validate that model_name is not empty
- Validate that task_file exists and is readable
- Add proper error messages for invalid inputs
- Handle edge cases gracefully

## Implementation Details
- Check model_name for valid characters (alphanumeric, dash, underscore)
- Verify task_file path exists and has .md extension
- Provide helpful error messages guiding users to correct usage
- Add validation for numeric inputs (prompts, interventions)

## Expected Outcome
- Robust input validation in place
- Clear error messages for users
- Script handles invalid inputs gracefully
- No crashes on unexpected input

**Time Estimate**: 15-30 minutes

## Success Criteria
- [ ] Model name validation implemented
- [ ] Task file validation implemented
- [ ] Numeric input validation added
- [ ] Error messages are clear and helpful
- [ ] Edge cases handled properly
- [ ] Tested with various invalid inputs