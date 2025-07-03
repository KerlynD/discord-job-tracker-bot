"""
Unit tests for the services module.
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import Base, Reminder, Stage
from services import JobTrackerService


@pytest.fixture
def db_session():
    """Create a test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def service(db_session):
    """Create a service instance with test database."""
    return JobTrackerService(db_session)


class TestJobTrackerService:
    """Test cases for JobTrackerService."""

    def test_add_application(self, service):
        """Test adding a new application."""
        app = service.add_application("Google", "Software Engineer", 123)

        assert app.company == "Google"
        assert app.role == "Software Engineer"
        assert app.user_id == 123
        assert app.id is not None

        # Check that initial stage is created
        assert len(app.stages) == 1
        assert app.stages[0].stage == "Applied"

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
        service.add_application("Google", "Software Engineer", 123)
        service.add_application("Meta", "Product Manager", 123)

        apps = service.list_applications(123)

        assert len(apps) == 2
        company_names = [app.company for app in apps]
        assert "Google" in company_names
        assert "Meta" in company_names

    def test_list_applications_with_stage_filter(self, service):
        """Test listing applications with stage filter."""
        service.add_application("Google", "Software Engineer", 123)
        service.add_application("Meta", "Product Manager", 123)

        # Update one to OA stage
        service.update_application_stage("Google", "OA", 123)

        # Filter by Applied stage
        applied_apps = service.list_applications(123, stage_filter="Applied")
        assert len(applied_apps) == 1
        assert applied_apps[0].company == "Meta"

        # Filter by OA stage
        oa_apps = service.list_applications(123, stage_filter="OA")
        assert len(oa_apps) == 1
        assert oa_apps[0].company == "Google"

    def test_get_stale_applications(self, service):
        """Test getting stale applications."""
        import time

        app1 = service.add_application("Google", "Software Engineer", 123)
        service.add_application("Meta", "Product Manager", 123)

        # Wait a moment to ensure our update timestamps are after the creation
        time.sleep(0.1)

        # Update Google first with a current time to make it the most recent stage
        service.update_application_stage("Google", "OA", 123)

        # Now modify both stages to ensure OA is the most recent but still stale
        all_stages = service.db.query(Stage).filter(Stage.app_id == app1.id).all()
        for stage in all_stages:
            if stage.stage == "Applied":
                # Make Applied stage very old
                stage.date = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=10)
            elif stage.stage == "OA":
                # Make OA stage stale but more recent than Applied
                stage.date = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=8)
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
        # Handle timezone comparison - ensure both are timezone-naive
        now = datetime.now(UTC).replace(tzinfo=None)
        reminder_due = reminder.due_at
        if reminder_due.tzinfo is not None:
            reminder_due = reminder_due.replace(tzinfo=None)
        assert reminder_due > now

    def test_add_reminder_nonexistent_application(self, service):
        """Test adding reminder for non-existent application raises an error."""
        with pytest.raises(ValueError, match="No application found"):
            service.add_reminder("NonExistent", 123, 3)

    def test_get_due_reminders(self, service):
        """Test getting due reminders."""
        app = service.add_application("Google", "Software Engineer", 123)

        # Add a reminder that's due
        past_date = datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1)
        reminder = Reminder(app_id=app.id, due_at=past_date, sent=False)
        service.db.add(reminder)
        service.db.commit()

        due_reminders = service.get_due_reminders()

        assert len(due_reminders) == 1
        assert due_reminders[0].app_id == app.id

    def test_mark_reminder_sent(self, service):
        """Test marking a reminder as sent."""
        service.add_application("Google", "Software Engineer", 123)
        reminder = service.add_reminder("Google", 123, 3)

        service.mark_reminder_sent(reminder.id)

        service.db.refresh(reminder)
        assert reminder.sent

    def test_get_application_stats(self, service):
        """Test getting application statistics."""
        # Add applications with different stages
        service.add_application("Google", "Software Engineer", 123)
        service.add_application("Meta", "Product Manager", 123)
        service.add_application("Amazon", "DevOps Engineer", 123)

        service.update_application_stage("Google", "OA", 123)
        service.update_application_stage("Meta", "Phone", 123)

        stats = service.get_application_stats(123)

        assert stats["Applied"] == 1  # Amazon
        assert stats["OA"] == 1  # Google
        assert stats["Phone"] == 1  # Meta

    def test_export_applications_csv(self, service):
        """Test exporting applications to CSV."""
        service.add_application("Google", "Software Engineer", 123)

        csv_data = service.export_applications_csv(123)

        assert "Company,Role,Current Stage,Created At,Last Updated" in csv_data
        assert "Google,Software Engineer,Applied" in csv_data

    def test_current_stage_property(self, service):
        """Test the current_stage property of Application."""
        app = service.add_application("Google", "Software Engineer", 123)

        # Initially should be "Applied"
        assert app.current_stage.stage == "Applied"

        # Update to OA
        service.update_application_stage("Google", "OA", 123)
        service.db.refresh(app)

        # Should now be "OA"
        assert app.current_stage.stage == "OA"

    def test_pagination(self, service):
        """Test pagination in list_applications."""
        # Add 20 applications
        for i in range(20):
            service.add_application(f"Company{i}", f"Role{i}", 123)

        # Get first page (limit 15)
        page1 = service.list_applications(123, limit=15, offset=0)
        assert len(page1) == 15

        # Get second page
        page2 = service.list_applications(123, limit=15, offset=15)
        assert len(page2) == 5

        # Check total count
        total_count = service.get_application_count(123)
        assert total_count == 20
