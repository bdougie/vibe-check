#!/usr/bin/env python3
"""
Reset the sample project to its original state with all intentional issues.

This script restores the sample project files to their original state,
allowing repeated benchmark testing with consistent starting conditions.
"""

from pathlib import Path
import shutil
import subprocess


def reset_sample_project():
    """Reset the sample project to original state."""
    print("Resetting sample project to original state...")
    
    project_dir = Path("sample_project")
    
    # Check if we're in the right directory
    if not project_dir.exists():
        print("Error: sample_project directory not found!")
        print("Please run this script from the vibe-check root directory.")
        return False
    
    # Use git to reset if in a git repo
    try:
        # Check if sample_project is tracked by git
        result = subprocess.run(
            ["git", "ls-files", "sample_project"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.stdout:
            # Files are tracked, use git to reset
            print("Using git to reset sample project files...")
            subprocess.run(
                ["git", "checkout", "HEAD", "--", "sample_project"],
                check=True
            )
            print("✓ Sample project reset using git")
            return True
    except subprocess.CalledProcessError:
        pass
    except FileNotFoundError:
        pass
    
    # If git reset didn't work, recreate from backup
    backup_dir = Path("sample_project_backup")
    
    if backup_dir.exists():
        print("Restoring from backup...")
        shutil.rmtree(project_dir)
        shutil.copytree(backup_dir, project_dir)
        print("✓ Sample project restored from backup")
        return True
    
    print("Warning: No backup found. Creating backup from current state...")
    shutil.copytree(project_dir, backup_dir)
    print("✓ Backup created at sample_project_backup/")
    print("  The current state has been preserved as the 'original'.")
    return True


def create_backup():
    """Create a backup of the sample project."""
    project_dir = Path("sample_project")
    backup_dir = Path("sample_project_backup")
    
    if not project_dir.exists():
        print("Error: sample_project directory not found!")
        return False
    
    if backup_dir.exists():
        print("Backup already exists. Overwrite? (y/n): ", end="")
        response = input().strip().lower()
        if response != 'y':
            print("Backup cancelled.")
            return False
        shutil.rmtree(backup_dir)
    
    shutil.copytree(project_dir, backup_dir)
    print("✓ Backup created at sample_project_backup/")
    return True


def main():
    """Main entry point."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--backup":
        create_backup()
    else:
        reset_sample_project()
        print("\nSample project is ready for benchmark testing!")
        print("All intentional issues have been restored.")


if __name__ == "__main__":
    main()