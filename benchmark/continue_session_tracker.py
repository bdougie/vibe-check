#!/usr/bin/env python3
"""
Continue Session Tracker

Tracks and extracts metrics from Continue IDE extension session data.
"""

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
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

        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error reading sessions file: {e}")
            return None

    def load_session(self, session_id: str) -> Optional[Dict]:
        """Load a specific Continue session by ID."""
        session_file = self.sessions_dir / f"{session_id}.json"

        if not session_file.exists():
            logger.warning(f"Session file not found: {session_file}")
            return None

        try:
            with open(session_file, "r") as f:
                data = json.load(f)
                self.current_session_id = session_id
                self.session_data = data
                return data
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error reading session file: {e}")
            return None

    def extract_metrics(self) -> Dict:
        """Extract metrics from the loaded session data."""
        if not self.session_data:
            logger.warning("No session data loaded")
            return self.metrics

        # Reset metrics
        self.metrics = {
            "prompts_sent": 0,
            "tokens_generated": 0,
            "tokens_prompt": 0,
            "tool_calls": [],
            "messages": [],
            "session_duration": 0,
            "models_used": set(),
            "errors": [],
            "continue_session_id": self.current_session_id,
        }

        # Extract history items
        history = self.session_data.get("history", [])

        for item in history:
            if not isinstance(item, dict):
                continue

            # Count prompts (user messages)
            if item.get("role") == "user":
                self.metrics["prompts_sent"] += 1
                self.metrics["messages"].append(
                    {"role": "user", "content": item.get("content", "")[:100]}
                )

            # Count assistant responses
            elif item.get("role") == "assistant":
                content = item.get("content", "")
                self.metrics["messages"].append(
                    {"role": "assistant", "content": content[:100]}
                )

                # Track model used
                if "model" in item:
                    self.metrics["models_used"].add(item["model"])

            # Extract tool calls
            if "tool_calls" in item and isinstance(item["tool_calls"], list):
                for tool_call in item["tool_calls"]:
                    if isinstance(tool_call, dict):
                        self.metrics["tool_calls"].append(
                            {
                                "function": tool_call.get("function", {}).get(
                                    "name", "unknown"
                                ),
                                "id": tool_call.get("id"),
                            }
                        )

        # Convert set to list for JSON serialization
        self.metrics["models_used"] = list(self.metrics["models_used"])

        return self.metrics

    def get_token_usage_from_db(self, start_time: datetime = None) -> Dict:
        """Extract token usage metrics from Continue's SQLite database or JSONL files."""
        token_metrics = {
            "total_prompt_tokens": 0,
            "total_generated_tokens": 0,
            "total_requests": 0,
            "by_model": {},
        }
        
        # First try the SQLite database if it exists
        if self.devdata_db.exists():
            try:
                conn = sqlite3.connect(self.devdata_db)
                cursor = conn.cursor()
                
                # Check if the table exists
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='tokensGenerated'
                """)
                
                if cursor.fetchone():
                    # Table exists, query it
                    if not start_time:
                        start_time = datetime.now() - timedelta(hours=1)
                    
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
                else:
                    logger.debug("tokensGenerated table does not exist in SQLite database")
                    conn.close()
                    
            except sqlite3.Error as e:
                logger.debug(f"Could not query SQLite database: {e}")
        
        # Fallback to JSONL file if database doesn't work
        tokens_file = self.dev_data_dir / "0.2.0" / "tokensGenerated.jsonl"
        if tokens_file.exists():
            try:
                if not start_time:
                    start_time = datetime.now() - timedelta(hours=1)
                
                with open(tokens_file, "r") as f:
                    for line in f:
                        if line.strip():
                            try:
                                entry = json.loads(line)
                                # Check timestamp if available
                                entry_time = entry.get("timestamp", 0)
                                if entry_time >= start_time.timestamp():
                                    model = entry.get("model", "unknown")
                                    prompt_tokens = entry.get("promptTokens", 0)
                                    generated_tokens = entry.get("generatedTokens", 0)
                                    
                                    token_metrics["total_prompt_tokens"] += prompt_tokens
                                    token_metrics["total_generated_tokens"] += generated_tokens
                                    token_metrics["total_requests"] += 1
                                    
                                    if model not in token_metrics["by_model"]:
                                        token_metrics["by_model"][model] = {
                                            "prompt_tokens": 0,
                                            "generated_tokens": 0,
                                            "requests": 0,
                                        }
                                    
                                    token_metrics["by_model"][model]["prompt_tokens"] += prompt_tokens
                                    token_metrics["by_model"][model]["generated_tokens"] += generated_tokens
                                    token_metrics["by_model"][model]["requests"] += 1
                            except json.JSONDecodeError:
                                continue
                
                # Update main metrics
                self.metrics["tokens_prompt"] = token_metrics["total_prompt_tokens"]
                self.metrics["tokens_generated"] = token_metrics["total_generated_tokens"]
                
                logger.debug(f"Loaded token metrics from JSONL file: {token_metrics['total_requests']} requests")
                return token_metrics
                
            except IOError as e:
                logger.debug(f"Could not read tokensGenerated.jsonl: {e}")
        
        logger.debug("No token usage data available from Continue")
        return token_metrics

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

    def get_comprehensive_metrics(self) -> Dict:
        """Get all available metrics from session and database."""
        # Extract session metrics
        self.extract_metrics()

        # Add session duration
        self.metrics["session_duration"] = self.calculate_session_duration()

        # Add token usage from database
        token_metrics = self.get_token_usage_from_db()
        self.metrics["token_metrics"] = token_metrics

        # Parse event logs for additional insights
        quick_edits = self.parse_event_logs("quickEdit")
        self.metrics["quick_edits_count"] = len(quick_edits)

        autocompletes = self.parse_event_logs("autocomplete")
        self.metrics["autocompletes_count"] = len(autocompletes)

        return self.metrics


def find_active_continue_session() -> Optional[str]:
    """Find the most recent active Continue session."""
    tracker = ContinueSessionTracker()
    return tracker.find_latest_session()


def extract_metrics_from_continue(session_id: Optional[str] = None) -> Optional[Dict]:
    """Extract metrics from Continue session data.

    Args:
        session_id: Optional session ID. If not provided, uses the latest session.

    Returns:
        Dictionary of metrics or None if no session found.
    """
    tracker = ContinueSessionTracker()

    # Find session ID if not provided
    if not session_id:
        session_id = tracker.find_latest_session()

    if not session_id:
        logger.info("No Continue session found")
        return None

    # Load the session
    if not tracker.load_session(session_id):
        logger.warning(f"Could not load Continue session: {session_id}")
        return None

    # Get comprehensive metrics
    metrics = tracker.get_comprehensive_metrics()

    # Format for benchmark compatibility
    return {
        "continue_session_id": session_id,
        "prompts_sent": metrics.get("prompts_sent", 0),
        "tokens_generated": metrics.get("tokens_generated", 0),
        "tokens_prompt": metrics.get("tokens_prompt", 0),
        "tool_calls": len(metrics.get("tool_calls", [])),
        "human_interventions": 0,  # This would need manual tracking
        "chars_sent": sum(
            len(m.get("content", ""))
            for m in metrics.get("messages", [])
            if m.get("role") == "user"
        ),
        "chars_received": sum(
            len(m.get("content", ""))
            for m in metrics.get("messages", [])
            if m.get("role") == "assistant"
        ),
        "session_duration": metrics.get("session_duration", 0),
        "models_used": metrics.get("models_used", []),
        "quick_edits_count": metrics.get("quick_edits_count", 0),
        "autocompletes_count": metrics.get("autocompletes_count", 0),
    }


if __name__ == "__main__":
    # Test the tracker
    logging.basicConfig(level=logging.DEBUG)

    tracker = ContinueSessionTracker()
    session_id = tracker.find_latest_session()

    if session_id:
        print(f"Found session: {session_id}")
        tracker.load_session(session_id)
        metrics = tracker.get_comprehensive_metrics()
        print(json.dumps(metrics, indent=2, default=str))
    else:
        print("No Continue sessions found")