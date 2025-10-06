#!/usr/bin/env python3
"""
Test script to demonstrate TTS integration with GameManager
"""

import os
from unittest.mock import Mock

# Set TTS configuration
os.environ["TTS_ENABLED"] = "true"
os.environ["TTS_ENGINE"] = "pyttsx3"
os.environ["TTS_SPEED"] = "150"
os.environ["TTS_VOLUME"] = "1.0"

from game_manager import GameManager


def main():
    print("=" * 60)
    print("GameManager TTS Integration Test")
    print("=" * 60)
    print()

    # Create mock SocketIO
    mock_socketio = Mock()

    # Create GameManager
    print("Creating GameManager with TTS enabled...")
    gm = GameManager(mock_socketio)

    # Check TTS status
    print(f"TTS Enabled: {gm.tts.is_enabled()}")
    print(f"TTS Engine: {gm.tts.engine_name}")
    print(f"TTS Speed: {gm.tts.speed}")
    print(f"TTS Volume: {gm.tts.volume}")
    print()

    # Start a new game
    print("Starting new 301 game...")
    gm.new_game(game_type="301", player_names=["Alice", "Bob"])
    print()

    # Simulate some throws
    print("Simulating game throws with TTS announcements...")
    print("-" * 60)

    # Throw 1: Triple 20
    print("\n1. Alice throws Triple 20")
    gm.process_score({"score": 20, "multiplier": "TRIPLE"})

    # Throw 2: Double 18
    print("\n2. Alice throws Double 18")
    gm.process_score({"score": 18, "multiplier": "DOUBLE"})

    # Throw 3: Single 15
    print("\n3. Alice throws Single 15")
    gm.process_score({"score": 15, "multiplier": "SINGLE"})

    # Next player
    print("\n4. Moving to next player...")
    gm.next_player()

    # Throw 4: Bullseye
    print("\n5. Bob throws Bullseye")
    gm.process_score({"score": 25, "multiplier": "BULL"})

    # Throw 5: Double Bullseye
    print("\n6. Bob throws Double Bullseye")
    gm.process_score({"score": 25, "multiplier": "DBLBULL"})

    print()
    print("-" * 60)
    print("\nTest completed!")
    print()

    # Show how to configure TTS
    print("=" * 60)
    print("TTS Configuration Options")
    print("=" * 60)
    print()
    print("You can configure TTS using environment variables:")
    print("  TTS_ENABLED=true/false  - Enable/disable TTS")
    print("  TTS_ENGINE=pyttsx3/gtts - Choose TTS engine")
    print("  TTS_SPEED=150           - Speech speed (words per minute)")
    print("  TTS_VOLUME=1.0          - Volume level (0.0 to 1.0)")
    print("  TTS_VOICE=default       - Voice type (engine-specific)")
    print()
    print("Or use the REST API endpoints:")
    print("  POST /api/tts/configure - Configure TTS settings")
    print("  POST /api/tts/enable    - Enable TTS")
    print("  POST /api/tts/disable   - Disable TTS")
    print("  POST /api/tts/test      - Test TTS with custom text")
    print()
    print("Example speeds:")
    print("  100 - Slow")
    print("  150 - Normal (default)")
    print("  200 - Fast")
    print("  250 - Very fast")
    print()

    # Test speed changes
    print("Testing different speeds...")
    print("-" * 60)

    speeds = [100, 150, 200]
    for speed in speeds:
        print(f"\nSetting speed to {speed}...")
        gm.tts.set_speed(speed)
        gm.tts.speak(f"This is speech at {speed} words per minute")

    print()
    print("=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
