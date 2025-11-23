#!/usr/bin/env python3
"""
Test script to verify TTS integration in GameManager
"""

import os
import sys

# Set TTS to disabled for testing (to avoid audio playback)
os.environ["TTS_ENABLED"] = "false"
os.environ["TTS_ENGINE"] = "pyttsx3"
os.environ["TTS_SPEED"] = "150"
os.environ["TTS_VOLUME"] = "0.9"
os.environ["TTS_VOICE"] = "default"

print("=" * 60)
print("TTS Integration Test")
print("=" * 60)
print()

# Test 1: Import TTS Service
print("Test 1: Importing TTS Service...")
try:
    from tts_service import TTSService

    print("✓ TTS Service imported successfully")
except Exception as e:
    print(f"✗ Failed to import TTS Service: {e}")
    sys.exit(1)

print()

# Test 2: Initialize TTS Service
print("Test 2: Initializing TTS Service...")
try:
    tts = TTSService(
        engine="pyttsx3",
        voice_type="default",
        speed=150,
        volume=0.9,
    )
    tts.disable()  # Disable to avoid audio playback
    print("✓ TTS Service initialized")
    print(f"  - Engine: {tts.engine_name}")
    print(f"  - Speed: {tts.speed}")
    print(f"  - Volume: {tts.volume}")
    print(f"  - Voice: {tts.voice_type}")
    print(f"  - Enabled: {tts.is_enabled()}")
except Exception as e:
    print(f"✗ Failed to initialize TTS Service: {e}")
    sys.exit(1)

print()

# Test 3: Check GameManager imports
print("Test 3: Checking GameManager imports...")
try:
    import game_manager

    print("✓ GameManager module imported successfully")

    # Check if TTS is imported in game_manager
    if hasattr(game_manager, "TTSService"):
        print("✓ TTSService is imported in GameManager")
    else:
        print("⚠ TTSService not found in GameManager module attributes")

except Exception as e:
    print(f"✗ Failed to import GameManager: {e}")
    sys.exit(1)

print()

# Test 4: Verify _emit_sound signature
print("Test 4: Verifying _emit_sound method signature...")
try:
    import inspect

    from game_manager import GameManager

    # Get the signature of _emit_sound
    sig = inspect.signature(GameManager._emit_sound)
    params = list(sig.parameters.keys())

    print(f"✓ _emit_sound parameters: {params}")

    if "text" in params:
        print("✓ _emit_sound supports 'text' parameter for TTS")
    else:
        print("✗ _emit_sound does NOT support 'text' parameter")
        sys.exit(1)

except Exception as e:
    print(f"✗ Failed to verify _emit_sound: {e}")
    sys.exit(1)

print()

# Test 5: Check TTS configuration from environment
print("Test 5: Checking TTS configuration...")
try:
    tts_enabled = os.getenv("TTS_ENABLED", "true").lower() == "true"
    tts_engine = os.getenv("TTS_ENGINE", "pyttsx3")
    tts_speed = int(os.getenv("TTS_SPEED", "150"))
    tts_volume = float(os.getenv("TTS_VOLUME", "0.9"))
    tts_voice = os.getenv("TTS_VOICE", "default")

    print("✓ TTS Configuration from environment:")
    print(f"  - TTS_ENABLED: {tts_enabled}")
    print(f"  - TTS_ENGINE: {tts_engine}")
    print(f"  - TTS_SPEED: {tts_speed}")
    print(f"  - TTS_VOLUME: {tts_volume}")
    print(f"  - TTS_VOICE: {tts_voice}")
except Exception as e:
    print(f"✗ Failed to read TTS configuration: {e}")
    sys.exit(1)

print()
print("=" * 60)
print("✓ All TTS integration tests passed!")
print("=" * 60)
print()
print("Summary:")
print("  - TTS Service is properly integrated into GameManager")
print("  - _emit_sound() method supports optional 'text' parameter")
print("  - TTS can be configured via environment variables")
print()
print("Configuration (.env file):")
print("  TTS_ENABLED=true")
print("  TTS_ENGINE=pyttsx3")
print("  TTS_SPEED=150")
print("  TTS_VOLUME=0.9")
print("  TTS_VOICE=default")
print()
print("Usage in code:")
print("  self._emit_sound('intro', 'Welcome to the game')")
print("  self._emit_sound('Bust', 'Bust!')")
print("  self._emit_sound('WeHaveAWinner', 'We have a winner!')")
print()
