"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture
def rabbitmq_config():
    """Sample RabbitMQ configuration."""
    return {
        "host": "localhost",
        "port": 5672,
        "user": "guest",
        "password": "guest",
        "vhost": "/",
        "exchange": "darts",
        "topic": "darts.scores.#",
    }


@pytest.fixture
def mock_callback():
    """Mock callback function for RabbitMQ."""

    def callback(message):
        return message

    return callback


@pytest.fixture
def tts_config():
    """Sample TTS configuration."""
    return {
        "engine": "pyttsx3",
        "voice_type": "default",
        "speed": 150,
        "volume": 1.0,
        "language": "en",
    }
