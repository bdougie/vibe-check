#!/usr/bin/env python3
"""
Test suite for benchmark/continue_session_tracker.py
Specifically tests the fixes for graceful database handling
"""

from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from benchmark.continue_session_tracker import (
    ContinueSessionTracker,
    extract_metrics_from_continue,
    find_active_continue_session,
)


class TestContinueSessionTracker:
    """Test cases for ContinueSessionTracker class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.tracker = ContinueSessionTracker()

        # Override paths to use temp directory
        self.tracker.continue_dir = Path(self.temp_dir) / ".continue"
        self.tracker.sessions_dir = self.tracker.continue_dir / "sessions"
        self.tracker.dev_data_dir = self.tracker.continue_dir / "dev_data"
        self.tracker.devdata_db = self.tracker.dev_data_dir / "devdata.sqlite"

        # Create directory structure
        self.tracker.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.tracker.dev_data_dir.mkdir(parents=True, exist_ok=True)
        (self.tracker.dev_data_dir / "0.2.0").mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clean up after tests."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_init(self):
        """Test tracker initialization."""
        tracker = ContinueSessionTracker()
        assert tracker.continue_dir == Path.home() / ".continue"
        assert tracker.current_session_id is None
        assert tracker.session_data is None
        assert tracker.metrics["prompts_sent"] == 0

    def test_find_latest_session_no_file(self):
        """Test finding session when sessions.json doesn't exist."""
        result = self.tracker.find_latest_session()
        assert result is None

    def test_find_latest_session_empty_file(self):
        """Test finding session with empty sessions.json."""
        sessions_file = self.tracker.sessions_dir / "sessions.json"
        with open(sessions_file, "w") as f:
            json.dump([], f)

        result = self.tracker.find_latest_session()
        assert result is None

    def test_find_latest_session_valid(self):
        """Test finding latest session with valid data."""
        sessions_file = self.tracker.sessions_dir / "sessions.json"
        sessions_data = [
            {"sessionId": "session-1", "timestamp": 1000},
            {"sessionId": "session-2", "timestamp": 2000},
            {"sessionId": "session-3", "timestamp": 3000},
        ]
        with open(sessions_file, "w") as f:
            json.dump(sessions_data, f)

        result = self.tracker.find_latest_session()
        assert result == "session-3"

    def test_load_session_not_found(self):
        """Test loading a session that doesn't exist."""
        result = self.tracker.load_session("nonexistent")
        assert result is None

    def test_load_session_valid(self):
        """Test loading a valid session."""
        session_id = "test-session"
        session_data = {
            "sessionId": session_id,
            "history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ],
        }

        session_file = self.tracker.sessions_dir / f"{session_id}.json"
        with open(session_file, "w") as f:
            json.dump(session_data, f)

        result = self.tracker.load_session(session_id)
        assert result is not None
        assert self.tracker.current_session_id == session_id
        assert self.tracker.session_data == session_data

    def test_extract_metrics_no_session(self):
        """Test extracting metrics without loaded session."""
        metrics = self.tracker.extract_metrics()
        assert metrics["prompts_sent"] == 0
        assert "continue_session_id" not in metrics

    def test_extract_metrics_with_session(self):
        """Test extracting metrics from loaded session."""
        self.tracker.session_data = {
            "history": [
                {"role": "user", "content": "Test prompt 1"},
                {"role": "assistant", "content": "Response 1", "model": "gpt-4"},
                {"role": "user", "content": "Test prompt 2"},
                {"role": "assistant", "content": "Response 2", "model": "gpt-4"},
                {
                    "role": "assistant",
                    "tool_calls": [
                        {"function": {"name": "test_function"}, "id": "call-1"}
                    ],
                },
            ]
        }
        self.tracker.current_session_id = "test-session"

        metrics = self.tracker.extract_metrics()
        assert metrics["prompts_sent"] == 2
        assert (
            len(metrics["messages"]) == 5
        )  # 2 user + 3 assistant (including tool call message)
        assert len(metrics["tool_calls"]) == 1
        assert "gpt-4" in metrics["models_used"]
        assert metrics["continue_session_id"] == "test-session"

    def test_get_token_usage_no_database(self):
        """Test token usage when database doesn't exist."""
        metrics = self.tracker.get_token_usage_from_db()
        assert metrics["total_prompt_tokens"] == 0
        assert metrics["total_generated_tokens"] == 0
        assert metrics["total_requests"] == 0

    def test_get_token_usage_database_no_table(self):
        """Test token usage when database exists but table doesn't."""
        # Create SQLite database without the tokensGenerated table
        conn = sqlite3.connect(self.tracker.devdata_db)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE other_table (id INTEGER)")
        conn.commit()
        conn.close()

        metrics = self.tracker.get_token_usage_from_db()
        assert metrics["total_prompt_tokens"] == 0
        assert metrics["total_generated_tokens"] == 0
        assert metrics["total_requests"] == 0

    def test_get_token_usage_database_with_table(self):
        """Test token usage with valid database and table."""
        # Create SQLite database with tokensGenerated table
        conn = sqlite3.connect(self.tracker.devdata_db)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE tokensGenerated (
                model TEXT,
                promptTokens INTEGER,
                generatedTokens INTEGER,
                timestamp REAL
            )
        """
        )

        # Insert test data
        now = datetime.now().timestamp()
        cursor.execute(
            """
            INSERT INTO tokensGenerated VALUES 
            ('gpt-4', 100, 200, ?),
            ('gpt-4', 150, 250, ?),
            ('claude', 50, 100, ?)
        """,
            (now, now, now),
        )
        conn.commit()
        conn.close()

        metrics = self.tracker.get_token_usage_from_db()
        assert metrics["total_prompt_tokens"] == 300  # 100 + 150 + 50
        assert metrics["total_generated_tokens"] == 550  # 200 + 250 + 100
        assert metrics["total_requests"] == 3
        assert "gpt-4" in metrics["by_model"]
        assert "claude" in metrics["by_model"]

    def test_get_token_usage_jsonl_fallback(self):
        """Test token usage fallback to JSONL file."""
        # Create JSONL file with token data
        tokens_file = self.tracker.dev_data_dir / "0.2.0" / "tokensGenerated.jsonl"
        now = datetime.now().timestamp()

        jsonl_data = [
            {
                "model": "gpt-4",
                "promptTokens": 100,
                "generatedTokens": 200,
                "timestamp": now,
            },
            {
                "model": "gpt-4",
                "promptTokens": 150,
                "generatedTokens": 250,
                "timestamp": now,
            },
            {
                "model": "claude",
                "promptTokens": 50,
                "generatedTokens": 100,
                "timestamp": now,
            },
        ]

        with open(tokens_file, "w") as f:
            for entry in jsonl_data:
                f.write(json.dumps(entry) + "\n")

        metrics = self.tracker.get_token_usage_from_db()
        assert metrics["total_prompt_tokens"] == 300
        assert metrics["total_generated_tokens"] == 550
        assert metrics["total_requests"] == 3
        assert "gpt-4" in metrics["by_model"]
        assert "claude" in metrics["by_model"]

    def test_get_token_usage_old_timestamp_filtered(self):
        """Test that old timestamps are filtered out."""
        tokens_file = self.tracker.dev_data_dir / "0.2.0" / "tokensGenerated.jsonl"

        # Create entries with different timestamps
        now = datetime.now().timestamp()
        two_hours_ago = (datetime.now() - timedelta(hours=2)).timestamp()

        jsonl_data = [
            {
                "model": "gpt-4",
                "promptTokens": 100,
                "generatedTokens": 200,
                "timestamp": now,
            },
            {
                "model": "gpt-4",
                "promptTokens": 150,
                "generatedTokens": 250,
                "timestamp": two_hours_ago,
            },
        ]

        with open(tokens_file, "w") as f:
            for entry in jsonl_data:
                f.write(json.dumps(entry) + "\n")

        # Should only include recent entry (within last hour by default)
        metrics = self.tracker.get_token_usage_from_db()
        assert metrics["total_prompt_tokens"] == 100
        assert metrics["total_generated_tokens"] == 200
        assert metrics["total_requests"] == 1

    def test_parse_event_logs_missing_file(self):
        """Test parsing event logs when file doesn't exist."""
        events = self.tracker.parse_event_logs("quickEdit")
        assert events == []

    def test_parse_event_logs_valid_file(self):
        """Test parsing valid event log file."""
        event_file = self.tracker.dev_data_dir / "0.2.0" / "quickEdit.jsonl"

        events_data = [
            {"type": "quickEdit", "timestamp": 1000},
            {"type": "quickEdit", "timestamp": 2000},
        ]

        with open(event_file, "w") as f:
            for event in events_data:
                f.write(json.dumps(event) + "\n")

        events = self.tracker.parse_event_logs("quickEdit")
        assert len(events) == 2
        assert events[0]["type"] == "quickEdit"

    def test_calculate_session_duration_no_data(self):
        """Test calculating duration with no session data."""
        duration = self.tracker.calculate_session_duration()
        assert duration == 0

    def test_calculate_session_duration_with_timestamps(self):
        """Test calculating duration with valid timestamps."""
        self.tracker.session_data = {
            "history": [
                {"timestamp": 1000, "content": "start"},
                {"timestamp": 2000, "content": "middle"},
                {"timestamp": 5000, "content": "end"},
            ]
        }

        duration = self.tracker.calculate_session_duration()
        assert duration == 4.0  # (5000 - 1000) / 1000

    def test_get_comprehensive_metrics(self):
        """Test getting comprehensive metrics."""
        # Set up session data
        self.tracker.session_data = {
            "history": [
                {"role": "user", "content": "Test", "timestamp": 1000},
                {"role": "assistant", "content": "Response", "timestamp": 2000},
            ]
        }

        # Create event logs
        quick_edit_file = self.tracker.dev_data_dir / "0.2.0" / "quickEdit.jsonl"
        with open(quick_edit_file, "w") as f:
            f.write(json.dumps({"type": "quickEdit"}) + "\n")

        autocomplete_file = self.tracker.dev_data_dir / "0.2.0" / "autocomplete.jsonl"
        with open(autocomplete_file, "w") as f:
            f.write(json.dumps({"type": "autocomplete"}) + "\n")
            f.write(json.dumps({"type": "autocomplete"}) + "\n")

        metrics = self.tracker.get_comprehensive_metrics()
        assert metrics["prompts_sent"] == 1
        assert metrics["session_duration"] == 1.0
        assert metrics["quick_edits_count"] == 1
        assert metrics["autocompletes_count"] == 2
        assert "token_metrics" in metrics

    def test_database_error_handling(self):
        """Test graceful handling of database errors."""
        # Create a corrupted database file
        with open(self.tracker.devdata_db, "w") as f:
            f.write("This is not a valid SQLite database")

        # Should not raise an exception
        metrics = self.tracker.get_token_usage_from_db()
        assert metrics["total_prompt_tokens"] == 0
        assert metrics["total_generated_tokens"] == 0

    def test_jsonl_error_handling(self):
        """Test graceful handling of corrupted JSONL files."""
        tokens_file = self.tracker.dev_data_dir / "0.2.0" / "tokensGenerated.jsonl"

        # Write invalid JSON
        with open(tokens_file, "w") as f:
            f.write("This is not valid JSON\n")
            f.write('{"valid": "json", "promptTokens": 100}\n')
            f.write("Another invalid line\n")

        # Should skip invalid lines and process valid ones
        metrics = self.tracker.get_token_usage_from_db()
        # Only the valid JSON line should be processed (but has no timestamp so filtered out)
        assert isinstance(metrics, dict)


