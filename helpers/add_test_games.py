#!/usr/bin/env python3
"""
Add test game data to the database for testing history/dashboard
"""

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

load_dotenv()

from src.core.database_models import GameResult, GameType, Player, Score
from src.core.database_service import DatabaseService


def add_test_games():
    """Add test game data for testuser001"""

    db_service = DatabaseService()
    session = db_service.db_manager.get_session()

    try:
        # Get or create testuser001
        player = session.query(Player).filter_by(username="testuser001").first()
        if not player:
            print("Player 'testuser001' not found. Creating...")
            player = Player(
                username="testuser001",
                name="Test user001",
                email="test.user.001@letsplaydarts.eu",
            )
            session.add(player)
            session.flush()
            print(f"Created player: {player.username} (ID: {player.id})")
        else:
            print(f"Found player: {player.username} (ID: {player.id})")

        # Get game type 301
        game_type = session.query(GameType).filter_by(name="301").first()
        if not game_type:
            print("Game type '301' not found. Creating...")
            game_type = GameType(name="301", display_name="301")
            session.add(game_type)
            session.flush()
            print(f"Created game type: {game_type.name} (ID: {game_type.id})")
        else:
            print(f"Found game type: {game_type.name} (ID: {game_type.id})")

        # Create 5 test games
        print("\nCreating test games...")
        base_time = datetime.now(tz=timezone.utc) - timedelta(days=5)

        for i in range(5):
            game_session_id = str(uuid.uuid4())
            started_at = base_time + timedelta(days=i, hours=2)
            finished_at = started_at + timedelta(minutes=15 + i * 2)

            # Create game result
            game_result = GameResult(
                game_session_id=game_session_id,
                player_id=player.id,
                game_type_id=game_type.id,
                player_order=0,  # Single player games for now
                start_score=301,
                started_at=started_at,
                finished_at=finished_at,
                is_winner=(i % 2 == 0),  # Win every other game
                final_score=0 if (i % 2 == 0) else 50,  # Winner gets 0, loser gets remaining points
                double_out_enabled=True,
            )
            session.add(game_result)
            session.flush()  # Get the game_result.id

            # Create some sample scores for this game
            remaining = 301
            for throw_seq in range(1, 16):  # 15 throws (5 turns x 3 throws)
                turn_number = (throw_seq - 1) // 3 + 1
                throw_in_turn = (throw_seq - 1) % 3 + 1

                # Mix of scores
                base_score = 20 if throw_in_turn == 1 else (15 if throw_in_turn == 2 else 18)
                multiplier_type = "TRIPLE" if throw_in_turn == 1 else "SINGLE"
                multiplier_val = 3 if throw_in_turn == 1 else 1
                actual_score = base_score * multiplier_val

                score_before = remaining
                remaining = max(0, remaining - actual_score)
                score_after = remaining

                score = Score(
                    game_result_id=game_result.id,
                    player_id=player.id,
                    throw_sequence=throw_seq,
                    turn_number=turn_number,
                    throw_in_turn=throw_in_turn,
                    base_score=base_score,
                    multiplier=multiplier_type,
                    multiplier_value=multiplier_val,
                    actual_score=actual_score,
                    score_before=score_before,
                    score_after=score_after,
                    dartboard_sends_actual_score=True,
                    is_bust=False,
                    is_finish=(remaining == 0),
                    thrown_at=started_at + timedelta(seconds=throw_seq * 10),
                )
                session.add(score)

                if remaining == 0:
                    break

            print(f"  Game {i+1}: {game_session_id} - {'WON' if game_result.is_winner else 'LOST'}")

        session.commit()
        print("\n✅ Successfully created 5 test games with scores!")

        # Verify the data
        print("\nVerifying data...")
        game_count = session.query(GameResult).filter_by(player_id=player.id).count()
        score_count = session.query(Score).filter_by(player_id=player.id).count()
        print(f"  Total games for {player.username}: {game_count}")
        print(f"  Total scores for {player.username}: {score_count}")

        # Show recent games
        recent_games = db_service.get_recent_games(limit=10, username="testuser001")
        print(f"\n  Recent games from API: {len(recent_games)}")
        for game in recent_games[:3]:
            winner = game.get("winner", "N/A")
            print(
                f"    - {game['game_session_id'][:8]}... | {game['game_type']} | "
                f"Winner: {winner}",
            )

    except Exception as e:
        session.rollback()
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        session.close()


if __name__ == "__main__":
    print("Adding test game data to database...")
    print(f"Database URL: {os.getenv('DATABASE_URL', 'Not set')}\n")
    add_test_games()
