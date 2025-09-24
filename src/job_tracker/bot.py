"""
Main Discord bot for job application tracking.
"""

import logging
import os
import sys
import time
from datetime import datetime
from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

from .ai_service import JobSearchAI
from .models import create_engine_and_session, init_database
from .scheduler import ReminderScheduler
from .services import JobTrackerService
from .utils.formatting import (
    create_ascii_bar_chart,
    format_application_list,
    format_discord_timestamp,
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

# Initialize AI service (with error handling for missing API key)
try:
    ai_search = JobSearchAI()
    AI_ENABLED = True
except ValueError as e:
    logger.warning(f"AI search disabled: {e}")
    ai_search = None
    AI_ENABLED = False


class PrivacySettingsView(discord.ui.View):
    """View for managing privacy settings."""
    
    def __init__(self, user_id: int, current_setting: bool):
        super().__init__(timeout=300)  # 5 minute timeout
        self.user_id = user_id
        self.current_setting = current_setting
        
        # Update button styles based on current setting
        self.enable_button.style = discord.ButtonStyle.success if current_setting else discord.ButtonStyle.secondary
        self.disable_button.style = discord.ButtonStyle.danger if not current_setting else discord.ButtonStyle.secondary
    
    @discord.ui.button(label="✅ Enable Cross-User Search", style=discord.ButtonStyle.success)
    async def enable_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Enable cross-user search for this user."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ You can only change your own privacy settings.", ephemeral=True)
            return
        
        try:
            db_session = get_db_session()
            service = get_service(db_session)
            
            service.update_user_preferences(self.user_id, allow_cross_user_search=True)
            self.current_setting = True
            
            # Update button styles
            self.enable_button.style = discord.ButtonStyle.success
            self.disable_button.style = discord.ButtonStyle.secondary
            
            embed = discord.Embed(
                title="🔒 Privacy Settings Updated",
                description="✅ **Cross-user search enabled**\n\nYour application data can now be included in community analytics and aggregate searches by other users.",
                color=discord.Color.green()
            )
            embed.set_footer(text="Your data will be anonymized when shared with others")
            
            await interaction.response.edit_message(embed=embed, view=self)
            
            db_session.close()
            
        except Exception as e:
            logger.exception(f"Error updating privacy settings: {e}")
            await interaction.response.send_message("❌ An error occurred while updating settings.", ephemeral=True)
    
    @discord.ui.button(label="❌ Disable Cross-User Search", style=discord.ButtonStyle.secondary)
    async def disable_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Disable cross-user search for this user."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ You can only change your own privacy settings.", ephemeral=True)
            return
        
        try:
            db_session = get_db_session()
            service = get_service(db_session)
            
            service.update_user_preferences(self.user_id, allow_cross_user_search=False)
            self.current_setting = False
            
            # Update button styles
            self.enable_button.style = discord.ButtonStyle.secondary
            self.disable_button.style = discord.ButtonStyle.danger
            
            embed = discord.Embed(
                title="🔒 Privacy Settings Updated",
                description="❌ **Cross-user search disabled**\n\nYour application data will NOT be included in community analytics. Only you can search your own data.",
                color=discord.Color.red()
            )
            embed.set_footer(text="You can re-enable this at any time")
            
            await interaction.response.edit_message(embed=embed, view=self)
            
            db_session.close()
            
        except Exception as e:
            logger.exception(f"Error updating privacy settings: {e}")
            await interaction.response.send_message("❌ An error occurred while updating settings.", ephemeral=True)


