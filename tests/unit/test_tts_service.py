"""Unit tests for tts_service module."""

from unittest.mock import MagicMock, patch

from tts_service import TTSService


class TestTTSService:
    """Test TTSService class."""

    @patch("tts_service.GTTS_AVAILABLE", True)
    def test_initialization_gtts(self):
        """Test initialization with gTTS engine."""
        tts = TTSService(engine="gtts")
        assert tts.engine_name == "gtts"
        assert tts.enabled is True

    @patch("tts_service.PYTTSX3_AVAILABLE", True)
    @patch("tts_service.pyttsx3")
    def test_initialization_pyttsx3(self, mock_pyttsx3):
        """Test initialization with pyttsx3 engine."""
        mock_engine = MagicMock()
        mock_pyttsx3.init.return_value = mock_engine

        tts = TTSService(engine="pyttsx3")
        assert tts.engine_name == "pyttsx3"
        assert tts.enabled is True
        mock_pyttsx3.init.assert_called_once()

    @patch("tts_service.GTTS_AVAILABLE", False)
    @patch("tts_service.PYTTSX3_AVAILABLE", False)
    def test_initialization_no_engine_available(self):
        """Test initialization when no engine is available."""
        tts = TTSService(engine="gtts")
        assert tts.enabled is False

    def test_enable_disable(self):
        """Test enabling and disabling TTS."""
        with patch("tts_service.GTTS_AVAILABLE", True):
            tts = TTSService(engine="gtts")
            assert tts.enabled is True

            tts.disable()
            assert tts.enabled is False

            tts.enable()
            assert tts.enabled is True

    def test_speak_when_disabled(self):
        """Test speak method when TTS is disabled."""
        with patch("tts_service.GTTS_AVAILABLE", True):
            tts = TTSService(engine="gtts")
            tts.disable()

            # Should return False and not raise error
            result = tts.speak("test")
            assert result is False

    @patch("tts_service.GTTS_AVAILABLE", True)
    @patch("tts_service.gTTS")
    def test_speak_gtts_generate_audio(self, mock_gtts):
        """Test speak method with gTTS engine generating audio."""
        mock_gtts_instance = MagicMock()
        mock_gtts.return_value = mock_gtts_instance

        # Mock the audio stream
        mock_audio_fp = MagicMock()
        mock_audio_fp.read.return_value = b"audio_data"
        mock_gtts_instance.write_to_fp.return_value = None

        tts = TTSService(engine="gtts")

        with patch("tts_service.io.BytesIO", return_value=mock_audio_fp):
            result = tts.speak("Hello world", generate_audio=True)

        assert result == b"audio_data"
        mock_gtts.assert_called_once()
        mock_audio_fp.seek.assert_called_once_with(0)
        mock_audio_fp.read.assert_called_once()

    @patch("tts_service.PYTTSX3_AVAILABLE", True)
    @patch("tts_service.pyttsx3")
    def test_speak_pyttsx3(self, mock_pyttsx3):
        """Test speak method with pyttsx3 engine."""
        mock_engine = MagicMock()
        mock_pyttsx3.init.return_value = mock_engine

        tts = TTSService(engine="pyttsx3")
        result = tts.speak("Hello world")

        assert result is True
        mock_engine.say.assert_called_once_with("Hello world")
        mock_engine.runAndWait.assert_called_once()

    @patch("tts_service.GTTS_AVAILABLE", True)
    @patch("tts_service.gTTS")
    def test_speak_gtts_error(self, mock_gtts):
        """Test speak method with gTTS when an error occurs."""
        mock_gtts.side_effect = Exception("TTS error")

        tts = TTSService(engine="gtts")
        # Test with generate_audio=True (returns None on error)
        result = tts.speak("Hello world", generate_audio=True)
        assert result is None

        # Test without generate_audio - gTTS doesn't support server-side playback
        # so it just logs and returns True (not an error case)
        # To test error handling, we need to mock the generate_audio_data method
        with patch.object(tts, "generate_audio_data", side_effect=Exception("Error")):
            result2 = tts.speak("Hello world", generate_audio=True)
            assert result2 is None

    @patch("tts_service.PYTTSX3_AVAILABLE", True)
    @patch("tts_service.pyttsx3")
    def test_speak_pyttsx3_error(self, mock_pyttsx3):
        """Test speak method with pyttsx3 when an error occurs."""
        mock_engine = MagicMock()
        mock_engine.say.side_effect = Exception("TTS error")
        mock_pyttsx3.init.return_value = mock_engine

        tts = TTSService(engine="pyttsx3")
        result = tts.speak("Hello world")

        assert result is False

    @patch("tts_service.PYTTSX3_AVAILABLE", True)
    @patch("tts_service.pyttsx3")
    def test_set_voice_type(self, mock_pyttsx3):
        """Test setting voice type."""
        mock_engine = MagicMock()
        mock_voice = MagicMock()
        mock_voice.name = "English Female"
        mock_voice.id = "voice_id_1"
        mock_engine.getProperty.return_value = [mock_voice]
        mock_pyttsx3.init.return_value = mock_engine

        # Voice should be set during initialization
        assert mock_engine.setProperty.call_count >= 2  # rate, volume, and possibly voice

    @patch("tts_service.PYTTSX3_AVAILABLE", True)
    @patch("tts_service.pyttsx3")
    def test_get_available_voices(self, mock_pyttsx3):
        """Test getting available voices."""
        mock_engine = MagicMock()
        mock_voice1 = MagicMock()
        mock_voice1.name = "Voice 1"
        mock_voice1.id = "voice_1"
        mock_voice2 = MagicMock()
        mock_voice2.name = "Voice 2"
        mock_voice2.id = "voice_2"
        mock_engine.getProperty.return_value = [mock_voice1, mock_voice2]
        mock_pyttsx3.init.return_value = mock_engine

        tts = TTSService(engine="pyttsx3")
        voices = tts.get_available_voices()

        assert len(voices) == 2
        assert voices[0]["name"] == "Voice 1"
        assert voices[1]["name"] == "Voice 2"

    @patch("tts_service.GTTS_AVAILABLE", True)
    def test_speak_empty_text(self):
        """Test speak method with empty text."""
        tts = TTSService(engine="gtts")
        result = tts.speak("")

        # Should return False for empty text
        assert result is False

    @patch("tts_service.GTTS_AVAILABLE", True)
    @patch("tts_service.gTTS")
    def test_generate_audio_data_with_language(self, mock_gtts):
        """Test generate_audio_data method with specific language."""
        mock_gtts_instance = MagicMock()
        mock_gtts.return_value = mock_gtts_instance

        mock_audio_fp = MagicMock()
        mock_audio_fp.read.return_value = b"audio_data"

        tts = TTSService(engine="gtts")

        with patch("tts_service.io.BytesIO", return_value=mock_audio_fp):
            result = tts.generate_audio_data("Bonjour", lang="fr")

        # gTTS should be called with the language parameter
        assert result == b"audio_data"
        call_args = mock_gtts.call_args
        assert call_args is not None
        assert call_args[1]["lang"] == "fr"

    @patch("tts_service.PYTTSX3_AVAILABLE", True)
    @patch("tts_service.pyttsx3")
    def test_initialization_with_all_parameters(self, mock_pyttsx3):
        """Test initialization with all parameters."""
        mock_engine = MagicMock()
        mock_pyttsx3.init.return_value = mock_engine

        tts = TTSService(
            engine="pyttsx3",
            voice_type="male",
            speed=200,
            volume=0.8,
        )

        assert tts.engine_name == "pyttsx3"
        assert tts.voice_type == "male"
        assert tts.speed == 200
        assert tts.volume == 0.8
        mock_engine.setProperty.assert_any_call("rate", 200)
        mock_engine.setProperty.assert_any_call("volume", 0.8)

    @patch("tts_service.PYTTSX3_AVAILABLE", True)
    @patch("tts_service.pyttsx3")
    def test_pyttsx3_initialization_error(self, mock_pyttsx3):
        """Test pyttsx3 initialization error handling."""
        mock_pyttsx3.init.side_effect = Exception("Init error")

        tts = TTSService(engine="pyttsx3")

        # Should disable TTS on initialization error
        assert tts.enabled is False

    @patch("tts_service.GTTS_AVAILABLE", True)
    def test_get_available_voices_gtts(self):
        """Test getting available voices with gTTS engine."""
        tts = TTSService(engine="gtts")
        voices = tts.get_available_voices()

        # gTTS doesn't have voice enumeration, should return empty list
        assert voices == []

    @patch("tts_service.GTTS_AVAILABLE", True)
    def test_speak_gtts_without_generate_audio(self):
        """Test speak method with gTTS without generating audio."""
        tts = TTSService(engine="gtts")
        # gTTS doesn't support server-side playback, just logs
        result = tts.speak("Hello world", generate_audio=False)
        assert result is True

    @patch("tts_service.PYTTSX3_AVAILABLE", True)
    @patch("tts_service.pyttsx3")
    def test_set_speed(self, mock_pyttsx3):
        """Test setting speech speed."""
        mock_engine = MagicMock()
        mock_pyttsx3.init.return_value = mock_engine

        tts = TTSService(engine="pyttsx3")
        tts.set_speed(180)

        assert tts.speed == 180
        mock_engine.setProperty.assert_any_call("rate", 180)

    @patch("tts_service.PYTTSX3_AVAILABLE", True)
    @patch("tts_service.pyttsx3")
    def test_set_speed_error(self, mock_pyttsx3):
        """Test setting speech speed with error."""
        mock_engine = MagicMock()
        mock_engine.setProperty.side_effect = Exception("Set property error")
        mock_pyttsx3.init.return_value = mock_engine

        tts = TTSService(engine="pyttsx3")
        # Should not raise exception, just log error
        tts.set_speed(180)
        assert tts.speed == 180

    @patch("tts_service.PYTTSX3_AVAILABLE", True)
    @patch("tts_service.pyttsx3")
    def test_set_volume(self, mock_pyttsx3):
        """Test setting speech volume."""
        mock_engine = MagicMock()
        mock_pyttsx3.init.return_value = mock_engine

        tts = TTSService(engine="pyttsx3")
        tts.set_volume(0.7)

        assert tts.volume == 0.7
        mock_engine.setProperty.assert_any_call("volume", 0.7)

    @patch("tts_service.PYTTSX3_AVAILABLE", True)
    @patch("tts_service.pyttsx3")
    def test_set_volume_clamping(self, mock_pyttsx3):
        """Test volume clamping to valid range."""
        mock_engine = MagicMock()
        mock_pyttsx3.init.return_value = mock_engine

        tts = TTSService(engine="pyttsx3")

        # Test upper bound
        tts.set_volume(1.5)
        assert tts.volume == 1.0

        # Test lower bound
        tts.set_volume(-0.5)
        assert tts.volume == 0.0

    @patch("tts_service.PYTTSX3_AVAILABLE", True)
    @patch("tts_service.pyttsx3")
    def test_set_volume_error(self, mock_pyttsx3):
        """Test setting volume with error."""
        mock_engine = MagicMock()
        mock_engine.setProperty.side_effect = Exception("Set property error")
        mock_pyttsx3.init.return_value = mock_engine

        tts = TTSService(engine="pyttsx3")
        # Should not raise exception, just log error
        tts.set_volume(0.5)
        assert tts.volume == 0.5

    @patch("tts_service.PYTTSX3_AVAILABLE", True)
    @patch("tts_service.pyttsx3")
    def test_set_voice(self, mock_pyttsx3):
        """Test setting voice."""
        mock_engine = MagicMock()
        mock_voice1 = MagicMock()
        mock_voice1.name = "English Male"
        mock_voice1.id = "voice_male"
        mock_voice2 = MagicMock()
        mock_voice2.name = "English Female"
        mock_voice2.id = "voice_female"
        mock_engine.getProperty.return_value = [mock_voice1, mock_voice2]
        mock_pyttsx3.init.return_value = mock_engine

        tts = TTSService(engine="pyttsx3")
        tts.set_voice("female")

        assert tts.voice_type == "female"
        # Should have set the voice property
        calls = [call for call in mock_engine.setProperty.call_args_list if call[0][0] == "voice"]
        assert len(calls) > 0

    @patch("tts_service.PYTTSX3_AVAILABLE", True)
    @patch("tts_service.pyttsx3")
    def test_set_voice_error(self, mock_pyttsx3):
        """Test setting voice with error."""
        mock_engine = MagicMock()
        mock_engine.getProperty.side_effect = Exception("Get property error")
        mock_pyttsx3.init.return_value = mock_engine

        tts = TTSService(engine="pyttsx3")
        # Should not raise exception, just log error
        tts.set_voice("female")
        assert tts.voice_type == "female"

    @patch("tts_service.PYTTSX3_AVAILABLE", True)
    @patch("tts_service.pyttsx3")
    def test_get_available_voices_error(self, mock_pyttsx3):
        """Test getting available voices with error."""
        mock_engine = MagicMock()
        mock_engine.getProperty.side_effect = Exception("Get property error")
        mock_pyttsx3.init.return_value = mock_engine

        tts = TTSService(engine="pyttsx3")
        voices = tts.get_available_voices()

        # Should return empty list on error
        assert voices == []

    @patch("tts_service.GTTS_AVAILABLE", True)
    @patch("tts_service.gTTS")
    def test_generate_audio_data_disabled(self, mock_gtts):
        """Test generate_audio_data when TTS is disabled."""
        tts = TTSService(engine="gtts")
        tts.disable()

        result = tts.generate_audio_data("Hello")
        assert result is None

    @patch("tts_service.GTTS_AVAILABLE", True)
    @patch("tts_service.gTTS")
    def test_generate_audio_data_empty_text(self, mock_gtts):
        """Test generate_audio_data with empty text."""
        tts = TTSService(engine="gtts")

        result = tts.generate_audio_data("")
        assert result is None

    @patch("tts_service.GTTS_AVAILABLE", True)
    @patch("tts_service.gTTS")
    def test_generate_audio_data_error(self, mock_gtts):
        """Test generate_audio_data with error."""
        mock_gtts.side_effect = Exception("TTS error")

        tts = TTSService(engine="gtts")
        result = tts.generate_audio_data("Hello")

        assert result is None

    @patch("tts_service.GTTS_AVAILABLE", True)
    @patch("tts_service.gTTS")
    def test_generate_audio_data_slow_speed(self, mock_gtts):
        """Test generate_audio_data with slow speed."""
        mock_gtts_instance = MagicMock()
        mock_gtts.return_value = mock_gtts_instance

        mock_audio_fp = MagicMock()
        mock_audio_fp.read.return_value = b"audio_data"

        tts = TTSService(engine="gtts", speed=50)  # Slow speed

        with patch("tts_service.io.BytesIO", return_value=mock_audio_fp):
            result = tts.generate_audio_data("Hello")

        assert result == b"audio_data"
        # Should be called with slow=True
        call_args = mock_gtts.call_args
        assert call_args[1]["slow"] is True

    @patch("tts_service.GTTS_AVAILABLE", True)
    def test_is_enabled(self):
        """Test is_enabled method."""
        tts = TTSService(engine="gtts")
        assert tts.is_enabled() is True

        tts.disable()
        assert tts.is_enabled() is False

        tts.enable()
        assert tts.is_enabled() is True
