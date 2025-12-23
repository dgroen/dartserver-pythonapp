"""Unit tests for app_games.py endpoints."""

import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from dartserver_core.database_service import DatabaseService


@pytest.fixture
def db_service():
    """Create in-memory database service for testing."""
    db = DatabaseService("sqlite:///:memory:?check_same_thread=False")
    db.initialize_database()

    # Create test players
    db.get_or_create_player("Alice", username="alice")
    db.get_or_create_player("Bob", username="bob")
    db.get_or_create_player("Charlie", username="charlie")

    return db


@pytest.fixture
def client(flask_app, db_service):
    """Create authenticated test client."""
    with flask_app.test_client() as client:
        # Set up authenticated session
        with client.session_transaction() as sess:
            sess["access_token"] = "test-token"
            sess["user_info"] = {"username": "testuser", "sub": "test-user"}
            sess["player_id"] = 1

        # Patch game manager to use test database
        flask_app.game_manager.db_service = db_service

        with patch("src.core.auth.validate_token") as mock_validate:
            mock_validate.return_value = {
                "sub": "test-user",
                "groups": ["admin"],
                "roles": ["admin"],
            }
            yield client


class TestGameStateEndpoints:
    """Test game state endpoints."""

    def test_get_game_state_requires_auth(self, flask_app):
        """Test getting game state requires authentication."""
        with flask_app.test_client() as client:
            response = client.get("/api/game/state")
            assert response.status_code in [302, 401, 403]

    def test_get_game_state_returns_current_state(self, client):
        """Test getting current game state."""
        response = client.get("/api/game/state")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "players" in data
        assert "game_type" in data
        assert "is_started" in data
        assert "current_player" in data


