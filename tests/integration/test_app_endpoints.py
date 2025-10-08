"""Integration tests for Flask application endpoints."""

import json
from unittest.mock import patch

import pytest

from app import app as flask_app


@pytest.fixture
def mock_auth():
    """Mock authentication decorators."""
    # Mock validate_token to return valid claims
    with patch("auth.validate_token") as mock_validate:
        mock_validate.return_value = {
            "sub": "test-user",
            "username": "testuser",
            "groups": ["admin"],  # Admin role has all permissions
            "roles": ["admin"],
        }
        yield mock_validate


@pytest.fixture
def app(mock_auth):
    """Create Flask app for testing."""
    with patch("app.start_rabbitmq_consumer"):
        flask_app.config["TESTING"] = True
        yield flask_app


@pytest.fixture
def client(app):
    """Create test client."""
    client = app.test_client()
    # Set up session with access token for authenticated requests
    with client.session_transaction() as sess:
        sess["access_token"] = "test-token"
        sess["user_info"] = {"username": "testuser", "sub": "test-user"}
    return client


class TestAppEndpoints:
    """Test Flask application endpoints."""

    def test_index_route(self, client):
        """Test index route returns HTML."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"<!DOCTYPE html>" in response.data or b"<html" in response.data

    def test_control_route(self, client):
        """Test control route returns HTML."""
        response = client.get("/control")
        assert response.status_code == 200
        assert b"<!DOCTYPE html>" in response.data or b"<html" in response.data

    def test_get_game_state(self, client):
        """Test getting game state."""
        response = client.get("/api/game/state")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "players" in data
        assert "game_type" in data
        assert "is_started" in data

    def test_new_game_default(self, client):
        """Test starting new game with defaults."""
        response = client.post(
            "/api/game/new",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"

    def test_new_game_301(self, client):
        """Test starting new 301 game."""
        response = client.post(
            "/api/game/new",
            data=json.dumps({"game_type": "301", "players": ["Alice", "Bob"]}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"

    def test_new_game_cricket(self, client):
        """Test starting new cricket game."""
        response = client.post(
            "/api/game/new",
            data=json.dumps({"game_type": "cricket", "players": ["Alice", "Bob"]}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"

    def test_get_players(self, client):
        """Test getting players."""
        # Start a game first
        client.post(
            "/api/game/new",
            data=json.dumps({"game_type": "301", "players": ["Alice", "Bob"]}),
            content_type="application/json",
        )
        # Get players
        response = client.get("/api/players")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list)

    def test_add_player(self, client):
        """Test adding a player."""
        # Start a game first
        client.post(
            "/api/game/new",
            data=json.dumps({"game_type": "301", "players": ["Alice"]}),
            content_type="application/json",
        )
        # Add player
        response = client.post(
            "/api/players",
            data=json.dumps({"name": "Bob"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"

    def test_remove_player(self, client):
        """Test removing a player."""
        # Start a game with 3 players
        client.post(
            "/api/game/new",
            data=json.dumps({"game_type": "301", "players": ["Alice", "Bob", "Charlie"]}),
            content_type="application/json",
        )
        # Remove player
        response = client.delete("/api/players/1")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"

    def test_game_flow_301(self, client):
        """Test complete 301 game flow."""
        # Start game
        response = client.post(
            "/api/game/new",
            data=json.dumps({"game_type": "301", "players": ["Alice", "Bob"]}),
            content_type="application/json",
        )
        assert response.status_code == 200

        # Get game state
        response = client.get("/api/game/state")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["is_started"] is True
        assert data["game_type"] == "301"

    def test_game_flow_cricket(self, client):
        """Test complete cricket game flow."""
        # Start game
        response = client.post(
            "/api/game/new",
            data=json.dumps({"game_type": "cricket", "players": ["Alice", "Bob"]}),
            content_type="application/json",
        )
        assert response.status_code == 200

        # Get game state
        response = client.get("/api/game/state")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["is_started"] is True
        assert data["game_type"] == "cricket"

    def test_invalid_route(self, client):
        """Test invalid route returns 404."""
        response = client.get("/api/invalid")
        assert response.status_code == 404

    def test_post_without_json(self, client):
        """Test POST without JSON content type."""
        response = client.post("/api/game/new", data="not json")
        # Should handle gracefully
        assert response.status_code in [200, 400, 415]