class TestModuleFunctions:
    """Test module-level functions."""

    @patch("benchmark.continue_session_tracker.ContinueSessionTracker")
    def test_find_active_continue_session(self, mock_tracker_class):
        """Test finding active Continue session."""
        mock_tracker = MagicMock()
        mock_tracker.find_latest_session.return_value = "session-123"
        mock_tracker_class.return_value = mock_tracker

        result = find_active_continue_session()
        assert result == "session-123"
        mock_tracker.find_latest_session.assert_called_once()

    @patch("benchmark.continue_session_tracker.ContinueSessionTracker")
    def test_extract_metrics_from_continue_no_session(self, mock_tracker_class):
        """Test extracting metrics when no session found."""
        mock_tracker = MagicMock()
        mock_tracker.find_latest_session.return_value = None
        mock_tracker_class.return_value = mock_tracker

        result = extract_metrics_from_continue()
        assert result is None

    @patch("benchmark.continue_session_tracker.ContinueSessionTracker")
    def test_extract_metrics_from_continue_with_session(self, mock_tracker_class):
        """Test extracting metrics with valid session."""
        mock_tracker = MagicMock()
        mock_tracker.find_latest_session.return_value = "session-123"
        mock_tracker.load_session.return_value = {"history": []}
        mock_tracker.get_comprehensive_metrics.return_value = {
            "prompts_sent": 5,
            "tokens_generated": 1000,
            "tokens_prompt": 500,
            "tool_calls": [{"name": "test"}],
            "messages": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ],
            "session_duration": 120,
            "models_used": ["gpt-4"],
            "quick_edits_count": 3,
            "autocompletes_count": 10,
        }
        mock_tracker_class.return_value = mock_tracker

        result = extract_metrics_from_continue("session-123")

        assert result is not None
        assert result["continue_session_id"] == "session-123"
        assert result["prompts_sent"] == 5
        assert result["tokens_generated"] == 1000
        assert result["tokens_prompt"] == 500
        assert result["tool_calls"] == 1  # Length of tool_calls list
        assert result["chars_sent"] == 5  # Length of "Hello"
        assert result["chars_received"] == 9  # Length of "Hi there!"
        assert result["session_duration"] == 120
        assert result["models_used"] == ["gpt-4"]
        assert result["quick_edits_count"] == 3
        assert result["autocompletes_count"] == 10


