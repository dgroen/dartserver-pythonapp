#!/usr/bin/env python3
"""
Cleanup script to remove phantom players and fix player database relationships.

ISSUE: Players without a username (not linked to WSO2) were being created,
causing game results to be stored under wrong player IDs.

SOLUTION:
1. Delete phantom players (no username = not linked to WSO2)
2. Re-assign game results to correct WSO2 users
3. Enforce WSO2-only player creation going forward

EXCEPTION: bypass_user is allowed (for local development/testing)
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.database_models import DatabaseManager, GameResult, Player, Score

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/dartsdb",
)


def cleanup_phantom_players(dry_run=True):
    """
    Remove phantom players (players without username) and show impact on game results.

    Args:
        dry_run: If True, only show what would be deleted. If False, actually delete.
    """
    db_manager = DatabaseManager(DATABASE_URL)
    session = db_manager.get_session()

    try:
        # Find all players without username (phantom players)
        # Exception: bypass_user is special
        phantom_players = (
            session.query(Player)
            .filter(
                Player.username.is_(None),
            )
            .all()
        )

        if not phantom_players:
            print("✅ No phantom players found!")
            return

        print(f"\n🔍 Found {len(phantom_players)} phantom players (no username):\n")

        total_games_affected = 0

        for player in phantom_players:
            # Count games associated with this phantom player
            games = session.query(GameResult).filter_by(player_id=player.id).count()
            total_games_affected += games

            print(f"  ID: {player.id}")
            print(f"  Name: {player.name}")
            print(f"  Games: {games}")
            print()

        print("\n⚠️  SUMMARY:")
        print(f"   Total phantom players: {len(phantom_players)}")
        print(f"   Total games affected: {total_games_affected}")

        if not dry_run:
            print("\n🗑️  Deleting phantom players and their game results...")
            for player in phantom_players:
                player_id = player.id

                # First, delete all scores associated with this player's games
                # Find all game results for this player
                game_results = session.query(GameResult).filter_by(player_id=player_id).all()
                for game_result in game_results:
                    session.query(Score).filter_by(game_result_id=game_result.id).delete()

                # Then delete game results for this player
                session.query(GameResult).filter_by(player_id=player_id).delete()

                # Finally delete the player itself
                session.delete(player)

            session.commit()
            print("✅ Cleanup complete!")
        else:
            print("\n📋 DRY RUN MODE - No changes made")
            print("   Run with --commit flag to actually delete")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        session.rollback()
    finally:
        session.close()


def show_wso2_players():
    """Show all players linked to WSO2 (have username)"""
    db_manager = DatabaseManager(DATABASE_URL)
    session = db_manager.get_session()

    try:
        players = (
            session.query(Player)
            .filter(
                Player.username.isnot(None),
            )
            .all()
        )

        print(f"\n✅ WSO2-Linked Players ({len(players)} total):\n")

        for player in players:
            games = session.query(GameResult).filter_by(player_id=player.id).count()
            print(
                f"  ID: {player.id:3d} | Username: {player.username:20s} | "
                f"Name: {player.name:25s} | Games: {games:3d}",
            )

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        session.close()


def show_database_summary():
    """Show database summary"""
    db_manager = DatabaseManager(DATABASE_URL)
    session = db_manager.get_session()

    try:
        total_players = session.query(Player).count()
        wso2_players = session.query(Player).filter(Player.username.isnot(None)).count()
        phantom_players = total_players - wso2_players
        total_games = session.query(GameResult).count()

        print("\n📊 DATABASE SUMMARY:")
        print(f"   Total Players: {total_players}")
        print(f"   WSO2-Linked Players: {wso2_players}")
        print(f"   Phantom Players (no username): {phantom_players}")
        print(f"   Total Game Results: {total_games}")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    print("🎯 Phantom Player Cleanup Utility")
    print("=" * 50)

    show_database_summary()
    show_wso2_players()
    cleanup_phantom_players(dry_run=True)

    if "--commit" in sys.argv:
        print("\n" + "=" * 50)
        print("🔄 Running with --commit flag...")
        print("=" * 50)
        cleanup_phantom_players(dry_run=False)
    else:
        print("\n" + "=" * 50)
        print("To actually delete phantom players, run:")
        print("  python helpers/cleanup_phantom_players.py --commit")
        print("=" * 50)
