"""
Calculator module with intentional issues for benchmarking.

EASY ISSUES:
- Line 12: Typo in docstring "paramter" should be "parameter"
- Line 25: Typo in variable name "reuslt" should be "result"
- Line 38: Typo in comment "Divsion" should be "Division"
"""


class Calculator:
    """Basic calculator with arithmetic operations."""

    def add(self, a, b):
        """Add two numbers.

        Args:
            a: First paramter  # TYPO: Should be "parameter"
            b: Second parameter

        Returns:
            Sum of a and b
        """
        return a + b

    def subtract(self, a, b):
        """Subtract b from a."""
        reuslt = a - b  # TYPO: Should be "result"
        return reuslt

    def multiply(self, a, b):
        """Multiply two numbers.

        Args:
            a: First number
            b: Second number

        Returns:
            Product of a and b
        """
        return a * b

    def divide(self, a, b):
        """Divsion operation."""  # TYPO: Should be "Division"
        # No validation - intentional issue for medium task
        return a / b

    def power(self, base, exponent):
        """Calculate base raised to exponent.

        Missing input validation - intentional for medium task.
        """
        return base**exponent

    def factorial(self, n):
        """Calculate factorial of n.

        Inefficient implementation - intentional for hard task.
        """
        if n == 0:
            return 1
        result = 1
        for i in range(1, n + 1):
            result *= i
        return result
