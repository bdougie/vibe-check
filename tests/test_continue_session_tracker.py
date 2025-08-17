#!/usr/bin/env python3
"""
Test suite for Continue session tracker
"""

import json
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import MagicMock, patch

import pytest

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from benchmark.continue_session_tracker import (
    ContinueSessionTracker,
    extract_metrics_from_continue,
    find_active_continue_session,
)


class TestContinueSessionTracker:
    """Test cases for Continue session tracker."""

    def setup_method(self):
        """Set up test environment before each test."""
        self.tracker = ContinueSessionTracker()
        # Use temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        self.tracker.continue_dir = Path(self.temp_dir) / ".continue"
        self.tracker.sessions_dir = self.tracker.continue_dir / "sessions"
        self.tracker.dev_data_dir = self.tracker.continue_dir / "dev_data"
        self.tracker.devdata_db = self.tracker.dev_data_dir / "devdata.sqlite"

    def teardown_method(self):
        """Clean up after each test."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def create_mock_session(self, session_id="test-session-123"):
        """Create a mock Continue session for testing."""
        self.tracker.sessions_dir.mkdir(parents=True, exist_ok=True)

        # Create sessions list
        sessions_data = [
            {
                "sessionId": session_id,
                "title": "Test Session",
                "workspaceDirectory": "/test/workspace",
                "timestamp": 1700000000000,
            }
        ]

        with open(self.tracker.sessions_dir / "sessions.json", "w") as f:
            json.dump(sessions_data, f)

        # Create session file
        session_data = {
            "sessionId": session_id,
            "title": "Test Session",
            "workspaceDirectory": "/test/workspace",
            "history": [
                {
                    "role": "user",
                    "content": "Write a function to calculate factorial",
                    "timestamp": 1700000000000,
                },
                {
                    "role": "assistant",
                    "content": "Here's a factorial function...",
                    "model": "gpt-4",
                    "timestamp": 1700000001000,
                },
                {
                    "role": "user",
                    "content": "Add error handling",
                    "timestamp": 1700000002000,
                },
                {
                    "role": "assistant",
                    "content": "I'll add error handling...",
                    "model": "gpt-4",
                    "timestamp": 1700000003000,
                    "tool_calls": [
                        {
                            "id": "call_123",
                            "function": {
                                "name": "writeFile",
                                "arguments": '{"path": "factorial.py", "content": "def factorial(n)..."}',
                            },
                        }
                    ],
                },
            ],
        }

        with open(self.tracker.sessions_dir / f"{session_id}.json", "w") as f:
            json.dump(session_data, f)

        return session_id

    def test_initialization(self):
        """Test tracker initialization."""
        assert self.tracker.current_session_id is None
        assert self.tracker.session_data is None
        assert self.tracker.metrics["prompts_sent"] == 0
        assert self.tracker.metrics["tokens_generated"] == 0

    def test_find_latest_session(self):
        """Test finding the latest Continue session."""
        # No sessions initially
        assert self.tracker.find_latest_session() is None

        # Create mock session
        session_id = self.create_mock_session()
        found_id = self.tracker.find_latest_session()

        assert found_id == session_id

    def test_load_session(self):
        """Test loading a Continue session."""
        session_id = self.create_mock_session()

        # Load the session
        data = self.tracker.load_session(session_id)

        assert data is not None
        assert self.tracker.current_session_id == session_id
        assert self.tracker.session_data is not None
        assert "history" in self.tracker.session_data

    def test_load_session_not_found(self):
        """Test loading a non-existent session."""
        data = self.tracker.load_session("non-existent-session")

        assert data is None
        assert self.tracker.current_session_id is None

    def test_parse_session_messages(self):
        """Test parsing messages from session data."""
        session_id = self.create_mock_session()
        self.tracker.load_session(session_id)

        # Extract metrics which parses messages
        metrics = self.tracker.extract_metrics()

        assert metrics["prompts_sent"] == 2  # Two user messages
        assert len(metrics["messages"]) == 4  # Total messages
        assert len(metrics["tool_calls"]) == 1  # One tool call
        assert "gpt-4" in metrics["models_used"]

    def test_calculate_session_duration(self):
        """Test calculating session duration."""
        session_id = self.create_mock_session()
        self.tracker.load_session(session_id)

        duration = self.tracker.calculate_session_duration()

        # Duration should be 3 seconds (3000ms)
        assert duration == 3.0

    @patch("sqlite3.connect")
    def test_get_token_usage_from_db(self, mock_connect):
        """Test extracting token usage from SQLite database."""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Mock query results
        mock_cursor.fetchall.return_value = [
            (
                1000,
                2000,
                5,
                "gpt-4",
            ),  # prompt_tokens, generated_tokens, requests, model
            (500, 1000, 3, "gpt-3.5-turbo"),
        ]

        # Create database file (empty, just for existence check)
        self.tracker.dev_data_dir.mkdir(parents=True, exist_ok=True)
        self.tracker.devdata_db.touch()

        # Get token usage
        token_metrics = self.tracker.get_token_usage_from_db()

        assert token_metrics["total_prompt_tokens"] == 1500
        assert token_metrics["total_generated_tokens"] == 3000
        assert token_metrics["total_requests"] == 8
        assert "gpt-4" in token_metrics["by_model"]

    def test_parse_event_logs(self):
        """Test parsing JSONL event log files."""
        # Create mock event log
        event_dir = self.tracker.dev_data_dir / "0.2.0"
        event_dir.mkdir(parents=True, exist_ok=True)

        events = [
            {
                "event": "quickEdit",
                "timestamp": 1700000000,
                "data": {"file": "test.py"},
            },
            {
                "event": "quickEdit",
                "timestamp": 1700000001,
                "data": {"file": "test2.py"},
            },
        ]

        with open(event_dir / "quickEdit.jsonl", "w") as f:
            for event in events:
                f.write(json.dumps(event) + "\n")

        # Parse events
        parsed_events = self.tracker.parse_event_logs("quickEdit")

        assert len(parsed_events) == 2
        assert parsed_events[0]["event"] == "quickEdit"

    def test_get_human_interventions(self):
        """Test estimating human interventions."""
        # This feature is not implemented in the tracker
        # Human interventions need to be tracked manually
        pass

    def test_export_metrics_for_benchmark(self):
        """Test exporting metrics in benchmark format."""
        session_id = self.create_mock_session()
        self.tracker.load_session(session_id)

        # Get comprehensive metrics
        metrics = self.tracker.get_comprehensive_metrics()

        assert metrics["prompts_sent"] == 2
        assert len(metrics["tool_calls"]) == 1
        assert metrics["continue_session_id"] == session_id
        assert "models_used" in metrics
        assert metrics["session_duration"] == 3.0

    def test_extract_all_metrics(self):
        """Test extracting all metrics from a session."""
        session_id = self.create_mock_session()
        self.tracker.load_session(session_id)

        # Mock database - patch the method to update metrics correctly
        def mock_get_token_usage(start_time=None):
            # Update the tracker's metrics as the real method would
            self.tracker.metrics["tokens_prompt"] = 1500
            self.tracker.metrics["tokens_generated"] = 3000
            return {
                "total_prompt_tokens": 1500,
                "total_generated_tokens": 3000,
                "total_requests": 8,
                "by_model": {},
            }

        with patch.object(
            self.tracker, "get_token_usage_from_db", mock_get_token_usage
        ):
            metrics = self.tracker.get_comprehensive_metrics()

        assert metrics["prompts_sent"] == 2
        assert metrics["tokens_prompt"] == 1500
        assert metrics["tokens_generated"] == 3000
        assert metrics["session_duration"] == 3.0
        assert len(metrics["tool_calls"]) == 1


class TestModuleFunctions:
    """Test module-level functions."""

    @patch("benchmark.continue_session_tracker.ContinueSessionTracker")
    def test_find_active_continue_session(self, mock_tracker_class):
        """Test finding active Continue session."""
        mock_tracker = MagicMock()
        mock_tracker.find_latest_session.return_value = "session-123"
        mock_tracker_class.return_value = mock_tracker

        session_id = find_active_continue_session()

        assert session_id == "session-123"
        mock_tracker.find_latest_session.assert_called_once()

    @patch("benchmark.continue_session_tracker.ContinueSessionTracker")
    def test_extract_metrics_from_continue(self, mock_tracker_class):
        """Test extracting metrics from Continue."""
        mock_tracker = MagicMock()
        mock_tracker.find_latest_session.return_value = "session-123"
        mock_tracker.load_session.return_value = {"sessionId": "session-123"}
        mock_tracker.get_comprehensive_metrics.return_value = {
            "prompts_sent": 5,
            "tokens_generated": 1000,
            "tool_calls": [],
            "messages": [],
            "session_duration": 100,
            "models_used": ["gpt-4"],
            "quick_edits_count": 0,
            "autocompletes_count": 0,
        }
        mock_tracker_class.return_value = mock_tracker

        metrics = extract_metrics_from_continue("session-123")

        assert metrics["prompts_sent"] == 5
        assert metrics["tokens_generated"] == 1000
        mock_tracker.load_session.assert_called_once_with("session-123")


class TestIntegration:
    """Integration tests with actual file system."""

    @pytest.mark.integration
    def test_full_workflow(self):
        """Test full workflow with mock Continue data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            tracker = ContinueSessionTracker()
            tracker.continue_dir = Path(temp_dir) / ".continue"
            tracker.sessions_dir = tracker.continue_dir / "sessions"
            tracker.dev_data_dir = tracker.continue_dir / "dev_data"

            # Create session directory structure
            tracker.sessions_dir.mkdir(parents=True, exist_ok=True)

            # Create mock session
            session_id = "integration-test-session"
            sessions_data = [{"sessionId": session_id, "title": "Integration Test"}]

            with open(tracker.sessions_dir / "sessions.json", "w") as f:
                json.dump(sessions_data, f)

            session_data = {
                "sessionId": session_id,
                "history": [
                    {"role": "user", "content": "Test prompt", "timestamp": 1000},
                    {"role": "assistant", "content": "Response", "timestamp": 2000},
                ],
            }

            with open(tracker.sessions_dir / f"{session_id}.json", "w") as f:
                json.dump(session_data, f)

            # Load session first
            tracker.load_session(session_id)

            # Extract metrics
            metrics = tracker.get_comprehensive_metrics()

            assert metrics["prompts_sent"] == 1
            assert metrics["session_duration"] == 1.0
            assert tracker.current_session_id == session_id
