# Task: Implement Recursive Dependency Resolver

**Difficulty**: Medium  
**Repo**: Your current project  
**Issue**: Create a system to automatically resolve model dependencies and optimal execution order  

## Problem Description
Some models depend on others:
- Model A requires Model B's embedding output
- Model C needs results from both A and B
- Circular dependencies must be detected
- Parallel execution where possible

## Requirements
Implement a dependency resolver that:
1. Parses dependency declarations
2. Builds a directed graph
3. Detects circular dependencies
4. Determines optimal execution order
5. Maximizes parallelization

## Input Format
```yaml
models:
  model_a:
    depends_on: [model_b]
  model_b:
    depends_on: []
  model_c:
    depends_on: [model_a, model_b]
  model_d:
    depends_on: [model_c]
```

## Challenges
- Handle circular dependency detection
- Optimize for minimal execution time
- Support optional dependencies
- Handle dependency failures gracefully
- Provide clear resolution paths

## Algorithm Requirements
- Use topological sorting
- Implement cycle detection
- Calculate critical path
- Support dynamic dependencies
- Handle partial failures

## Expected Outcome
- DependencyResolver class
- Graph visualization capability
- Execution plan generator
- Parallel execution support
- Clear error reporting

**Time Estimate**: 45-60 minutes

## Success Criteria
- [ ] Correctly builds dependency graph
- [ ] Detects all circular dependencies
- [ ] Generates optimal execution order
- [ ] Handles complex dependency chains
- [ ] Supports parallel execution
- [ ] Provides helpful debugging output