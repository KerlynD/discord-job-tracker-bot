"""
Tests for the job tracker services.
"""

import time
from unittest.mock import Mock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.job_tracker.models import Application, Base, Reminder, Stage
from src.job_tracker.services import JobTrackerService


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def service(db_session):
    """Create a JobTrackerService instance for testing."""
    return JobTrackerService(db_session)


class TestJobTrackerService:
    """Test cases for JobTrackerService."""

    def test_add_application(self, service):
        """Test adding a new application."""
        app = service.add_application("Google", "Software Engineer", 123, "Summer")

        assert app.company == "Google"
        assert app.role == "Software Engineer"
        assert app.season == "Summer"
        assert app.user_id == 123
        assert app.id is not None

        # Check that initial stage is created
        assert len(app.stages) == 1
        assert app.stages[0].stage == "Applied"

    def test_add_application_default_season(self, service):
        """Test adding application with default season."""
        app = service.add_application("Google", "Software Engineer", 123)

        assert app.season == "Summer"

    def test_add_application_invalid_season(self, service):
        """Test adding application with invalid season raises an error."""
        with pytest.raises(ValueError, match="Invalid season"):
            service.add_application("Google", "Software Engineer", 123, "Invalid")

    def test_add_duplicate_application(self, service):
        """Test adding a duplicate application raises an error."""
        service.add_application("Google", "Software Engineer", 123)

        with pytest.raises(ValueError, match="already exists"):
            service.add_application("Google", "Software Engineer", 123)

    def test_update_application_stage(self, service):
        """Test updating application stage."""
        app = service.add_application("Google", "Software Engineer", 123)

        stage = service.update_application_stage("Google", "OA", 123)

        assert stage.stage == "OA"
        assert stage.app_id == app.id

        # Check that application now has 2 stages
        service.db.refresh(app)
        assert len(app.stages) == 2
        
        # Check that current stage is now OA
        assert app.current_stage.stage == "OA"

    def test_update_application_stage_with_custom_date(self, service):
        """Test updating application stage with custom timestamp."""
        app = service.add_application("Google", "Software Engineer", 123)
        custom_timestamp = int(time.time()) - 86400  # 1 day ago

        stage = service.update_application_stage("Google", "OA", 123, custom_timestamp)

        assert stage.stage == "OA"
        assert stage.date == custom_timestamp

    def test_update_nonexistent_application(self, service):
        """Test updating a non-existent application raises an error."""
        with pytest.raises(ValueError, match="No application found"):
            service.update_application_stage("NonExistent", "OA", 123)

    def test_invalid_stage(self, service):
        """Test updating with invalid stage raises an error."""
        service.add_application("Google", "Software Engineer", 123)

        with pytest.raises(ValueError, match="Invalid stage"):
            service.update_application_stage("Google", "InvalidStage", 123)

    def test_list_applications(self, service):
        """Test listing applications."""
        app1 = service.add_application("Google", "Software Engineer", 123, "Summer")
        app2 = service.add_application("Meta", "Product Manager", 123, "Fall")

        apps = service.list_applications(123)

        assert len(apps) == 2
        assert apps[0].company in ["Google", "Meta"]
        assert apps[1].company in ["Google", "Meta"]

    def test_list_applications_with_season_filter(self, service):
        """Test listing applications with season filter."""
        app1 = service.add_application("Google", "Software Engineer", 123, "Summer")
        app2 = service.add_application("Meta", "Product Manager", 123, "Fall")

        apps = service.list_applications(123, season_filter="Summer")

        assert len(apps) == 1
        assert apps[0].company == "Google"

    def test_get_stale_applications(self, service):
        """Test getting stale applications."""
        app1 = service.add_application("Google", "Software Engineer", 123)
        service.add_application("Meta", "Product Manager", 123)

        # Update Google with a current time to make it the most recent stage
        service.update_application_stage("Google", "OA", 123)

        # Now modify both stages to ensure OA is the most recent but still stale
        all_stages = service.db.query(Stage).filter(Stage.app_id == app1.id).all()
        stale_timestamp = int(time.time()) - (8 * 24 * 60 * 60)  # 8 days ago
        
        for stage in all_stages:
            if stage.stage == "Applied":
                # Make Applied stage very old
                stage.date = int(time.time()) - (10 * 24 * 60 * 60)  # 10 days ago
            elif stage.stage == "OA":
                # Make OA stage stale but more recent than Applied
                stage.date = stale_timestamp
        service.db.commit()

        # Update Meta with a recent date
        service.update_application_stage("Meta", "OA", 123)

        stale_apps = service.get_stale_applications(123, days_threshold=7)

        assert len(stale_apps) == 1
        assert stale_apps[0].company == "Google"

    def test_add_reminder(self, service):
        """Test adding a reminder."""
        app = service.add_application("Google", "Software Engineer", 123)

        reminder = service.add_reminder("Google", 123, 3)

        assert reminder.app_id == app.id
        assert not reminder.sent
        # Check that reminder is set for approximately 3 days from now
        now = int(time.time())
        expected_due = now + (3 * 24 * 60 * 60)
        assert abs(reminder.due_at - expected_due) < 60  # Within 1 minute

    def test_get_due_reminders(self, service):
        """Test getting due reminders."""
        app = service.add_application("Google", "Software Engineer", 123)
        
        # Create a reminder that's already due (1 hour ago)
        past_due = int(time.time()) - 3600
        reminder = Reminder(app_id=app.id, due_at=past_due, sent=False)
        service.db.add(reminder)
        service.db.commit()

        due_reminders = service.get_due_reminders()

        assert len(due_reminders) == 1
        assert due_reminders[0].id == reminder.id

    def test_get_active_companies(self, service):
        """Test getting active companies (non-rejected)."""
        # Add some applications
        service.add_application("Google", "Software Engineer", 123)
        service.add_application("Meta", "Product Manager", 123)
        service.add_application("Apple", "iOS Developer", 123)
        
        # Reject one application
        service.update_application_stage("Apple", "Rejected", 123)
        
        active_companies = service.get_active_companies(123)
        
        assert len(active_companies) == 2
        assert "Google" in active_companies
        assert "Meta" in active_companies
        assert "Apple" not in active_companies

    def test_get_application_stats(self, service):
        """Test getting application statistics."""
        service.add_application("Google", "Software Engineer", 123)
        service.add_application("Meta", "Product Manager", 123)
        service.update_application_stage("Google", "OA", 123)

        stats = service.get_application_stats(123)

        assert stats["Applied"] == 1  # Meta
        assert stats["OA"] == 1  # Google

    def test_export_applications_csv(self, service):
        """Test exporting applications to CSV."""
        service.add_application("Google", "Software Engineer", 123, "Summer")
        service.add_application("Meta", "Product Manager", 123, "Fall")

        csv_data = service.export_applications_csv(123)

        lines = csv_data.split("\n")
        assert lines[0] == "Company,Role,Season,Current Stage,Created At,Last Updated"
        assert len(lines) == 3  # Header + 2 applications
        assert "Google,Software Engineer,Summer" in lines[1]
        assert "Meta,Product Manager,Fall" in lines[2]
