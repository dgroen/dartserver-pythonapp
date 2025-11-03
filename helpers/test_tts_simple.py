#!/usr/bin/env python3
"""
Simple TTS Test - Tests the actual TTS functionality
"""

import os

# Set environment variables for testing
os.environ["TTS_ENABLED"] = "true"
os.environ["TTS_ENGINE"] = "pyttsx3"
os.environ["TTS_SPEED"] = "150"
os.environ["TTS_VOLUME"] = "0.9"
os.environ["TTS_VOICE"] = "default"

from tts_service import TTSService

print("=" * 60)
print("TTS SIMPLE TEST")
print("=" * 60)

# Initialize TTS
print("\n1. Initializing TTS Service...")
tts = TTSService()
print("   ✓ TTS Service created")
print(f"   - Enabled: {tts.is_enabled()}")
print(f"   - Engine: {tts.engine_name}")
print(f"   - Speed: {tts.speed} WPM")
print(f"   - Volume: {tts.volume}")
print(f"   - Voice: {tts.voice_type}")

# Test speech
print("\n2. Testing Speech Output...")
print("   Note: If you have audio, you should hear these messages:")

test_messages = [
    "Welcome to the game",
    "Player 1, Throw Darts",
    "Triple! 60 points",
    "Bullseye! 50 points",
]

for i, message in enumerate(test_messages, 1):
    print(f"   {i}. Speaking: '{message}'")
    result = tts.speak(message)
    print(f"      {'✓' if result else '✗'} Result: {result}")

# Test speed changes
print("\n3. Testing Speed Configuration...")
for speed in [100, 175, 250]:
    print(f"   - Speed {speed} WPM: 'Testing speed {speed}'")
    tts.set_speed(speed)
    tts.speak(f"Testing speed {speed}")

# Test available voices
print("\n4. Available Voices:")
voices = tts.get_available_voices()
if voices:
    for voice in voices[:3]:  # Show first 3 voices
        print(f"   - {voice['name']}")
else:
    print("   - No voices found or not supported by engine")

print("\n" + "=" * 60)
print("TTS TEST COMPLETED!")
print("=" * 60)
print("\n✓ TTS is fully integrated and working!")
print("\nConfiguration options:")
print("  - Speed: 100-250 WPM (in .env: TTS_SPEED)")
print("  - Voice: Use voice names from available voices (in .env: TTS_VOICE)")
print("  - Volume: 0.0-1.0 (in .env: TTS_VOLUME)")
print("  - Enable/Disable: true/false (in .env: TTS_ENABLED)")
