"""Unit tests for single-player game endpoint."""

import json
from unittest.mock import patch

import pytest
from dartserver_core.database_service import DatabaseService


@pytest.fixture
def db_service():
    """Create in-memory database service for testing."""
    db = DatabaseService("sqlite:///:memory:")
    db.initialize_database()

    # Create test player
    player = db.get_or_create_player("Test Player", username="testuser")

    return db, player


@pytest.fixture
def mock_auth_player():
    """Mock authentication decorators with player role."""
    with patch("dartserver_core.auth.validate_token") as mock_validate:
        mock_validate.return_value = {
            "sub": "test-user",
            "username": "testuser",
            "preferred_username": "testuser",
            "name": "Test Player",
            "groups": ["player"],
            "roles": ["player"],
        }
        yield mock_validate


@pytest.fixture
def mock_auth_admin():
    """Mock authentication decorators with admin role."""
    with patch("dartserver_core.auth.validate_token") as mock_validate:
        mock_validate.return_value = {
            "sub": "test-user",
            "username": "testuser",
            "preferred_username": "testuser",
            "name": "Test Player",
            "groups": ["admin"],
            "roles": ["admin"],
        }
        yield mock_validate


@pytest.fixture
def mock_auth_gamemaster():
    """Mock authentication decorators with gamemaster role."""
    with patch("dartserver_core.auth.validate_token") as mock_validate:
        mock_validate.return_value = {
            "sub": "test-user",
            "username": "testuser",
            "preferred_username": "testuser",
            "name": "Test Player",
            "groups": ["gamemaster"],
            "roles": ["gamemaster"],
        }
        yield mock_validate


@pytest.fixture
def app_with_player(mock_auth_player, db_service):
    """Create Flask app for testing with player role."""
    db, player = db_service
    with (
        patch("src.app.app.start_rabbitmq_consumer"),
        patch("dartserver_app.game_manager.DatabaseService") as mock_db_class,
    ):
        mock_db_class.return_value = db
        flask_app.config["TESTING"] = True
        game_manager.db_service = db
        yield flask_app, player


@pytest.fixture
def app_with_admin(mock_auth_admin, db_service):
    """Create Flask app for testing with admin role."""
    db, player = db_service
    with (
        patch("src.app.app.start_rabbitmq_consumer"),
        patch("dartserver_app.game_manager.DatabaseService") as mock_db_class,
    ):
        mock_db_class.return_value = db
        flask_app.config["TESTING"] = True
        game_manager.db_service = db
        yield flask_app, player


@pytest.fixture
def app_with_gamemaster(mock_auth_gamemaster, db_service):
    """Create Flask app for testing with gamemaster role."""
    db, player = db_service
    with (
        patch("src.app.app.start_rabbitmq_consumer"),
        patch("dartserver_app.game_manager.DatabaseService") as mock_db_class,
    ):
        mock_db_class.return_value = db
        flask_app.config["TESTING"] = True
        game_manager.db_service = db
        yield flask_app, player


@pytest.fixture
def client_player(app_with_player, db_service):
    """Create test client with player role."""
    app, player = app_with_player
    db, _ = db_service
    game_manager.db_service = db

    client = app.test_client()
    with client.session_transaction() as sess:
        sess["access_token"] = "test-token"
        sess["player_id"] = player.id
        sess["user_info"] = {
            "username": "testuser",
            "preferred_username": "testuser",
            "name": "Test Player",
            "sub": "test-user",
        }
    return client


@pytest.fixture
def client_admin(app_with_admin, db_service):
    """Create test client with admin role."""
    app, player = app_with_admin
    db, _ = db_service
    game_manager.db_service = db

    client = app.test_client()
    with client.session_transaction() as sess:
        sess["access_token"] = "test-token"
        sess["player_id"] = player.id
        sess["user_info"] = {
            "username": "testuser",
            "preferred_username": "testuser",
            "name": "Test Player",
            "sub": "test-user",
        }
    return client


