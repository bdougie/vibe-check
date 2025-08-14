# Task: Debug and Fix Race Condition

**Difficulty**: Hard  
**Repo**: Your current project  
**Issue**: The batch_runner.py occasionally produces inconsistent results when running parallel tests  

## Problem Description
When running multiple models in parallel, some results are occasionally missing or overwritten. The issue appears intermittently and is hard to reproduce consistently. Investigation shows that file writing operations may be colliding.

## Requirements
- Identify the root cause of the race condition
- Implement proper thread-safe file operations
- Add appropriate locking mechanisms
- Ensure results are never lost or corrupted
- Maintain performance (don't serialize everything)

## Clues
- Issue occurs more frequently with faster models
- Results sometimes show data from wrong models
- File timestamps occasionally don't match execution order
- No explicit thread synchronization in current code

## Expected Outcome
- Race condition identified and documented
- Thread-safe solution implemented
- No data loss or corruption
- Minimal performance impact
- Clear explanation of the fix

**Time Estimate**: 45-60 minutes

## Success Criteria
- [ ] Root cause correctly identified
- [ ] Explanation demonstrates understanding of concurrency
- [ ] Solution uses appropriate synchronization
- [ ] Tests can run in parallel without issues
- [ ] Performance degradation < 10%
- [ ] Edge cases considered