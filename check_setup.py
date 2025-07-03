#!/usr/bin/env python3
"""
Setup verification script for the Job Tracker Bot.
Checks if all dependencies are installed and basic functionality works.
"""

import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.12 or higher."""
    print("Checking Python version...")
    if sys.version_info < (3, 12):
        print(f"❌ Python 3.12+ required, but you have {sys.version_info.major}.{sys.version_info.minor}")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} is supported")
    return True

def check_dependencies():
    """Check if all required dependencies are available."""
    print("\nChecking dependencies...")
    required_packages = [
        "discord",
        "sqlalchemy",
        "aiosqlite",
        "apscheduler",
        "dotenv",
        "pydantic",
        "alembic"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - not installed")
            missing.append(package)
    
    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print("Run 'poetry install' or 'pip install -r requirements.txt' to install them.")
        return False
    
    return True

def check_database():
    """Check if database models can be imported and initialized."""
    print("\nChecking database setup...")
    try:
        from models import Base, Application, Stage, Reminder, create_engine_and_session, init_database
        
        # Try to create an in-memory database
        engine, session_local = create_engine_and_session("sqlite:///:memory:")
        init_database(engine)
        
        print("✅ Database models work correctly")
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def check_services():
    """Check if service layer works correctly."""
    print("\nChecking service layer...")
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
        app = service.add_application("Test Company", "Test Role", 123456)
        
        print("✅ Service layer works correctly")
        session.close()
        return True
    except Exception as e:
        print(f"❌ Service layer failed: {e}")
        return False

def check_formatting():
    """Check if formatting utilities work."""
    print("\nChecking formatting utilities...")
    try:
        from utils.formatting import create_ascii_bar_chart, format_stats_summary
        
        test_data = {"Applied": 5, "OA": 3, "Phone": 2}
        chart = create_ascii_bar_chart(test_data)
        summary = format_stats_summary(test_data)
        
        print("✅ Formatting utilities work correctly")
        return True
    except Exception as e:
        print(f"❌ Formatting utilities failed: {e}")
        return False

def check_env_file():
    """Check if .env file exists and has required variables."""
    print("\nChecking environment configuration...")
    env_file = Path(".env")
    
    if not env_file.exists():
        print("⚠️  .env file not found")
        print("   Copy env.example to .env and fill in your Discord bot token")
        return False
    
    try:
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        token = os.getenv("DISCORD_TOKEN")
        
        if not token or token == "your_bot_token_here":
            print("⚠️  DISCORD_TOKEN not set in .env file")
            print("   Add your Discord bot token to the .env file")
            return False
        
        print("✅ Environment configuration looks good")
        return True
    except Exception as e:
        print(f"❌ Environment setup failed: {e}")
        return False

def run_tests():
    """Run the test suite."""
    print("\nRunning tests...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-v", "tests/"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            print("✅ All tests passed")
            return True
        else:
            print("❌ Some tests failed")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        return False

def main():
    """Main setup verification function."""
    print("🔍 Job Tracker Bot Setup Verification")
    print("=" * 40)
    
    checks = [
        check_python_version,
        check_dependencies,
        check_database,
        check_services,
        check_formatting,
        check_env_file,
        run_tests
    ]
    
    passed = 0
    total = len(checks)
    
    for check in checks:
        if check():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"📊 Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All checks passed! Your bot is ready to run.")
        print("   Start the bot with: python bot.py")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 