"""
Formatting utilities for the job tracker bot.
"""


def format_discord_timestamp(timestamp: int, format_type: str = "F") -> str:
    """
    Format a unix timestamp for Discord display.
    
    Args:
        timestamp: Unix timestamp
        format_type: Discord timestamp format type
            - "t": Short time (16:20)
            - "T": Long time (16:20:30)
            - "d": Short date (20/04/2021)
            - "D": Long date (20 April 2021)
            - "f": Short datetime (20 April 2021 16:20)
            - "F": Long datetime (Tuesday, 20 April 2021 16:20)
            - "R": Relative time (2 months ago)
    
    Returns:
        Discord timestamp markdown string
    """
    return f"<t:{timestamp}:{format_type}>"


def create_ascii_bar_chart(
    data: dict[str, int], title: str = "Application Statistics", max_width: int = 40
) -> str:
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


def format_application_list(applications: list, title: str = "Applications") -> str:
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
        if app.season != "Full time":
            line += f" ({app.season})"
        lines.append(line)
        lines.append(f"    └─ Stage: {stage_name}")

        if current_stage:
            lines.append(
                f"    └─ Updated: {format_discord_timestamp(current_stage.date, 'f')}"
            )

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

    message = "🔔 **Job Application Reminder**\n\n"
    message += f"**Company:** {application.company}\n"
    message += f"**Role:** {application.role}\n"
    if application.season != "Full time":
        message += f"**Season:** {application.season}\n"
    message += f"**Current Stage:** {stage_name}\n"

    if current_stage:
        message += f"**Last Updated:** {format_discord_timestamp(current_stage.date, 'f')} ({format_discord_timestamp(current_stage.date, 'R')})\n"

    message += "\n💡 Consider following up or updating the application status!"

    return message


def format_stage_choices() -> list[dict[str, str]]:
    """
    Format stage choices for Discord slash command options.

    Returns:
        List of choice dictionaries for Discord
    """
    from ..models import Stage  # noqa: PLC0415

    choices = []
    for stage in Stage.VALID_STAGES:
        choices.append(
            {
                "name": stage,
                "value": stage,
            }
        )

    return choices


def format_season_choices() -> list[dict[str, str]]:
    """
    Format season choices for Discord slash command options.

    Returns:
        List of choice dictionaries for Discord
    """
    from ..models import Application  # noqa: PLC0415

    choices = []
    for season in Application.VALID_SEASONS:
        choices.append(
            {
                "name": season,
                "value": season,
            }
        )

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

    return text[: max_length - 3] + "..."


def format_stats_summary(stats: dict[str, int]) -> str:
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
