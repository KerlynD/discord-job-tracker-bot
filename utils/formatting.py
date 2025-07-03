"""
Formatting utilities for the job tracker bot.
"""
from typing import Dict, List
import math


def create_ascii_bar_chart(data: Dict[str, int], title: str = "Application Statistics", max_width: int = 40) -> str:
    """
    Create an ASCII bar chart from a dictionary of data.
    
    Args:
        data: Dictionary with labels as keys and counts as values
        title: Title for the chart
        max_width: Maximum width of the bars in characters
        
    Returns:
        Formatted ASCII bar chart as a string
    """
    if not data:
        return f"**{title}**\n```\nNo data available\n```"
    
    # Find the maximum value for scaling
    max_value = max(data.values())
    if max_value == 0:
        return f"**{title}**\n```\nNo applications found\n```"
    
    # Create the chart
    lines = [title, "=" * len(title), ""]
    
    # Sort by value (descending) for better visual
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
    
    for label, count in sorted_data:
        # Calculate bar length
        bar_length = int((count / max_value) * max_width)
        
        # Create the bar
        bar = "█" * bar_length
        
        # Format the line
        line = f"{label:>10} │{bar:<{max_width}} {count:>3}"
        lines.append(line)
    
    # Add summary
    total = sum(data.values())
    lines.extend(["", f"Total: {total} applications"])
    
    return "```\n" + "\n".join(lines) + "\n```"


def format_application_list(applications: List, title: str = "Applications") -> str:
    """
    Format a list of applications for Discord display.
    
    Args:
        applications: List of Application objects
        title: Title for the list
        
    Returns:
        Formatted string suitable for Discord
    """
    if not applications:
        return f"**{title}**\n```\nNo applications found\n```"
    
    lines = [f"**{title}**", ""]
    
    for i, app in enumerate(applications, 1):
        current_stage = app.current_stage
        stage_name = current_stage.stage if current_stage else "Unknown"
        
        # Format the application entry
        line = f"{i:>2}. **{app.company}** - {app.role}"
        lines.append(line)
        lines.append(f"    └─ Stage: {stage_name}")
        
        if current_stage:
            lines.append(f"    └─ Updated: {current_stage.date.strftime('%Y-%m-%d %H:%M')}")
        
        lines.append("")  # Empty line for spacing
    
    return "\n".join(lines)


def format_reminder_message(application, reminder) -> str:
    """
    Format a reminder message for DM.
    
    Args:
        application: Application object
        reminder: Reminder object
        
    Returns:
        Formatted reminder message
    """
    current_stage = application.current_stage
    stage_name = current_stage.stage if current_stage else "Unknown"
    
    message = f"🔔 **Job Application Reminder**\n\n"
    message += f"**Company:** {application.company}\n"
    message += f"**Role:** {application.role}\n"
    message += f"**Current Stage:** {stage_name}\n"
    
    if current_stage:
        days_since_update = (reminder.due_at - current_stage.date).days
        message += f"**Last Updated:** {current_stage.date.strftime('%Y-%m-%d')} ({days_since_update} days ago)\n"
    
    message += f"\n💡 Consider following up or updating the application status!"
    
    return message


def format_stage_choices() -> List[Dict[str, str]]:
    """
    Format stage choices for Discord slash command options.
    
    Returns:
        List of choice dictionaries for Discord
    """
    from models import Stage
    
    choices = []
    for stage in Stage.VALID_STAGES:
        choices.append({
            "name": stage,
            "value": stage
        })
    
    return choices


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to fit within Discord's limits.
    
    Args:
        text: Text to truncate
        max_length: Maximum length allowed
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."


def format_stats_summary(stats: Dict[str, int]) -> str:
    """
    Format a brief stats summary for quick display.
    
    Args:
        stats: Dictionary of stage counts
        
    Returns:
        Formatted summary string
    """
    if not stats:
        return "No applications tracked yet"
    
    total = sum(stats.values())
    summary_parts = []
    
    for stage, count in stats.items():
        percentage = (count / total) * 100
        summary_parts.append(f"{stage}: {count} ({percentage:.1f}%)")
    
    return f"**Total: {total}** | " + " | ".join(summary_parts) 