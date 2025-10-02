"""
Example WebSocket client for the Darts Game
"""

import time

import socketio

# Create a Socket.IO client
sio = socketio.Client()


# Event handlers
@sio.on("connect")
def on_connect():
    print("✓ Connected to server")


@sio.on("disconnect")
def on_disconnect():
    print("✗ Disconnected from server")


@sio.on("game_state")
def on_game_state(data):
    print("\n📊 Game State Update:")
    print(f"  Game Type: {data.get('game_type', 'N/A')}")
    print(f"  Started: {data.get('is_started', False)}")
    print(f"  Current Player: {data.get('current_player', 0) + 1}")

    if data.get("players"):
        print(f"  Players: {len(data['players'])}")
        for i, player in enumerate(data["players"]):
            print(f"    {i+1}. {player['name']}")

    if data.get("game_data") and data["game_data"].get("players"):
        print("\n  Scores:")
        for player in data["game_data"]["players"]:
            print(f"    {player['name']}: {player['score']}")


@sio.on("play_sound")
def on_play_sound(data):
    print(f'🔊 Play Sound: {data.get("sound")}')


@sio.on("play_video")
def on_play_video(data):
    print(f'🎬 Play Video: {data.get("video")} (angle: {data.get("angle")}°)')


@sio.on("message")
def on_message(data):
    print(f'💬 Message: {data.get("text")}')


@sio.on("big_message")
def on_big_message(data):
    print(f'📢 Big Message: {data.get("text")}')


def example_1_connect_and_listen():
    """Example 1: Connect and listen to events"""
    print("\n=== Example 1: Connect and Listen ===")

    try:
        sio.connect("http://localhost:5000")
        print("Listening for events... (Press Ctrl+C to stop)")

        # Keep the connection alive
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        sio.disconnect()


def example_2_start_game():
    """Example 2: Start a new game via WebSocket"""
    print("\n=== Example 2: Start New Game ===")

    try:
        sio.connect("http://localhost:5000")

        # Start a new 301 game
        print("Starting new 301 game...")
        sio.emit(
            "new_game",
            {
                "game_type": "301",
                "players": ["Alice", "Bob", "Charlie"],
            },
        )

        # Wait for game state update
        time.sleep(2)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        sio.disconnect()


def example_3_add_players():
    """Example 3: Add players via WebSocket"""
    print("\n=== Example 3: Add Players ===")

    try:
        sio.connect("http://localhost:5000")

        # Add players
        players = ["David", "Emma", "Frank"]
        for player_name in players:
            print(f"Adding player: {player_name}")
            sio.emit("add_player", {"name": player_name})
            time.sleep(1)

        # Wait for updates
        time.sleep(2)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        sio.disconnect()


def example_4_send_manual_score():
    """Example 4: Send manual scores via WebSocket"""
    print("\n=== Example 4: Send Manual Scores ===")

    try:
        sio.connect("http://localhost:5000")

        # Start a game first
        print("Starting new 301 game...")
        sio.emit(
            "new_game",
            {
                "game_type": "301",
                "players": ["Player 1", "Player 2"],
            },
        )
        time.sleep(2)

        # Send some scores
        scores = [
            {"score": 20, "multiplier": "TRIPLE"},
            {"score": 19, "multiplier": "DOUBLE"},
            {"score": 18, "multiplier": "SINGLE"},
        ]

        print("\nSending scores...")
        for score in scores:
            print(f"  Sending: {score}")
            sio.emit("manual_score", score)
            time.sleep(2)

        # Move to next player
        print("\nMoving to next player...")
        sio.emit("next_player")
        time.sleep(2)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        sio.disconnect()


def example_5_cricket_game():
    """Example 5: Play a Cricket game"""
    print("\n=== Example 5: Cricket Game ===")

    try:
        sio.connect("http://localhost:5000")

        # Start cricket game
        print("Starting new Cricket game...")
        sio.emit(
            "new_game",
            {
                "game_type": "cricket",
                "players": ["Player 1", "Player 2"],
            },
        )
        time.sleep(2)

        # Send cricket scores
        cricket_scores = [
            {"score": 20, "multiplier": "TRIPLE"},  # 3 hits on 20
            {"score": 19, "multiplier": "DOUBLE"},  # 2 hits on 19
            {"score": 25, "multiplier": "BULL"},  # 1 hit on Bull
        ]

        print("\nSending Cricket scores...")
        for score in cricket_scores:
            print(f"  Sending: {score}")
            sio.emit("manual_score", score)
            time.sleep(2)

        time.sleep(2)

    except Exception as e:
        print(f"Error: {e}")
    finally:
        sio.disconnect()


def interactive_mode():
    """Interactive mode - send commands manually"""
    print("\n=== Interactive Mode ===")
    print("Commands:")
    print("  new <type>     - Start new game (301, 401, 501, cricket)")
    print("  add <name>     - Add player")
    print("  score <n> <m>  - Send score (n=number, m=SINGLE/DOUBLE/TRIPLE)")
    print("  next           - Next player")
    print("  skip <n>       - Skip to player n")
    print("  quit           - Exit")
    print()

    try:
        sio.connect("http://localhost:5000")

        while True:
            cmd = input("> ").strip().split()

            if not cmd:
                continue

            if cmd[0] == "quit":
                break

            if cmd[0] == "new" and len(cmd) > 1:
                game_type = cmd[1]
                sio.emit(
                    "new_game",
                    {
                        "game_type": game_type,
                        "players": ["Player 1", "Player 2"],
                    },
                )
                print(f"Started new {game_type} game")

            elif cmd[0] == "add" and len(cmd) > 1:
                name = " ".join(cmd[1:])
                sio.emit("add_player", {"name": name})
                print(f"Added player: {name}")

            elif cmd[0] == "score" and len(cmd) >= 3:
                score = int(cmd[1])
                multiplier = cmd[2].upper()
                sio.emit(
                    "manual_score",
                    {
                        "score": score,
                        "multiplier": multiplier,
                    },
                )
                print(f"Sent score: {score} x {multiplier}")

            elif cmd[0] == "next":
                sio.emit("next_player")
                print("Next player")

            elif cmd[0] == "skip" and len(cmd) > 1:
                player_id = int(cmd[1]) - 1
                sio.emit("skip_to_player", {"player_id": player_id})
                print(f"Skipped to player {cmd[1]}")

            else:
                print("Unknown command")

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sio.disconnect()


def main():
    """Main menu"""
    print("=" * 60)
    print("Darts Game WebSocket Client Examples")
    print("=" * 60)
    print("\nMake sure the application is running on http://localhost:5000")
    print("\nSelect an example:")
    print("  1. Connect and listen to events")
    print("  2. Start a new game")
    print("  3. Add players")
    print("  4. Send manual scores")
    print("  5. Play Cricket game")
    print("  6. Interactive mode")
    print("  0. Exit")

    choice = input("\nEnter choice: ").strip()

    if choice == "1":
        example_1_connect_and_listen()
    elif choice == "2":
        example_2_start_game()
    elif choice == "3":
        example_3_add_players()
    elif choice == "4":
        example_4_send_manual_score()
    elif choice == "5":
        example_5_cricket_game()
    elif choice == "6":
        interactive_mode()
    elif choice == "0":
        print("Goodbye!")
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
