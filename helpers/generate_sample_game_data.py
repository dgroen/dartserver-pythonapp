#!/usr/bin/env python3
"""
Generate sample game data for testing results page in local development.
This script creates test games for the bypass_user when AUTH_DISABLED=true
"""

import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Import database models
from src.core.database_models import GameResult, GameType, Player, Score


def generate_sample_data():
    """Generate sample game data for testing"""
    # Get database URL
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("❌ DATABASE_URL not set in environment")
        return False

    try:
        # Create engine and session
        engine = create_engine(db_url)
        session_factory = sessionmaker(bind=engine)
        session = session_factory()

        # Get or create bypass_user player
        player = session.query(Player).filter(Player.username == "bypass_user").first()
        if not player:
            player = Player(
                username="bypass_user",
                email="bypass@local.dev",
                name="Bypass User",
            )
            session.add(player)
            session.commit()
            print(f"✅ Created bypass_user player (ID: {player.id})")
        else:
            print(f"✅ Found existing bypass_user player (ID: {player.id})")

        # Create sample opponents
        opponent1 = session.query(Player).filter(Player.username == "opponent1").first()
        if not opponent1:
            opponent1 = Player(
                username="opponent1",
                email="opponent1@local.dev",
                name="Opponent 1",
            )
            session.add(opponent1)
            session.commit()

        opponent2 = session.query(Player).filter(Player.username == "opponent2").first()
        if not opponent2:
            opponent2 = Player(
                username="opponent2",
                email="opponent2@local.dev",
                name="Opponent 2",
            )
            session.add(opponent2)
            session.commit()

        # Get or create game types
        game_301 = session.query(GameType).filter(GameType.name == "301").first()
        if not game_301:
            game_301 = GameType(name="301", description="301 dart game")
            session.add(game_301)
            session.commit()

        game_501 = session.query(GameType).filter(GameType.name == "501").first()
        if not game_501:
            game_501 = GameType(name="501", description="501 dart game")
            session.add(game_501)
            session.commit()

        game_cricket = session.query(GameType).filter(GameType.name == "Cricket").first()
        if not game_cricket:
            game_cricket = GameType(name="Cricket", description="Cricket dart game")
            session.add(game_cricket)
            session.commit()

        # Create sample games
        now = datetime.now(tz=timezone.utc)
        sample_games = [
            {
                "game_type": game_301,
                "players": [player, opponent1],
                "winner_id": player.id,
                "winner_name": "Bypass User",
                "time_offset": 1,  # 1 hour ago
                "duration_minutes": 15,
            },
            {
                "game_type": game_501,
                "players": [player, opponent1, opponent2],
                "winner_id": opponent2.id,
                "winner_name": "Opponent 2",
                "time_offset": 3,  # 3 hours ago
                "duration_minutes": 25,
            },
            {
                "game_type": game_cricket,
                "players": [player, opponent2],
                "winner_id": player.id,
                "winner_name": "Bypass User",
                "time_offset": 5,  # 5 hours ago
                "duration_minutes": 20,
            },
            {
                "game_type": game_301,
                "players": [player, opponent1, opponent2],
                "winner_id": player.id,
                "winner_name": "Bypass User",
                "time_offset": 24,  # 1 day ago
                "duration_minutes": 18,
            },
            {
                "game_type": game_501,
                "players": [player, opponent1],
                "winner_id": opponent1.id,
                "winner_name": "Opponent 1",
                "time_offset": 48,  # 2 days ago
                "duration_minutes": 30,
            },
        ]

        created_count = 0
        for sample in sample_games:
            # Check if game already exists
            existing = (
                session.query(GameResult)
                .filter(
                    GameResult.started_at
                    == (now - timedelta(hours=sample["time_offset"])).replace(minute=0, second=0),
                )
                .first()
            )
            if existing:
                print(f"⏭️  Game already exists for {sample['game_type'].name}")
                continue

            start_time = now - timedelta(hours=sample["time_offset"])
            finish_time = start_time + timedelta(minutes=sample["duration_minutes"])
            game_session_id = f"sample_{start_time.timestamp()}"

            # Create GameResult for each player
            for player_order, p in enumerate(sample["players"]):
                is_winner = p.id == sample["winner_id"]
                # Set start score based on game type
                game_type_name = sample["game_type"].name
                if game_type_name == "301":
                    start_score = 301
                elif game_type_name == "501":
                    start_score = 501
                elif game_type_name == "401":
                    start_score = 401
                else:
                    start_score = 0  # Cricket or other types
                final_score = 0 if is_winner else 50 + (player_order * 10)

                game_result = GameResult(
                    game_type_id=sample["game_type"].id,
                    player_id=p.id,
                    player_order=player_order,
                    start_score=start_score,
                    final_score=final_score,
                    is_winner=is_winner,
                    double_out_enabled=False,
                    started_at=start_time,
                    finished_at=finish_time,
                    game_session_id=game_session_id,
                )
                session.add(game_result)
                session.flush()

                # Create a sample score record for game replay
                score = Score(
                    game_result_id=game_result.id,
                    player_id=p.id,
                    throw_sequence=1,
                    turn_number=1,
                    throw_in_turn=1,
                    base_score=10,
                    multiplier="SINGLE",
                    multiplier_value=1,
                    actual_score=10,
                    score_before=start_score,
                    score_after=start_score - 10,
                    dartboard_sends_actual_score=False,
                )
                session.add(score)

            session.commit()
            created_count += 1
            print(
                f"✅ Created {sample['game_type'].name} game "
                f"({sample['time_offset']}h ago, winner: {sample['winner_name']})",
            )

        session.close()

        if created_count > 0:
            print(f"\n✨ Successfully created {created_count} sample games!")
            print("\n📊 You can now:")
            print("   1. Visit http://localhost:5000/history to see game history")
            print("   2. Visit http://localhost:5000/mobile/results to see mobile results")
            print("   3. Check API at http://localhost:5000/api/player/history")
            return True
        print("\n⏭️  Sample games already exist!")
        return True

    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🎯 Darts Game - Sample Data Generator")
    print("=" * 50)
    success = generate_sample_data()
    sys.exit(0 if success else 1)
