"""
Business logic and CRUD operations for the job tracker bot.
"""

import time
from datetime import datetime

from sqlalchemy.orm import Session

from .models import Application, Reminder, Stage


def safe_timestamp_conversion(date_value) -> int:
    """Convert various date formats to unix timestamp."""
    if isinstance(date_value, int):
        return date_value
    elif isinstance(date_value, str):
        # Try to parse various string formats
        try:
            # Try ISO format first
            dt = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            return int(dt.timestamp())
        except ValueError:
            try:
                # Try common datetime format
                dt = datetime.strptime(date_value, '%Y-%m-%d %H:%M:%S.%f')
                return int(dt.timestamp())
            except ValueError:
                try:
                    # Try without microseconds
                    dt = datetime.strptime(date_value, '%Y-%m-%d %H:%M:%S')
                    return int(dt.timestamp())
                except ValueError:
                    # If all else fails, return current time
                    return int(time.time())
    else:
        return int(time.time())


class JobTrackerService:
    """Service class for job tracking operations."""

    def __init__(self, db_session: Session):
        self.db = db_session

    def add_application(
        self, 
        company: str, 
        role: str, 
        user_id: int, 
        season: str = "Summer",
        guild_id: int | None = None
    ) -> Application:
        """Add a new job application with default 'Applied' stage."""
        # Validate season
        if season not in Application.VALID_SEASONS:
            msg = f"Invalid season '{season}'. Valid seasons: {', '.join(Application.VALID_SEASONS)}"
            raise ValueError(msg)
            
        # Check if application already exists
        existing = (
            self.db.query(Application)
            .filter(
                Application.company == company,
                Application.role == role,
                Application.user_id == user_id,
            )
            .first()
        )

        if existing:
            msg = f"Application for {company} - {role} already exists"
            raise ValueError(msg)

        # Create new application
        app = Application(
            company=company,
            role=role,
            season=season,
            user_id=user_id,
            guild_id=guild_id,
            created_at=int(time.time()),
        )
        self.db.add(app)
        self.db.commit()
        self.db.refresh(app)

        # Add initial "Applied" stage
        stage = Stage(
            app_id=app.id,
            stage="Applied",
            date=int(time.time()),
        )
        self.db.add(stage)
        self.db.commit()

        return app

    def update_application_stage(
        self, company: str, stage: str, user_id: int, date: int | None = None
    ) -> Stage:
        """Update the stage of an existing application."""
        if stage not in Stage.VALID_STAGES:
            msg = f"Invalid stage '{stage}'. Valid stages: {', '.join(Stage.VALID_STAGES)}"
            raise ValueError(msg)

        # Find the application
        app = (
            self.db.query(Application)
            .filter(
                Application.company == company,
                Application.user_id == user_id,
            )
            .first()
        )

        if not app:
            msg = f"No application found for {company}"
            raise ValueError(msg)

        # Create new stage record
        if date is None:
            # Ensure the new stage has a timestamp later than any existing stage
            latest_stage = (
                self.db.query(Stage)
                .filter(Stage.app_id == app.id)
                .order_by(Stage.date.desc())
                .first()
            )
            current_time = int(time.time())
            if latest_stage:
                latest_date = safe_timestamp_conversion(latest_stage.date)
                if latest_date >= current_time:
                    stage_date = latest_date + 1  # Ensure it's at least 1 second later
                else:
                    stage_date = current_time
            else:
                stage_date = current_time
        else:
            stage_date = date

        new_stage = Stage(
            app_id=app.id,
            stage=stage,
            date=stage_date,
        )
        self.db.add(new_stage)
        self.db.commit()

        return new_stage

    def list_applications(
        self,
        user_id: int,
        stage_filter: str | None = None,
        season_filter: str | None = None,
        limit: int = 15,
        offset: int = 0,
    ) -> list[Application]:
        """List applications with optional stage/season filtering and pagination."""
        query = self.db.query(Application).filter(Application.user_id == user_id)
        
        if season_filter:
            query = query.filter(Application.season == season_filter)
            
        apps = query.offset(offset).limit(limit).all()

        if stage_filter:
            # Filter by current stage
            filtered_apps = []
            for app in apps:
                current_stage = app.current_stage
                if current_stage and current_stage.stage == stage_filter:
                    filtered_apps.append(app)
            return filtered_apps

        return apps

    def get_stale_applications(
        self, user_id: int, days_threshold: int = 7
    ) -> list[Application]:
        """Get applications that haven't been updated in the specified number of days."""
        cutoff_timestamp = int(time.time()) - (days_threshold * 24 * 60 * 60)

        # Get all applications for user
        apps = self.db.query(Application).filter(Application.user_id == user_id).all()

        stale_apps = []
        for app in apps:
            # Find the most recent stage for this application
            latest_stage = (
                self.db.query(Stage)
                .filter(Stage.app_id == app.id)
                .order_by(Stage.date.desc())
                .first()
            )

            if latest_stage:
                stage_timestamp = safe_timestamp_conversion(latest_stage.date)
                if stage_timestamp < cutoff_timestamp:
                    stale_apps.append(app)

        return stale_apps

    def add_reminder(self, company: str, user_id: int, days_from_now: int) -> Reminder:
        """Add a reminder for an application."""
        # Find the application
        app = (
            self.db.query(Application)
            .filter(
                Application.company == company,
                Application.user_id == user_id,
            )
            .first()
        )

        if not app:
            msg = f"No application found for {company}"
            raise ValueError(msg)

        # Calculate due date
        due_at = int(time.time()) + (days_from_now * 24 * 60 * 60)

        # Create reminder
        reminder = Reminder(
            app_id=app.id,
            due_at=due_at,
            sent=False,
        )
        self.db.add(reminder)
        self.db.commit()

        return reminder

    def get_due_reminders(self) -> list[Reminder]:
        """Get all unsent reminders that are due."""
        now = int(time.time())
        return (
            self.db.query(Reminder)
            .filter(Reminder.due_at <= now, Reminder.sent.is_(False))
            .all()
        )

    def mark_reminder_sent(self, reminder_id: int) -> None:
        """Mark a reminder as sent."""
        reminder = self.db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if reminder:
            reminder.sent = True
            self.db.commit()

    def get_application_stats(self, user_id: int) -> dict[str, int]:
        """Get statistics about applications by current stage."""
        stats = {}

        # Get all applications for user
        apps = self.db.query(Application).filter(Application.user_id == user_id).all()

        for app in apps:
            # Get the most recent stage for this application directly from database
            latest_stage = (
                self.db.query(Stage)
                .filter(Stage.app_id == app.id)
                .order_by(Stage.date.desc())
                .first()
            )
            
            if latest_stage:
                stage_name = latest_stage.stage
                stats[stage_name] = stats.get(stage_name, 0) + 1

        return stats

    def get_application_by_company(
        self, company: str, user_id: int
    ) -> Application | None:
        """Get an application by company name for a specific user."""
        return (
            self.db.query(Application)
            .filter(
                Application.company == company,
                Application.user_id == user_id,
            )
            .first()
        )

    def get_application_count(
        self, user_id: int, stage_filter: str | None = None, season_filter: str | None = None
    ) -> int:
        """Get the total count of applications for pagination."""
        query = self.db.query(Application).filter(Application.user_id == user_id)
        
        if season_filter:
            query = query.filter(Application.season == season_filter)
            
        apps = query.all()

        if stage_filter:
            # Count applications whose current stage matches the filter
            count = 0
            for app in apps:
                # Get the most recent stage for this application
                latest_stage = (
                    self.db.query(Stage)
                    .filter(Stage.app_id == app.id)
                    .order_by(Stage.date.desc())
                    .first()
                )
                if latest_stage and latest_stage.stage == stage_filter:
                    count += 1
            return count

        return len(apps)

    def get_active_companies(self, user_id: int) -> list[str]:
        """Get list of companies for applications that haven't been rejected."""
        apps = self.db.query(Application).filter(Application.user_id == user_id).all()
        
        active_companies = []
        for app in apps:
            # Get the most recent stage for this application directly from database
            latest_stage = (
                self.db.query(Stage)
                .filter(Stage.app_id == app.id)
                .order_by(Stage.date.desc())
                .first()
            )
            
            # Only include companies that aren't rejected
            if latest_stage and latest_stage.stage != "Rejected":
                active_companies.append(app.company)
        
        # Return unique companies, sorted alphabetically
        return sorted(list(set(active_companies)))

    def export_applications_csv(self, user_id: int) -> str:
        """Export applications to CSV format."""
        apps = self.db.query(Application).filter(Application.user_id == user_id).all()

        csv_lines = ["Company,Role,Season,Current Stage,Created At,Last Updated"]

        for app in apps:
            # Get the most recent stage for this application
            latest_stage = (
                self.db.query(Stage)
                .filter(Stage.app_id == app.id)
                .order_by(Stage.date.desc())
                .first()
            )
            
            stage_name = latest_stage.stage if latest_stage else "Unknown"
            last_updated_timestamp = safe_timestamp_conversion(latest_stage.date) if latest_stage else safe_timestamp_conversion(app.created_at)

            csv_lines.append(
                f"{app.company},{app.role},{app.season},{stage_name},{safe_timestamp_conversion(app.created_at)},{last_updated_timestamp}",
            )

        return "\n".join(csv_lines)
