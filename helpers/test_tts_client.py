#!/usr/bin/env python3
"""
Test script for client-side TTS implementation
"""

import base64
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from tts_service import TTSService

# Load environment variables from .env file
load_dotenv()


def test_tts_audio_generation():
    """Test TTS audio generation for client-side playback"""

    print("=" * 60)
    print("Testing Client-Side TTS Implementation")
    print("=" * 60)

    # Check environment configuration
    print("\n1. Checking Environment Configuration:")
    print(f"   TTS_ENABLED: {os.getenv('TTS_ENABLED', 'true')}")
    print(f"   TTS_ENGINE: {os.getenv('TTS_ENGINE', 'pyttsx3')}")
    print(f"   TTS_SPEED: {os.getenv('TTS_SPEED', '150')}")
    print(f"   TTS_VOLUME: {os.getenv('TTS_VOLUME', '0.9')}")

    # Check if gTTS is configured
    tts_engine = os.getenv("TTS_ENGINE", "pyttsx3")
    if tts_engine != "gtts":
        print(f"\n   ⚠️  WARNING: TTS_ENGINE is set to '{tts_engine}'")
        print("   For client-side playback, TTS_ENGINE should be 'gtts'")
        print("   Update your .env file: TTS_ENGINE=gtts")
    else:
        print("   ✅ TTS_ENGINE correctly set to 'gtts'")

    # Initialize TTS service
    print("\n2. Initializing TTS Service:")
    try:
        tts = TTSService(
            engine=tts_engine,
            voice_type=os.getenv("TTS_VOICE", "default"),
            speed=int(os.getenv("TTS_SPEED", "150")),
            volume=float(os.getenv("TTS_VOLUME", "0.9")),
        )
        print("   ✅ TTS Service initialized successfully")
    except Exception as e:
        print(f"   ❌ Failed to initialize TTS Service: {e}")
        return False

    # Test audio generation
    print("\n3. Testing Audio Generation:")
    test_text = "Triple twenty! Sixty points!"

    try:
        audio_data = tts.generate_audio_data(test_text)

        if audio_data:
            print("   ✅ Audio generated successfully")
            print(f"   Audio size: {len(audio_data)} bytes")

            # Test base64 encoding
            print("\n4. Testing Base64 Encoding:")
            audio_base64 = base64.b64encode(audio_data).decode("utf-8")
            print("   ✅ Base64 encoding successful")
            print(f"   Encoded size: {len(audio_base64)} characters")
            print(f"   Size increase: {(len(audio_base64) / len(audio_data) - 1) * 100:.1f}%")

            # Test decoding
            print("\n5. Testing Base64 Decoding:")
            decoded_data = base64.b64decode(audio_base64)
            if decoded_data == audio_data:
                print("   ✅ Decoding successful - data integrity verified")
            else:
                print("   ❌ Decoding failed - data mismatch")
                return False

            # Save test audio file
            print("\n6. Saving Test Audio File:")
            test_file = "./tests/data/test_tts_audio.mp3"
            with Path.open(test_file, "wb") as f:
                f.write(audio_data)
            print(f"   ✅ Test audio saved to: {test_file}")
            print(f"   You can play it with: mpg123 {test_file}")

            return True
        print("   ❌ Audio generation returned None")
        return False

    except Exception as e:
        print(f"   ❌ Audio generation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_speak_method():
    """Test the speak method with generate_audio parameter"""

    print("\n" + "=" * 60)
    print("Testing speak() Method with generate_audio Parameter")
    print("=" * 60)

    tts_engine = os.getenv("TTS_ENGINE", "pyttsx3")
    tts = TTSService(
        engine=tts_engine,
        voice_type=os.getenv("TTS_VOICE", "default"),
        speed=int(os.getenv("TTS_SPEED", "150")),
        volume=float(os.getenv("TTS_VOLUME", "0.9")),
    )

    test_text = "Welcome to the game"

    print("\n1. Testing speak() with generate_audio=True:")
    try:
        result = tts.speak(test_text, generate_audio=True)
        if result and isinstance(result, bytes):
            print(f"   ✅ Returned audio bytes: {len(result)} bytes")
        else:
            print(f"   ❌ Expected bytes, got: {type(result)}")
            return False
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

    print("\n2. Testing speak() with generate_audio=False:")
    try:
        result = tts.speak(test_text, generate_audio=False)
        print(f"   ✅ Returned: {result} (type: {type(result).__name__})")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

    return True


def main():
    """Run all tests"""

    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "TTS Client-Side Implementation Test" + " " * 13 + "║")
    print("╚" + "=" * 58 + "╝")

    # Run tests
    test1_passed = test_tts_audio_generation()
    test2_passed = test_speak_method()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Audio Generation Test: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"speak() Method Test:   {'✅ PASSED' if test2_passed else '❌ FAILED'}")

    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! Client-side TTS is working correctly.")
        print("\nNext steps:")
        print("1. Start the application: python app.py")
        print("2. Open the game in your browser")
        print("3. Make a throw and listen for TTS audio")
        return 0
    print("\n❌ Some tests failed. Please check the errors above.")
    print("\nTroubleshooting:")
    print("1. Ensure TTS_ENGINE=gtts in your .env file")
    print("2. Check internet connection (gTTS requires internet)")
    print("3. Verify gTTS is installed: pip install gtts")
    return 1


if __name__ == "__main__":
    sys.exit(main())
