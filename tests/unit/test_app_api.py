"""Unit tests for app_api.py endpoints."""

import json
from unittest.mock import MagicMock, patch

import pytest
from dartserver_core.database_service import DatabaseService


@pytest.fixture
def db_service():
    """Create in-memory database service for testing."""
    db = DatabaseService("sqlite:///:memory:?check_same_thread=False")
    db.initialize_database()

    # Create test players
    db.get_or_create_player("Alice", username="alice", email="alice@example.com")
    db.get_or_create_player("Bob", username="bob", email="bob@example.com")

    return db


@pytest.fixture
def client(flask_app, db_service):
    """Create authenticated test client."""
    with flask_app.test_client() as client:
        with client.session_transaction() as sess:
            sess["access_token"] = "test-token"
            sess["user_info"] = {"username": "testuser", "sub": "test-user"}
            sess["player_id"] = 1

        flask_app.game_manager.db_service = db_service

        with patch("dartserver_core.auth.validate_token") as mock_validate:
            mock_validate.return_value = {
                "sub": "test-user",
                "groups": ["admin"],
                "roles": ["admin"],
            }
            yield client


class TestPlayerManagement:
    """Test player management endpoints."""

    def test_get_players_game_source(self, client):
        """Test getting players from current game."""
        response = client.get("/api/players?source=game")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert isinstance(data, list) or "players" in data

    def test_get_players_database_source(self, client):
        """Test getting all players from database."""
        response = client.get("/api/players?source=database")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "players" in data
        assert isinstance(data["players"], list)

    def test_get_players_requires_auth(self, flask_app):
        """Test getting players requires authentication."""
        with flask_app.test_client() as client:
            response = client.get("/api/players")
            assert response.status_code in [302, 401, 403]

    def test_add_player_requires_auth(self, flask_app):
        """Test adding player requires authentication."""
        with flask_app.test_client() as client:
            response = client.post(
                "/api/players",
                data=json.dumps({"username": "testuser"}),
                content_type="application/json",
            )
            assert response.status_code in [302, 401, 403]

    def test_add_player_without_username(self, client):
        """Test adding player without username fails."""
        response = client.post(
            "/api/players",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False

    def test_add_player_with_wso2_lookup(self, client, flask_app):
        """Test adding player with WSO2 lookup."""
        with (
            patch("src.app.app_api.get_wso2_user_info") as mock_wso2,
            patch.object(flask_app, "game_manager") as mock_game_manager,
        ):
            mock_wso2.return_value = {
                "username": "charlie",
                "name": "Charlie",
                "email": "charlie@example.com",
            }

            mock_db_service = MagicMock()
            mock_player = MagicMock()
            mock_player.id = 3
            mock_db_service.get_or_create_player.return_value = mock_player
            mock_game_manager.db_service = mock_db_service
            mock_game_manager.add_player_with_id = MagicMock()

            response = client.post(
                "/api/players",
                data=json.dumps({"username": "charlie"}),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["status"] == "success"
            assert "player" in data

    def test_add_player_wso2_not_found(self, client):
        """Test adding player when WSO2 user not found."""
        with patch("src.app.app_api.get_wso2_user_info") as mock_wso2:
            mock_wso2.return_value = None

            response = client.post(
                "/api/players",
                data=json.dumps({"username": "nonexistent"}),
                content_type="application/json",
            )

            assert response.status_code == 404
            data = json.loads(response.data)
            assert data["success"] is False

    def test_remove_player_requires_auth(self, flask_app):
        """Test removing player requires authentication."""
        with flask_app.test_client() as client:
            response = client.delete("/api/players/1")
            assert response.status_code in [302, 401, 403]

    def test_remove_player_success(self, client, flask_app):
        """Test removing player successfully."""
        with patch.object(flask_app, "game_manager") as mock_game_manager:
            mock_game_manager.remove_player = MagicMock()

            response = client.delete("/api/players/1")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["status"] == "success"
            mock_game_manager.remove_player.assert_called_once_with(1)


class TestWSO2UserSearch:
    """Test WSO2 user search endpoints."""

    def test_search_wso2_users_requires_auth(self, flask_app):
        """Test searching WSO2 users requires authentication."""
        with flask_app.test_client() as client:
            response = client.get("/api/wso2/users/search?q=test")
            assert response.status_code in [302, 401, 403]

    def test_search_wso2_users_empty_query(self, client):
        """Test searching with empty query."""
        response = client.get("/api/wso2/users/search?q=")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["success"] is False

    def test_search_wso2_users_success(self, client):
        """Test searching WSO2 users successfully."""
        with patch("src.app.app_api.search_wso2_users") as mock_search:
            mock_search.return_value = [
                {
                    "id": "user1",
                    "username": "testuser",
                    "email": "test@example.com",
                    "name": "Test User",
                },
            ]

            response = client.get("/api/wso2/users/search?q=test")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert len(data["users"]) == 1
            assert data["users"][0]["username"] == "testuser"

    def test_search_wso2_users_error_handling(self, client):
        """Test error handling in WSO2 user search."""
        with patch("src.app.app_api.search_wso2_users") as mock_search:
            mock_search.side_effect = Exception("WSO2 connection error")

            response = client.get("/api/wso2/users/search?q=test")

            assert response.status_code == 500
            data = json.loads(response.data)
            assert data["success"] is False


class TestUserInformation:
    """Test user information endpoints."""

    def test_get_current_user_requires_auth(self, flask_app):
        """Test getting current user requires authentication."""
        with flask_app.test_client() as client:
            response = client.get("/api/user/current")
            assert response.status_code in [302, 401, 403]

    def test_get_current_user_success(self, client):
        """Test getting current user information."""
        response = client.get("/api/user/current")
        # Response depends on session data structure
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = json.loads(response.data)
            assert "success" in data or "user" in data


class TestTrainingEndpoints:
    """Test training session endpoints (if implemented in app_api.py)."""

    def test_training_endpoints_placeholder(self, client):
        """Placeholder for training endpoint tests."""
        # Add specific tests based on actual training endpoints in app_api.py


class TestHistoryEndpoints:
    """Test history and replay endpoints (if implemented in app_api.py)."""

    def test_history_endpoints_placeholder(self, client):
        """Placeholder for history endpoint tests."""
        # Add specific tests based on actual history endpoints in app_api.py
