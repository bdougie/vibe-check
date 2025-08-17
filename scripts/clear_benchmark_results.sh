#!/bin/bash

# Script to clear benchmark results
echo "Clearing benchmark results..."

# Remove all result directories and files in benchmark/results/
if [ -d "./benchmark/results" ]; then
    rm -rf ./benchmark/results/*
    echo "✓ Cleared benchmark/results/ directory"
else
    echo "⚠ benchmark/results/ directory not found"
fi

# Remove the results summary CSV file
if [ -f "./benchmark/results_summary.csv" ]; then
    rm -f ./benchmark/results_summary.csv
    echo "✓ Removed results_summary.csv"
else
    echo "⚠ results_summary.csv not found"
fi

echo "Done! All benchmark results have been cleared."