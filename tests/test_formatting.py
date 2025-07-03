"""
Unit tests for the formatting utilities.
"""

from datetime import datetime

from utils.formatting import (
    create_ascii_bar_chart,
    format_application_list,
    format_reminder_message,
    format_stats_summary,
    truncate_text,
)


class TestFormattingUtilities:
    """Test cases for formatting utilities."""

    def test_create_ascii_bar_chart(self):
        """Test creating ASCII bar chart."""
        data = {"Applied": 5, "OA": 3, "Phone": 2, "Offer": 1}

        chart = create_ascii_bar_chart(data, "Test Chart")

        assert "Test Chart" in chart
        assert "Applied" in chart
        assert "OA" in chart
        assert "Phone" in chart
        assert "Offer" in chart
        assert "Total: 11 applications" in chart

    def test_create_ascii_bar_chart_empty_data(self):
        """Test creating ASCII bar chart with empty data."""
        data = {}

        chart = create_ascii_bar_chart(data, "Empty Chart")

        assert "Empty Chart" in chart
        assert "No data available" in chart

    def test_create_ascii_bar_chart_zero_values(self):
        """Test creating ASCII bar chart with zero values."""
        data = {"Applied": 0, "OA": 0}

        chart = create_ascii_bar_chart(data, "Zero Chart")

        assert "Zero Chart" in chart
        assert "No applications found" in chart

    def test_format_stats_summary(self):
        """Test formatting stats summary."""
        stats = {"Applied": 5, "OA": 3, "Phone": 2}

        summary = format_stats_summary(stats)

        assert "Total: 10" in summary
        assert "Applied: 5 (50.0%)" in summary
        assert "OA: 3 (30.0%)" in summary
        assert "Phone: 2 (20.0%)" in summary

    def test_format_stats_summary_empty(self):
        """Test formatting empty stats summary."""
        stats = {}

        summary = format_stats_summary(stats)

        assert summary == "No applications tracked yet"

    def test_truncate_text(self):
        """Test text truncation."""
        long_text = "This is a very long text that should be truncated because it exceeds the maximum length."

        # Test with default length
        truncated = truncate_text(long_text, 50)
        assert len(truncated) <= 50
        assert truncated.endswith("...")

        # Test with text shorter than limit
        short_text = "Short text"
        truncated = truncate_text(short_text, 50)
        assert truncated == short_text

        # Test with exact limit
        exact_text = "A" * 50
        truncated = truncate_text(exact_text, 50)
        assert truncated == exact_text

    def test_format_application_list_empty(self):
        """Test formatting empty application list."""
        apps = []

        formatted = format_application_list(apps, "Empty List")

        assert "Empty List" in formatted
        assert "No applications found" in formatted


class MockApplication:
    """Mock application object for testing."""

    def __init__(self, company, role, current_stage_name="Applied", stage_date=None):
        self.company = company
        self.role = role
        self.current_stage = MockStage(current_stage_name, stage_date or datetime.now())


class MockStage:
    """Mock stage object for testing."""

    def __init__(self, stage, date):
        self.stage = stage
        self.date = date


class MockReminder:
    """Mock reminder object for testing."""

    def __init__(self, due_at):
        self.due_at = due_at


class TestFormattingWithMocks:
    """Test formatting functions with mock objects."""

    def test_format_application_list_with_apps(self):
        """Test formatting application list with mock applications."""
        apps = [
            MockApplication("Google", "Software Engineer", "Applied"),
            MockApplication("Meta", "Product Manager", "OA"),
        ]

        formatted = format_application_list(apps, "Test Apps")

        assert "Test Apps" in formatted
        assert "Google" in formatted
        assert "Software Engineer" in formatted
        assert "Meta" in formatted
        assert "Product Manager" in formatted
        assert "Applied" in formatted
        assert "OA" in formatted

    def test_format_reminder_message(self):
        """Test formatting reminder message."""
        app = MockApplication("Google", "Software Engineer", "Applied")
        reminder = MockReminder(datetime.now())

        message = format_reminder_message(app, reminder)

        assert "Job Application Reminder" in message
        assert "Google" in message
        assert "Software Engineer" in message
        assert "Applied" in message
        assert "Consider following up" in message
