"""
Examples of using the Darts Game API
"""

import json
import time

import requests

# Base URL of the application
BASE_URL = "http://localhost:5000"


def example_1_start_301_game():
    """Example 1: Start a new 301 game with custom players"""
    print("\n=== Example 1: Start 301 Game ===")

    response = requests.post(
        f"{BASE_URL}/api/game/new",
        json={
            "game_type": "301",
            "players": ["Alice", "Bob", "Charlie"],
            "double_out": False,
        },
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


def example_2_start_cricket_game():
    """Example 2: Start a new Cricket game"""
    print("\n=== Example 2: Start Cricket Game ===")

    response = requests.post(
        f"{BASE_URL}/api/game/new",
        json={
            "game_type": "cricket",
            "players": ["Player 1", "Player 2"],
        },
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


def example_3_get_game_state():
    """Example 3: Get current game state"""
    print("\n=== Example 3: Get Game State ===")

    response = requests.get(f"{BASE_URL}/api/game/state")

    print(f"Status: {response.status_code}")
    print("Game State:")
    print(json.dumps(response.json(), indent=2))


def example_4_add_players():
    """Example 4: Add players to the game"""
    print("\n=== Example 4: Add Players ===")

    players = ["David", "Emma"]

    for player_name in players:
        response = requests.post(
            f"{BASE_URL}/api/players",
            json={
                "name": player_name,
            },
        )
        print(f"Added {player_name}: {response.json()}")
        time.sleep(0.5)


def example_5_get_players():
    """Example 5: Get all players"""
    print("\n=== Example 5: Get All Players ===")

    response = requests.get(f"{BASE_URL}/api/players")

    print(f"Status: {response.status_code}")
    print(f"Players: {response.json()}")


def example_6_simulate_301_game():
    """Example 6: Simulate a complete 301 game"""
    print("\n=== Example 6: Simulate 301 Game ===")

    # Start new game
    print("Starting new 301 game...")
    requests.post(
        f"{BASE_URL}/api/game/new",
        json={
            "game_type": "301",
            "players": ["Alice", "Bob"],
        },
    )

    # Simulate some throws
    throws = [
        {"score": 20, "multiplier": "TRIPLE"},  # 60 points
        {"score": 20, "multiplier": "TRIPLE"},  # 60 points
        {"score": 20, "multiplier": "TRIPLE"},  # 60 points
    ]

    print("\nSimulating throws for Player 1...")
    for throw in throws:
        print(f"  Throw: {throw}")
        time.sleep(1)

    # Get final state
    response = requests.get(f"{BASE_URL}/api/game/state")
    state = response.json()

    print("\nGame State after throws:")
    if state.get("game_data") and state["game_data"].get("players"):
        for player in state["game_data"]["players"]:
            print(f"  {player['name']}: {player['score']} points")


def example_7_simulate_cricket_game():
    """Example 7: Simulate a Cricket game"""
    print("\n=== Example 7: Simulate Cricket Game ===")

    # Start new cricket game
    print("Starting new Cricket game...")
    requests.post(
        f"{BASE_URL}/api/game/new",
        json={
            "game_type": "cricket",
            "players": ["Player 1", "Player 2"],
        },
    )

    print("\nCricket game started!")
    print("Players need to hit 15, 16, 17, 18, 19, 20, and Bull (25)")
    print("Each number needs 3 hits to open")

    # Get game state
    response = requests.get(f"{BASE_URL}/api/game/state")
    state = response.json()

    print("\nInitial Cricket State:")
    if state.get("game_data") and state["game_data"].get("players"):
        for player in state["game_data"]["players"]:
            print(f"\n{player['name']}:")
            print(f"  Score: {player['score']}")
            print(f"  Targets: {player.get('targets', {})}")


def example_8_full_game_workflow():
    """Example 8: Complete game workflow"""
    print("\n=== Example 8: Complete Game Workflow ===")

    # 1. Add players
    print("\n1. Adding players...")
    for name in ["Alice", "Bob"]:
        requests.post(f"{BASE_URL}/api/players", json={"name": name})

    # 2. Start game
    print("2. Starting 301 game...")
    requests.post(
        f"{BASE_URL}/api/game/new",
        json={
            "game_type": "301",
            "players": ["Alice", "Bob"],
        },
    )

    # 3. Check initial state
    print("3. Checking initial state...")
    response = requests.get(f"{BASE_URL}/api/game/state")
    state = response.json()
    print(f"   Game Type: {state['game_type']}")
    print(f"   Players: {len(state['players'])}")
    print(f"   Started: {state['is_started']}")

    # 4. Game is now ready for scores via RabbitMQ or manual entry
    print("\n4. Game is ready!")
    print("   - Send scores via RabbitMQ")
    print("   - Or use the web control panel")
    print("   - Or use WebSocket events")


def example_9_double_out_game():
    """Example 9: Start a 501 game with double-out"""
    print("\n=== Example 9: 501 Game with Double-Out ===")

    response = requests.post(
        f"{BASE_URL}/api/game/new",
        json={
            "game_type": "501",
            "players": ["Player 1", "Player 2"],
            "double_out": True,
        },
    )

    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print("Note: Players must finish with a double to win!")


def main():
    """Run all examples"""
    print("=" * 60)
    print("Darts Game API Examples")
    print("=" * 60)
    print("\nMake sure the application is running on http://localhost:5000")
    print("\nPress Enter to continue...")
    input()

    try:
        # Run examples
        example_1_start_301_game()
        time.sleep(1)

        example_2_start_cricket_game()
        time.sleep(1)

        example_3_get_game_state()
        time.sleep(1)

        example_4_add_players()
        time.sleep(1)

        example_5_get_players()
        time.sleep(1)

        example_6_simulate_301_game()
        time.sleep(1)

        example_7_simulate_cricket_game()
        time.sleep(1)

        example_8_full_game_workflow()
        time.sleep(1)

        example_9_double_out_game()

        print("\n" + "=" * 60)
        print("All examples completed!")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the application")
        print("Make sure the application is running on http://localhost:5000")
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
