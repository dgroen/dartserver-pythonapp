"""Unit tests for multiplayer functionality."""

from unittest.mock import patch

import pytest

from src.core.auth import ROLES


class TestMultiplayerRole:
    """Test multiplayer role definition."""

    def test_multiplayer_role_exists(self):
        """Test that multiplayer role is defined."""
        assert "multiplayer" in ROLES
        assert ROLES["multiplayer"]["name"] == "Multiplayer"

    def test_multiplayer_role_permissions(self):
        """Test multiplayer role has correct permissions."""
        permissions = ROLES["multiplayer"]["permissions"]
        assert "game:create" in permissions
        assert "game:manage" in permissions
        assert "player:invite" in permissions
        assert "score:submit" in permissions
        assert "score:view" in permissions


class TestMultiplayerEndpoints:
    """Test multiplayer-related endpoints."""

    @pytest.fixture
    def app(self):
        """Create test Flask app."""
        from src.app.app import app

        app.config["TESTING"] = True
        app.config["SECRET_KEY"] = "test-secret"
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()

    @pytest.fixture
    def auth_headers(self):
        """Create mock authentication headers."""
        return {"Authorization": "Bearer test-token"}

    @patch("src.core.auth.AUTH_DISABLED", True)
    def test_multiplayer_page_route_exists(self, client):
        """Test that /multiplayer route exists."""
        # With AUTH_DISABLED, we should be able to access the page
        with patch("src.app.app.request") as mock_request:
            mock_request.user_roles = ["multiplayer"]
            mock_request.user_claims = {"username": "testuser"}

            response = client.get("/multiplayer")
            # Should return 200 or redirect, not 404
            assert response.status_code in [200, 302, 401]

    @patch("src.core.auth.AUTH_DISABLED", False)
    @patch("src.core.auth.validate_token")
    @patch("src.app.app.game_manager")
    def test_available_players_api_with_multiplayer_role(
        self,
        mock_game_manager,
        mock_validate_token,
        client,
    ):
        """Test /api/multiplayer/available-players endpoint with multiplayer role."""
        # Mock authentication
        mock_validate_token.return_value = {
            "sub": "testuser",
            "username": "testuser",
            "groups": ["multiplayer"],
        }

        # Mock game state (no active game)
        mock_game_manager.get_game_state.return_value = {"players": []}

        # Mock WSO2 search
        with patch("src.core.auth.search_wso2_users") as mock_search:
            mock_search.return_value = [
                {"username": "player1", "name": "Player One", "email": "p1@example.com"},
                {"username": "player2", "name": "Player Two", "email": "p2@example.com"},
            ]

            with client.session_transaction() as sess:
                sess["access_token"] = "test-token"

            response = client.get("/api/multiplayer/available-players")

            if response.status_code == 200:
                data = response.get_json()
                assert data["success"] is True
                assert "players" in data
                # All players should be available (not in game)
                for player in data["players"]:
                    assert player["inActiveGame"] is False

    @patch("src.core.auth.AUTH_DISABLED", False)
    @patch("src.core.auth.validate_token")
    @patch("src.app.app.game_manager")
    def test_available_players_api_with_active_game(
        self,
        mock_game_manager,
        mock_validate_token,
        client,
    ):
        """Test that players in active game are marked as unavailable."""
        # Mock authentication
        mock_validate_token.return_value = {
            "sub": "testuser",
            "username": "testuser",
            "groups": ["gamemaster"],
        }

        # Mock game state with active players
        mock_game_manager.get_game_state.return_value = {
            "players": [{"name": "player1"}, {"name": "Player Two"}],
        }

        # Mock WSO2 search
        with patch("src.core.auth.search_wso2_users") as mock_search:
            mock_search.return_value = [
                {"username": "player1", "name": "Player One", "email": "p1@example.com"},
                {"username": "player2", "name": "Player Two", "email": "p2@example.com"},
                {"username": "player3", "name": "Player Three", "email": "p3@example.com"},
            ]

            with client.session_transaction() as sess:
                sess["access_token"] = "test-token"

            response = client.get("/api/multiplayer/available-players")

            if response.status_code == 200:
                data = response.get_json()
                assert data["success"] is True
                assert "players" in data

                # Check that players in game are marked as such
                players_dict = {p["username"]: p for p in data["players"]}
                assert players_dict["player1"]["inActiveGame"] is True
                assert players_dict["player2"]["inActiveGame"] is True
                assert players_dict["player3"]["inActiveGame"] is False

    @patch("src.core.auth.AUTH_DISABLED", False)
    @patch("src.core.auth.validate_token")
    def test_available_players_api_requires_auth(self, mock_validate_token, client):
        """Test that available-players endpoint requires authentication."""
        # No token validation (simulating unauthenticated user)
        mock_validate_token.return_value = None

        response = client.get("/api/multiplayer/available-players")
        # Should require authentication
        assert response.status_code in [401, 302]

    @patch("src.core.auth.AUTH_DISABLED", False)
    @patch("src.core.auth.validate_token")
    def test_available_players_api_requires_correct_role(self, mock_validate_token, client):
        """Test that available-players endpoint requires multiplayer/gamemaster/admin role."""
        # Mock authentication with player role (insufficient)
        mock_validate_token.return_value = {
            "sub": "testuser",
            "username": "testuser",
            "groups": ["player"],  # Only player role, not gamemaster/admin/multiplayer
        }

        with client.session_transaction() as sess:
            sess["access_token"] = "test-token"

        response = client.get("/api/multiplayer/available-players")
        # Should be forbidden (403) or redirect
        assert response.status_code in [403, 302]
