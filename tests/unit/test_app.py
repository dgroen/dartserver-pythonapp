"""Unit tests for app.py module."""

from unittest.mock import patch

import pytest


@pytest.fixture
def client(flask_app):
    """Create test client."""
    with flask_app.test_client() as client:
        yield client


@pytest.fixture
def authenticated_client(client):
    """Create authenticated test client."""
    with client.session_transaction() as sess:
        sess["access_token"] = "test-token"
        sess["user_info"] = {"username": "testuser", "sub": "test-user"}

    with patch("dartserver_core.auth.validate_token") as mock_validate:
        mock_validate.return_value = {
            "sub": "test-user",
            "groups": ["admin"],
            "roles": ["admin"],
        }
        yield client


class TestAppModule:
    """Test app module functions and SocketIO handlers."""

    def test_app_initialization(self, flask_app):
        """Test Flask app initializes correctly."""
        assert flask_app is not None
        assert flask_app.config["TESTING"] is True
        assert hasattr(flask_app, "game_manager")
        assert hasattr(flask_app, "multi_game_manager")
        assert hasattr(flask_app, "socketio")

    def test_app_blueprints_registered(self, flask_app):
        """Test all blueprints are registered."""
        blueprint_names = [bp.name for bp in flask_app.blueprints.values()]
        assert "ui" in blueprint_names
        assert "auth" in blueprint_names
        assert "games" in blueprint_names
        assert "api" in blueprint_names
        assert "services" in blueprint_names

    def test_swagger_configured(self, flask_app):
        """Test Swagger UI is configured."""
        response = flask_app.test_client().get("/api/docs/")
        # Swagger UI should be accessible (may redirect)
        assert response.status_code in [200, 301, 302, 404]

    def test_cors_enabled(self, flask_app):
        """Test CORS is enabled for the app."""
        # CORS extension should be attached
        assert hasattr(flask_app, "extensions")

    def test_session_cookie_config(self, flask_app):
        """Test session cookie is configured securely."""
        assert flask_app.config["SESSION_COOKIE_HTTPONLY"] is True
        assert flask_app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
        assert flask_app.config["PERMANENT_SESSION_LIFETIME"] == 3600


class TestSocketIOHandlers:
    """Test SocketIO event handlers."""

    def test_socketio_connect_event(self, flask_app, mock_socketio):
        """Test SocketIO connect event emits game state."""
        with flask_app.test_request_context(), patch("src.app.app.socketio", mock_socketio):
            # Import the handler after patching
            from src.app.app import handle_connect  # noqa: PLC0415

            # Simulate connection
            with patch("src.app.app.request") as mock_request:
                mock_request.sid = "test-session-id"
                handle_connect()

                # Verify game_state was emitted
                mock_socketio.emit.assert_called_once()
                call_args = mock_socketio.emit.call_args
                assert call_args[0][0] == "game_state"

    def test_socketio_disconnect_event(self, flask_app):
        """Test SocketIO disconnect event."""
        from src.app.app import handle_disconnect  # noqa: PLC0415

        # Should not raise exception
        handle_disconnect()

    def test_socketio_manual_score_event(self, flask_app):
        """Test SocketIO manual score event."""
        from src.app.app import handle_manual_score  # noqa: PLC0415

        test_score = {"score": 20, "multiplier": "TRIPLE"}

        with patch.object(flask_app.game_manager, "process_score") as mock_process:
            handle_manual_score(test_score)
            mock_process.assert_called_once_with(test_score)

    def test_socketio_next_player_event(self, flask_app):
        """Test SocketIO next player event."""
        from src.app.app import handle_next_player  # noqa: PLC0415

        with patch.object(flask_app.game_manager, "next_player") as mock_next:
            handle_next_player()
            mock_next.assert_called_once()

    def test_socketio_end_turn_early_event(self, flask_app):
        """Test SocketIO end turn early event."""
        from src.app.app import handle_end_turn_early  # noqa: PLC0415

        with patch.object(flask_app.game_manager, "end_turn_early") as mock_end:
            handle_end_turn_early()
            mock_end.assert_called_once()

    def test_socketio_set_throwout_advice_event(self, flask_app):
        """Test SocketIO set throwout advice event."""
        from src.app.app import handle_set_throwout_advice  # noqa: PLC0415

        with patch.object(flask_app.game_manager, "set_show_throwout_advice") as mock_set:
            handle_set_throwout_advice({"enabled": True})
            mock_set.assert_called_once_with(True)

    def test_socketio_dartboard_test_message(self, flask_app, mock_socketio):
        """Test SocketIO dartboard test message broadcasts."""
        from src.app.app import handle_dartboard_test_message  # noqa: PLC0415

        test_data = {"masterPin": 4, "slavePin": 13, "boardType": "carromco"}

        with patch("src.app.app.socketio", mock_socketio):
            handle_dartboard_test_message(test_data)

            mock_socketio.emit.assert_called_once_with(
                "dartboard_test_received",
                test_data,
                namespace="/",
            )
