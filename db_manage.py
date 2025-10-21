#!/usr/bin/env python3
"""
Database Management Script for Darts Game Application

This script provides convenient commands for managing the database,
including migrations, seeding initial data, and viewing database status.
"""

import datetime
import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from src.core.database_models import GameType, Player

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/dartsdb")


def get_session():
    """Create and return a database session."""
    engine = create_engine(DATABASE_URL)
    session = sessionmaker(bind=engine)
    return session()


def seed_game_types():
    """Seed the database with initial game types."""
    session = get_session()

    game_types = [
        GameType(
            name="301",
            description="Standard 301 game - race to zero from 301 points",
            created_at=datetime.datetime.now(tz=datetime.timezone.utc),
        ),
        GameType(
            name="401",
            description="Standard 401 game - race to zero from 401 points",
            created_at=datetime.datetime.now(tz=datetime.timezone.utc),
        ),
        GameType(
            name="501",
            description="Standard 501 game - race to zero from 501 points",
            created_at=datetime.datetime.now(tz=datetime.timezone.utc),
        ),
        GameType(
            name="cricket",
            description="Cricket game - close numbers 15-20 and bullseye",
            created_at=datetime.datetime.now(tz=datetime.timezone.utc),
        ),
    ]

    try:
        # Check if game types already exist
        existing = session.query(GameType).count()
        if existing > 0:
            print(f"Game types already exist ({existing} found). Skipping seed.")
            return

        # Add game types
        for gt in game_types:
            session.add(gt)

        session.commit()
        print(f"✓ Successfully seeded {len(game_types)} game types")

        # Display seeded data
        for gt in game_types:
            print(f"  - {gt.name}: {gt.description}")

    except Exception as e:
        session.rollback()
        print(f"✗ Error seeding game types: {e}")
    finally:
        session.close()


def show_status():
    """Show database connection status and table information."""
    try:
        session = get_session()

        print("=" * 60)
        print("DATABASE STATUS")
        print("=" * 60)
        print(f"Database URL: {DATABASE_URL}")
        print()

        # Test connection
        result = session.execute(text("SELECT version()"))
        version = result.scalar()
        print("✓ Connection successful")
        print(f"PostgreSQL Version: {version.split(',')[0]}")
        print()

        # Show table counts
        print("Table Statistics:")
        print("-" * 60)

        tables = [
            ("player", Player),
            ("gametype", GameType),
        ]

        for table_name, model in tables:
            try:
                count = session.query(model).count()
                print(f"  {table_name:20s}: {count:6d} records")
            except Exception as e:
                print(f"  {table_name:20s}: Error - {e}")

        # Show gameresults and scores counts using raw SQL
        try:
            result = session.execute(text("SELECT COUNT(*) FROM gameresults"))
            count = result.scalar()
            print(f"  {'gameresults':20s}: {count:6d} records")
        except Exception as e:
            print(f"  {'gameresults':20s}: Error - {e}")

        try:
            result = session.execute(text("SELECT COUNT(*) FROM scores"))
            count = result.scalar()
            print(f"  {'scores':20s}: {count:6d} records")
        except Exception as e:
            print(f"  {'scores':20s}: Error - {e}")

        print()

        # Show recent games
        try:
            result = session.execute(
                text(
                    """
                SELECT
                    game_session_id,
                    COUNT(DISTINCT player_id) as player_count,
                    MAX(started_at) as started_at,
                    MAX(finished_at) as finished_at
                FROM gameresults
                GROUP BY game_session_id
                ORDER BY MAX(started_at) DESC
                LIMIT 5
            """,
                ),
            )

            games = result.fetchall()
            if games:
                print("Recent Games:")
                print("-" * 60)
                for game in games:
                    session_id = game[0][:8] + "..."
                    players = game[1]
                    started = game[2].strftime("%Y-%m-%d %H:%M:%S") if game[2] else "N/A"
                    finished = game[3].strftime("%Y-%m-%d %H:%M:%S") if game[3] else "In Progress"
                    print(
                        f"{session_id} | {players} players | Started: \
                            {started} | Finished: {finished}",
                    )
                print()
        except Exception as e:
            print(f"Could not fetch recent games: {e}")
            print()

        session.close()

    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        sys.exit(1)


def show_help():
    """Show help message."""
    print(
        """
Database Management Script
==========================

Usage: python db_manage.py <command>

Commands:
  status      Show database connection status and statistics
  seed        Seed the database with initial game types
  help        Show this help message

Examples:
  python db_manage.py status
  python db_manage.py seed
For migration commands, use Alembic directly:
  alembic current           # Show current migration
  alembic history           # Show migration history

See DATABASE_MIGRATIONS.md for more information.
""",
    )


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "status":
        show_status()
    elif command == "seed":
        seed_game_types()
    elif command == "help":
        show_help()
    else:
        print(f"Unknown command: {command}")
        show_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
