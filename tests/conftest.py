"""Pytest configuration and fixtures."""

import os
import sys
from unittest.mock import MagicMock

import pytest

from app import app

# Add parent directory to path
sys.path.insert(0, os.path.resolve(os.path.parent(__file__) / ".."))


@pytest.fixture
def mock_socketio():
    """Mock SocketIO instance."""
    mock = MagicMock()
    mock.emit = MagicMock()
    return mock


@pytest.fixture
def sample_players():
    """Sample player data for testing."""
    return [
        {"id": 0, "name": "Player 1"},
        {"id": 1, "name": "Player 2"},
    ]


@pytest.fixture
def sample_players_four():
    """Sample player data with four players."""
    return [
        {"id": 0, "name": "Alice"},
        {"id": 1, "name": "Bob"},
        {"id": 2, "name": "Charlie"},
        {"id": 3, "name": "Diana"},
    ]


@pytest.fixture
def sample_score_data():
    """Sample score data for testing."""
    return {
        "score": 20,
        "multiplier": "TRIPLE",
        "user": "Player 1",
    }


@pytest.fixture
def app_client():
    """Flask test client."""

    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def mock_rabbitmq_config():
    """Mock RabbitMQ configuration."""
    return {
        "host": "localhost",
        "port": 5672,
        "user": "guest",
        "password": "guest",
        "vhost": "/",
        "exchange": "darts_exchange",
        "topic": "darts.scores.#",
    }
