"""
Tests for formatting utilities.
"""

import time
from datetime import datetime

import pytest

from src.job_tracker.utils.formatting import (
    create_ascii_bar_chart,
    format_application_list,
    format_discord_timestamp,
    format_reminder_message,
    format_stats_summary,
    truncate_text,
)


class MockStage:
    """Mock stage object for testing."""

    def __init__(self, stage_name, date_timestamp=None):
        self.stage = stage_name
        self.date = date_timestamp or int(time.time())


class MockApplication:
    """Mock application object for testing."""

    def __init__(self, company, role, season="Full time", current_stage_name="Applied", stage_date=None):
        self.company = company
        self.role = role
        self.season = season
        self.current_stage = MockStage(current_stage_name, stage_date or int(time.time()))


class MockReminder:
    """Mock reminder object for testing."""

    def __init__(self, due_timestamp=None):
        self.due_at = due_timestamp or int(time.time())


def test_format_discord_timestamp():
    """Test Discord timestamp formatting."""
    timestamp = 1753235628  # Example timestamp
    
    # Test different format types
    assert format_discord_timestamp(timestamp, "F") == "<t:1753235628:F>"
    assert format_discord_timestamp(timestamp, "f") == "<t:1753235628:f>"
    assert format_discord_timestamp(timestamp, "R") == "<t:1753235628:R>"


def test_create_ascii_bar_chart():
    """Test ASCII bar chart creation."""
    data = {"Applied": 5, "OA": 3, "Phone": 2, "Offer": 1}

    chart = create_ascii_bar_chart(data)

    assert "Applied" in chart
    assert "OA" in chart
    assert "Phone" in chart
    assert "Offer" in chart
    assert "Total: 11 applications" in chart


def test_create_ascii_bar_chart_empty():
    """Test ASCII bar chart with empty data."""
    chart = create_ascii_bar_chart({})
    assert "No data available" in chart


def test_format_application_list():
    """Test application list formatting."""
    apps = [
        MockApplication("Google", "Software Engineer", "Summer"),
        MockApplication("Meta", "Product Manager", "Fall"),
        MockApplication("Apple", "iOS Developer"),  # Full time (default)
    ]

    formatted = format_application_list(apps, "Test Applications")

    assert "Test Applications" in formatted
    assert "Google" in formatted
    assert "Meta" in formatted
    assert "Apple" in formatted
    assert "Software Engineer" in formatted
    assert "(Summer)" in formatted
    assert "(Fall)" in formatted
    # Full time shouldn't show season in parentheses
    assert "iOS Developer (Full time)" not in formatted


def test_format_application_list_empty():
    """Test formatting empty application list."""
    formatted = format_application_list([], "Empty List")
    assert "Empty List" in formatted
    assert "No applications found" in formatted


def test_format_reminder_message():
    """Test reminder message formatting."""
    app = MockApplication("Google", "Software Engineer", "Summer", "OA")
    reminder = MockReminder()

    message = format_reminder_message(app, reminder)

    assert "Google" in message
    assert "Software Engineer" in message
    assert "Summer" in message
    assert "OA" in message
    assert "Job Application Reminder" in message
    assert "<t:" in message  # Discord timestamp


def test_format_reminder_message_full_time():
    """Test reminder message formatting for full time position."""
    app = MockApplication("Google", "Software Engineer", "Full time", "Applied")
    reminder = MockReminder()

    message = format_reminder_message(app, reminder)

    assert "Google" in message
    assert "Software Engineer" in message
    assert "Season: Full time" not in message  # Should not show full time season
    assert "Applied" in message


def test_format_stats_summary():
    """Test stats summary formatting."""
    stats = {"Applied": 5, "OA": 3, "Phone": 2, "Offer": 1}

    summary = format_stats_summary(stats)

    assert "Total: 11" in summary
    assert "Applied: 5" in summary
    assert "45.5%" in summary  # 5/11 * 100


def test_format_stats_summary_empty():
    """Test stats summary with empty data."""
    summary = format_stats_summary({})
    assert "No applications tracked yet" in summary


def test_truncate_text():
    """Test text truncation."""
    short_text = "Short text"
    long_text = "This is a very long text that should be truncated"

    assert truncate_text(short_text, 20) == short_text
    assert truncate_text(long_text, 20) == "This is a very lo..."
    assert len(truncate_text(long_text, 20)) == 20
