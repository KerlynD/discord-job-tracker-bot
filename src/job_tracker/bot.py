"""
Main Discord bot for job application tracking.
"""

import logging
import os
import sys
from datetime import datetime
from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from .models import create_engine_and_session, init_database
from .scheduler import ReminderScheduler
from .services import JobTrackerService
from .utils.formatting import (
    create_ascii_bar_chart,
    format_application_list,
    format_stats_summary,
)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# Bot configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///jobs.db")
MULTI_GUILD_SUPPORT = os.getenv("MULTI_GUILD_SUPPORT", "false").lower() == "true"

if not DISCORD_TOKEN:
    logger.error("DISCORD_TOKEN environment variable not set")
    sys.exit(1)

# Initialize database
engine, SessionLocal = create_engine_and_session(DATABASE_URL)
init_database(engine)

# Create bot instance
intents = discord.Intents.default()
# No need for message_content intent since we're using slash commands only
bot = commands.Bot(command_prefix="!", intents=intents)

# Initialize scheduler
reminder_scheduler = ReminderScheduler(bot, DATABASE_URL)


def get_db_session():
    """Get a database session."""
    return SessionLocal()


def get_service(db_session) -> JobTrackerService:
    """Get a service instance."""
    return JobTrackerService(db_session)


@bot.event
async def on_ready():
    """Called when the bot is ready."""
    logger.info(f"{bot.user} has connected to Discord!")
    logger.info(f"Bot is in {len(bot.guilds)} guilds")

    # Start the reminder scheduler
    await reminder_scheduler.start()

    # Sync commands
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} commands")
    except Exception as e:
        logger.exception(f"Failed to sync commands: {e}")


@bot.event
async def on_disconnect():
    """Called when the bot disconnects."""
    logger.info("Bot disconnected")
    try:
        await reminder_scheduler.stop()
    except Exception as e:
        logger.warning(f"Error stopping reminder scheduler on disconnect: {e}")


@app_commands.command(name="add", description="Add a new job application")
@app_commands.describe(
    company="Company name",
    role="Job role/title",
)
async def add_application(interaction: discord.Interaction, company: str, role: str):
    """Add a new job application."""
    await interaction.response.defer(
        ephemeral=False
    )  # Public - celebrate new applications!

    try:
        db_session = get_db_session()
        service = get_service(db_session)

        guild_id = interaction.guild_id if MULTI_GUILD_SUPPORT else None

        # Add the application
        app = service.add_application(
            company=company,
            role=role,
            user_id=interaction.user.id,
            guild_id=guild_id,
        )

        embed = discord.Embed(
            title="✅ Application Added",
            description=f"**{company}** - {role}",
            color=discord.Color.green(),
        )
        embed.add_field(name="Stage", value="Applied", inline=True)
        embed.add_field(
            name="Created", value=app.created_at.strftime("%Y-%m-%d %H:%M"), inline=True
        )

        await interaction.followup.send(embed=embed)

        db_session.close()

    except ValueError as e:
        await interaction.followup.send(f"❌ Error: {e}")
    except Exception as e:
        logger.exception(f"Error adding application: {e}")
        await interaction.followup.send(
            "❌ An error occurred while adding the application."
        )


@app_commands.command(
    name="update", description="Update the stage of a job application"
)
@app_commands.describe(
    company="Company name",
    stage="New stage",
    date="Date (YYYY-MM-DD format, optional)",
)
async def update_application(
    interaction: discord.Interaction,
    company: str,
    stage: Literal["Applied", "OA", "Phone", "On-site", "Offer", "Rejected"],
    date: str | None = None,
):
    """Update the stage of a job application."""
    await interaction.response.defer(ephemeral=False)  # Public - celebrate progress!

    try:
        db_session = get_db_session()
        service = get_service(db_session)

        # Parse date if provided
        update_date = None
        if date:
            try:
                update_date = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                await interaction.followup.send(
                    "❌ Invalid date format. Use YYYY-MM-DD."
                )
                return

        # Update the application
        new_stage = service.update_application_stage(
            company=company,
            stage=stage,
            user_id=interaction.user.id,
            date=update_date,
        )

        embed = discord.Embed(
            title="✅ Application Updated",
            description=f"**{company}** stage updated to **{stage}**",
            color=discord.Color.blue(),
        )
        embed.add_field(
            name="Date", value=new_stage.date.strftime("%Y-%m-%d %H:%M"), inline=True
        )

        await interaction.followup.send(embed=embed)

        db_session.close()

    except ValueError as e:
        await interaction.followup.send(f"❌ Error: {e}")
    except Exception as e:
        logger.exception(f"Error updating application: {e}")
        await interaction.followup.send(
            "❌ An error occurred while updating the application."
        )


