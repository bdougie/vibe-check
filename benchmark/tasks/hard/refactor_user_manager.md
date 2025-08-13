# Task: Refactor User Manager God Class

**Difficulty**: Hard
**Issue**: The UserManager class is a god class that violates single responsibility principle.

## Requirements
- Split UserManager into multiple focused classes:
  - UserRepository: Handle CRUD operations
  - AuthenticationService: Handle authentication logic
  - SessionManager: Manage sessions
  - UserValidator: Handle validation logic
- Eliminate code duplication
- Implement dependency injection where appropriate
- Maintain all existing functionality
- Follow SOLID principles

## File Location
`sample_project/src/user_manager.py`

## Expected Outcome
- Multiple smaller, focused classes
- Clear separation of concerns
- No repeated code (DRY principle)
- Improved testability
- Better maintainability

**Time Estimate**: 1-2 hours

## Success Criteria
- [ ] God class is split into at least 3-4 focused classes
- [ ] Each class has a single, clear responsibility
- [ ] Repeated validation code is extracted
- [ ] Repeated database code is extracted
- [ ] Dependencies are injected, not hardcoded
- [ ] All original functionality still works
- [ ] Code follows Python best practices
- [ ] Classes are properly documented