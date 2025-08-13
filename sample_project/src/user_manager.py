"""
User management module with code needing refactoring.

HARD ISSUES:
- Massive god class that needs to be split
- Repeated code that should be DRY
- Poor separation of concerns
- Tightly coupled components
- No dependency injection
"""

import hashlib
import datetime
import re


class UserManager:
    """Monolithic user management class - needs refactoring.
    
    ISSUE: This is a god class doing too many things:
    - User CRUD operations
    - Authentication
    - Authorization
    - Session management
    - Email validation
    - Password management
    - Logging
    - Database operations
    """
    
    def __init__(self):
        self.users = {}
        self.sessions = {}
        self.logs = []
        self.db_connection = None  # Simulated DB connection
    
    # ISSUE: Repeated database code - should be extracted
    def create_user(self, username, email, password):
        """Create a new user."""
        # Repeated validation code
        if not username or len(username) < 3:
            self.logs.append(f"Invalid username: {username}")
            return False
        
        if not email or not self.validate_email(email):
            self.logs.append(f"Invalid email: {email}")
            return False
        
        if not password or len(password) < 8:
            self.logs.append(f"Invalid password length")
            return False
        
        # Repeated database simulation
        if self.db_connection is None:
            self.db_connection = "Connected"
        
        # User creation logic mixed with validation and logging
        user_id = len(self.users) + 1
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        self.users[username] = {
            'id': user_id,
            'username': username,
            'email': email,
            'password': hashed_password,
            'created_at': datetime.datetime.now(),
            'last_login': None,
            'is_active': True,
            'is_admin': False,
            'profile': {},
            'settings': {},
            'permissions': []
        }
        
        self.logs.append(f"User created: {username}")
        return True
    
    def update_user(self, username, updates):
        """Update user information."""
        # Repeated validation code
        if not username or username not in self.users:
            self.logs.append(f"User not found: {username}")
            return False
        
        # Repeated database simulation
        if self.db_connection is None:
            self.db_connection = "Connected"
        
        # Update logic mixed with validation
        user = self.users[username]
        
        if 'email' in updates:
            if not self.validate_email(updates['email']):
                self.logs.append(f"Invalid email: {updates['email']}")
                return False
            user['email'] = updates['email']
        
        if 'password' in updates:
            if len(updates['password']) < 8:
                self.logs.append(f"Invalid password length")
                return False
            user['password'] = hashlib.sha256(updates['password'].encode()).hexdigest()
        
        self.logs.append(f"User updated: {username}")
        return True
    
    def delete_user(self, username):
        """Delete a user."""
        # Repeated validation code
        if not username or username not in self.users:
            self.logs.append(f"User not found: {username}")
            return False
        
        # Repeated database simulation
        if self.db_connection is None:
            self.db_connection = "Connected"
        
        del self.users[username]
        self.logs.append(f"User deleted: {username}")
        return True
    
    def authenticate(self, username, password):
        """Authenticate a user."""
        # Authentication logic mixed with session management
        if username not in self.users:
            self.logs.append(f"Authentication failed: {username}")
            return None
        
        user = self.users[username]
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        
        if user['password'] != hashed_password:
            self.logs.append(f"Authentication failed: {username}")
            return None
        
        # Session management mixed with authentication
        session_id = hashlib.sha256(f"{username}{datetime.datetime.now()}".encode()).hexdigest()
        self.sessions[session_id] = {
            'username': username,
            'created_at': datetime.datetime.now(),
            'last_activity': datetime.datetime.now()
        }
        
        user['last_login'] = datetime.datetime.now()
        self.logs.append(f"User authenticated: {username}")
        return session_id
    
    def authorize(self, session_id, permission):
        """Check user authorization."""
        # Authorization mixed with session validation
        if session_id not in self.sessions:
            self.logs.append(f"Invalid session: {session_id}")
            return False
        
        session = self.sessions[session_id]
        username = session['username']
        user = self.users[username]
        
        # Complex authorization logic that should be separated
        if user['is_admin']:
            return True
        
        if permission in user['permissions']:
            return True
        
        self.logs.append(f"Authorization denied: {username} for {permission}")
        return False
    
    def validate_email(self, email):
        """Validate email format."""
        # Email validation that should be in a separate validator
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def get_user_profile(self, username):
        """Get user profile."""
        # Repeated validation
        if username not in self.users:
            self.logs.append(f"User not found: {username}")
            return None
        
        return self.users[username]['profile']
    
    def update_user_profile(self, username, profile_data):
        """Update user profile."""
        # Repeated validation
        if username not in self.users:
            self.logs.append(f"User not found: {username}")
            return False
        
        self.users[username]['profile'].update(profile_data)
        self.logs.append(f"Profile updated: {username}")
        return True
    
    def get_user_settings(self, username):
        """Get user settings."""
        # Repeated validation
        if username not in self.users:
            self.logs.append(f"User not found: {username}")
            return None
        
        return self.users[username]['settings']
    
    def update_user_settings(self, username, settings):
        """Update user settings."""
        # Repeated validation
        if username not in self.users:
            self.logs.append(f"User not found: {username}")
            return False
        
        self.users[username]['settings'].update(settings)
        self.logs.append(f"Settings updated: {username}")
        return True
    
    def cleanup_sessions(self):
        """Clean up expired sessions."""
        # Session management that should be in separate class
        current_time = datetime.datetime.now()
        expired = []
        
        for session_id, session in self.sessions.items():
            if (current_time - session['last_activity']).seconds > 3600:
                expired.append(session_id)
        
        for session_id in expired:
            del self.sessions[session_id]
            self.logs.append(f"Session expired: {session_id}")
    
    def get_logs(self):
        """Get all logs."""
        return self.logs
    
    def clear_logs(self):
        """Clear all logs."""
        self.logs = []
    
    def export_users(self):
        """Export all users."""
        # Export functionality that should be separate
        return list(self.users.values())
    
    def import_users(self, users_data):
        """Import users."""
        # Import functionality that should be separate
        for user_data in users_data:
            username = user_data['username']
            self.users[username] = user_data
        
        self.logs.append(f"Imported {len(users_data)} users")
        return True