"""Pytest configuration and fixtures."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Disable TTS during tests to avoid timing issues
os.environ["TTS_ENABLED"] = "false"
# Use in-memory SQLite for tests
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app import app

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


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


@pytest.fixture
def mock_database_service():
    """Mock DatabaseService for testing."""
    with patch("game_manager.DatabaseService") as mock_db:
        mock_instance = MagicMock()
        mock_instance.initialize_database = MagicMock()
        mock_instance.start_new_game = MagicMock()
        mock_instance.record_throw = MagicMock()
        mock_instance.end_game = MagicMock()
        mock_instance.get_game_history = MagicMock(return_value=[])
        mock_instance.get_game_replay_data = MagicMock(return_value=None)
        mock_instance.current_game_session_id = "test-session-id"
        mock_db.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def in_memory_db():
    """Create an in-memory database for testing."""
    from database_service import DatabaseService

    db_service = DatabaseService("sqlite:///:memory:")
    db_service.initialize_database()
    return db_service