class TestIntegration:
    """Integration tests for the Continue session tracker."""

    def test_full_workflow(self):
        """Test the complete workflow from session creation to metrics extraction."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set up directory structure
            continue_dir = Path(temp_dir) / ".continue"
            sessions_dir = continue_dir / "sessions"
            dev_data_dir = continue_dir / "dev_data"
            sessions_dir.mkdir(parents=True)
            dev_data_dir.mkdir(parents=True)
            (dev_data_dir / "0.2.0").mkdir(parents=True)

            # Create sessions.json
            sessions_data = [
                {"sessionId": "session-1", "timestamp": 1000},
                {"sessionId": "session-2", "timestamp": 2000},
            ]
            with open(sessions_dir / "sessions.json", "w") as f:
                json.dump(sessions_data, f)

            # Create session file
            session_data = {
                "sessionId": "session-2",
                "history": [
                    {"role": "user", "content": "Write a function", "timestamp": 1000},
                    {
                        "role": "assistant",
                        "content": "Here's a function",
                        "model": "gpt-4",
                        "timestamp": 2000,
                    },
                    {
                        "role": "assistant",
                        "tool_calls": [{"function": {"name": "write_file"}, "id": "1"}],
                        "timestamp": 3000,
                    },
                ],
            }
            with open(sessions_dir / "session-2.json", "w") as f:
                json.dump(session_data, f)

            # Create token data
            tokens_file = dev_data_dir / "0.2.0" / "tokensGenerated.jsonl"
            now = datetime.now().timestamp()
            with open(tokens_file, "w") as f:
                f.write(
                    json.dumps(
                        {
                            "model": "gpt-4",
                            "promptTokens": 50,
                            "generatedTokens": 100,
                            "timestamp": now,
                        }
                    )
                    + "\n"
                )

            # Test with patched home directory
            with patch.object(Path, "home", return_value=Path(temp_dir)):
                # Extract metrics
                metrics = extract_metrics_from_continue()

                assert metrics is not None
                assert metrics["continue_session_id"] == "session-2"
                assert metrics["prompts_sent"] == 1
                assert metrics["tool_calls"] == 1
                assert metrics["tokens_prompt"] == 50
                assert metrics["tokens_generated"] == 100
                assert "gpt-4" in metrics["models_used"]
