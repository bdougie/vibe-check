# Planted Issues Documentation

This document lists all intentional issues in the sample project for AI benchmarking.

## Easy Tasks (2-5 minutes)

### 1. Fix Typos in calculator.py
**File**: `src/calculator.py`
**Issues**:
- Line 16: "paramter" → "parameter"
- Line 25: "reuslt" → "result" (appears twice)
- Line 39: "Divsion" → "Division"

### 2. Add .gitignore Entry
**File**: `.gitignore`
**Task**: Add common entries that are missing (e.g., `.DS_Store`, `Thumbs.db`)

## Medium Tasks (15-30 minutes)

### 3. Add Input Validation to calculator.py
**File**: `src/calculator.py`
**Function**: `divide()`
**Issue**: No check for division by zero
**Fix**: Add validation to prevent ZeroDivisionError

### 4. Add Input Validation to calculator.py
**File**: `src/calculator.py`
**Function**: `power()`
**Issue**: No validation for negative exponents with zero base
**Fix**: Add appropriate validation

### 5. Add Validation to data_processor.py
**File**: `src/data_processor.py`
**Function**: `process_data()`
**Issues**:
- No type checking for input data
- No validation for empty data
- No format validation

### 6. Add Error Handling to data_processor.py
**File**: `src/data_processor.py`
**Function**: `load_csv()`
**Issues**:
- No try/except for file operations
- No validation of file existence
- No handling of CSV parsing errors

### 7. Add Validation to data_processor.py
**File**: `src/data_processor.py`
**Function**: `filter_data()`
**Issue**: No check if key exists in data items

### 8. Add Bounds Checking to data_processor.py
**File**: `src/data_processor.py`
**Function**: `get_percentile()`
**Issues**:
- No validation that percentile is between 0-100
- No check for empty values list
- Incorrect percentile calculation (off-by-one)

### 9. Add Type Hints
**File**: `src/data_processor.py`
**Issue**: Missing type hints throughout the module
**Fix**: Add proper type hints to all functions

## Hard Tasks (1-3 hours)

### 10. Refactor God Class
**File**: `src/user_manager.py`
**Class**: `UserManager`
**Issues**:
- Massive god class doing too many things
- Should be split into:
  - UserRepository (CRUD operations)
  - AuthenticationService (auth logic)
  - SessionManager (session handling)
  - UserValidator (validation logic)
  - UserLogger (logging)
**Additional Issues**:
- Repeated validation code (DRY violation)
- Repeated database simulation code
- Mixed concerns throughout
- No dependency injection

### 11. Optimize Performance in analytics.py
**File**: `src/analytics.py`
**Function**: `find_duplicates_v1()` and `find_duplicates_v2()`
**Issues**:
- O(n²) complexity with nested loops
- Duplicate implementations (v1 and v2 nearly identical)
**Fix**: 
- Refactor to use set or dict for O(n) complexity
- Remove duplicate implementation

### 12. Optimize Prime Number Functions
**File**: `src/analytics.py`
**Functions**: `is_prime()` and `find_primes()`
**Issues**:
- `is_prime()`: Checks all numbers up to n-1 (should check up to sqrt(n))
- `find_primes()`: Should use Sieve of Eratosthenes algorithm
**Fix**: Implement efficient algorithms

### 13. Optimize Fibonacci Function
**File**: `src/analytics.py`
**Function**: `fibonacci()`
**Issue**: Exponential time complexity due to naive recursion
**Fix**: Use memoization or iterative approach

### 14. Refactor process_large_dataset()
**File**: `src/analytics.py`
**Function**: `process_large_dataset()`
**Issues**:
- Multiple unnecessary passes through data
- Poor memory usage
- Redundant counting logic
**Fix**: Combine passes, use Counter from collections

### 15. Remove Code Duplication
**File**: `src/analytics.py`
**Functions**: `calculate_mean()`, `count_occurrences()`
**Issues**:
- Inefficient implementations
- Could use built-in functions or numpy
**Fix**: Optimize or use standard library

## Testing Approach

1. **Easy tasks**: Should be completable with 1-2 prompts
2. **Medium tasks**: May require 3-5 prompts with some back-and-forth
3. **Hard tasks**: Will require multiple prompts, planning, and iterative refinement

## Success Criteria

For each task:
- [ ] Issue is correctly identified
- [ ] Fix is properly implemented
- [ ] No new bugs introduced
- [ ] Code follows Python conventions
- [ ] Tests pass (if applicable)

## Notes

- All issues are intentional and should NOT be fixed in the main sample_project
- Use `reset_sample_project.py` to restore original state after testing
- Each benchmark run should start from the original state
- Track which issues the AI successfully identifies and fixes