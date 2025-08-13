"""
Data processing module with issues for medium-level tasks.

MEDIUM ISSUES:
- Missing input validation in process_data()
- No error handling in load_csv()
- Missing type hints throughout
- No bounds checking in get_percentile()
"""

import csv
import json


class DataProcessor:
    """Process various data formats."""

    def __init__(self):
        self.data = []

    def process_data(self, data):
        """Process raw data.

        ISSUE: No validation of input data type or structure.
        """
        # Missing validation - should check if data is list
        # Should check for empty data
        # Should validate data format
        self.data = data
        return len(data)

    def load_csv(self, filepath):
        """Load data from CSV file.

        ISSUE: No error handling for file operations.
        """
        # Missing try/except block
        # No validation of file existence
        # No handling of CSV parsing errors
        with open(filepath, "r") as file:
            reader = csv.DictReader(file)
            self.data = list(reader)
        return self.data

    def save_json(self, filepath):
        """Save data to JSON file.

        ISSUE: No validation or error handling.
        """
        # Missing validation of self.data
        # No error handling for file write
        with open(filepath, "w") as file:
            json.dump(self.data, file)

    def filter_data(self, key, value):
        """Filter data by key-value pair.

        ISSUE: No validation of key existence.
        """
        # Should check if key exists in data items
        # Should handle non-dict items in data
        return [item for item in self.data if item[key] == value]

    def get_percentile(self, values, percentile):
        """Calculate percentile from values.

        ISSUE: No bounds checking for percentile value.
        """
        # Should validate percentile is between 0 and 100
        # Should check if values is non-empty
        # Missing proper percentile calculation
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[index]

    def merge_data(self, other_data):
        """Merge another dataset with current data.

        ISSUE: No type checking or validation.
        """
        # Should validate other_data is compatible type
        # Should handle None case
        self.data.extend(other_data)
        return len(self.data)
