#!/usr/bin/env python3
"""
Test script for TTS functionality
"""

from tts_service import TTSService


def test_pyttsx3():
    """Test pyttsx3 engine"""
    print("\n=== Testing pyttsx3 Engine ===")
    tts = TTSService(engine="pyttsx3", speed=150, volume=1.0)
    print(f"Engine: {tts.engine_name}")
    print(f"Enabled: {tts.enabled}")
    print(f"Speed: {tts.speed}")
    print(f"Volume: {tts.volume}")

    # Test available voices
    voices = tts.get_available_voices()
    print(f"\nAvailable voices: {len(voices)}")
    for i, voice in enumerate(voices[:3]):  # Show first 3
        print(f"  {i+1}. {voice.get('name', 'Unknown')} - {voice.get('id', 'N/A')}")

    # Test speech
    print("\nTesting speech...")
    tts.speak("Welcome to the game")
    tts.speak("Player one, throw darts")
    tts.speak("Bust!")
    tts.speak("We have a winner!")

    # Test speed changes
    print("\nTesting speed changes...")
    tts.set_speed(100)
    print(f"Speed set to: {tts.speed}")
    tts.speak("This is slower speech")

    tts.set_speed(200)
    print(f"Speed set to: {tts.speed}")
    tts.speak("This is faster speech")


def test_gtts():
    """Test gTTS engine"""
    print("\n=== Testing gTTS Engine ===")
    tts = TTSService(engine="gtts", speed=150, volume=1.0)
    print(f"Engine: {tts.engine_name}")
    print(f"Enabled: {tts.enabled}")

    # Test audio generation
    print("\nTesting audio generation...")
    audio_data = tts.generate_audio_data("Welcome to the game")
    if audio_data:
        print(f"Generated audio data: {len(audio_data)} bytes")
    else:
        print("Failed to generate audio data")


def test_configuration():
    """Test configuration changes"""
    print("\n=== Testing Configuration ===")
    tts = TTSService(engine="pyttsx3")

    # Test enable/disable
    print(f"Initial state: {tts.enabled}")
    tts.disable()
    print(f"After disable: {tts.enabled}")
    tts.enable()
    print(f"After enable: {tts.enabled}")

    # Test volume
    tts.set_volume(0.5)
    print(f"Volume set to: {tts.volume}")

    # Test voice change
    voices = tts.get_available_voices()
    if voices:
        tts.set_voice(voices[0]["id"])
        print(f"Voice changed to: {voices[0].get('name', 'Unknown')}")


if __name__ == "__main__":
    print("TTS Service Test Script")
    print("=" * 50)

    try:
        test_pyttsx3()
    except Exception as e:
        print(f"Error testing pyttsx3: {e}")

    try:
        test_gtts()
    except Exception as e:
        print(f"Error testing gTTS: {e}")

    try:
        test_configuration()
    except Exception as e:
        print(f"Error testing configuration: {e}")

    print("\n" + "=" * 50)
    print("Test completed!")