@app_commands.command(name="list", description="List job applications")
@app_commands.describe(
    stage="Filter by stage (optional)",
    page="Page number (default: 1)",
)
async def list_applications(
    interaction: discord.Interaction,
    stage: Literal["Applied", "OA", "Phone", "On-site", "Offer", "Rejected"]
    | None = None,
    page: int = 1,
):
    """List job applications with optional filtering."""
    await interaction.response.defer(ephemeral=True)

    try:
        db_session = get_db_session()
        service = get_service(db_session)

        # Calculate pagination
        limit = 15
        offset = (page - 1) * limit

        # Get applications
        applications = service.list_applications(
            user_id=interaction.user.id,
            stage_filter=stage,
            limit=limit,
            offset=offset,
        )

        # Get total count for pagination info
        total_count = service.get_application_count(interaction.user.id, stage)
        total_pages = (total_count + limit - 1) // limit

        # Format the list
        title = f"Applications{f' - {stage}' if stage else ''}"
        if total_pages > 1:
            title += f" (Page {page}/{total_pages})"

        formatted_list = format_application_list(applications, title)

        # Create embed
        embed = discord.Embed(
            title=title,
            description=formatted_list if applications else "No applications found.",
            color=discord.Color.blue(),
        )

        if total_pages > 1:
            embed.set_footer(
                text=f"Page {page} of {total_pages} • Total: {total_count} applications"
            )

        await interaction.followup.send(embed=embed)

        db_session.close()

    except Exception as e:
        logger.exception(f"Error listing applications: {e}")
        await interaction.followup.send(
            "❌ An error occurred while listing applications."
        )


@app_commands.command(name="todo", description="List applications that need attention")
async def todo_applications(interaction: discord.Interaction):
    """List applications that haven't been updated in over 7 days."""
    await interaction.response.defer(ephemeral=True)

    try:
        db_session = get_db_session()
        service = get_service(db_session)

        # Get stale applications
        stale_apps = service.get_stale_applications(
            interaction.user.id, days_threshold=7
        )

        # Format the list
        formatted_list = format_application_list(
            stale_apps, "🔔 Applications Needing Attention"
        )

        embed = discord.Embed(
            title="🔔 To-Do List",
            description=formatted_list
            if stale_apps
            else "🎉 All applications are up to date!",
            color=discord.Color.orange() if stale_apps else discord.Color.green(),
        )

        if stale_apps:
            embed.set_footer(
                text="These applications haven't been updated in over 7 days."
            )

        await interaction.followup.send(embed=embed)

        db_session.close()

    except Exception as e:
        logger.exception(f"Error getting todo list: {e}")
        await interaction.followup.send(
            "❌ An error occurred while getting the todo list."
        )


@app_commands.command(name="remind", description="Set a reminder for a job application")
@app_commands.describe(
    company="Company name",
    days="Days from now to remind (1-365)",
)
async def set_reminder(
    interaction: discord.Interaction,
    company: str,
    days: app_commands.Range[int, 1, 365],
):
    """Set a reminder for a job application."""
    await interaction.response.defer(ephemeral=True)

    try:
        db_session = get_db_session()
        service = get_service(db_session)

        # Add the reminder
        reminder = service.add_reminder(
            company=company,
            user_id=interaction.user.id,
            days_from_now=days,
        )

        embed = discord.Embed(
            title="⏰ Reminder Set",
            description=f"I'll remind you about **{company}** in {days} day{'s' if days != 1 else ''}.",
            color=discord.Color.purple(),
        )
        embed.add_field(
            name="Reminder Date",
            value=reminder.due_at.strftime("%Y-%m-%d %H:%M"),
            inline=True,
        )
        embed.set_footer(text="You'll receive a DM when the reminder is due.")

        await interaction.followup.send(embed=embed)

        db_session.close()

    except ValueError as e:
        await interaction.followup.send(f"❌ Error: {e}")
    except Exception as e:
        logger.exception(f"Error setting reminder: {e}")
        await interaction.followup.send(
            "❌ An error occurred while setting the reminder."
        )


