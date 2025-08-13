#!/usr/bin/env python3
"""
Continue Session Tracker

Automatically extracts metrics from Continue's session data and telemetry,
eliminating the need for manual input during benchmarks.
"""

from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
import sqlite3
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ContinueSessionTracker:
    """Tracks and extracts metrics from Continue IDE extension session data."""

    def __init__(self):
        """Initialize the Continue session tracker."""
        self.continue_dir = Path.home() / ".continue"
        self.sessions_dir = self.continue_dir / "sessions"
        self.dev_data_dir = self.continue_dir / "dev_data"
        self.devdata_db = self.dev_data_dir / "devdata.sqlite"
        self.current_session_id = None
        self.session_data = None
        self.metrics = {
            "prompts_sent": 0,
            "tokens_generated": 0,
            "tokens_prompt": 0,
            "tool_calls": [],
            "messages": [],
            "session_duration": 0,
            "models_used": set(),
            "errors": [],
        }

    def find_latest_session(self) -> Optional[str]:
        """Find the most recent Continue session ID."""
        sessions_file = self.sessions_dir / "sessions.json"

        if not sessions_file.exists():
            logger.warning(f"Sessions file not found: {sessions_file}")
            return None

        try:
            with open(sessions_file, "r") as f:
                sessions = json.load(f)

            if not sessions:
                return None

            # Sessions are typically ordered by creation time
            # Get the most recent one
            latest_session = sessions[-1] if isinstance(sessions, list) else None

            if latest_session and isinstance(latest_session, dict):
                return latest_session.get("sessionId")

            return None

        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error reading sessions file: {e}")
            return None

    def load_session(self, session_id: str = None) -> bool:
        """Load a Continue session by ID or find the latest one."""
        if not session_id:
            session_id = self.find_latest_session()
            if not session_id:
                logger.warning("No Continue sessions found")
                return False

        session_file = self.sessions_dir / f"{session_id}.json"

        if not session_file.exists():
            logger.warning(f"Session file not found: {session_file}")
            return False

        try:
            with open(session_file, "r") as f:
                self.session_data = json.load(f)
                self.current_session_id = session_id

            logger.info(f"Loaded session: {session_id}")
            return True

        except json.JSONDecodeError as e:
            logger.error(f"Error loading session file: {e}")
            return False

    def parse_session_messages(self) -> Dict:
        """Parse messages and tool calls from the loaded session."""
        if not self.session_data:
            return self.metrics

        history = self.session_data.get("history", [])

        for item in history:
            if isinstance(item, dict):
                # Count user prompts
                if item.get("role") == "user":
                    self.metrics["prompts_sent"] += 1
                    self.metrics["messages"].append(
                        {
                            "role": "user",
                            "content": item.get("content", "")[:100],  # First 100 chars
                            "timestamp": item.get("timestamp"),
                        }
                    )

                # Count assistant responses
                elif item.get("role") == "assistant":
                    self.metrics["messages"].append(
                        {
                            "role": "assistant",
                            "content": item.get("content", "")[:100],
                            "timestamp": item.get("timestamp"),
                        }
                    )

                    # Extract model information if available
                    if "model" in item:
                        self.metrics["models_used"].add(item["model"])

                # Look for tool calls
                if "toolCalls" in item or "tool_calls" in item:
                    tool_calls = item.get("toolCalls") or item.get("tool_calls", [])
                    for tool_call in tool_calls:
                        self.metrics["tool_calls"].append(
                            {
                                "name": tool_call.get("function", {}).get(
                                    "name", "unknown"
                                ),
                                "arguments": tool_call.get("function", {}).get(
                                    "arguments", {}
                                ),
                                "id": tool_call.get("id"),
                            }
                        )

        # Convert set to list for JSON serialization
        self.metrics["models_used"] = list(self.metrics["models_used"])

        return self.metrics

    def get_token_usage_from_db(self, start_time: datetime = None) -> Dict:
        """Extract token usage metrics from Continue's SQLite database."""
        if not self.devdata_db.exists():
            logger.warning(f"DevData database not found: {self.devdata_db}")
            return {}

        try:
            conn = sqlite3.connect(self.devdata_db)
            cursor = conn.cursor()

            # If no start time provided, get data from last hour
            if not start_time:
                start_time = datetime.now() - timedelta(hours=1)

            # Query token usage data
            # The schema may vary, but typically includes:
            # model, provider, promptTokens, generatedTokens, timestamp
            query = """
                SELECT 
                    SUM(promptTokens) as total_prompt_tokens,
                    SUM(generatedTokens) as total_generated_tokens,
                    COUNT(*) as total_requests,
                    model
                FROM tokensGenerated
                WHERE timestamp >= ?
                GROUP BY model
            """

            cursor.execute(query, (start_time.timestamp(),))
            results = cursor.fetchall()

            token_metrics = {
                "total_prompt_tokens": 0,
                "total_generated_tokens": 0,
                "total_requests": 0,
                "by_model": {},
            }

            for row in results:
                prompt_tokens, generated_tokens, requests, model = row
                token_metrics["total_prompt_tokens"] += prompt_tokens or 0
                token_metrics["total_generated_tokens"] += generated_tokens or 0
                token_metrics["total_requests"] += requests or 0
                token_metrics["by_model"][model] = {
                    "prompt_tokens": prompt_tokens or 0,
                    "generated_tokens": generated_tokens or 0,
                    "requests": requests or 0,
                }

            conn.close()

            # Update main metrics
            self.metrics["tokens_prompt"] = token_metrics["total_prompt_tokens"]
            self.metrics["tokens_generated"] = token_metrics["total_generated_tokens"]

            return token_metrics

        except sqlite3.Error as e:
            logger.error(f"Error querying token database: {e}")
            return {}

    def parse_event_logs(self, event_name: str = "quickEdit") -> List[Dict]:
        """Parse JSONL event log files from Continue's dev_data directory."""
        event_file = self.dev_data_dir / "0.2.0" / f"{event_name}.jsonl"

        if not event_file.exists():
            logger.debug(f"Event log not found: {event_file}")
            return []

        events = []
        try:
            with open(event_file, "r") as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line))
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error reading event log {event_file}: {e}")

        return events

    def calculate_session_duration(self) -> float:
        """Calculate the duration of the session in seconds."""
        if not self.session_data or "history" not in self.session_data:
            return 0

        history = self.session_data["history"]
        if not history:
            return 0

        # Find first and last timestamps
        timestamps = []
        for item in history:
            if isinstance(item, dict) and "timestamp" in item:
                timestamps.append(item["timestamp"])

        if len(timestamps) >= 2:
            # Timestamps are usually in milliseconds
            duration_ms = max(timestamps) - min(timestamps)
            return duration_ms / 1000.0  # Convert to seconds

        return 0

    def extract_all_metrics(self, session_id: str = None) -> Dict:
        """Extract all available metrics from Continue session data."""
        # Load session
        if not self.load_session(session_id):
            logger.warning("Failed to load Continue session")
            return self.metrics

        # Parse messages and tool calls
        self.parse_session_messages()

        # Get token usage from database
        self.get_token_usage_from_db()

        # Calculate session duration
        self.metrics["session_duration"] = self.calculate_session_duration()

        # Parse additional event logs
        quick_edits = self.parse_event_logs("quickEdit")
        self.metrics["quick_edits"] = len(quick_edits)

        autocompletes = self.parse_event_logs("autocomplete")
        self.metrics["autocompletes"] = len(autocompletes)

        return self.metrics

    def get_human_interventions(self) -> int:
        """Estimate human interventions based on session data."""
        # Human interventions can be estimated by:
        # 1. Number of user messages after initial prompt
        # 2. Quick edits that modify AI suggestions
        # 3. Rejected autocomplete suggestions

        interventions = 0

        # Count user messages after the first one
        if self.metrics["prompts_sent"] > 1:
            interventions = self.metrics["prompts_sent"] - 1

        # Add quick edits as interventions
        interventions += self.metrics.get("quick_edits", 0)

        return interventions

    def export_metrics_for_benchmark(self) -> Dict:
        """Export metrics in format compatible with BenchmarkMetrics."""
        return {
            "prompts_sent": self.metrics["prompts_sent"],
            "chars_sent": self.metrics["tokens_prompt"]
            * 4,  # Approximate chars from tokens
            "chars_received": self.metrics["tokens_generated"] * 4,
            "human_interventions": self.get_human_interventions(),
            "tool_calls": len(self.metrics["tool_calls"]),
            "session_duration": self.metrics["session_duration"],
            "models_used": self.metrics["models_used"],
            "continue_session_id": self.current_session_id,
            "tokens_prompt": self.metrics["tokens_prompt"],
            "tokens_generated": self.metrics["tokens_generated"],
        }


