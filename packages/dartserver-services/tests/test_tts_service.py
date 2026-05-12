"""Tests for TTSService."""

from dartserver_services import TTSService


def test_tts_initialization():
    """Test TTSService initialization."""
    tts = TTSService(engine="pyttsx3", speed=150, volume=0.8, language="en")

    assert tts.engine_name == "pyttsx3"
    assert tts.speed == 150
    assert tts.volume == 0.8
    assert tts.language == "en"


def test_tts_supported_languages():
    """Test getting supported languages."""
    supported = TTSService.get_supported_languages()

    assert isinstance(supported, dict)
    assert "en" in supported
    assert "nl" in supported
    assert "de" in supported
    assert "fr" in supported
    assert "es" in supported


def test_tts_volume_clamping():
    """Test volume clamping to 0.0-1.0 range."""
    tts = TTSService(volume=2.0)
    assert tts.volume == 1.0

    tts.set_volume(2.0)
    assert tts.volume == 1.0

    tts.set_volume(-1.0)
    assert tts.volume == 0.0

    tts.set_volume(0.5)
    assert tts.volume == 0.5


def test_tts_language_setting():
    """Test language setting."""
    tts = TTSService(language="en")
    assert tts.language == "en"

    tts.set_language("de")
    assert tts.language == "de"

    # Invalid language should not change
    tts.set_language("invalid")
    assert tts.language == "de"


def test_tts_enable_disable():
    """Test enabling and disabling TTS."""
    tts = TTSService(engine="pyttsx3")

    tts.disable()
    assert not tts.is_enabled()

    tts.enable()
    assert tts.is_enabled()


def test_tts_speak_with_disabled_engine():
    """Test speak method with disabled engine."""
    tts = TTSService(engine="invalid_engine")

    # Should return None when disabled and generate_audio=True
    result = tts.speak("Hello", generate_audio=True)
    assert result is None

    # Should return False when disabled and generate_audio=False
    result = tts.speak("Hello", generate_audio=False)
    assert result is False


def test_tts_speak_with_empty_text():
    """Test speak method with empty text."""
    tts = TTSService(engine="pyttsx3")

    result = tts.speak("", generate_audio=True)
    assert result is None

    result = tts.speak("", generate_audio=False)
    assert result is False
