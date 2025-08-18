# Task: Implement Advanced Todo Application with Persistence and Categories

**Difficulty**: Hard  
**Repo**: Your current project  
**Issue**: Create a comprehensive todo application with advanced features in sample_project  

## Requirements
- Extend or create `sample_project/src/advanced_todo_app.py`
- Implement a full-featured todo system with categories, priorities, and persistence
- Add due dates, tags, and search functionality
- Include data validation and comprehensive error handling
- Create a command-line interface for interaction
- Add unit tests in `sample_project/tests/test_advanced_todo.py`

## Implementation Details
- Use JSON file for persistence (`todos.json`)
- Support multiple categories (work, personal, urgent)
- Priority levels (high, medium, low)
- Due date tracking with overdue notifications
- Tag system for flexible organization
- Search by title, tags, or category
- Bulk operations (mark multiple as complete, delete completed)
- Statistics method (total todos, completed percentage, overdue count)
- Import/export functionality
- Undo last operation feature

## Data Structure
Each todo should contain:
- id (auto-generated UUID)
- title (required, max 100 chars)
- description (optional, max 500 chars)
- category (required, from predefined list)
- priority (default: medium)
- tags (list of strings)
- due_date (optional, ISO format)
- created_at (auto-generated)
- completed_at (nullable)
- completed (boolean)

## CLI Commands
Implement these commands:
- add: Create new todo with interactive prompts
- list: Show todos with filtering options
- complete: Mark todo(s) as done
- delete: Remove todo(s)
- search: Find todos by criteria
- stats: Display statistics
- export: Save to CSV/JSON
- import: Load from file

## Expected Outcome
- Production-ready todo application
- Clean architecture with separation of concerns
- Comprehensive test coverage (>80%)
- Detailed documentation
- Performance optimization for large datasets
- Model demonstrates advanced planning and architecture skills

**Time Estimate**: 45-60 minutes

## Success Criteria
- [ ] All data structure fields implemented correctly
- [ ] Persistence layer working with JSON
- [ ] Category and priority systems functional
- [ ] Tag-based organization implemented
- [ ] Search functionality works across all fields
- [ ] Due date tracking with overdue detection
- [ ] Bulk operations implemented
- [ ] Statistics calculation accurate
- [ ] Import/export features working
- [ ] Undo functionality implemented
- [ ] CLI interface intuitive and complete
- [ ] Comprehensive error handling
- [ ] Unit tests with >80% coverage
- [ ] Performance handles 1000+ todos efficiently
- [ ] Code follows best practices and design patterns