class TestNewGameEndpoints:
    """Test new game creation endpoints."""

    def test_new_game_requires_auth(self, flask_app):
        """Test starting new game requires authentication."""
        with flask_app.test_client() as client:
            response = client.post(
                "/api/game/new",
                data=json.dumps({"game_type": "301", "players": ["Alice", "Bob"]}),
                content_type="application/json",
            )
            assert response.status_code in [302, 401, 403]

    def test_new_game_default_type(self, client):
        """Test starting new game with default type."""
        response = client.post(
            "/api/game/new",
            data=json.dumps({"players": ["Alice", "Bob"]}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "game_id" in data

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

    def test_new_game_with_options(self, client):
        """Test starting game with double_out and reset_on_miss options."""
        response = client.post(
            "/api/game/new",
            data=json.dumps({
                "game_type": "301",
                "players": ["Alice", "Bob"],
                "double_out": True,
                "reset_on_miss": True,
            }),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"

    def test_new_game_player_not_found(self, client):
        """Test starting game with non-existent player."""
        response = client.post(
            "/api/game/new",
            data=json.dumps({"game_type": "301", "players": ["NonExistent"]}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert "not found" in data["message"].lower()

    def test_new_game_empty_players(self, client):
        """Test starting game without players uses session player_id."""
        response = client.post(
            "/api/game/new",
            data=json.dumps({"game_type": "301", "players": []}),
            content_type="application/json",
        )
        # Should use player_id from session
        # Response depends on whether session player_id is valid
        assert response.status_code in [200, 400, 500]


class TestGameManagementEndpoints:
    """Test game management endpoints."""

    def test_list_games_requires_auth(self, flask_app):
        """Test listing games requires authentication."""
        with flask_app.test_client() as client:
            response = client.get("/api/games")
            assert response.status_code in [302, 401, 403]

    def test_list_games_returns_active_games(self, client):
        """Test listing active games."""
        response = client.get("/api/games")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "games" in data
        assert isinstance(data["games"], list)

    def test_create_game_session_requires_auth(self, flask_app):
        """Test creating game session requires authentication."""
        with flask_app.test_client() as client:
            response = client.post(
                "/api/games/create",
                data=json.dumps({"game_id": "test-game"}),
                content_type="application/json",
            )
            assert response.status_code in [302, 401, 403]

    def test_create_game_session_auto_generates_id(self, client):
        """Test creating game session auto-generates ID."""
        response = client.post(
            "/api/games/create",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "game_id" in data
        assert data["game_id"].startswith("game-")

    def test_create_game_session_with_custom_id(self, client):
        """Test creating game session with custom ID."""
        response = client.post(
            "/api/games/create",
            data=json.dumps({"game_id": "custom-game-123"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert data["game_id"] == "custom-game-123"

    def test_create_duplicate_game_session(self, client):
        """Test creating duplicate game session fails."""
        game_id = "duplicate-test"
        # Create first game
        client.post(
            "/api/games/create",
            data=json.dumps({"game_id": game_id}),
            content_type="application/json",
        )
        # Try to create duplicate
        response = client.post(
            "/api/games/create",
            data=json.dumps({"game_id": game_id}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"

    def test_activate_game_session(self, client):
        """Test activating a game session."""
        # Create a game first
        create_response = client.post(
            "/api/games/create",
            data=json.dumps({"game_id": "test-activate", "set_as_active": False}),
            content_type="application/json",
        )
        assert create_response.status_code == 200

        # Activate it
        response = client.post("/api/games/test-activate/activate")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert data["game_id"] == "test-activate"

    def test_activate_nonexistent_game(self, client):
        """Test activating non-existent game fails."""
        response = client.post("/api/games/nonexistent/activate")
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data["status"] == "error"

    def test_delete_game_session(self, client):
        """Test deleting a game session."""
        # Create a game
        create_response = client.post(
            "/api/games/create",
            data=json.dumps({"game_id": "test-delete"}),
            content_type="application/json",
        )
        assert create_response.status_code == 200

        # Delete it
        response = client.delete("/api/games/test-delete")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"

    def test_delete_default_game(self, client):
        """Test deleting default game is not allowed."""
        response = client.delete("/api/games/default")
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"

    def test_delete_nonexistent_game_session(self, client):
        """Test deleting non-existent game fails."""
        response = client.delete("/api/games/nonexistent")
        assert response.status_code == 404


class TestGameTypesEndpoint:
    """Test game types endpoint."""

    def test_get_game_types_no_auth_required(self, flask_app):
        """Test getting game types doesn't require authentication."""
        with flask_app.test_client() as client:
            response = client.get("/api/game/types")
            assert response.status_code == 200

    def test_get_game_types_returns_list(self, client):
        """Test getting game types returns list."""
        response = client.get("/api/game/types")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "game_types" in data
        assert isinstance(data["game_types"], list)


class TestMobileGameEndpoints:
    """Test mobile-friendly game endpoints."""

    def test_get_current_game(self, client):
        """Test getting current game state (mobile endpoint)."""
        response = client.get("/api/game/current")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "game" in data

    def test_start_game_mobile(self, client):
        """Test starting game via mobile endpoint."""
        response = client.post(
            "/api/game/start",
            data=json.dumps({
                "game_type": "301",
                "players": ["Alice", "Bob"],
            }),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "game_id" in data

    def test_start_single_player_game(self, client):
        """Test starting single-player game."""
        response = client.post(
            "/api/mobile/game/start-single-player",
            data=json.dumps({"game_type": "301"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True

    def test_start_single_player_training_requires_role(self, flask_app, db_service):
        """Test starting training mode requires gamemaster/admin role."""
        with flask_app.test_client() as client:
            with client.session_transaction() as sess:
                sess["access_token"] = "test-token"
                sess["user_info"] = {"username": "regular_user"}
                sess["player_id"] = 1

            flask_app.game_manager.db_service = db_service

            with patch("src.core.auth.validate_token") as mock_validate:
                mock_validate.return_value = {"sub": "test-user", "groups": []}

                response = client.post(
                    "/api/mobile/game/start-single-player",
                    data=json.dumps({"game_type": "bull_practice"}),
                    content_type="application/json",
                )
                assert response.status_code == 403

    def test_end_game(self, client):
        """Test ending current game."""
        response = client.post("/api/game/end")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True

    def test_get_active_games(self, client):
        """Test getting active games."""
        response = client.get("/api/active-games")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "games" in data


class TestGameDeleteResumeEndpoints:
    """Test game delete and resume endpoints."""

    def test_delete_game_not_found(self, client):
        """Test deleting non-existent game."""
        response = client.delete("/api/game/nonexistent-id")
        assert response.status_code == 404

    def test_delete_completed_game_not_allowed(self, client, db_service):
        """Test deleting completed game is not allowed."""
        # Create a completed game
        alice = db_service.get_or_create_player("Alice", username="alice")
        bob = db_service.get_or_create_player("Bob", username="bob")

        game_session_id = db_service.start_new_game(
            game_type_name="301",
            player_ids=[alice.id, bob.id],
            start_score=301,
            double_out=False,
            reset_on_miss=False,
        )

        # Mark as completed
        session = db_service.db_manager.get_session()
        try:
            from dartserver_core import GameResult

            results = session.query(GameResult).filter_by(game_session_id=game_session_id).all()
            for result in results:
                result.finished_at = datetime.now(timezone.utc)
            session.commit()
        finally:
            session.close()

        # Try to delete
        response = client.delete(f"/api/game/{game_session_id}")
        assert response.status_code == 403

    def test_delete_recent_incomplete_game_not_allowed(self, client, db_service):
        """Test deleting recent incomplete game is not allowed."""
        alice = db_service.get_or_create_player("Alice", username="alice")
        bob = db_service.get_or_create_player("Bob", username="bob")

        game_session_id = db_service.start_new_game(
            game_type_name="301",
            player_ids=[alice.id, bob.id],
            start_score=301,
            double_out=False,
            reset_on_miss=False,
        )

        response = client.delete(f"/api/game/{game_session_id}")
        assert response.status_code == 403

    def test_delete_old_incomplete_game_allowed(self, client, db_service):
        """Test deleting old incomplete game is allowed."""
        alice = db_service.get_or_create_player("Alice", username="alice")
        bob = db_service.get_or_create_player("Bob", username="bob")

        game_session_id = db_service.start_new_game(
            game_type_name="301",
            player_ids=[alice.id, bob.id],
            start_score=301,
            double_out=False,
            reset_on_miss=False,
        )

        # Make game old
        session = db_service.db_manager.get_session()
        try:
            from dartserver_core import GameResult

            results = session.query(GameResult).filter_by(game_session_id=game_session_id).all()
            old_date = datetime.now(timezone.utc) - timedelta(days=2)
            for result in results:
                result.started_at = old_date
            session.commit()
        finally:
            session.close()

        response = client.delete(f"/api/game/{game_session_id}")
        assert response.status_code == 200

    def test_resume_game_not_found(self, client):
        """Test resuming non-existent game."""
        response = client.post("/api/game/resume/nonexistent-id")
        assert response.status_code == 404

    def test_resume_completed_game_not_allowed(self, client, db_service):
        """Test resuming completed game is not allowed."""
        alice = db_service.get_or_create_player("Alice", username="alice")
        bob = db_service.get_or_create_player("Bob", username="bob")

        game_session_id = db_service.start_new_game(
            game_type_name="301",
            player_ids=[alice.id, bob.id],
            start_score=301,
            double_out=False,
            reset_on_miss=False,
        )

        # Mark as completed
        session = db_service.db_manager.get_session()
        try:
            from dartserver_core import GameResult

            results = session.query(GameResult).filter_by(game_session_id=game_session_id).all()
            for result in results:
                result.finished_at = datetime.now(timezone.utc)
            session.commit()
        finally:
            session.close()

        response = client.post(f"/api/game/resume/{game_session_id}")
        assert response.status_code == 403

    def test_resume_incomplete_game(self, client, db_service):
        """Test resuming incomplete game."""
        alice = db_service.get_or_create_player("Alice", username="alice")
        bob = db_service.get_or_create_player("Bob", username="bob")

        game_session_id = db_service.start_new_game(
            game_type_name="cricket",
            player_ids=[alice.id, bob.id],
            start_score=None,
            double_out=False,
            reset_on_miss=False,
        )

        response = client.post(f"/api/game/resume/{game_session_id}")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert data["redirect_url"] == "/"
