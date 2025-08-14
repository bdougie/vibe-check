# Task: Optimize Complex Algorithm

**Difficulty**: Hard  
**Repo**: Your current project  
**Issue**: The analyze.py comparison algorithm has O(n³) complexity and becomes slow with many models  

## Problem Description
The current implementation compares every model against every other model for each metric, resulting in cubic time complexity. With 20+ models, analysis takes several minutes. The algorithm needs optimization while maintaining accuracy.

## Current Algorithm Issues
- Nested loops iterate through all models multiple times
- Redundant calculations for symmetric comparisons
- No caching of intermediate results
- Memory usage grows quadratically

## Requirements
- Reduce time complexity to O(n²) or better
- Maintain exact same output format
- Handle edge cases (single model, missing data)
- Document the optimization approach
- Prove correctness of the new algorithm

## Constraints
- Cannot use external libraries not already in project
- Must maintain backward compatibility
- Results must be deterministic
- Memory usage should not exceed O(n²)

## Expected Outcome
- Algorithm complexity reduced significantly
- Performance improvement measurable
- Clear documentation of approach
- Mathematical proof or explanation of correctness
- Benchmarks showing improvement

**Time Estimate**: 60-90 minutes

## Success Criteria
- [ ] Correct complexity analysis of current code
- [ ] New algorithm has better complexity
- [ ] Results remain identical
- [ ] Edge cases handled properly
- [ ] Clear explanation of optimization
- [ ] Performance benchmarks provided