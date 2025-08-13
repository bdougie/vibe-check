from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import time
import uuid
import warnings


class BenchmarkMetrics:
    def __init__(self, model_name, task_name):
        self.model_name = model_name
        self.task_name = task_name
        self.start_time = None
        self.initial_git_state = None
        self.metrics = {
            "model": model_name,
            "task": task_name,
            "prompts_sent": 0,
            "chars_sent": 0,
            "chars_received": 0,
            "human_interventions": 0,
            "task_completed": False,
            "completion_time": 0,
            "files_modified": 0,
            "lines_added": 0,
            "lines_removed": 0,
            "git_diff_details": [],
            "session_log": [],
        }

    def start_task(self):
        self.start_time = time.time()
        self.capture_initial_git_state()
        self.log_event("task_started")

    def log_prompt(self, prompt_text, response_text):
        self.metrics["prompts_sent"] += 1
        self.metrics["chars_sent"] += len(prompt_text)
        self.metrics["chars_received"] += len(response_text)
        self.log_event(
            "prompt_sent",
            {"prompt_length": len(prompt_text), "response_length": len(response_text)},
        )

    def log_human_intervention(self, intervention_type):
        self.metrics["human_interventions"] += 1
        self.log_event("human_intervention", {"type": intervention_type})

    def capture_initial_git_state(self):
        """Capture the initial git state when benchmark starts"""
        try:
            # Get current commit hash with timeout
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            commit_hash = result.stdout.strip() if result.returncode == 0 else None

            # Check for uncommitted changes with timeout
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )
            has_uncommitted = (
                bool(result.stdout.strip()) if result.returncode == 0 else False
            )

            self.initial_git_state = {
                "commit": commit_hash,
                "has_uncommitted_changes": has_uncommitted,
                "timestamp": time.time(),
            }

            self.log_event("git_state_captured", self.initial_git_state)
        except subprocess.TimeoutExpired as e:
            self.log_event(
                "git_state_capture_failed",
                {
                    "error": "Command timed out",
                    "command": e.cmd,
                    "timeout": e.timeout,
                    "working_dir": os.getcwd(),
                },
            )
        except Exception as e:
            self.log_event(
                "git_state_capture_failed",
                {"error": str(e), "working_dir": os.getcwd()},
            )

    def get_git_diff_stats(self):
        """Get git diff statistics for modified files"""
        try:
            # Get detailed diff stats with timeout
            result = subprocess.run(
                ["git", "diff", "--stat"],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )

            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split("\n")
                # Check for both singular and plural forms
                if lines and (
                    "file changed" in lines[-1] or "files changed" in lines[-1]
                ):
                    # Parse the summary line
                    summary = lines[-1]
                    files_modified = 0
                    lines_added = 0
                    lines_removed = 0

                    parts = summary.split(",")
                    for part_item in parts:
                        part_item = part_item.strip()
                        if "file" in part_item:
                            files_modified = int(part_item.split()[0])
                        elif "insertion" in part_item:
                            lines_added = int(part_item.split()[0])
                        elif "deletion" in part_item:
                            lines_removed = int(part_item.split()[0])

                    return files_modified, lines_added, lines_removed
        except subprocess.TimeoutExpired as e:
            self.log_event(
                "git_diff_stats_error",
                {
                    "error": "Command timed out",
                    "command": e.cmd,
                    "timeout": e.timeout,
                    "working_dir": os.getcwd(),
                },
            )
        except Exception as e:
            self.log_event(
                "git_diff_stats_error",
                {
                    "error": str(e),
                    "command": "git diff --stat",
                    "working_dir": os.getcwd(),
                },
            )

        return 0, 0, 0

    def get_detailed_git_diff(self):
        """Get detailed git diff information for each file"""
        try:
            # Get list of modified files with stats with timeout
            result = subprocess.run(
                ["git", "diff", "--numstat"],
                capture_output=True,
                text=True,
                check=False,
                timeout=30,
            )

            if result.returncode == 0 and result.stdout:
                diff_details = []
                for line in result.stdout.strip().split("\n"):
                    if line:
                        parts = line.split("\t")
                        if len(parts) >= 3:  # Validate we have enough parts
                            added, removed, filename = parts[:3]  # Take only first 3
                            try:
                                # Handle binary files and invalid numbers
                                added = 0 if added == "-" else int(added)
                                removed = 0 if removed == "-" else int(removed)
                                diff_details.append(
                                    {
                                        "filename": filename,
                                        "lines_added": added,
                                        "lines_removed": removed,
                                    }
                                )
                            except ValueError as e:
                                # Log but continue processing other files
                                self.log_event(
                                    "git_parse_error",
                                    {"error": str(e), "line": line, "parts": parts},
                                )
                return diff_details
        except subprocess.TimeoutExpired as e:
            self.log_event(
                "detailed_diff_error",
                {
                    "error": "Command timed out",
                    "command": e.cmd,
                    "timeout": e.timeout,
                    "working_dir": os.getcwd(),
                },
            )
        except Exception as e:
            self.log_event(
                "detailed_diff_error",
                {
                    "error": str(e),
                    "command": "git diff --numstat",
                    "working_dir": os.getcwd(),
                },
            )

        return []

    def capture_final_git_state(self):
        """Automatically capture git changes when task completes"""
        # Get basic stats
        files_modified, lines_added, lines_removed = self.get_git_diff_stats()

        # Get detailed diff
        diff_details = self.get_detailed_git_diff()

        # Update metrics
        self.metrics["files_modified"] = files_modified
        self.metrics["lines_added"] = lines_added
        self.metrics["lines_removed"] = lines_removed
        self.metrics["git_diff_details"] = diff_details

        # Log the automatic capture
        self.log_event(
            "git_stats_auto_captured",
            {
                "files": files_modified,
                "added": lines_added,
                "removed": lines_removed,
                "details": diff_details,
            },
        )

        return files_modified, lines_added, lines_removed

    def import_continue_session_metrics(self, session_id=None):
        """Import metrics from Continue session data if available."""
        try:
            from benchmark.continue_session_tracker import extract_metrics_from_continue

            continue_metrics = extract_metrics_from_continue(session_id)

            if continue_metrics:
                # Update metrics with Continue data
                self.metrics["prompts_sent"] = continue_metrics.get(
                    "prompts_sent", self.metrics["prompts_sent"]
                )
                self.metrics["chars_sent"] = continue_metrics.get(
                    "chars_sent", self.metrics["chars_sent"]
                )
                self.metrics["chars_received"] = continue_metrics.get(
                    "chars_received", self.metrics["chars_received"]
                )
                self.metrics["human_interventions"] = continue_metrics.get(
                    "human_interventions", self.metrics["human_interventions"]
                )
                self.metrics["continue_session_id"] = continue_metrics.get(
                    "continue_session_id"
                )
                self.metrics["tokens_prompt"] = continue_metrics.get("tokens_prompt", 0)
                self.metrics["tokens_generated"] = continue_metrics.get(
                    "tokens_generated", 0
                )
                self.metrics["tool_calls"] = continue_metrics.get("tool_calls", 0)

                self.log_event("continue_metrics_imported", continue_metrics)
                return True
        except ImportError:
            self.log_event("continue_import_failed", {"error": "Module not found"})
        except Exception as e:
            self.log_event("continue_import_error", {"error": str(e)})

        return False

    def complete_task(self, success=True, auto_import_continue=True):
        if self.start_time:
            self.metrics["completion_time"] = time.time() - self.start_time

        # Try to import Continue session metrics automatically
        if auto_import_continue:
            self.import_continue_session_metrics()

        # Automatically capture git changes before completing
        self.capture_final_git_state()

        self.metrics["task_completed"] = success
        self.metrics["initial_git_state"] = self.initial_git_state
        self.metrics["duration_seconds"] = self.metrics.get("completion_time", 0)
        self.log_event("task_completed", {"success": success})

        # Save results with UUID to prevent collisions
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        results_dir = Path("benchmark/results")
        results_dir.mkdir(parents=True, exist_ok=True)

        filename = (
            results_dir
            / f"{self.model_name}_{self.task_name}_{timestamp}_{unique_id}.json"
        )

        with filename.open("w") as f:
            json.dump(self.metrics, f, indent=2)

        return filename

    def log_event(self, event_type, data=None):
        event = {"timestamp": time.time(), "event": event_type, "data": data or {}}
        self.metrics["session_log"].append(event)

    def update_git_stats(self, files_modified, lines_added, lines_removed):
        """Update git statistics manually (deprecated - stats are now captured automatically)"""
        warnings.warn(
            "update_git_stats is deprecated. Git statistics are now captured automatically "
            "when complete_task() is called. This method will be removed in a future version.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.metrics["files_modified"] = files_modified
        self.metrics["lines_added"] = lines_added
        self.metrics["lines_removed"] = lines_removed
        self.log_event(
            "git_stats_updated",
            {"files": files_modified, "added": lines_added, "removed": lines_removed},
        )
