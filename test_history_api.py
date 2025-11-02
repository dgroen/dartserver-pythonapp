#!/usr/bin/env python3
"""Test the game history API"""

import sys
from pathlib import Path

from dotenv import load_dotenv

from src.core.database_models import GameResult
from src.core.database_service import DatabaseService

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

load_dotenv(".env.test")

db_service = DatabaseService()

# Test 1: Get recent games for testuser001
print("Test 1: Get recent games for username='testuser001'")
games = db_service.get_recent_games(limit=10, username="testuser001")
print(f"Found {len(games)} games:")
for game in games:
    winner = game.get("winner", "N/A")
    player_count = game["player_count"]
    print(
        f"  - {game['game_session_id'][:8]}... | {game['game_type']} | "
        f"Winner: {winner} | Players: {player_count}",
    )

# Test 2: Get all games (no username filter)
print("\nTest 2: Get all recent games (no username filter)")
all_games = db_service.get_recent_games(limit=10)
print(f"Found {len(all_games)} games total")

# Test 3: Check player_id 5
print("\nTest 3: Get games for player_id=5")

session = db_service.db_manager.get_session()
player_games = session.query(GameResult).filter_by(player_id=5).all()
print(f"Found {len(player_games)} games for player_id=5")
session.close()
