"""Unit tests for app.py database endpoints."""

from unittest.mock import MagicMock, patch

import pytest

from src.app.app import app


class TestDatabaseEndpoints:
    """Test database-related endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

    @pytest.fixture
    def mock_game_manager(self):
        """Mock game manager with database service."""
        with patch("src.app.app.game_manager") as mock_gm:
            mock_db_service = MagicMock()
            mock_gm.db_service = mock_db_service
            yield mock_gm, mock_db_service

    def test_get_game_history_success(self, client, mock_game_manager):
        """Test getting game history successfully."""
        _mock_gm, mock_db = mock_game_manager
        mock_db.get_recent_games.return_value = [
            {
                "game_session_id": "test-id",
                "game_type": "301",
                "player_count": 2,
                "winner": "Player 1",
                "started_at": "2024-01-01T00:00:00",
                "finished_at": "2024-01-01T00:30:00",
            },
        ]

        response = client.get("/api/game/history")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert len(data["games"]) == 1

    def test_get_game_history_with_limit(self, client, mock_game_manager):
        """Test getting game history with limit parameter."""
        _mock_gm, mock_db = mock_game_manager
        mock_db.get_recent_games.return_value = []

        response = client.get("/api/game/history?limit=5")
        assert response.status_code == 200
        mock_db.get_recent_games.assert_called_once_with(limit=5)

    def test_get_game_history_error(self, client, mock_game_manager):
        """Test game history endpoint when error occurs."""
        _mock_gm, mock_db = mock_game_manager
        mock_db.get_recent_games.side_effect = Exception("Database error")

        response = client.get("/api/game/history")
        assert response.status_code == 500
        data = response.get_json()
        assert data["status"] == "error"

    def test_get_game_replay_success(self, client, mock_game_manager):
        """Test getting game replay data successfully."""
        _mock_gm, mock_db = mock_game_manager
        mock_db.get_game_replay_data.return_value = {
            "game_session_id": "test-id",
            "game_type": "301",
            "players": [],
            "throws": [],
        }

        response = client.get("/api/game/replay/test-id")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        assert "game_data" in data

    def test_get_game_replay_not_found(self, client, mock_game_manager):
        """Test getting replay data for nonexistent game."""
        _mock_gm, mock_db = mock_game_manager
        mock_db.get_game_replay_data.return_value = None

        response = client.get("/api/game/replay/nonexistent")
        assert response.status_code == 404
        data = response.get_json()
        assert data["status"] == "error"

    def test_get_game_replay_error(self, client, mock_game_manager):
        """Test game replay endpoint when error occurs."""
        _mock_gm, mock_db = mock_game_manager
        mock_db.get_game_replay_data.side_effect = Exception("Database error")

        response = client.get("/api/game/replay/test-id")
        assert response.status_code == 500
        data = response.get_json()
        assert data["status"] == "error"


class TestTTSEndpoints:
    """Test TTS-related endpoints."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

    @pytest.fixture
    def mock_game_manager(self):
        """Mock game manager with TTS service."""
        with patch("src.app.app.game_manager") as mock_gm:
            mock_tts = MagicMock()
            mock_gm.tts = mock_tts
            yield mock_gm, mock_tts

    def test_tts_config_get(self, client, mock_game_manager):
        """Test getting TTS configuration."""
        _mock_gm, mock_tts = mock_game_manager
        mock_tts.is_enabled.return_value = True
        mock_tts.engine_name = "gtts"
        mock_tts.speed = 150
        mock_tts.volume = 0.9
        mock_tts.voice_type = "default"

        response = client.get("/api/tts/config")
        assert response.status_code == 200
        data = response.get_json()
        assert data["enabled"] is True
        assert data["engine"] == "gtts"
        assert data["speed"] == 150
        assert data["volume"] == 0.9
        assert data["voice"] == "default"

    def test_tts_config_update(self, client, mock_game_manager):
        """Test updating TTS configuration."""
        _mock_gm, mock_tts = mock_game_manager

        response = client.post(
            "/api/tts/config",
            json={"enabled": False, "speed": 200, "volume": 0.5},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        mock_tts.disable.assert_called_once()
        mock_tts.set_speed.assert_called_once_with(200)
        mock_tts.set_volume.assert_called_once_with(0.5)

    def test_tts_config_update_enable(self, client, mock_game_manager):
        """Test enabling TTS via config update."""
        _mock_gm, mock_tts = mock_game_manager

        response = client.post("/api/tts/config", json={"enabled": True})
        assert response.status_code == 200
        mock_tts.enable.assert_called_once()

    def test_tts_config_update_disable(self, client, mock_game_manager):
        """Test disabling TTS via config update."""
        _mock_gm, mock_tts = mock_game_manager

        response = client.post("/api/tts/config", json={"enabled": False})
        assert response.status_code == 200
        mock_tts.disable.assert_called_once()

    def test_tts_config_update_voice(self, client, mock_game_manager):
        """Test updating TTS voice."""
        _mock_gm, mock_tts = mock_game_manager

        response = client.post("/api/tts/config", json={"voice": "en-US"})
        assert response.status_code == 200
        mock_tts.set_voice.assert_called_once_with("en-US")

    def test_tts_voices_get(self, client, mock_game_manager):
        """Test getting available TTS voices."""
        _mock_gm, mock_tts = mock_game_manager
        mock_tts.get_available_voices.return_value = [
            {"id": "voice1", "name": "Voice 1", "languages": ["en"], "gender": "male"},
            {"id": "voice2", "name": "Voice 2", "languages": ["en"], "gender": "female"},
        ]

        response = client.get("/api/tts/voices")
        assert response.status_code == 200
        data = response.get_json()
        assert len(data) == 2
        assert data[0]["id"] == "voice1"

    def test_tts_test_success(self, client, mock_game_manager):
        """Test TTS test endpoint successfully."""
        _mock_gm, mock_tts = mock_game_manager
        mock_tts.speak.return_value = True

        response = client.post("/api/tts/test", json={"text": "Hello world"})
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "success"
        mock_tts.speak.assert_called_once_with("Hello world")

    def test_tts_test_failure(self, client, mock_game_manager):
        """Test TTS test endpoint when TTS fails."""
        _mock_gm, mock_tts = mock_game_manager
        mock_tts.speak.return_value = False

        response = client.post("/api/tts/test", json={"text": "Hello"})
        assert response.status_code == 500
        data = response.get_json()
        assert data["status"] == "error"

    def test_tts_test_default_text(self, client, mock_game_manager):
        """Test TTS test endpoint with default text."""
        _mock_gm, mock_tts = mock_game_manager
        mock_tts.speak.return_value = True

        response = client.post("/api/tts/test", json={})
        assert response.status_code == 200
        mock_tts.speak.assert_called_once_with("This is a test")

    def test_tts_generate_success(self, client, mock_game_manager):
        """Test TTS generate endpoint successfully."""
        _mock_gm, mock_tts = mock_game_manager
        mock_tts.generate_audio_data.return_value = b"audio_data"

        response = client.post("/api/tts/generate", json={"text": "Hello world"})
        assert response.status_code == 200
        assert response.data == b"audio_data"
        assert response.mimetype == "audio/mpeg"
        mock_tts.generate_audio_data.assert_called_once_with("Hello world", "en")

    def test_tts_generate_with_lang(self, client, mock_game_manager):
        """Test TTS generate endpoint with language parameter."""
        _mock_gm, mock_tts = mock_game_manager
        mock_tts.generate_audio_data.return_value = b"audio_data"

        response = client.post("/api/tts/generate", json={"text": "Bonjour", "lang": "fr"})
        assert response.status_code == 200
        mock_tts.generate_audio_data.assert_called_once_with("Bonjour", "fr")

    def test_tts_generate_no_text(self, client, mock_game_manager):
        """Test TTS generate endpoint without text."""
        response = client.post("/api/tts/generate", json={})
        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"
        assert "required" in data["message"].lower()

    def test_tts_generate_failure(self, client, mock_game_manager):
        """Test TTS generate endpoint when generation fails."""
        _mock_gm, mock_tts = mock_game_manager
        mock_tts.generate_audio_data.return_value = None

        response = client.post("/api/tts/generate", json={"text": "Hello"})
        assert response.status_code == 500
        data = response.get_json()
        assert data["status"] == "error"
