"""
Text-to-Speech Service for Dart Game
Provides configurable TTS with speed and voice type options
"""

import io
import logging
from typing import Any

try:  # Prefer the core shim so test patches on src.core.tts_service take effect
    from src.core import tts_service as core_tts
except Exception:  # pragma: no cover - fallback for environments without core shim
    core_tts = None

try:
    from gtts import gTTS as _gtts_impl

    _gtts_available_impl = True
except ImportError:  # pragma: no cover - optional dependency
    _gtts_impl = None
    _gtts_available_impl = False

try:
    import pyttsx3 as _pyttsx3_impl

    _pyttsx3_available_impl = True
except ImportError:  # pragma: no cover - optional dependency
    _pyttsx3_impl = None
    _pyttsx3_available_impl = False


def _get_gtts_available() -> bool:
    if core_tts and hasattr(core_tts, "GTTS_AVAILABLE"):
        return bool(getattr(core_tts, "GTTS_AVAILABLE"))
    return _gtts_available_impl


def _get_pyttsx3_available() -> bool:
    if core_tts and hasattr(core_tts, "PYTTSX3_AVAILABLE"):
        return bool(getattr(core_tts, "PYTTSX3_AVAILABLE"))
    return _pyttsx3_available_impl


def _get_gtts():
    if core_tts and hasattr(core_tts, "gTTS"):
        return getattr(core_tts, "gTTS")
    return _gtts_impl


def _get_pyttsx3():
    if core_tts and hasattr(core_tts, "pyttsx3"):
        return getattr(core_tts, "pyttsx3")
    return _pyttsx3_impl


# Expose availability flags for logging and tests
GTTS_AVAILABLE = _get_gtts_available()
PYTTSX3_AVAILABLE = _get_pyttsx3_available()


logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = {
    "en": "English",
    "nl": "Dutch",
    "de": "German",
    "fr": "French",
    "es": "Spanish",
    "it": "Italian",
    "pt": "Portuguese",
    "ru": "Russian",
    "ja": "Japanese",
    "zh-cn": "Chinese (Simplified)",
    "zh-tw": "Chinese (Traditional)",
    "ko": "Korean",
}


class TTSService:
    """Text-to-Speech service with configurable voice and speed"""

    def __init__(
        self,
        engine: str = "pyttsx3",
        voice_type: str = "default",
        speed: int = 150,
        volume: float = 1.0,
        language: str = "en",
    ):
        """
        Initialize TTS service

        Args:
            engine: TTS engine to use ('pyttsx3' or 'gtts')
            voice_type: Voice type identifier (engine-specific)
            speed: Speech rate (words per minute for pyttsx3, 0.5-2.0 for gtts)
            volume: Volume level (0.0 to 1.0)
            language: Language code (e.g., 'en', 'nl', 'de', 'fr', 'es')
        """
        self.engine_name = engine
        self.voice_type = voice_type
        self.speed = speed
        self.volume = volume
        self.language = language
        self.engine: Any = None
        self.enabled = True

        # Initialize the selected engine
        if engine == "pyttsx3" and _get_pyttsx3_available():
            self._init_pyttsx3()
        elif engine == "gtts" and _get_gtts_available():
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
            pyttsx3_module = _get_pyttsx3()
            if not pyttsx3_module:
                self.enabled = False
                return

            self.engine = pyttsx3_module.init()
            self.engine.setProperty("rate", self.speed)
            self.engine.setProperty("volume", self.volume)

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
        if not _get_gtts_available():
            logger.error("gTTS is not available")
            self.enabled = False
        else:
            logger.info("gTTS engine ready")

    def speak(self, text: str, generate_audio: bool = False) -> bool | bytes | None:
        """
        Speak the given text or generate audio data

        Args:
            text: Text to speak
            generate_audio: If True, return audio data instead of playing locally

        Returns:
            If generate_audio is True: audio bytes or None
            If generate_audio is False: True if successful, False otherwise
        """
        if not self.enabled or not text:
            return None if generate_audio else False

        try:
            if generate_audio:
                return self.generate_audio_data(text, self.language)

            if self.engine_name == "pyttsx3" and self.engine:
                self.engine.say(text)
                self.engine.runAndWait()
                return True
            if self.engine_name == "gtts" and _get_gtts_available():
                logger.info(f"gTTS would generate audio for: {text}")
                return True
        except Exception:
            logger.exception("TTS speak error")
            return None if generate_audio else False

        return None if generate_audio else False

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

        lang_to_use = lang if lang else self.language

        try:
            gtts_cls = _get_gtts()
            if self.engine_name == "gtts" and _get_gtts_available() and gtts_cls:
                slow = self.speed < 100 if isinstance(self.speed, int) else self.speed < 1.0

                tts = gtts_cls(text=text, lang=lang_to_use, slow=slow)
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

    def set_language(self, language: str):
        """
        Set language

        Args:
            language: Language code (e.g., 'en', 'nl', 'de', 'fr', 'es')
        """
        if language in SUPPORTED_LANGUAGES:
            self.language = language
            logger.info(f"Language set to: {SUPPORTED_LANGUAGES[language]}")
        else:
            logger.warning(f"Language '{language}' not supported. Keeping current: {self.language}")

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

    @staticmethod
    def get_supported_languages() -> dict:
        """
        Get all supported languages

        Returns:
            Dictionary mapping language codes to language names
        """
        return SUPPORTED_LANGUAGES

    def enable(self):
        """Enable TTS"""
        self.enabled = True

    def disable(self):
        """Disable TTS"""
        self.enabled = False

    def is_enabled(self) -> bool:
        """Check if TTS is enabled"""
        return self.enabled
