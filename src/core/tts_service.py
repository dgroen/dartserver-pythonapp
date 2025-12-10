"""Shared TTS dependency flags used by tests and services."""

import io

try:
    from gtts import gTTS

    GTTS_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    gTTS = None  # type: ignore  # noqa: N816
    GTTS_AVAILABLE = False

try:
    import pyttsx3  # type: ignore

    PYTTSX3_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    pyttsx3 = None  # type: ignore
    PYTTSX3_AVAILABLE = False

__all__ = ["gTTS", "pyttsx3", "GTTS_AVAILABLE", "PYTTSX3_AVAILABLE", "io"]
