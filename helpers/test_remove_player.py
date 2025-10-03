#!/usr/bin/env python3
"""
Test script to reproduce the remove player issue
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


@sio.on("message")
def on_message(data):
    print(f'💬 Message: {data.get("text")}')


def test_remove_player():
    """Test removing a player via WebSocket"""
    try:
        # Connect to server
        print("Connecting to server...")
        sio.connect("http://localhost:5000")
        time.sleep(1)

        # Start a new game with 3 players
        print("\n1️⃣ Starting new game with 3 players...")
        sio.emit(
            "new_game",
            {
                "game_type": "301",
                "players": ["Alice", "Bob", "Charlie"],
                "double_out": False,
            },
        )
        time.sleep(2)

        # Try to remove player at index 1 (Bob)
        print("\n2️⃣ Attempting to remove player at index 1 (Bob)...")
        sio.emit("remove_player", {"player_id": 1})
        time.sleep(2)

        # Try to remove player at index 0 (Alice)
        print("\n3️⃣ Attempting to remove player at index 0 (Alice)...")
        sio.emit("remove_player", {"player_id": 0})
        time.sleep(2)

        # Try to remove the last remaining player (should fail - minimum 2 players)
        print("\n4️⃣ Attempting to remove last player (should fail)...")
        sio.emit("remove_player", {"player_id": 0})
        time.sleep(2)

        print("\n✅ Test completed")

    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        sio.disconnect()


if __name__ == "__main__":
    test_remove_player()