@app_commands.command(name="stats", description="View application statistics")
async def view_stats(interaction: discord.Interaction):
    """View application statistics with ASCII bar chart."""
    await interaction.response.defer(
        ephemeral=False
    )  # Public - show off your progress!

    try:
        db_session = get_db_session()
        service = get_service(db_session)

        # Get statistics
        stats = service.get_application_stats(interaction.user.id)

        if not stats:
            embed = discord.Embed(
                title="📊 Application Statistics",
                description="No applications found. Use `/add` to start tracking!",
                color=discord.Color.blue(),
            )
            await interaction.followup.send(embed=embed)
            return

        # Create ASCII bar chart
        chart = create_ascii_bar_chart(stats, "Application Statistics")

        # Create summary
        summary = format_stats_summary(stats)

        embed = discord.Embed(
            title="📊 Application Statistics",
            description=f"{summary}\n\n{chart}",
            color=discord.Color.blue(),
        )

        await interaction.followup.send(embed=embed)

        db_session.close()

    except Exception as e:
        logger.exception(f"Error getting stats: {e}")
        await interaction.followup.send(
            "❌ An error occurred while getting statistics."
        )


@app_commands.command(name="export", description="Export applications to CSV")
async def export_applications(interaction: discord.Interaction):
    """Export applications to CSV format."""
    await interaction.response.defer(ephemeral=True)

    try:
        db_session = get_db_session()
        service = get_service(db_session)

        # Get CSV data
        csv_data = service.export_applications_csv(interaction.user.id)

        if (
            not csv_data
            or csv_data == "Company,Role,Current Stage,Created At,Last Updated"
        ):
            await interaction.followup.send("❌ No applications to export.")
            return

        # Create file
        filename = f"job_applications_{interaction.user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(csv_data)

        # Send file
        with open(filename, "rb") as f:
            file = discord.File(f, filename=filename)
            await interaction.followup.send(
                "📄 Here's your application data export:",
                file=file,
            )

        # Clean up
        os.remove(filename)

        db_session.close()

    except Exception as e:
        logger.exception(f"Error exporting applications: {e}")
        await interaction.followup.send(
            "❌ An error occurred while exporting applications."
        )


@app_commands.command(name="test_reminder", description="Test the reminder system")
async def test_reminder(interaction: discord.Interaction):
    """Test the reminder system."""
    await interaction.response.defer(ephemeral=True)

    try:
        result = await reminder_scheduler.test_reminder_system(interaction.user.id)
        await interaction.followup.send(f"🧪 Test Result: {result}")

    except Exception as e:
        logger.exception(f"Error testing reminder: {e}")
        await interaction.followup.send(
            "❌ An error occurred while testing the reminder system."
        )


# Add commands to the bot's tree
bot.tree.add_command(add_application)
bot.tree.add_command(update_application)
bot.tree.add_command(list_applications)
bot.tree.add_command(todo_applications)
bot.tree.add_command(set_reminder)
bot.tree.add_command(view_stats)
bot.tree.add_command(export_applications)
bot.tree.add_command(test_reminder)


def main():
    """Main entry point for the bot."""
    logger.info("Starting Job Tracker Bot...")

    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN environment variable not set")
        sys.exit(1)

    try:
        bot.run(DISCORD_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception(f"Bot crashed: {e}")
    finally:
        logger.info("Bot shutdown complete")


if __name__ == "__main__":
    main()
