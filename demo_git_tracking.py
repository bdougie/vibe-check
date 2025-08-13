#!/usr/bin/env python3
"""
Demo script to show automatic git tracking in action.
This demonstrates the new automatic git diff tracking feature.
"""

from benchmark.metrics import BenchmarkMetrics
import tempfile
from pathlib import Path


def demo_git_tracking():
    """Demonstrate automatic git tracking functionality"""
    print("=" * 60)
    print("AUTOMATIC GIT TRACKING DEMO")
    print("=" * 60)
    
    # Create a metrics instance
    metrics = BenchmarkMetrics("demo_model", "demo_task")
    
    print("\n1. Starting task (captures initial git state)...")
    metrics.start_task()
    
    if metrics.initial_git_state:
        print(f"   ✓ Captured initial commit: {metrics.initial_git_state.get('commit', 'unknown')[:8]}")
        print(f"   ✓ Has uncommitted changes: {metrics.initial_git_state.get('has_uncommitted_changes', False)}")
    
    print("\n2. Simulating work...")
    print("   (In a real benchmark, the AI would modify files here)")
    
    # You could make actual file changes here to see them tracked
    # For example:
    # with open("test_file.txt", "w") as f:
    #     f.write("test content")
    
    print("\n3. Completing task (automatically captures git changes)...")
    result_file = metrics.complete_task(success=True)
    
    print(f"\n4. Results saved to: {result_file}")
    print(f"   ✓ Files modified: {metrics.metrics['files_modified']}")
    print(f"   ✓ Lines added: {metrics.metrics['lines_added']}")
    print(f"   ✓ Lines removed: {metrics.metrics['lines_removed']}")
    
    if metrics.metrics.get('git_diff_details'):
        print("\n5. Detailed changes:")
        for detail in metrics.metrics['git_diff_details']:
            print(f"   • {detail['filename']}: +{detail['lines_added']}/-{detail['lines_removed']}")
    else:
        print("\n5. No file changes detected (working directory is clean)")
    
    print("\n" + "=" * 60)
    print("Key Features:")
    print("  • Git state captured automatically at task start")
    print("  • Git diff captured automatically at task completion")
    print("  • No manual input required for git statistics")
    print("  • Detailed per-file change tracking")
    print("=" * 60)
    
    # Clean up
    if result_file.exists():
        result_file.unlink()
        print(f"\n(Demo file {result_file} cleaned up)")


if __name__ == "__main__":
    demo_git_tracking()