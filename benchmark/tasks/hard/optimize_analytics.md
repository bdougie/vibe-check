# Task: Optimize Analytics Performance

**Difficulty**: Hard
**Issue**: The Analytics class contains inefficient algorithms and duplicate code.

## Requirements
- Optimize `find_duplicates` from O(n²) to O(n) complexity
- Remove duplicate implementation (v1 and v2)
- Optimize `is_prime()` to check only up to sqrt(n)
- Implement Sieve of Eratosthenes for `find_primes()`
- Fix `fibonacci()` exponential complexity with memoization or iteration
- Refactor `process_large_dataset()` to minimize passes through data

## File Location
`sample_project/src/analytics.py`

## Expected Outcome
- Significantly improved performance for all functions
- No duplicate code
- Efficient algorithms implemented
- Memory usage optimized

**Time Estimate**: 1-3 hours

## Success Criteria
- [ ] `find_duplicates()` runs in O(n) time
- [ ] Duplicate implementation removed
- [ ] `is_prime()` only checks up to sqrt(n)
- [ ] `find_primes()` uses Sieve of Eratosthenes
- [ ] `fibonacci()` uses memoization or iteration
- [ ] `process_large_dataset()` makes single pass through data
- [ ] All functions produce correct results
- [ ] Performance improvements are measurable