@pytest.fixture
def client_gamemaster(app_with_gamemaster, db_service):
    """Create test client with gamemaster role."""
    app, player = app_with_gamemaster
    db, _ = db_service
    game_manager.db_service = db

    client = app.test_client()
    with client.session_transaction() as sess:
        sess["access_token"] = "test-token"
        sess["player_id"] = player.id
        sess["user_info"] = {
            "username": "testuser",
            "preferred_username": "testuser",
            "name": "Test Player",
            "sub": "test-user",
        }
    return client


class TestStartSinglePlayerGame:
    """Test the /api/mobile/game/start-single-player endpoint."""

    def test_start_single_player_game_default_301(self, client_player):
        """Test starting a single-player 301 game with defaults."""
        response = client_player.post(
            "/api/mobile/game/start-single-player",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "301" in data["message"]
        assert "game" in data
        assert data["game"]["game_type"] == "301"
        assert data["game"]["is_started"] is True
        assert len(data["game"]["players"]) == 1

    def test_start_single_player_game_501(self, client_player):
        """Test starting a single-player 501 game."""
        response = client_player.post(
            "/api/mobile/game/start-single-player",
            data=json.dumps({"game_type": "501"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "501" in data["message"]
        assert data["game"]["game_type"] == "501"

    def test_start_single_player_game_cricket(self, client_player):
        """Test starting a single-player cricket game."""
        response = client_player.post(
            "/api/mobile/game/start-single-player",
            data=json.dumps({"game_type": "cricket"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "cricket" in data["message"]
        assert data["game"]["game_type"] == "cricket"

    def test_start_single_player_game_round_the_clock(self, client_player):
        """Test starting a single-player round the clock game."""
        response = client_player.post(
            "/api/mobile/game/start-single-player",
            data=json.dumps({"game_type": "round_the_clock"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "round_the_clock" in data["message"]
        assert data["game"]["game_type"] == "round_the_clock"

    def test_start_single_player_game_with_double_out(self, client_player):
        """Test starting a single-player game with double out enabled."""
        response = client_player.post(
            "/api/mobile/game/start-single-player",
            data=json.dumps({"game_type": "301", "double_out": True}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True

    def test_start_single_player_game_with_reset_on_miss(self, client_player):
        """Test starting round the clock with reset on miss (hard mode)."""
        response = client_player.post(
            "/api/mobile/game/start-single-player",
            data=json.dumps({"game_type": "round_the_clock", "reset_on_miss": True}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True

    def test_training_mode_denied_for_player_role(self, client_player):
        """Test that training modes are denied for player role."""
        response = client_player.post(
            "/api/mobile/game/start-single-player",
            data=json.dumps({"game_type": "bull_practice"}),
            content_type="application/json",
        )
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data["success"] is False
        assert "requires gamemaster or admin role" in data["error"]

    def test_training_mode_allowed_for_admin(self, client_admin):
        """Test that training modes are allowed for admin role."""
        response = client_admin.post(
            "/api/mobile/game/start-single-player",
            data=json.dumps({"game_type": "bull_practice"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["game"]["game_type"] == "bull_practice"

    def test_training_mode_allowed_for_gamemaster(self, client_gamemaster):
        """Test that training modes are allowed for gamemaster role."""
        response = client_gamemaster.post(
            "/api/mobile/game/start-single-player",
            data=json.dumps({"game_type": "bull_practice"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["game"]["game_type"] == "bull_practice"

    def test_start_game_without_player_id(self, app_with_player):
        """Test starting game without player ID in session."""
        app, _ = app_with_player
        client = app.test_client()
        with client.session_transaction() as sess:
            sess["access_token"] = "test-token"
            sess["user_info"] = {"username": "testuser"}
            # Deliberately not setting player_id

        response = client.post(
            "/api/mobile/game/start-single-player",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data["success"] is False
        assert "Player ID not available" in data["error"]

    def test_start_game_requires_authentication(self, db_service):
        """Test that the endpoint requires authentication."""
        db, _ = db_service
        with patch("src.app.app.start_rabbitmq_consumer"):
            flask_app.config["TESTING"] = True
            game_manager.db_service = db
            client = flask_app.test_client()

            # No session data at all
            response = client.post(
                "/api/mobile/game/start-single-player",
                data=json.dumps({}),
                content_type="application/json",
            )
            # Should redirect to login (302) when not authenticated
            assert response.status_code in [302, 401]
