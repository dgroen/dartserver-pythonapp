#!/usr/bin/env python3
"""
Script to manually add the bull_practice game type to the database.
This is a one-time fix script that can be run if the automatic initialization didn't work.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

from src.core.database_models import DatabaseManager, GameType

load_dotenv()


def add_bull_practice_game_type():
    """Add bull_practice game type to the database if it doesn't exist"""

    # Get database URL from environment
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/dartsdb",
    )

    print(f"Connecting to database: {database_url}")

    # Initialize database manager
    db_manager = DatabaseManager(database_url)
    session = db_manager.get_session()

    try:
        # Check if bull_practice already exists
        existing = session.query(GameType).filter_by(name="bull_practice").first()

        if existing:
            print("✅ bull_practice game type already exists!")
            print(f"   ID: {existing.id}")
            print(f"   Name: {existing.name}")
            print(f"   Description: {existing.description}")
        else:
            # Add the new game type
            bull_practice = GameType(
                name="bull_practice",
                description=(
                    "Bull Practice - training game to practice hitting bulls - "
                    "auto-restarts after each round"
                ),
            )
            session.add(bull_practice)
            session.commit()
            print("✅ Successfully added bull_practice game type!")
            print(f"   ID: {bull_practice.id}")
            print(f"   Name: {bull_practice.name}")
            print(f"   Description: {bull_practice.description}")

        # Show all game types
        print("\n📋 All game types in database:")
        all_game_types = session.query(GameType).order_by(GameType.id).all()
        for gt in all_game_types:
            print(f"   {gt.id}. {gt.name} - {gt.description}")

    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        return 1
    finally:
        session.close()

    return 0


if __name__ == "__main__":
    sys.exit(add_bull_practice_game_type())
