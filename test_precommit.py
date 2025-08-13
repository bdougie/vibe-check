#!/usr/bin/env python3
"""
Test script to demonstrate pre-commit hook functionality
This file intentionally has some linting issues that ruff should catch/fix
"""

import os, sys # Multiple imports on one line (ruff will fix)

def poorly_formatted_function(x,y,z): # Missing spaces (ruff will fix)
    # Unused variable (ruff will catch)
    unused_var = "this is unused"
    
    result=x+y+z # Missing spaces (ruff will fix)
    return result

# Trailing whitespace on next line (ruff will fix)    


class TestClass:
    def __init__(self):
        pass
    
    def method_with_issues(self):
        # Using string concatenation instead of f-string (ruff will suggest)
        message = "Hello " + "world"
        
        # Using unnecessary comprehension (ruff will suggest)
        numbers = [x for x in range(10)]
        
        return message, numbers

if __name__ == "__main__":
    # Print statement without f-string (ruff will suggest)
    print("Testing pre-commit hooks")
    
    # Function call with poor formatting
    result = poorly_formatted_function(1,2,3)
    print("Result:", result)
    
    # Instantiate test class
    test = TestClass()
    msg, nums = test.method_with_issues()
    print("Message:", msg)
    print("Numbers:", nums)