def find_active_continue_session() -> Optional[str]:
    """Find the most recently active Continue session."""
    tracker = ContinueSessionTracker()
    return tracker.find_latest_session()


def extract_metrics_from_continue(session_id: str = None) -> Dict:
    """
    Extract benchmark metrics from Continue session data.

    Args:
        session_id: Optional Continue session ID. If not provided, uses latest session.

    Returns:
        Dictionary of metrics compatible with BenchmarkMetrics
    """
    tracker = ContinueSessionTracker()
    tracker.extract_all_metrics(session_id)
    return tracker.export_metrics_for_benchmark()


if __name__ == "__main__":
    # Demo/test the tracker
    import pprint

    print("🔍 Continue Session Tracker Demo")
    print("=" * 60)

    tracker = ContinueSessionTracker()

    # Find latest session
    session_id = tracker.find_latest_session()
    if session_id:
        print(f"Found session: {session_id}")

        # Extract metrics
        metrics = tracker.extract_all_metrics(session_id)

        print("\n📊 Extracted Metrics:")
        pprint.pprint(metrics, width=100)

        print("\n📈 Benchmark Export:")
        benchmark_metrics = tracker.export_metrics_for_benchmark()
        pprint.pprint(benchmark_metrics, width=100)
    else:
        print(
            "No Continue sessions found. Make sure Continue is installed and has been used."
        )
        print(f"Looking in: {tracker.sessions_dir}")
