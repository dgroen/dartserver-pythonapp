#!/usr/bin/env python3
"""
Test script to verify that raw dartboard data shows on the dartboard-testing page.
This simulates a dartboard sending GPIO pin data to the /api/Throw/zone endpoint.
"""

import json
import sys
import time

import requests
import socketio

# Configuration
BASE_URL = "http://localhost:5000"
BOARD_TYPE = "carromco"  # Change to your board type

# Test data: simulate hitting different zones
TEST_THROWS = [
    {"masterPin": 4, "slavePin": 13, "boardType": BOARD_TYPE, "description": "First test throw"},
    {"masterPin": 4, "slavePin": 12, "boardType": BOARD_TYPE, "description": "Second test throw"},
    {"masterPin": 2, "slavePin": 13, "boardType": BOARD_TYPE, "description": "Third test throw"},
]


def test_websocket_connection():
    """Test WebSocket connection and event reception"""
    print("🔌 Testing WebSocket connection...")

    received_events = []

    # Create Socket.IO client
    sio = socketio.Client()

    @sio.on("dartboard_test_received")
    def on_dartboard_test(data):
        print(f"✅ Received dartboard_test_received event: {json.dumps(data, indent=2)}")
        received_events.append(data)

    @sio.on("connect")
    def on_connect():
        print("✅ Connected to WebSocket server")

    @sio.on("disconnect")
    def on_disconnect():
        print("🔌 Disconnected from WebSocket server")

    try:
        # Connect to server
        sio.connect(BASE_URL)
        time.sleep(1)  # Give connection time to establish

        # Send test throws
        print(f"\n📡 Sending {len(TEST_THROWS)} test throws to /api/Throw/zone...")
        for i, throw in enumerate(TEST_THROWS, 1):
            print(f"\n🎯 Test throw #{i}: {throw['description']}")
            print(f"   Master Pin: {throw['masterPin']}, Slave Pin: {throw['slavePin']}")

            response = requests.post(
                f"{BASE_URL}/api/Throw/zone",
                json=throw,
                headers={"Content-Type": "application/json"},
                timeout=30,
            )

            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ HTTP Response: {result['status']}")
                if "zone_info" in result:
                    zone = result["zone_info"]
                    score_str = (
                        f"{zone['zone_number']} x {zone['multiplier_type']} = {zone['score']}"
                    )
                    print(f"   🎯 Zone Info: {score_str}")
            else:
                print(f"   ❌ HTTP Error: {response.status_code} - {response.text}")

            # Wait for WebSocket event
            time.sleep(0.5)

        # Give time for all events to arrive
        print("\n⏳ Waiting for WebSocket events...")
        time.sleep(2)

        # Check results
        print("\n📊 Summary:")
        print(f"   HTTP Requests sent: {len(TEST_THROWS)}")
        print(f"   WebSocket events received: {len(received_events)}")

        if len(received_events) == len(TEST_THROWS):
            print("\n✅ SUCCESS: All throws generated WebSocket events!")
            print("   The raw data should now appear on the dartboard-testing page.")
            return True
        if len(received_events) > 0:
            print(
                f"\n⚠️  PARTIAL: Only {len(received_events)}/{len(TEST_THROWS)} events received",
            )
            return False
        print("\n❌ FAILURE: No WebSocket events received")
        print("   The dartboard-testing page will NOT show raw data.")
        return False

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False
    finally:
        sio.disconnect()


def main():
    """Main test function"""
    print("=" * 70)
    print("🎯 Dartboard Raw Data Test")
    print("=" * 70)
    print(f"\nServer: {BASE_URL}")
    print(f"Board Type: {BOARD_TYPE}")
    print(
        "\nThis test will:\n"
        "1. Connect to the WebSocket server\n"
        "2. Send test throws to /api/Throw/zone\n"
        "3. Listen for dartboard_test_received events\n"
        "4. Verify raw data appears on the admin page\n",
    )

    # Check if server is running
    print("\n🔍 Checking server health...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print(f"⚠️  Server returned status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to server: {e}")
        print(f"\nPlease make sure the server is running at {BASE_URL}")
        sys.exit(1)

    # Run the test
    success = test_websocket_connection()

    print("\n" + "=" * 70)
    if success:
        print("✅ TEST PASSED")
        print("\n📝 Next steps:")
        print(f"   1. Open {BASE_URL}/admin/dartboard-testing in your browser")
        print("   2. Select the dartboard type")
        print("   3. Run this script again to see live raw data in the message log")
        sys.exit(0)
    else:
        print("❌ TEST FAILED")
        print("\n🔧 Troubleshooting:")
        print("   1. Check that the server is running properly")
        print("   2. Verify the dartboard type exists in the database")
        print("   3. Check server logs for errors")
        sys.exit(1)


if __name__ == "__main__":
    main()
