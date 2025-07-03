"""
SQLAlchemy models for the job tracker bot.
"""
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship, sessionmaker

Base = declarative_base()


class Application(Base):
    """Represents a job application."""
    
    __tablename__ = "applications"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    guild_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # For multi-guild support
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    
    # Relationships
    stages: Mapped[List["Stage"]] = relationship("Stage", back_populates="application", cascade="all, delete-orphan")
    reminders: Mapped[List["Reminder"]] = relationship("Reminder", back_populates="application", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Application(id={self.id}, company='{self.company}', role='{self.role}')>"
    
    @property
    def current_stage(self) -> Optional["Stage"]:
        """Get the most recent stage for this application."""
        if not self.stages:
            return None
        return max(self.stages, key=lambda s: s.date)


class Stage(Base):
    """Represents a stage in the job application process."""
    
    __tablename__ = "stages"
    
    # Valid stage values
    VALID_STAGES = {"Applied", "OA", "Phone", "On-site", "Offer", "Rejected"}
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    app_id: Mapped[int] = mapped_column(Integer, ForeignKey("applications.id"), nullable=False)
    stage: Mapped[str] = mapped_column(String(50), nullable=False)
    date: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    
    # Relationships
    application: Mapped["Application"] = relationship("Application", back_populates="stages")
    
    def __repr__(self) -> str:
        return f"<Stage(id={self.id}, app_id={self.app_id}, stage='{self.stage}', date={self.date})>"


class Reminder(Base):
    """Represents a scheduled reminder for a job application."""
    
    __tablename__ = "reminders"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    app_id: Mapped[int] = mapped_column(Integer, ForeignKey("applications.id"), nullable=False)
    due_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    sent: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    application: Mapped["Application"] = relationship("Application", back_populates="reminders")
    
    def __repr__(self) -> str:
        return f"<Reminder(id={self.id}, app_id={self.app_id}, due_at={self.due_at}, sent={self.sent})>"


# Database setup functions
def create_engine_and_session(database_url: str = "sqlite:///jobs.db"):
    """Create database engine and session factory."""
    engine = create_engine(database_url, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal


def init_database(engine) -> None:
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine) 