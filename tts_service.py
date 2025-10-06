"""
Text-to-Speech Service for Dart Game
Provides configurable TTS with speed and voice type options
"""

import io
import logging

try:
    from gtts import gTTS

    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

try:
    import pyttsx3

    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False


logger = logging.getLogger(__name__)


class TTSService:
    """Text-to-Speech service with configurable voice and speed"""

    def __init__(
        self,
        engine: str = "pyttsx3",
        voice_type: str = "default",
        speed: int = 150,
        volume: float = 1.0,
    ):
        """
        Initialize TTS service

        Args:
            engine: TTS engine to use ('pyttsx3' or 'gtts')
            voice_type: Voice type identifier (engine-specific)
            speed: Speech rate (words per minute for pyttsx3, 0.5-2.0 for gtts)
            volume: Volume level (0.0 to 1.0)
        """
        self.engine_name = engine
        self.voice_type = voice_type
        self.speed = speed
        self.volume = volume
        self.engine = None
        self.enabled = True

        # Initialize the selected engine
        if engine == "pyttsx3" and PYTTSX3_AVAILABLE:
            self._init_pyttsx3()
        elif engine == "gtts" and GTTS_AVAILABLE:
            self._init_gtts()
        else:
            logger.warning(
                f"TTS engine '{engine}' not available. "
                f"pyttsx3: {PYTTSX3_AVAILABLE}, gtts: {GTTS_AVAILABLE}",
            )
            self.enabled = False

    def _init_pyttsx3(self):
        """Initialize pyttsx3 engine"""
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", self.speed)
            self.engine.setProperty("volume", self.volume)

            # Set voice if specified
            if self.voice_type != "default":
                voices = self.engine.getProperty("voices")
                for voice in voices:
                    if self.voice_type.lower() in voice.name.lower():
                        self.engine.setProperty("voice", voice.id)
                        break

            logger.info("pyttsx3 TTS engine initialized successfully")
        except Exception:
            logger.exception("Failed to initialize pyttsx3")
            self.enabled = False

    def _init_gtts(self):
        """Initialize gTTS (Google Text-to-Speech)"""
        # gTTS doesn't need initialization, but we validate it's available
        if not GTTS_AVAILABLE:
            logger.error("gTTS is not available")
            self.enabled = False
        else:
            logger.info("gTTS engine ready")

    def speak(self, text: str) -> bool:
        """
        Speak the given text

        Args:
            text: Text to speak

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not text:
            return False

        try:
            if self.engine_name == "pyttsx3" and self.engine:
                self.engine.say(text)
                self.engine.runAndWait()
                return True
            if self.engine_name == "gtts" and GTTS_AVAILABLE:
                # Note: gTTS generates audio files, not real-time speech
                # This is a placeholder for server-side generation
                logger.info(f"gTTS would generate audio for: {text}")
                return True
        except Exception:
            logger.exception("TTS speak error")
            return False

        return False

    def generate_audio_data(self, text: str, lang: str = "en") -> bytes | None:
        """
        Generate audio data for the given text (useful for web streaming)

        Args:
            text: Text to convert to speech
            lang: Language code (for gTTS)

        Returns:
            Audio data as bytes, or None if failed
        """
        if not self.enabled or not text:
            return None

        try:
            if self.engine_name == "gtts" and GTTS_AVAILABLE:
                # Adjust speed for gTTS (slow parameter)
                slow = self.speed < 100 if isinstance(self.speed, int) else self.speed < 1.0

                tts = gTTS(text=text, lang=lang, slow=slow)
                audio_fp = io.BytesIO()
                tts.write_to_fp(audio_fp)
                audio_fp.seek(0)
                return audio_fp.read()
        except Exception:
            logger.exception("TTS audio generation error")

        return None

    def set_speed(self, speed: int):
        """
        Set speech speed

        Args:
            speed: Speech rate (words per minute for pyttsx3, 0.5-2.0 for gtts)
        """
        self.speed = speed
        if self.engine_name == "pyttsx3" and self.engine:
            try:
                self.engine.setProperty("rate", speed)
            except Exception:
                logger.exception("Failed to set speed")

    def set_volume(self, volume: float):
        """
        Set speech volume

        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.volume = max(0.0, min(1.0, volume))
        if self.engine_name == "pyttsx3" and self.engine:
            try:
                self.engine.setProperty("volume", self.volume)
            except Exception:
                logger.exception("Failed to set volume")

    def set_voice(self, voice_type: str):
        """
        Set voice type

        Args:
            voice_type: Voice identifier (engine-specific)
        """
        self.voice_type = voice_type
        if self.engine_name == "pyttsx3" and self.engine:
            try:
                voices = self.engine.getProperty("voices")
                for voice in voices:
                    if voice_type.lower() in voice.name.lower():
                        self.engine.setProperty("voice", voice.id)
                        logger.info(f"Voice set to: {voice.name}")
                        break
            except Exception:
                logger.exception("Failed to set voice")

    def get_available_voices(self) -> list:
        """
        Get list of available voices

        Returns:
            List of voice information dictionaries
        """
        if self.engine_name == "pyttsx3" and self.engine:
            try:
                voices = self.engine.getProperty("voices")
                return [
                    {
                        "id": voice.id,
                        "name": voice.name,
                        "languages": voice.languages,
                        "gender": getattr(voice, "gender", "unknown"),
                    }
                    for voice in voices
                ]
            except Exception:
                logger.exception("Failed to get voices")

        return []

    def enable(self):
        """Enable TTS"""
        self.enabled = True

    def disable(self):
        """Disable TTS"""
        self.enabled = False

    def is_enabled(self) -> bool:
        """Check if TTS is enabled"""
        return self.enabled
