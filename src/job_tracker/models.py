"""
SQLAlchemy models for the job tracker bot.
"""

import time
from typing import ClassVar, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import (
    Mapped,
    declarative_base,
    mapped_column,
    relationship,
    sessionmaker,
)

Base = declarative_base()


class Application(Base):
    """Represents a job application."""

    __tablename__ = "applications"
    
    # Valid season values
    VALID_SEASONS: ClassVar[set[str]] = {
        "Summer",
        "Fall", 
        "Winter",
        "Full time",
    }

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(255), nullable=False)
    season: Mapped[str] = mapped_column(String(20), nullable=False, default="Summer")
    created_at: Mapped[int] = mapped_column(
        Integer, default=lambda: int(time.time())
    )
    guild_id: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # For multi-guild support
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationships
    stages: Mapped[list["Stage"]] = relationship(
        "Stage", back_populates="application", cascade="all, delete-orphan"
    )
    reminders: Mapped[list["Reminder"]] = relationship(
        "Reminder", back_populates="application", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Application(id={self.id}, company='{self.company}', role='{self.role}', season='{self.season}')>"
        )

    @property
    def current_stage(self) -> Optional["Stage"]:
        """Get the most recent stage for this application."""
        if not self.stages:
            return None
        
        # Handle mixed date types (strings and integers)
        def safe_date_key(stage):
            if isinstance(stage.date, int):
                return stage.date
            elif isinstance(stage.date, str):
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(stage.date.replace('Z', '+00:00'))
                    return int(dt.timestamp())
                except ValueError:
                    try:
                        dt = datetime.strptime(stage.date, '%Y-%m-%d %H:%M:%S.%f')
                        return int(dt.timestamp())
                    except ValueError:
                        try:
                            dt = datetime.strptime(stage.date, '%Y-%m-%d %H:%M:%S')
                            return int(dt.timestamp())
                        except ValueError:
                            return 0
            else:
                return 0
        
        return max(self.stages, key=safe_date_key)


class Stage(Base):
    """Represents a stage in the job application process."""

    __tablename__ = "stages"

    # Valid stage values
    VALID_STAGES: ClassVar[set[str]] = {
        "Applied",
        "OA",
        "Phone",
        "On-site",
        "Offer",
        "Rejected",
    }

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    app_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("applications.id"), nullable=False
    )
    stage: Mapped[str] = mapped_column(String(50), nullable=False)
    date: Mapped[int] = mapped_column(
        Integer, default=lambda: int(time.time())
    )

    # Relationships
    application: Mapped["Application"] = relationship(
        "Application", back_populates="stages"
    )

    def __repr__(self) -> str:
        return f"<Stage(id={self.id}, app_id={self.app_id}, stage='{self.stage}', date={self.date})>"


class Reminder(Base):
    """Represents a scheduled reminder for a job application."""

    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    app_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("applications.id"), nullable=False
    )
    due_at: Mapped[int] = mapped_column(Integer, nullable=False)
    sent: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    application: Mapped["Application"] = relationship(
        "Application", back_populates="reminders"
    )

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
