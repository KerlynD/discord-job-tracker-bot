"""
Reminder scheduler for the job tracker bot.
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import sessionmaker

from models import create_engine_and_session, Reminder
from services import JobTrackerService
from utils.formatting import format_reminder_message

logger = logging.getLogger(__name__)


class ReminderScheduler:
    """Handles scheduled reminders for job applications."""
    
    def __init__(self, bot: commands.Bot, database_url: str = "sqlite:///jobs.db"):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.database_url = database_url
        self.engine, self.SessionLocal = create_engine_and_session(database_url)
        
    async def start(self) -> None:
        """Start the reminder scheduler."""
        logger.info("Starting reminder scheduler...")
        
        # Schedule reminder checks every minute
        self.scheduler.add_job(
            self.check_reminders,
            CronTrigger(minute="*"),  # Every minute
            id="reminder_check",
            max_instances=1,
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("Reminder scheduler started")
    
    async def stop(self) -> None:
        """Stop the reminder scheduler."""
        logger.info("Stopping reminder scheduler...")
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                logger.info("Reminder scheduler stopped")
            else:
                logger.info("Reminder scheduler was not running")
        except Exception as e:
            logger.warning(f"Error stopping scheduler: {e}")
    
    async def check_reminders(self) -> None:
        """Check for due reminders and send DMs."""
        try:
            db_session = self.SessionLocal()
            service = JobTrackerService(db_session)
            
            # Get all due reminders
            due_reminders = service.get_due_reminders()
            
            logger.info(f"Found {len(due_reminders)} due reminders")
            
            for reminder in due_reminders:
                try:
                    await self.send_reminder(reminder, service)
                except Exception as e:
                    logger.error(f"Failed to send reminder {reminder.id}: {e}")
                    # Continue with other reminders even if one fails
            
            db_session.close()
            
        except Exception as e:
            logger.error(f"Error checking reminders: {e}")
    
    async def send_reminder(self, reminder, service: JobTrackerService) -> None:
        """Send a reminder DM to the user."""
        try:
            # Get the application associated with this reminder
            application = service.get_application_by_company(
                reminder.application.company, 
                reminder.application.user_id
            )
            
            if not application:
                logger.warning(f"Application not found for reminder {reminder.id}")
                service.mark_reminder_sent(reminder.id)
                return
            
            # Get the user
            user = self.bot.get_user(application.user_id)
            if not user:
                try:
                    user = await self.bot.fetch_user(application.user_id)
                except discord.NotFound:
                    logger.warning(f"User {application.user_id} not found for reminder {reminder.id}")
                    service.mark_reminder_sent(reminder.id)
                    return
            
            # Format the reminder message
            message = format_reminder_message(application, reminder)
            
            # Send the DM
            try:
                await user.send(message)
                logger.info(f"Sent reminder {reminder.id} to user {user.id}")
            except discord.Forbidden:
                logger.warning(f"Cannot send DM to user {user.id} (DMs disabled)")
            except discord.HTTPException as e:
                logger.error(f"Failed to send DM to user {user.id}: {e}")
                return
            
            # Mark reminder as sent
            service.mark_reminder_sent(reminder.id)
            
        except Exception as e:
            logger.error(f"Error sending reminder {reminder.id}: {e}")
            raise
    
    async def add_manual_reminder(self, reminder_id: int) -> None:
        """Manually trigger a specific reminder (for testing)."""
        try:
            db_session = self.SessionLocal()
            service = JobTrackerService(db_session)
            
            # Get the specific reminder
            reminder = db_session.query(Reminder).filter(
                Reminder.id == reminder_id
            ).first()
            
            if reminder and not reminder.sent:
                await self.send_reminder(reminder, service)
            
            db_session.close()
            
        except Exception as e:
            logger.error(f"Error manually triggering reminder {reminder_id}: {e}")
    
    def get_scheduler_status(self) -> dict:
        """Get the current status of the scheduler."""
        return {
            "running": self.scheduler.running,
            "jobs": len(self.scheduler.get_jobs()),
            "next_run": self.scheduler.get_jobs()[0].next_run_time if self.scheduler.get_jobs() else None
        }
    
    async def test_reminder_system(self, user_id: int) -> str:
        """Test the reminder system by sending a test message."""
        try:
            user = self.bot.get_user(user_id)
            if not user:
                user = await self.bot.fetch_user(user_id)
            
            test_message = "🧪 **Test Reminder**\n\nThis is a test message to verify the reminder system is working correctly!"
            
            await user.send(test_message)
            return f"Test reminder sent successfully to {user.display_name}"
            
        except discord.NotFound:
            return f"User {user_id} not found"
        except discord.Forbidden:
            return f"Cannot send DM to user (DMs disabled)"
        except Exception as e:
            return f"Error sending test reminder: {e}" 