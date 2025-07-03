# Job Tracker Bot

A Discord bot for tracking job applications with stages, reminders, and analytics. Built with Python 3.12, discord.py v2, SQLAlchemy, and SQLite.

## Features

- **📝 Add Applications**: Track job applications with company and role
- **🔄 Update Stages**: Move applications through stages (Applied → OA → Phone → On-site → Offer → Rejected)
- **📊 Analytics**: View application statistics with ASCII bar charts
- **⏰ Reminders**: Set DM reminders for follow-ups
- **📋 List & Filter**: View applications with pagination and stage filtering
- **🔔 Todo List**: See applications needing attention (>7 days old)
- **📄 Export**: Export data to CSV format

## Quick Start

### Prerequisites

- Python 3.12 or higher
- Discord Bot Token ([Create one here](https://discord.com/developers/applications))
- Poetry (recommended) or pip

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd job-tracker-bot
   ```

2. **Install dependencies**
   ```bash
   # Using Poetry (recommended)
   poetry install
   
   # Or using pip
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   Create a `.env` file in the project root:
   ```env
   DISCORD_TOKEN=your_bot_token_here
   DATABASE_URL=sqlite:///jobs.db
   MULTI_GUILD_SUPPORT=false
   LOG_LEVEL=INFO
   ```

4. **Run the bot**
   ```bash
   # Using Poetry (recommended)
   poetry run job-tracker-bot
   
   # Or using the run script
   python run_bot.py
   
   # Or directly
   python -m src.job_tracker.bot
   ```

## Discord Bot Setup

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" section
4. Create a bot and copy the token
5. Enable the following bot permissions:
   - Send Messages
   - Use Slash Commands
   - Send Messages in Threads
   - Send Private Messages
6. Invite the bot to your server using the OAuth2 URL generator

## Commands

### Core Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/add` | Add a new job application | `/add company:Google role:Software Engineer` |
| `/update` | Update application stage | `/update company:Google stage:OA date:2024-01-15` |
| `/list` | List applications (with optional filtering) | `/list stage:Applied page:1` |
| `/todo` | Show applications needing attention | `/todo` |
| `/remind` | Set a reminder for an application | `/remind company:Google days:3` |
| `/stats` | View application statistics | `/stats` |
| `/export` | Export applications to CSV | `/export` |

### Valid Stages

- **Applied**: Initial application submitted
- **OA**: Online Assessment/Coding Challenge
- **Phone**: Phone/Video Interview
- **On-site**: On-site/Final Interview
- **Offer**: Job offer received
- **Rejected**: Application rejected

## Examples

### Basic Usage Flow

1. **Add an application**
   ```
   /add company:Google role:Software Engineer
   ```

2. **Update the stage**
   ```
   /update company:Google stage:OA
   ```

3. **Set a reminder**
   ```
   /remind company:Google days:7
   ```

4. **Check your applications**
   ```
   /list
   ```

5. **View statistics**
   ```
   /stats
   ```

### Advanced Usage

- **Filter by stage**: `/list stage:Phone`
- **Paginate results**: `/list page:2`
- **Set date for stage**: `/update company:Meta stage:Offer date:2024-01-20`
- **Export data**: `/export`

## Database Schema

### Applications Table
- `id` - Primary key
- `company` - Company name
- `role` - Job role/title
- `created_at` - When application was added
- `guild_id` - Discord guild ID (for multi-guild support)
- `user_id` - Discord user ID

### Stages Table
- `id` - Primary key
- `app_id` - Foreign key to applications
- `stage` - Stage name
- `date` - When stage was reached

### Reminders Table
- `id` - Primary key
- `app_id` - Foreign key to applications
- `due_at` - When reminder should be sent
- `sent` - Whether reminder has been sent

## Development

### Running Tests

```bash
# Using Poetry
poetry run pytest

# Or directly
python -m pytest

# With coverage
poetry run pytest --cov=. --cov-report=html
```

### Code Quality

```bash
# Format code
poetry run black .

# Lint code
poetry run ruff check .

# Type checking
poetry run mypy .
```

### Database Migrations

```bash
# Create a new migration
poetry run alembic revision --autogenerate -m "Description"

# Apply migrations
poetry run alembic upgrade head

# Rollback migrations
poetry run alembic downgrade -1
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DISCORD_TOKEN` | Discord bot token | Required |
| `DATABASE_URL` | Database connection string | `sqlite:///jobs.db` |
| `MULTI_GUILD_SUPPORT` | Enable multi-guild support | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Multi-Guild Support

To enable multi-guild support (separate data per Discord server):
1. Set `MULTI_GUILD_SUPPORT=true` in your `.env` file
2. Restart the bot
3. Each guild will have isolated application data

## Deployment

### Local Development
Follow the Quick Start guide above.

### Production Deployment

#### Heroku
1. Create a Heroku app
2. Set environment variables in Heroku dashboard
3. Deploy using Git or GitHub integration
4. Use Heroku Postgres for production database

#### Railway/Render
1. Connect your repository
2. Set environment variables
3. Deploy automatically

#### Docker
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY . .

RUN pip install poetry && poetry install --no-dev

CMD ["poetry", "run", "job-tracker-bot"]
```

## Features Roadmap

### Current (v1.0)
- ✅ Basic CRUD operations
- ✅ Stage management
- ✅ Reminders system
- ✅ Statistics and analytics
- ✅ CSV export
- ✅ Unit tests

### Planned (v2.0)
- 🔄 Web dashboard
- 🔄 Integration with job boards
- 🔄 Interview preparation checklists
- 🔄 Application deadline tracking
- 🔄 Email notifications
- 🔄 Advanced analytics and reporting

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run tests and ensure they pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- **Issues**: Create an issue on GitHub
- **Questions**: Ask in the repository discussions
- **Feature Requests**: Create an issue with the "enhancement" label

## Changelog

### v1.0.0 (2024-01-01)
- Initial release
- Core application tracking functionality
- Reminder system
- Statistics and analytics
- CSV export
- Comprehensive test suite

---

**Happy job hunting! 🎯** 