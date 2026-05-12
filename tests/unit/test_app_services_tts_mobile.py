"""Unit tests for app_services.py endpoints (Part 2: TTS and Mobile services)."""

import json
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def client(flask_app):
    """Create authenticated test client."""
    with flask_app.test_client() as client:
        with client.session_transaction() as sess:
            sess["access_token"] = "test-token"
            sess["user_info"] = {"username": "testuser", "sub": "test-user"}
            sess["player_id"] = 1

        with patch("dartserver_core.auth.validate_token") as mock_validate:
            mock_validate.return_value = {
                "sub": "test-user",
                "groups": ["admin", "gamemaster"],
                "roles": ["admin", "gamemaster"],
            }
            yield client


class TestTTSConfigEndpoints:
    """Test TTS configuration endpoints."""

    def test_get_tts_config(self, client):
        """Test getting TTS configuration."""
        with patch("src.app.app_services.current_app") as mock_app:
            mock_tts = MagicMock()
            mock_tts.is_enabled.return_value = True
            mock_tts.engine_name = "gtts"
            mock_tts.speed = 150
            mock_tts.volume = 1.0
            mock_tts.voice_type = "default"
            mock_tts.language = "en"

            mock_game_manager = MagicMock()
            mock_game_manager.tts = mock_tts
            mock_app.game_manager = mock_game_manager

            response = client.get("/api/tts/config")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["enabled"] is True
            assert data["engine"] == "gtts"
            assert data["speed"] == 150

    def test_update_tts_config_enable(self, client):
        """Test enabling TTS."""
        with patch("src.app.app_services.current_app") as mock_app:
            mock_tts = MagicMock()
            mock_game_manager = MagicMock()
            mock_game_manager.tts = mock_tts
            mock_app.game_manager = mock_game_manager

            response = client.post(
                "/api/tts/config",
                data=json.dumps({"enabled": True}),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["status"] == "success"
            mock_tts.enable.assert_called_once()

    def test_update_tts_config_disable(self, client):
        """Test disabling TTS."""
        with patch("src.app.app_services.current_app") as mock_app:
            mock_tts = MagicMock()
            mock_game_manager = MagicMock()
            mock_game_manager.tts = mock_tts
            mock_app.game_manager = mock_game_manager

            response = client.post(
                "/api/tts/config",
                data=json.dumps({"enabled": False}),
                content_type="application/json",
            )

            assert response.status_code == 200
            mock_tts.disable.assert_called_once()

    def test_update_tts_config_speed(self, client):
        """Test updating TTS speed."""
        with patch("src.app.app_services.current_app") as mock_app:
            mock_tts = MagicMock()
            mock_game_manager = MagicMock()
            mock_game_manager.tts = mock_tts
            mock_app.game_manager = mock_game_manager

            response = client.post(
                "/api/tts/config",
                data=json.dumps({"speed": 175}),
                content_type="application/json",
            )

            assert response.status_code == 200
            mock_tts.set_speed.assert_called_once_with(175)

    def test_update_tts_config_volume(self, client):
        """Test updating TTS volume."""
        with patch("src.app.app_services.current_app") as mock_app:
            mock_tts = MagicMock()
            mock_game_manager = MagicMock()
            mock_game_manager.tts = mock_tts
            mock_app.game_manager = mock_game_manager

            response = client.post(
                "/api/tts/config",
                data=json.dumps({"volume": 0.8}),
                content_type="application/json",
            )

            assert response.status_code == 200
            mock_tts.set_volume.assert_called_once_with(0.8)

    def test_get_tts_voices(self, client):
        """Test getting available TTS voices."""
        with patch("src.app.app_services.current_app") as mock_app:
            mock_tts = MagicMock()
            mock_tts.get_available_voices.return_value = [
                {"id": "voice1", "name": "Voice 1"},
                {"id": "voice2", "name": "Voice 2"},
            ]
            mock_game_manager = MagicMock()
            mock_game_manager.tts = mock_tts
            mock_app.game_manager = mock_game_manager

            response = client.get("/api/tts/voices")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data) == 2
            assert data[0]["id"] == "voice1"

    def test_get_tts_languages(self, client):
        """Test getting supported TTS languages."""
        with patch(
            "dartserver_services.tts_service.TTSService.get_supported_languages",
        ) as mock_langs:
            mock_langs.return_value = {
                "en": "English",
                "nl": "Dutch",
                "de": "German",
            }

            response = client.get("/api/tts/languages")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert "en" in data
            assert data["en"] == "English"

    def test_test_tts_success(self, client):
        """Test TTS with custom text."""
        with patch("src.app.app_services.current_app") as mock_app:
            mock_tts = MagicMock()
            mock_tts.speak.return_value = True
            mock_game_manager = MagicMock()
            mock_game_manager.tts = mock_tts
            mock_app.game_manager = mock_game_manager

            response = client.post(
                "/api/tts/test",
                data=json.dumps({"text": "Hello, World!"}),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["status"] == "success"
            mock_tts.speak.assert_called_once_with("Hello, World!")

    def test_test_tts_failure(self, client):
        """Test TTS failure."""
        with patch("src.app.app_services.current_app") as mock_app:
            mock_tts = MagicMock()
            mock_tts.speak.return_value = False
            mock_game_manager = MagicMock()
            mock_game_manager.tts = mock_tts
            mock_app.game_manager = mock_game_manager

            response = client.post(
                "/api/tts/test",
                data=json.dumps({"text": "Test"}),
                content_type="application/json",
            )

            assert response.status_code == 500
            data = json.loads(response.data)
            assert data["status"] == "error"


class TestMobileAppPages:
    """Test mobile app page endpoints."""

    def test_mobile_app_requires_auth(self, flask_app):
        """Test mobile app page requires authentication."""
        with flask_app.test_client() as client:
            response = client.get("/mobile")
            assert response.status_code in [302, 401, 403]

    def test_mobile_app_renders_for_authenticated_user(self, client):
        """Test mobile app renders for authenticated user."""
        response = client.get("/mobile")
        assert response.status_code == 200
        assert b"<!DOCTYPE html>" in response.data or b"<html" in response.data

    def test_mobile_gameplay_requires_auth(self, flask_app):
        """Test mobile gameplay page requires authentication."""
        with flask_app.test_client() as client:
            response = client.get("/mobile/gameplay")
            assert response.status_code in [302, 401, 403]

    def test_mobile_gameplay_renders(self, client):
        """Test mobile gameplay page renders."""
        response = client.get("/mobile/gameplay")
        assert response.status_code == 200

    def test_mobile_gamemaster_requires_role(self, flask_app):
        """Test mobile gamemaster page requires role."""
        with flask_app.test_client() as client:
            with client.session_transaction() as sess:
                sess["access_token"] = "test-token"

            with patch("dartserver_core.auth.validate_token") as mock_validate:
                mock_validate.return_value = {"sub": "test-user", "groups": []}

                response = client.get("/mobile/gamemaster")
                assert response.status_code in [302, 401, 403]

    def test_mobile_gamemaster_renders_for_gamemaster(self, client):
        """Test mobile gamemaster page renders for gamemaster."""
        response = client.get("/mobile/gamemaster")
        assert response.status_code == 200

    def test_mobile_dartboard_setup_renders(self, client):
        """Test mobile dartboard setup page renders."""
        response = client.get("/mobile/dartboard-setup")
        assert response.status_code == 200

    def test_mobile_results_renders(self, client):
        """Test mobile results page renders."""
        response = client.get("/mobile/results")
        assert response.status_code == 200

    def test_mobile_account_renders(self, client):
        """Test mobile account page renders."""
        response = client.get("/mobile/account")
        assert response.status_code == 200

    def test_mobile_hotspot_renders(self, client):
        """Test mobile hotspot page renders."""
        response = client.get("/mobile/hotspot")
        assert response.status_code == 200


class TestAPIKeyManagement:
    """Test API key management endpoints."""

    def test_get_api_keys_requires_auth(self, flask_app):
        """Test getting API keys requires authentication."""
        with flask_app.test_client() as client:
            response = client.get("/api/mobile/apikeys")
            assert response.status_code in [302, 401, 403]

    def test_get_api_keys_success(self, client):
        """Test getting API keys."""
        with patch("src.app.app_services.get_mobile_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_user_api_keys.return_value = [
                {"id": 1, "key_name": "Test Key", "created_at": "2024-01-01"},
            ]
            mock_get_service.return_value = mock_service

            response = client.get("/api/mobile/apikeys")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert len(data["api_keys"]) == 1

    def test_get_api_keys_no_player_id(self, flask_app):
        """Test getting API keys without player_id in session."""
        with flask_app.test_client() as client:
            with client.session_transaction() as sess:
                sess["access_token"] = "test-token"
                # No player_id

            with patch("dartserver_core.auth.validate_token") as mock_validate:
                mock_validate.return_value = {"sub": "test-user", "groups": ["admin"]}

                response = client.get("/api/mobile/apikeys")

                assert response.status_code == 401

    def test_create_api_key_success(self, client):
        """Test creating an API key."""
        with patch("src.app.app_services.get_mobile_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.create_api_key.return_value = {
                "success": True,
                "api_key": {"id": 2, "key": "new-key-123"},
            }
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/mobile/apikeys",
                data=json.dumps({"key_name": "My New Key"}),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True

    def test_revoke_api_key_success(self, client):
        """Test revoking an API key."""
        with patch("src.app.app_services.get_mobile_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.revoke_api_key.return_value = {"success": True}
            mock_get_service.return_value = mock_service

            response = client.delete("/api/mobile/apikeys/1")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True


class TestDartboardManagement:
    """Test dartboard management endpoints."""

    def test_get_dartboards_requires_auth(self, flask_app):
        """Test getting dartboards requires authentication."""
        with flask_app.test_client() as client:
            response = client.get("/api/mobile/dartboards")
            assert response.status_code in [302, 401, 403]

    def test_get_dartboards_success(self, client):
        """Test getting dartboards."""
        with patch("src.app.app_services.get_mobile_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_user_dartboards.return_value = [
                {"id": 1, "name": "My Dartboard"},
            ]
            mock_get_service.return_value = mock_service

            response = client.get("/api/mobile/dartboards")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert len(data["dartboards"]) == 1

    def test_register_dartboard_success(self, client):
        """Test registering a dartboard."""
        with patch("src.app.app_services.get_mobile_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.register_dartboard.return_value = {
                "success": True,
                "dartboard": {"id": 2, "name": "New Board"},
            }
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/mobile/dartboards",
                data=json.dumps(
                    {
                        "dartboard_id": "board-123",
                        "name": "New Board",
                        "wpa_key": "secret-key",
                    },
                ),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True

    def test_register_dartboard_missing_fields(self, client):
        """Test registering dartboard with missing fields."""
        response = client.post(
            "/api/mobile/dartboards",
            data=json.dumps({"dartboard_id": "board-123"}),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False

    def test_delete_dartboard_success(self, client):
        """Test deleting a dartboard."""
        with patch("src.app.app_services.get_mobile_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.delete_dartboard.return_value = {"success": True}
            mock_get_service.return_value = mock_service

            response = client.delete("/api/mobile/dartboards/1")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True


class TestHotspotConfiguration:
    """Test hotspot configuration endpoints."""

    def test_get_hotspot_configs(self, client):
        """Test getting hotspot configurations."""
        with patch("src.app.app_services.get_mobile_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.get_hotspot_configs.return_value = [
                {"id": 1, "ssid": "TestHotspot"},
            ]
            mock_get_service.return_value = mock_service

            response = client.get("/api/mobile/hotspot")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert len(data["configs"]) == 1

    def test_create_hotspot_config_success(self, client):
        """Test creating hotspot configuration."""
        with patch("src.app.app_services.get_mobile_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.create_hotspot_config.return_value = {
                "success": True,
                "config": {"id": 2},
            }
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/mobile/hotspot",
                data=json.dumps(
                    {
                        "dartboard_id": 1,
                        "ssid": "MyHotspot",
                        "password": "mypassword",
                    },
                ),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True

    def test_toggle_hotspot_success(self, client):
        """Test toggling hotspot."""
        with patch("src.app.app_services.get_mobile_service") as mock_get_service:
            mock_service = MagicMock()
            mock_service.toggle_hotspot.return_value = {
                "success": True,
                "is_enabled": True,
            }
            mock_get_service.return_value = mock_service

            response = client.post(
                "/api/mobile/hotspot/1/toggle",
                data=json.dumps({"enabled": True}),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True


class TestDartboardAPIEndpoints:
    """Test dartboard API endpoints (authenticated with API key)."""

    def test_dartboard_connect_requires_api_key(self, flask_app):
        """Test dartboard connect requires API key."""
        with flask_app.test_client() as client:
            response = client.post(
                "/api/dartboard/connect",
                data=json.dumps({"dartboard_id": "board-123"}),
                content_type="application/json",
            )
            assert response.status_code == 401

    def test_dartboard_submit_score_requires_api_key(self, flask_app):
        """Test dartboard score submission requires API key."""
        with flask_app.test_client() as client:
            response = client.post(
                "/api/dartboard/score",
                data=json.dumps({"score": 20, "multiplier": "TRIPLE"}),
                content_type="application/json",
            )
            assert response.status_code == 401
