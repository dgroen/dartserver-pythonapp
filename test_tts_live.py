#!/usr/bin/env python3
"""
Live TTS Test - Tests the actual TTS functionality
"""

import os
import sys

# Set environment variables for testing
os.environ["TTS_ENABLED"] = "true"
os.environ["TTS_ENGINE"] = "pyttsx3"
os.environ["TTS_SPEED"] = "150"
os.environ["TTS_VOLUME"] = "0.9"
os.environ["TTS_VOICE"] = "default"

from tts_service import TTSService


def test_tts_basic():
    """Test basic TTS functionality"""
    print("=" * 60)
    print("TTS LIVE TEST")
    print("=" * 60)

    # Initialize TTS
    print("\n1. Initializing TTS Service...")
    tts = TTSService()
    print("   ✓ TTS Service created")
    print(f"   - Enabled: {tts.is_enabled()}")
    print(f"   - Engine type: {type(tts.engine).__name__}")

    # Test configuration
    print("\n2. Testing Configuration...")
    config = tts.get_config()
    print(f"   - Enabled: {config['enabled']}")
    print(f"   - Engine: {config['engine']}")
    print(f"   - Speed: {config['speed']}")
    print(f"   - Volume: {config['volume']}")
    print(f"   - Voice: {config['voice']}")

    # Test speech (this will actually speak if audio is available)
    print("\n3. Testing Speech Output...")
    print("   Note: If you have audio, you should hear the following messages:")

    test_messages = [
        "Welcome to the game",
        "Player 1, Throw Darts",
        "Triple! 60 points",
        "Bullseye! 50 points",
        "Bust!",
        "We have a winner!",
    ]

    for i, message in enumerate(test_messages, 1):
        print(f"   {i}. Speaking: '{message}'")
        try:
            tts.speak(message)
            print("      ✓ Success")
        except Exception as e:
            print(f"      ✗ Error: {e}")

    # Test speed changes
    print("\n4. Testing Speed Configuration...")
    speeds = [100, 150, 200]
    for speed in speeds:
        print(f"   - Setting speed to {speed} WPM...")
        tts.set_speed(speed)
        print(f"     Speaking at {speed} WPM: 'Testing speed {speed}'")
        try:
            tts.speak(f"Testing speed {speed}")
            print("     ✓ Success")
        except Exception as e:
            print(f"     ✗ Error: {e}")

    # Test enable/disable
    print("\n5. Testing Enable/Disable...")
    print(f"   - Currently enabled: {tts.is_enabled()}")
    tts.disable()
    print(f"   - After disable: {tts.is_enabled()}")
    tts.speak("This should not be heard")
    print("   ✓ Disabled successfully (no speech)")
    tts.enable()
    print(f"   - After enable: {tts.is_enabled()}")
    tts.speak("TTS is back online")
    print("   ✓ Enabled successfully")

    print("\n" + "=" * 60)
    print("TTS LIVE TEST COMPLETED")
    print("=" * 60)
    print("\nIf you heard the speech messages, TTS is working correctly!")
    print("If not, check your audio output settings.")


if __name__ == "__main__":
    try:
        test_tts_basic()
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
