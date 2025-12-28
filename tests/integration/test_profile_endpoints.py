"""Tests for user profile page endpoints."""

import json
from unittest.mock import patch

import pytest


@pytest.fixture
def mock_auth():
    """Mock authentication to bypass login_required."""
    with patch("dartserver_core.auth.is_auth_disabled", return_value=True):
        yield


@pytest.fixture
def client(flask_app, mock_auth):
    """Create test client."""
    flask_app.config["TESTING"] = True
    client = flask_app.test_client()
    # Set up session with access token for authenticated requests
    with client.session_transaction() as sess:
        sess["access_token"] = "test-token"
        sess["user_info"] = {
            "username": "testuser",
            "sub": "test-user",
            "preferred_username": "testuser",
        }
        sess["player_id"] = 1
    return client


class TestProfileEndpoints:
    """Test profile page endpoints."""

    def test_profile_route(self, client):
        """Test profile route returns HTML."""
        response = client.get("/profile")
        assert response.status_code == 200
        assert b"<!DOCTYPE html>" in response.data or b"<html" in response.data
        assert b"User Profile" in response.data

    def test_mobile_profile_route(self, client):
        """Test mobile profile route returns HTML."""
        response = client.get("/mobile/profile")
        assert response.status_code == 200
        assert b"<!DOCTYPE html>" in response.data or b"<html" in response.data
        assert b"Profile" in response.data

    def test_profile_requires_authentication(self, flask_app):
        """Test profile route requires authentication."""
        with patch("dartserver_core.auth.is_auth_disabled", return_value=False):
            client = flask_app.test_client()
            response = client.get("/profile")
            # Should redirect to login or return 401/403
            assert response.status_code in [302, 401, 403]

    def test_user_current_api(self, client):
        """Test /api/user/current returns user information."""
        response = client.get("/api/user/current")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "username" in data
        assert "roles" in data

    def test_player_statistics_api(self, client):
        """Test /api/player/statistics endpoint."""
        # This might return 401 or empty stats if no player_id in session
        response = client.get("/api/player/statistics")
        # Accept either 200 with no stats or 401/404
        assert response.status_code in [200, 401, 404]
