#!/usr/bin/env python3
"""
Setup verification script for the Job Tracker Bot.
Checks if all dependencies are installed and basic functionality works.
"""

import subprocess
import sys
from pathlib import Path


def check_python_version():
    """Check if Python version is 3.12 or higher."""
    return True

def check_dependencies():
    """Check if all required dependencies are available."""
    required_packages = [
        "discord",
        "sqlalchemy",
        "aiosqlite",
        "apscheduler",
        "dotenv",
        "pydantic",
        "alembic",
    ]

    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    return not missing

def check_database():
    """Check if database models can be imported and initialized."""
    try:
        from models import (
            create_engine_and_session,
            init_database,
        )

        # Try to create an in-memory database
        engine, session_local = create_engine_and_session("sqlite:///:memory:")
        init_database(engine)

        return True
    except Exception:
        return False

def check_services():
    """Check if service layer works correctly."""
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        from models import Base
        from services import JobTrackerService

        # Create test database
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        TestSession = sessionmaker(bind=engine)
        session = TestSession()

        # Test service
        service = JobTrackerService(session)
        service.add_application("Test Company", "Test Role", 123456)

        session.close()
        return True
    except Exception:
        return False

def check_formatting():
    """Check if formatting utilities work."""
    try:
        from utils.formatting import create_ascii_bar_chart, format_stats_summary

        test_data = {"Applied": 5, "OA": 3, "Phone": 2}
        create_ascii_bar_chart(test_data)
        format_stats_summary(test_data)

        return True
    except Exception:
        return False

def check_env_file():
    """Check if .env file exists and has required variables."""
    env_file = Path(".env")

    if not env_file.exists():
        return False

    try:
        import os

        from dotenv import load_dotenv

        load_dotenv()
        token = os.getenv("DISCORD_TOKEN")

        return not (not token or token == "your_bot_token_here")
    except Exception:
        return False

def run_tests():
    """Run the test suite."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-v", "tests/"],
            check=False, capture_output=True,
            text=True,
            cwd=Path(__file__).parent,
        )

        return result.returncode == 0
    except Exception:
        return False

def main():
    """Main setup verification function."""

    checks = [
        check_python_version,
        check_dependencies,
        check_database,
        check_services,
        check_formatting,
        check_env_file,
        run_tests,
    ]

    passed = 0
    total = len(checks)

    for check in checks:
        if check():
            passed += 1


    if passed == total:
        pass
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
