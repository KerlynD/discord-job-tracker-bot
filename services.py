"""
Business logic and CRUD operations for the job tracker bot.
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from models import Application, Reminder, Stage


def ensure_timezone_naive(dt: datetime) -> datetime:
    """Ensure a datetime is timezone-naive (remove timezone info)."""
    if dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


class JobTrackerService:
    """Service class for job tracking operations."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def add_application(self, company: str, role: str, user_id: int, guild_id: Optional[int] = None) -> Application:
        """Add a new job application with default 'Applied' stage."""
        # Check if application already exists
        existing = self.db.query(Application).filter(
            Application.company == company,
            Application.role == role,
            Application.user_id == user_id
        ).first()
        
        if existing:
            raise ValueError(f"Application for {company} - {role} already exists")
        
        # Create new application
        app = Application(
            company=company,
            role=role,
            user_id=user_id,
            guild_id=guild_id,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        self.db.add(app)
        self.db.commit()
        self.db.refresh(app)
        
        # Add initial "Applied" stage
        stage = Stage(
            app_id=app.id,
            stage="Applied",
            date=datetime.now(timezone.utc).replace(tzinfo=None)
        )
        self.db.add(stage)
        self.db.commit()
        
        return app
    
    def update_application_stage(self, company: str, stage: str, user_id: int, date: Optional[datetime] = None) -> Stage:
        """Update the stage of an existing application."""
        if stage not in Stage.VALID_STAGES:
            raise ValueError(f"Invalid stage '{stage}'. Valid stages: {', '.join(Stage.VALID_STAGES)}")
        
        # Find the application
        app = self.db.query(Application).filter(
            Application.company == company,
            Application.user_id == user_id
        ).first()
        
        if not app:
            raise ValueError(f"No application found for {company}")
        
        # Create new stage record
        stage_date = date or datetime.now(timezone.utc).replace(tzinfo=None)
        if stage_date and stage_date.tzinfo is not None:
            stage_date = stage_date.replace(tzinfo=None)
        
        new_stage = Stage(
            app_id=app.id,
            stage=stage,
            date=stage_date
        )
        self.db.add(new_stage)
        self.db.commit()
        
        return new_stage
    
    def list_applications(self, user_id: int, stage_filter: Optional[str] = None, limit: int = 15, offset: int = 0) -> List[Application]:
        """List applications with optional stage filtering and pagination."""
        apps = self.db.query(Application).filter(Application.user_id == user_id).offset(offset).limit(limit).all()
        
        if stage_filter:
            # Filter by current stage
            filtered_apps = []
            for app in apps:
                current_stage = app.current_stage
                if current_stage and current_stage.stage == stage_filter:
                    filtered_apps.append(app)
            return filtered_apps
        
        return apps
    
    def get_stale_applications(self, user_id: int, days_threshold: int = 7) -> List[Application]:
        """Get applications that haven't been updated in the specified number of days."""
        cutoff_date = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days_threshold)
        
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
                stage_date = ensure_timezone_naive(latest_stage.date)
                if stage_date < cutoff_date:
                    stale_apps.append(app)
        
        return stale_apps
    
    def add_reminder(self, company: str, user_id: int, days_from_now: int) -> Reminder:
        """Add a reminder for an application."""
        # Find the application
        app = self.db.query(Application).filter(
            Application.company == company,
            Application.user_id == user_id
        ).first()
        
        if not app:
            raise ValueError(f"No application found for {company}")
        
        # Calculate due date
        due_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(days=days_from_now)
        
        # Create reminder
        reminder = Reminder(
            app_id=app.id,
            due_at=due_at,
            sent=False
        )
        self.db.add(reminder)
        self.db.commit()
        
        return reminder
    
    def get_due_reminders(self) -> List[Reminder]:
        """Get all unsent reminders that are due."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        return (
            self.db.query(Reminder)
            .filter(Reminder.due_at <= now, Reminder.sent == False)
            .all()
        )
    
    def mark_reminder_sent(self, reminder_id: int) -> None:
        """Mark a reminder as sent."""
        reminder = self.db.query(Reminder).filter(Reminder.id == reminder_id).first()
        if reminder:
            reminder.sent = True
            self.db.commit()
    
    def get_application_stats(self, user_id: int) -> Dict[str, int]:
        """Get statistics about applications by current stage."""
        stats = {}
        
        # Get all applications for user
        apps = self.db.query(Application).filter(Application.user_id == user_id).all()
        
        for app in apps:
            current_stage = app.current_stage
            if current_stage:
                stage_name = current_stage.stage
                stats[stage_name] = stats.get(stage_name, 0) + 1
        
        return stats
    
    def get_application_by_company(self, company: str, user_id: int) -> Optional[Application]:
        """Get an application by company name for a specific user."""
        return self.db.query(Application).filter(
            Application.company == company,
            Application.user_id == user_id
        ).first()
    
    def get_application_count(self, user_id: int, stage_filter: Optional[str] = None) -> int:
        """Get the total count of applications for pagination."""
        apps = self.db.query(Application).filter(Application.user_id == user_id).all()
        
        if stage_filter:
            # Count applications whose current stage matches the filter
            count = 0
            for app in apps:
                current_stage = app.current_stage
                if current_stage and current_stage.stage == stage_filter:
                    count += 1
            return count
        
        return len(apps)
    
    def export_applications_csv(self, user_id: int) -> str:
        """Export applications to CSV format."""
        apps = self.db.query(Application).filter(Application.user_id == user_id).all()
        
        csv_lines = ["Company,Role,Current Stage,Created At,Last Updated"]
        
        for app in apps:
            current_stage = app.current_stage
            stage_name = current_stage.stage if current_stage else "Unknown"
            last_updated = current_stage.date if current_stage else app.created_at
            
            csv_lines.append(
                f"{app.company},{app.role},{stage_name},{app.created_at.isoformat()},{last_updated.isoformat()}"
            )
        
        return "\n".join(csv_lines) 