class PaginationView(discord.ui.View):
    """Pagination view for list command with buttons to navigate pages."""
    
    def __init__(self, user_id: int, stage_filter: str | None = None, season_filter: str | None = None):
        super().__init__(timeout=300)  # 5 minute timeout
        self.user_id = user_id
        self.stage_filter = stage_filter
        self.season_filter = season_filter
        self.current_page = 1
        self.total_pages = 1
        self.limit = 15
        
    async def update_embed(self, interaction: discord.Interaction):
        """Update the embed with new page data."""
        try:
            db_session = get_db_session()
            service = get_service(db_session)
            
            # Calculate pagination
            offset = (self.current_page - 1) * self.limit
            
            # Get applications
            applications = service.list_applications(
                user_id=self.user_id,
                stage_filter=self.stage_filter,
                season_filter=self.season_filter,
                limit=self.limit,
                offset=offset,
            )
            
            # Get total count for pagination info
            total_count = service.get_application_count(self.user_id, self.stage_filter, self.season_filter)
            self.total_pages = (total_count + self.limit - 1) // self.limit
            
            # Format the list
            filters = []
            if self.stage_filter:
                filters.append(self.stage_filter)
            if self.season_filter:
                filters.append(self.season_filter)
            
            title = "Applications"
            if filters:
                title += f" - {' & '.join(filters)}"
            if self.total_pages > 1:
                title += f" (Page {self.current_page}/{self.total_pages})"
            
            formatted_list = format_application_list(applications, title)
            
            # Create embed
            embed = discord.Embed(
                title=title,
                description=formatted_list if applications else "No applications found.",
                color=discord.Color.blue(),
            )
            
            if self.total_pages > 1:
                embed.set_footer(
                    text=f"Page {self.current_page} of {self.total_pages} • Total: {total_count} applications"
                )
            
            # Update button states
            self.previous_button.disabled = self.current_page <= 1
            self.next_button.disabled = self.current_page >= self.total_pages
            
            await interaction.response.edit_message(embed=embed, view=self)
            
            db_session.close()
            
        except Exception as e:
            logger.exception(f"Error updating pagination: {e}")
            await interaction.response.send_message(
                "❌ An error occurred while updating the list.", ephemeral=True
            )
    
    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.primary)
    async def previous_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to previous page."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Only the command user can navigate pages.", ephemeral=True)
            return
            
        if self.current_page > 1:
            self.current_page -= 1
            await self.update_embed(interaction)
        else:
            await interaction.response.defer()
    
    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Go to next page."""
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Only the command user can navigate pages.", ephemeral=True)
            return
            
        if self.current_page < self.total_pages:
            self.current_page += 1
            await self.update_embed(interaction)
        else:
            await interaction.response.defer()
    
    async def on_timeout(self):
        """Called when the view times out."""
        # Disable all buttons when timeout occurs
        for item in self.children:
            item.disabled = True


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

    # Sync commands globally (takes longer to appear but more reliable)
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} commands globally")
        
        # Log all synced commands for debugging
        for command in synced:
            logger.info(f"- Synced command: /{command.name}")
            
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




# Autocomplete function for companies
async def company_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    """Autocomplete function for company names."""
    try:
        db_session = get_db_session()
        service = get_service(db_session)
        
        active_companies = service.get_active_companies(interaction.user.id)
        db_session.close()
        
        # Filter companies based on current input
        filtered = [
            company for company in active_companies 
            if current.lower() in company.lower()
        ][:25]  # Discord limits to 25 choices
        
        return [
            app_commands.Choice(name=company, value=company)
            for company in filtered
        ]
    except Exception as e:
        logger.exception(f"Error in company autocomplete: {e}")
        return []


@app_commands.command(name="search", description="Search your applications using natural language")
@app_commands.describe(
    query="Natural language question about your applications (e.g., 'How many Bloomberg interviews?')",
)
async def search_applications(
    interaction: discord.Interaction,
    query: str,
):
    """Search applications using AI-powered natural language processing."""
    if not AI_ENABLED:
        await interaction.response.send_message(
            "❌ AI search is not available. Please set the GEMINI_API_KEY environment variable.",
            ephemeral=True
        )
        return
    
    await interaction.response.defer(ephemeral=False)
    
    try:
        # Validate the query
        is_valid, error_msg = ai_search.validate_query(query)
        if not is_valid:
            logger.warning(f"Search query blocked for user {interaction.user.id}: {error_msg}")
            await interaction.followup.send(f"❌ {error_msg}")
            return
        
        db_session = get_db_session()
        
        # Get AI response
        response = await ai_search.search(db_session, interaction.user.id, query)
        
        # Create embed for the response
        embed = discord.Embed(
            title="🔍 Search Results",
            description=response,
            color=discord.Color.purple(),
        )
        embed.add_field(
            name="Query",
            value=f"*{query}*",
            inline=False
        )
        embed.set_footer(text="Powered by Gemini AI")
        
        await interaction.followup.send(embed=embed)
        
        db_session.close()
        
    except Exception as e:
        logger.exception(f"Error in search command: {e}")
        await interaction.followup.send(
            "❌ An error occurred while processing your search query."
        )


@app_commands.command(name="add", description="Add a new job application")
@app_commands.describe(
    company="Company name",
    role="Job role/title",
    season="Application season (default: Summer)",
    application_date="Date you applied as unix timestamp (optional, defaults to now)",
)
async def add_application(
    interaction: discord.Interaction, 
    company: str, 
    role: str,
    season: Literal["Summer", "Fall", "Winter", "Full time"] = "Summer",
    application_date: int | None = None,
):
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
            season=season,
            user_id=interaction.user.id,
            guild_id=guild_id,
            application_date=application_date,
        )

        embed = discord.Embed(
            title="✅ Application Added",
            description=f"**{company}** - {role}",
            color=discord.Color.green(),
        )
        embed.add_field(name="Stage", value="Applied", inline=True)
        embed.add_field(name="Season", value=season, inline=True)
        embed.add_field(
            name="Created", value=format_discord_timestamp(app.created_at, "f"), inline=True
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
    company="Company name (select from your applications)",
    stage="New stage",
    date="Date as unix timestamp (optional, defaults to now)",
)
@app_commands.autocomplete(company=company_autocomplete)
async def update_application(
    interaction: discord.Interaction,
    company: str,
    stage: Literal["Applied", "OA", "Phone", "On-site", "Offer", "Rejected", "Ghosted"],
    date: int | None = None,
):
    """Update the stage of a job application."""
    await interaction.response.defer(ephemeral=False)  # Public - celebrate progress!

    try:
        db_session = get_db_session()
        service = get_service(db_session)

        # Update the application
        new_stage = service.update_application_stage(
            company=company,
            stage=stage,
            user_id=interaction.user.id,
            date=date,
        )

        embed = discord.Embed(
            title="✅ Application Updated",
            description=f"**{company}** stage updated to **{stage}**",
            color=discord.Color.blue(),
        )
        embed.add_field(
            name="Date", value=format_discord_timestamp(new_stage.date, "f"), inline=True
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
    season="Filter by season (optional)",
)
async def list_applications(
    interaction: discord.Interaction,
    stage: Literal["Applied", "OA", "Phone", "On-site", "Offer", "Rejected", "Ghosted"]
    | None = None,
    season: Literal["Summer", "Fall", "Winter", "Full time"] | None = None,
):
    """List job applications with optional filtering and pagination buttons."""
    await interaction.response.defer(ephemeral=True)

    try:
        db_session = get_db_session()
        service = get_service(db_session)

        # Calculate pagination
        limit = 15
        offset = 0  # Always start from page 1

        # Get applications
        applications = service.list_applications(
            user_id=interaction.user.id,
            stage_filter=stage,
            season_filter=season,
            limit=limit,
            offset=offset,
        )

        # Get total count for pagination info
        total_count = service.get_application_count(interaction.user.id, stage, season)
        total_pages = (total_count + limit - 1) // limit

        # Format the list
        filters = []
        if stage:
            filters.append(stage)
        if season:
            filters.append(season)
        
        title = "Applications"
        if filters:
            title += f" - {' & '.join(filters)}"
        if total_pages > 1:
            title += f" (Page 1/{total_pages})"

        formatted_list = format_application_list(applications, title)

        # Create embed
        embed = discord.Embed(
            title=title,
            description=formatted_list if applications else "No applications found.",
            color=discord.Color.blue(),
        )

        if total_pages > 1:
            embed.set_footer(
                text=f"Page 1 of {total_pages} • Total: {total_count} applications"
            )

        # Create pagination view if there are multiple pages
        if total_pages > 1:
            view = PaginationView(user_id=interaction.user.id, stage_filter=stage, season_filter=season)
            view.current_page = 1
            view.total_pages = total_pages
            
            # Set initial button states
            view.previous_button.disabled = True  # First page, so disable previous
            view.next_button.disabled = False
            
            await interaction.followup.send(embed=embed, view=view)
        else:
            # No pagination needed
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
    company="Company name (select from your applications)",
    days="Days from now to remind (1-365)",
)
@app_commands.autocomplete(company=company_autocomplete)
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
            value=format_discord_timestamp(reminder.due_at, "f"),
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
            or csv_data == "Company,Role,Season,Current Stage,Created At,Last Updated"
        ):
            await interaction.followup.send("❌ No applications to export.")
            return

        # Create file
        filename = f"job_applications_{interaction.user.id}_{int(time.time())}.csv"

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


@app_commands.command(name="security", description="Manage your privacy settings")
async def security_settings(interaction: discord.Interaction):
    """Manage user privacy and security settings."""
    await interaction.response.defer(ephemeral=True)
    
    try:
        db_session = get_db_session()
        service = get_service(db_session)
        
        # Get current preferences
        prefs = service.get_user_preferences(interaction.user.id)
        
        # Create view with privacy toggle
        view = PrivacySettingsView(interaction.user.id, prefs.allow_cross_user_search)
        
        embed = discord.Embed(
            title="🔒 Privacy & Security Settings",
            description="Manage how your application data can be used in cross-user searches.",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Cross-User Search",
            value=f"**Status**: {'Enabled' if prefs.allow_cross_user_search else 'Disabled'}\n"
                  f"When enabled, other users can include your data in aggregate searches like "
                  f"'Who is in the Bloomberg process?' Your data will be anonymized as 'User_{interaction.user.id}'.",
            inline=False
        )
        
        embed.add_field(
            name="What This Means",
            value="• **Enabled**: Your applications appear in community analytics\n"
                  "• **Disabled**: Only you can search your own data\n"
                  "• **Always**: Your personal data stays private to you",
            inline=False
        )
        
        embed.set_footer(text="Use the buttons below to change your settings")
        
        await interaction.followup.send(embed=embed, view=view)
        
        db_session.close()
        
    except Exception as e:
        logger.exception(f"Error showing security settings: {e}")
        await interaction.followup.send(
            "❌ An error occurred while loading security settings."
        )


@app_commands.command(name="sync", description="Force sync bot commands (admin only)")
async def force_sync(interaction: discord.Interaction):
    """Force sync all bot commands with Discord."""
    await interaction.response.defer(ephemeral=True)
    
    try:
        synced = await bot.tree.sync()
        await interaction.followup.send(f"Successfully synced {len(synced)} commands")
        logger.info(f"Force synced {len(synced)} commands by {interaction.user}")
        
    except Exception as e:
        logger.exception(f"Error force syncing commands: {e}")
        await interaction.followup.send(
            "An error occurred while syncing commands."
        )


# Add commands to the bot's tree
bot.tree.add_command(search_applications)
bot.tree.add_command(add_application)
bot.tree.add_command(update_application)
bot.tree.add_command(list_applications)
bot.tree.add_command(todo_applications)
bot.tree.add_command(set_reminder)
bot.tree.add_command(view_stats)
bot.tree.add_command(export_applications)
bot.tree.add_command(test_reminder)
bot.tree.add_command(security_settings)
bot.tree.add_command(force_sync)


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
