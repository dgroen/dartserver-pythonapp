#!/usr/bin/env python3
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.core.database_models import DatabaseManager, GameResult, Player

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/dartsdb",
)

db_manager = DatabaseManager(DATABASE_URL)
session = db_manager.get_session()

try:
    # Check players 11 and 21
    for player_id in [11, 21]:
        player = session.query(Player).filter_by(id=player_id).first()
        if player:
            games = session.query(GameResult).filter_by(player_id=player.id).count()
            print(f"\nPlayer ID {player_id}:")
            print(f"  Name: {player.name}")
            print(f"  Username: {player.username}")
            print(f"  Email: {player.email}")
            print(f"  Games: {games}")
        else:
            print(f"\nPlayer ID {player_id}: NOT FOUND")

finally:
    session.close()
