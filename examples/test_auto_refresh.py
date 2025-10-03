"""
Test script to verify automatic UI refresh functionality
This script tests that the UI automatically refreshes when scores are sent via API
"""

import json
import time

import requests

# Base URL of the application
BASE_URL = "http://localhost:5000"


def test_api_auto_refresh():
    """Test that API calls trigger automatic UI refresh via WebSocket"""
    print("\n" + "=" * 60)
    print("Testing Automatic UI Refresh")
    print("=" * 60)
    print("\nThis test verifies that the UI automatically refreshes when:")
    print("1. A new game is started via API")
    print("2. Players are added/removed via API")
    print("3. Scores are submitted via API")
    print("\nMake sure you have the game UI open in a browser!")
    print("URL: http://localhost:5000")
    print("\nPress Enter to continue...")
    input()

    try:
        # Test 1: Start a new game
        print("\n--- Test 1: Starting New Game ---")
        print("Watch the UI - it should automatically update!")
        response = requests.post(
            f"{BASE_URL}/api/game/new",
            json={
                "game_type": "301",
                "players": ["Alice", "Bob"],
                "double_out": False,
            },
        )
        print(f"✓ New game started: {response.json()}")
        time.sleep(2)

        # Test 2: Add a player
        print("\n--- Test 2: Adding Player ---")
        print("Watch the UI - a new player should appear!")
        response = requests.post(
            f"{BASE_URL}/api/players",
            json={"name": "Charlie"},
        )
        print(f"✓ Player added: {response.json()}")
        time.sleep(2)

        # Test 3: Submit scores via API
        print("\n--- Test 3: Submitting Scores ---")
        print("Watch the UI - scores should update in real-time!")

        scores = [
            {"score": 20, "multiplier": "TRIPLE", "description": "Triple 20 (60 points)"},
            {"score": 19, "multiplier": "TRIPLE", "description": "Triple 19 (57 points)"},
            {"score": 18, "multiplier": "DOUBLE", "description": "Double 18 (36 points)"},
        ]

        for score_data in scores:
            print(f"\nSubmitting: {score_data['description']}")
            response = requests.post(
                f"{BASE_URL}/api/score",
                json={"score": score_data["score"], "multiplier": score_data["multiplier"]},
            )
            print(f"✓ Score submitted: {response.json()}")
            time.sleep(2)

        # Test 4: Get current game state
        print("\n--- Test 4: Current Game State ---")
        response = requests.get(f"{BASE_URL}/api/game/state")
        state = response.json()
        print("\nCurrent Game State:")
        print(json.dumps(state, indent=2))

        # Test 5: Remove a player
        print("\n--- Test 5: Removing Player ---")
        print("Watch the UI - Charlie should disappear!")
        response = requests.delete(f"{BASE_URL}/api/players/2")
        print(f"✓ Player removed: {response.json()}")
        time.sleep(2)

        print("\n" + "=" * 60)
        print("✓ All tests completed successfully!")
        print("=" * 60)
        print("\nIf the UI updated automatically during these tests,")
        print("then the automatic refresh is working correctly!")

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to the application")
        print("Make sure the application is running on http://localhost:5000")
    except Exception as e:
        print(f"\n❌ Error: {e}")


def test_rabbitmq_score_submission():
    """
    Test score submission via RabbitMQ (requires RabbitMQ setup)
    This is a placeholder - actual implementation would require pika library
    """
    print("\n" + "=" * 60)
    print("RabbitMQ Score Submission Test")
    print("=" * 60)
    print("\nTo test RabbitMQ score submission:")
    print("1. Make sure RabbitMQ is running")
    print("2. Use the bridge_nodejs_to_rabbitmq.js script")
    print("3. Or use a RabbitMQ client to publish messages to:")
    print("   Exchange: darts_exchange")
    print("   Topic: darts.scores.#")
    print('   Message format: {"score": 20, "multiplier": "TRIPLE"}')
    print("\nThe UI should automatically refresh when messages are received!")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Darts Game - Automatic UI Refresh Tests")
    print("=" * 60)

    # Test API-based auto refresh
    test_api_auto_refresh()

    # Show RabbitMQ info
    print("\n")
    test_rabbitmq_score_submission()


if __name__ == "__main__":
    main()
