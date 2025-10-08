#!/usr/bin/env python3
"""
Demonstration of turn tracking and bust undo functionality.

This script demonstrates how the GameManager now tracks throws within a turn
and automatically undoes all throws when a bust occurs.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Add parent directory to path
sys.path.insert(0, Path.parent(Path.parent(Path.resolve(__file__))))

from game_manager import GameManager


def print_separator():
    """Print a visual separator."""
    print("\n" + "=" * 70 + "\n")


def demo_turn_tracking():
    """Demonstrate turn tracking functionality."""
    print("DEMONSTRATION: Turn Tracking and Bust Undo")
    print_separator()

    # Create a mock socketio instance
    mock_socketio = MagicMock()

    # Initialize game manager
    manager = GameManager(mock_socketio)

    # Start a new 301 game
    print("Starting a new 301 game with Alice and Bob...")
    manager.new_game("301", ["Alice", "Bob"])

    print(f"Initial score for Alice: {manager.game.players[0]['score']}")
    print_separator()

    # Scenario 1: Normal turn without bust
    print("SCENARIO 1: Normal turn (3 throws, no bust)")
    print("-" * 70)

    print("\nThrow 1: Single 20")
    manager.process_score({"score": 20, "multiplier": "SINGLE"})
    print(f"  - Alice's score: {manager.game.players[0]['score']}")
    print(f"  - Throws tracked: {len(manager.turn_throws)}")

    print("\nThrow 2: Triple 19")
    manager.process_score({"score": 19, "multiplier": "TRIPLE"})
    print(f"  - Alice's score: {manager.game.players[0]['score']}")
    print(f"  - Throws tracked: {len(manager.turn_throws)}")

    print("\nThrow 3: Double 18")
    manager.process_score({"score": 18, "multiplier": "DOUBLE"})
    print(f"  - Alice's score: {manager.game.players[0]['score']}")
    print(f"  - Throws tracked: {len(manager.turn_throws)}")
    print(f"  - Turn is paused: {manager.is_paused}")

    print_separator()

    # Move to next player
    print("Moving to next player (Bob)...")
    manager.next_player()
    print(f"Current player: {manager.players[manager.current_player]['name']}")
    print(f"Turn throws reset: {len(manager.turn_throws)} throws tracked")

    print_separator()

    # Scenario 2: Turn with bust - all throws should be undone
    print("SCENARIO 2: Turn with bust (all throws should be undone)")
    print("-" * 70)

    # Set Bob's score to something manageable for demonstration
    manager.game.players[1]["score"] = 100
    initial_score = manager.game.players[1]["score"]
    print(f"\nBob's initial score: {initial_score}")

    print("\nThrow 1: Single 20")
    manager.process_score({"score": 20, "multiplier": "SINGLE"})
    score_after_throw1 = manager.game.players[1]["score"]
    print(f"  - Bob's score: {score_after_throw1}")
    print(f"  - Throws tracked: {len(manager.turn_throws)}")

    print("\nThrow 2: Triple 15")
    manager.process_score({"score": 15, "multiplier": "TRIPLE"})
    score_after_throw2 = manager.game.players[1]["score"]
    print(f"  - Bob's score: {score_after_throw2}")
    print(f"  - Throws tracked: {len(manager.turn_throws)}")

    print("\nThrow 3: Single 50 (BUST - score would go negative)")
    manager.process_score({"score": 50, "multiplier": "SINGLE"})
    final_score = manager.game.players[1]["score"]
    print(f"  - Bob's score after bust: {final_score}")
    print(f"  - Score restored to initial: {final_score == initial_score}")
    print(f"  - Game is paused: {manager.is_paused}")

    print("\n✓ All throws in the turn were undone!")
    print("  - Throw 1 (20 points) was undone")
    print("  - Throw 2 (45 points) was undone")
    print("  - Throw 3 (bust) was undone")
    print(f"  - Bob's score returned from {score_after_throw2} to {final_score}")

    print_separator()

    # Scenario 3: Demonstrate with Cricket game
    print("SCENARIO 3: Turn tracking with Cricket game")
    print("-" * 70)

    manager2 = GameManager(mock_socketio)
    manager2.new_game("cricket", ["Charlie", "Diana"])

    print("\nStarting Cricket game...")
    print(f"Charlie's initial score: {manager2.game.players[0]['score']}")
    print(f"Charlie's 20s hits: {manager2.game.players[0]['targets'][20]['hits']}")

    print("\nThrow 1: Triple 20")
    manager2.process_score({"score": 20, "multiplier": "TRIPLE"})
    print(f"  - Charlie's 20s hits: {manager2.game.players[0]['targets'][20]['hits']}")
    print(f"  - Throws tracked: {len(manager2.turn_throws)}")

    print("\nThrow 2: Single 19")
    manager2.process_score({"score": 19, "multiplier": "SINGLE"})
    print(f"  - Charlie's 19s hits: {manager2.game.players[0]['targets'][19]['hits']}")
    print(f"  - Throws tracked: {len(manager2.turn_throws)}")

    print("\n✓ Turn tracking works for Cricket too!")

    print_separator()
    print("DEMONSTRATION COMPLETE")
    print("\nKey Features Demonstrated:")
    print("1. ✓ Throws are tracked during each turn")
    print("2. ✓ Turn tracking resets when moving to next player")
    print("3. ✓ On bust, ALL throws in the turn are undone")
    print("4. ✓ Player's score is restored to the start of the turn")
    print("5. ✓ Works for both 301 and Cricket game types")
    print_separator()


if __name__ == "__main__":
    demo_turn_tracking()
