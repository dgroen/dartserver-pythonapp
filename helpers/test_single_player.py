#!/usr/bin/env python3
"""
Test script to verify single-player game functionality
"""

import time

import socketio

# Create a Socket.IO client
sio = socketio.Client()


@sio.on("connect")
def on_connect():
    print("✓ Connected to server")


@sio.on("disconnect")
def on_disconnect():
    print("✗ Disconnected from server")


@sio.on("game_state")
def on_game_state(data):
    print("\n📊 Game State Update:")
    print(f'  Players: {[p["name"] for p in data.get("players", [])]}')
    print(f'  Current Player: {data.get("current_player")}')
    print(f'  Is Started: {data.get("is_started")}')
    if data.get("game_data") and data["game_data"].get("players"):
        for player in data["game_data"]["players"]:
            print(f'    - {player["name"]}: {player.get("score", 0)} points')


@sio.on("message")
def on_message(data):
    print(f'💬 Message: {data.get("text")}')


def test_single_player():
    """Test single-player game functionality"""
    try:
        # Connect to server
        print("Connecting to server...")
        sio.connect("http://localhost:5000")
        time.sleep(1)

        # Test 1: Start a game with 3 players
        print("\n" + "=" * 60)
        print("Test 1: Start game with 3 players")
        print("=" * 60)
        sio.emit(
            "new_game",
            {
                "game_type": "301",
                "players": ["Alice", "Bob", "Charlie"],
                "double_out": False,
            },
        )
        time.sleep(2)

        # Test 2: Remove one player (Bob) - should work
        print("\n" + "=" * 60)
        print("Test 2: Remove Bob (should work - 2 players remaining)")
        print("=" * 60)
        sio.emit("remove_player", {"player_id": 1})
        time.sleep(2)

        # Test 3: Remove another player (Charlie) - should work, leaving 1 player
        print("\n" + "=" * 60)
        print("Test 3: Remove Charlie (should work - 1 player remaining)")
        print("=" * 60)
        sio.emit("remove_player", {"player_id": 1})
        time.sleep(2)

        # Test 4: Try to remove the last player - should fail
        print("\n" + "=" * 60)
        print("Test 4: Try to remove Alice (should FAIL - need at least 1 player)")
        print("=" * 60)
        sio.emit("remove_player", {"player_id": 0})
        time.sleep(2)

        # Test 5: Submit a score in single-player mode
        print("\n" + "=" * 60)
        print("Test 5: Submit score in single-player mode")
        print("=" * 60)
        sio.emit(
            "manual_score",
            {
                "score": 20,
                "multiplier": "TRIPLE",
            },
        )
        time.sleep(2)

        # Test 6: Start a new single-player game directly
        print("\n" + "=" * 60)
        print("Test 6: Start a new single-player game directly")
        print("=" * 60)
        sio.emit(
            "new_game",
            {
                "game_type": "501",
                "players": ["Solo Player"],
                "double_out": True,
            },
        )
        time.sleep(2)

        # Test 7: Submit multiple scores in single-player
        print("\n" + "=" * 60)
        print("Test 7: Submit multiple scores")
        print("=" * 60)
        scores = [
            {"score": 20, "multiplier": "TRIPLE", "desc": "Triple 20 (60)"},
            {"score": 19, "multiplier": "TRIPLE", "desc": "Triple 19 (57)"},
            {"score": 18, "multiplier": "DOUBLE", "desc": "Double 18 (36)"},
        ]

        for score_data in scores:
            print(f'\n  Submitting: {score_data["desc"]}')
            sio.emit(
                "manual_score",
                {
                    "score": score_data["score"],
                    "multiplier": score_data["multiplier"],
                },
            )
            time.sleep(1.5)

        print("\n" + "=" * 60)
        print("✅ All single-player tests completed!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
    finally:
        sio.disconnect()


if __name__ == "__main__":
    test_single_player()
