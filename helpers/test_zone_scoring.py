#!/usr/bin/env python3
"""
Test script to verify that zone-based scoring works correctly.
This tests the fix for the base_value vs actual score issue.
"""


import requests

# Configuration
BASE_URL = "http://localhost:5000"
BOARD_TYPE = "carromco"

# Test cases: different zones and multipliers
TEST_CASES = [
    {
        "name": "Triple 20 (most common high score)",
        "masterPin": 4,
        "slavePin": 13,
        "expected_base": 20,
        "expected_multiplier": "TRIPLE",
        "expected_score": 60,
    },
    {
        "name": "Double 20",
        "masterPin": 4,
        "slavePin": 12,
        "expected_base": 20,
        "expected_multiplier": "DOUBLE",
        "expected_score": 40,
    },
    {
        "name": "Single 9",
        "masterPin": 2,
        "slavePin": 13,
        "expected_base": 9,
        "expected_multiplier": "SINGLE",
        "expected_score": 9,
    },
    {
        "name": "Bullseye (single bull)",
        "masterPin": 16,
        "slavePin": 13,
        "expected_base": 25,
        "expected_multiplier": "BULL",
        "expected_score": 25,
    },
]


def test_zone_scoring():
    """Test that zone-based scoring calculates correctly"""
    print("=" * 70)
    print("🎯 Zone-Based Scoring Test")
    print("=" * 70)
    print(f"\nServer: {BASE_URL}")
    print(f"Board Type: {BOARD_TYPE}")
    print("\nTesting that zone mappings return correct scores...\n")

    passed = 0
    failed = 0

    for i, test in enumerate(TEST_CASES, 1):
        print(f"\n[Test {i}] {test['name']}")
        print(f"  Pins: master={test['masterPin']}, slave={test['slavePin']}")

        try:
            response = requests.post(
                f"{BASE_URL}/api/Throw/zone",
                json={
                    "masterPin": test["masterPin"],
                    "slavePin": test["slavePin"],
                    "boardType": BOARD_TYPE,
                },
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            if response.status_code != 200:
                print(f"  ❌ HTTP Error: {response.status_code}")
                print(f"     {response.text}")
                failed += 1
                continue

            data = response.json()

            if data["status"] != "success":
                print(f"  ❌ API Error: {data.get('message', 'Unknown error')}")
                failed += 1
                continue

            zone_info = data["zone_info"]

            # Verify the zone info
            checks = [
                (
                    "Zone Number",
                    zone_info["zone_number"],
                    test["expected_base"],
                ),
                (
                    "Multiplier",
                    zone_info["multiplier_type"],
                    test["expected_multiplier"],
                ),
                (
                    "Base Value",
                    zone_info["base_value"],
                    test["expected_base"],
                ),
                ("Score", zone_info["score"], test["expected_score"]),
            ]

            all_passed = True
            for check_name, actual, expected in checks:
                if actual == expected:
                    print(f"  ✅ {check_name}: {actual}")
                else:
                    print(f"  ❌ {check_name}: {actual} (expected {expected})")
                    all_passed = False

            if all_passed:
                print("  ✅ PASSED")
                passed += 1
            else:
                print("  ❌ FAILED")
                failed += 1

        except Exception as e:
            print(f"  ❌ Exception: {e}")
            failed += 1

    # Summary
    print("\n" + "=" * 70)
    print(f"📊 Results: {passed} passed, {failed} failed out of {len(TEST_CASES)} tests")

    if failed == 0:
        print("✅ ALL TESTS PASSED")
        print("\n🎯 Zone scoring is working correctly!")
        print("   - base_value contains the zone number (e.g., 20)")
        print("   - score contains the calculated value (e.g., 60 for triple 20)")
        print("   - The /api/Throw/zone endpoint now uses 'score' for game logic")
        return True
    print("❌ SOME TESTS FAILED")
    return False


def main():
    """Main test function"""
    # Check server health
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code != 200:
            print(f"⚠️  Server health check returned {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        print(f"   Please make sure the server is running at {BASE_URL}")
        return 1

    success = test_zone_scoring()

    return 0 if success else 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
