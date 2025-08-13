"""
Analytics module with performance issues and code duplication.

HARD ISSUES:
- Inefficient algorithms that need optimization
- Code duplication that needs DRY refactoring
- Poor data structure choices
"""


class Analytics:
    """Analytics processor with performance issues."""

    def __init__(self):
        self.data = []

    def calculate_mean(self, numbers):
        """Calculate mean - inefficient implementation.

        ISSUE: Recalculates sum every time, should cache or optimize.
        """
        if not numbers:
            return 0

        # Inefficient: Multiple passes through data
        total = 0
        count = 0
        for num in numbers:
            total += num
            count += 1

        return total / count

    def calculate_median(self, numbers):
        """Calculate median - inefficient sorting.

        ISSUE: Sorts entire list when we only need middle elements.
        """
        if not numbers:
            return 0

        # Inefficient: Full sort when we only need middle
        sorted_nums = sorted(numbers)
        n = len(sorted_nums)

        if n % 2 == 0:
            return (sorted_nums[n // 2 - 1] + sorted_nums[n // 2]) / 2
        else:
            return sorted_nums[n // 2]

    def find_duplicates_v1(self, items):
        """Find duplicates - O(n²) complexity.

        ISSUE: Nested loops create O(n²) complexity.
        """
        duplicates = []

        # Inefficient nested loops
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if items[i] == items[j] and items[i] not in duplicates:
                    duplicates.append(items[i])

        return duplicates

    def find_duplicates_v2(self, items):
        """Find duplicates - duplicate implementation.

        ISSUE: Duplicate of v1 with slight variation.
        """
        result = []

        # Almost identical to v1 - should be refactored
        for idx1 in range(len(items)):
            for idx2 in range(idx1 + 1, len(items)):
                if items[idx1] == items[idx2]:
                    if items[idx1] not in result:
                        result.append(items[idx1])

        return result

    def count_occurrences(self, items):
        """Count item occurrences - inefficient.

        ISSUE: Recreates count for each unique item.
        """
        counts = {}

        # Inefficient: Counts all items for each unique item
        unique_items = list(set(items))
        for item in unique_items:
            count = 0
            for element in items:
                if element == item:
                    count += 1
            counts[item] = count

        return counts

    def is_prime(self, n):
        """Check if number is prime - inefficient.

        ISSUE: Checks all numbers up to n-1.
        """
        if n < 2:
            return False

        # Inefficient: Should only check up to sqrt(n)
        for i in range(2, n):
            if n % i == 0:
                return False

        return True

    def find_primes(self, limit):
        """Find all primes up to limit - very inefficient.

        ISSUE: Rechecks each number independently.
        """
        primes = []

        # Inefficient: Should use Sieve of Eratosthenes
        for num in range(2, limit + 1):
            if self.is_prime(num):
                primes.append(num)

        return primes

    def fibonacci(self, n):
        """Calculate nth Fibonacci number - exponential complexity.

        ISSUE: Exponential time complexity due to recursion.
        """
        # Inefficient recursive implementation
        if n <= 1:
            return n
        return self.fibonacci(n - 1) + self.fibonacci(n - 2)

    def process_large_dataset(self, data):
        """Process large dataset - multiple inefficiencies.

        ISSUE: Multiple passes through data, poor memory usage.
        """
        results = {}

        # First pass - get unique values (inefficient)
        unique_values = []
        for item in data:
            if item not in unique_values:
                unique_values.append(item)

        # Second pass - count occurrences (redundant with count_occurrences)
        for value in unique_values:
            count = 0
            for item in data:
                if item == value:
                    count += 1
            results[value] = count

        # Third pass - calculate percentages (could be combined)
        total = len(data)
        percentages = {}
        for value, count in results.items():
            percentages[value] = (count / total) * 100

        return percentages
