#!/usr/bin/env python3
"""
End-to-end test to verify zone-based scoring integrates correctly with game logic.
This ensures the fix for base_value vs actual score is working in a real game.
"""

import time

import requests

# Configuration
BASE_URL = "http://localhost:5000"
BOARD_TYPE = "carromco"


def create_test_game():
    """Create a new 301 game for testing"""
    print("\n1️⃣  Creating new 301 game...")

    response = requests.post(
        f"{BASE_URL}/api/game/new",
        json={
            "game_type": "301",
            "players": [{"username": "testplayer1", "name": "Test Player 1"}],
            "double_out": False,
        },
        headers={"Content-Type": "application/json"},
        timeout=30,
    )

    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Game created: {data.get('message', 'success')}")
        return True
    print(f"   ❌ Failed to create game: {response.status_code}")
    print(f"      {response.text}")
    return False


def get_game_state():
    """Get current game state"""
    response = requests.get(f"{BASE_URL}/api/game/state", timeout=30)
    if response.status_code == 200:
        return response.json()
    return None


def submit_zone_throw(master_pin, slave_pin, description=""):
    """Submit a throw via zone endpoint"""
    print(f"\n   🎯 Throwing: {description}")
    print(f"      Pins: master={master_pin}, slave={slave_pin}")

    response = requests.post(
        f"{BASE_URL}/api/Throw/zone",
        json={"masterPin": master_pin, "slavePin": slave_pin, "boardType": BOARD_TYPE},
        headers={"Content-Type": "application/json"},
        timeout=30,
    )

    if response.status_code == 200:
        data = response.json()
        zone_info = data.get("zone_info", {})
        zone_num = zone_info.get("zone_number")
        mult_type = zone_info.get("multiplier_type")
        score = zone_info.get("score")
        print(f"      ✅ Score: {zone_num} x {mult_type} = {score}")
        return zone_info.get("score", 0)
    print(f"      ❌ Failed: {response.status_code}")
    print(f"         {response.text}")
    return None


def test_game_integration():
    """Test full game integration with zone-based scoring"""
    print("=" * 70)
    print("🎯 Zone Scoring Game Integration Test")
    print("=" * 70)
    print(f"\nServer: {BASE_URL}")
    print(f"Board Type: {BOARD_TYPE}")
    print("\nThis test creates a 301 game and verifies zone-based scoring")
    print("works correctly with the game logic.\n")

    # Create game
    if not create_test_game():
        return False

    time.sleep(0.5)

    # Get initial state
    print("\n2️⃣  Getting initial game state...")
    state = get_game_state()
    if not state:
        print("   ❌ Failed to get game state")
        return False

    initial_score = state.get("players", [{}])[0].get("current_score", 0)
    print(f"   ✅ Starting score: {initial_score}")

    # Submit three throws using zone endpoint
    print("\n3️⃣  Submitting throws via /api/Throw/zone...")

    throws = [
        (4, 13, "Triple 20 (should score 60)"),
        (4, 12, "Double 20 (should score 40)"),
        (2, 13, "Single 9 (should score 9)"),
    ]

    expected_scores = []
    for master, slave, desc in throws:
        score = submit_zone_throw(master, slave, desc)
        if score is None:
            print("   ❌ Throw failed")
            return False
        expected_scores.append(score)

    time.sleep(0.5)

    # Get final state
    print("\n4️⃣  Getting final game state...")
    state = get_game_state()
    if not state:
        print("   ❌ Failed to get game state")
        return False

    final_score = state.get("players", [{}])[0].get("current_score", 0)
    print(f"   ✅ Final score: {final_score}")

    # Verify scoring
    print("\n5️⃣  Verifying scores...")
    total_thrown = sum(expected_scores)
    expected_final = initial_score - total_thrown

    print(f"   Initial score: {initial_score}")
    print(f"   Total thrown: {total_thrown} (60 + 40 + 9)")
    print(f"   Expected final: {expected_final}")
    print(f"   Actual final: {final_score}")

    if final_score == expected_final:
        print("   ✅ CORRECT! Scores match perfectly.")
        print("\n" + "=" * 70)
        print("✅ TEST PASSED")
        print("\n🎯 Zone-based scoring is working correctly!")
        print("   The endpoint now properly uses the calculated 'score' field")
        print("   instead of 'base_value', ensuring accurate game scoring.")
        print("=" * 70)
        return True
    print(f"   ❌ MISMATCH! Expected {expected_final}, got {final_score}")
    diff = final_score - expected_final
    print(f"   Difference: {diff}")

    if abs(diff) == total_thrown * 2:
        print("\n   💡 Diagnosis: Scores are being DOUBLED")
        print("      This suggests base_value is being used instead of score,")
        print("      and the multiplier is being applied twice.")
    elif abs(diff) == total_thrown // 2:
        print("\n   💡 Diagnosis: Scores are being HALVED")
        print("      This suggests the score is being divided incorrectly.")

    print("\n" + "=" * 70)
    print("❌ TEST FAILED")
    print("=" * 70)
    return False


def main():
    """Main test function"""
    # Check server health
    print("🔍 Checking server health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✅ Server is running\n")
        else:
            print(f"⚠️  Server returned status {response.status_code}\n")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        print(f"   Please make sure the server is running at {BASE_URL}")
        return 1

    success = test_game_integration()
    return 0 if success else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
