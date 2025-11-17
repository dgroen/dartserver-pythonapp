"""Integration tests for Flask application endpoints."""

import json
from unittest.mock import patch

import pytest

from src.app.app import app as flask_app
from src.app.app import game_manager
from src.core.database_service import DatabaseService


@pytest.fixture
def db_service():
    """Create in-memory database service for testing."""
    db = DatabaseService("sqlite:///:memory:")
    db.initialize_database()

    # Create test players
    db.get_or_create_player("Alice", username="alice")
    db.get_or_create_player("Bob", username="bob")
    db.get_or_create_player("Charlie", username="charlie")
    db.get_or_create_player("Diana", username="diana")

    return db


@pytest.fixture
def mock_auth():
    """Mock authentication decorators."""
    # Mock validate_token to return valid claims
    with patch("src.core.auth.validate_token") as mock_validate:
        mock_validate.return_value = {
            "sub": "test-user",
            "username": "testuser",
            "groups": ["admin"],  # Admin role has all permissions
            "roles": ["admin"],
        }
        yield mock_validate


@pytest.fixture
def app(mock_auth, db_service):
    """Create Flask app for testing."""
    with (
        patch("src.app.app.start_rabbitmq_consumer"),
        patch(
            "src.app.game_manager.DatabaseService",
        ) as mock_db_class,
    ):
        mock_db_class.return_value = db_service
        flask_app.config["TESTING"] = True
        game_manager.db_service = db_service
        yield flask_app


@pytest.fixture
def client(app, db_service):
    """Create test client."""
    # Make sure game_manager uses the test database
    game_manager.db_service = db_service

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
        """Test starting new game with defaults (using Alice and Bob from fixtures)."""
        response = client.post(
            "/api/game/new",
            data=json.dumps({"players": ["Alice", "Bob"]}),
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
        # Add player - must use username and mock WSO2
        with patch("src.core.auth.get_wso2_user_info") as mock_wso2:
            mock_wso2.return_value = {
                "username": "bob",
                "name": "Bob",
                "email": "bob@example.com",
            }
            response = client.post(
                "/api/players",
                data=json.dumps({"username": "bob"}),
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

    def test_delete_game_not_found(self, client):
        """Test deleting a non-existent game."""
        response = client.delete("/api/game/nonexistent-game-id")
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert "not found" in data["message"].lower()

    def test_delete_completed_game(self, client, db_service):
        """Test that completed games cannot be deleted."""
        # Create a completed game in the database
        from datetime import datetime, timezone

        # Get test players
        alice = db_service.get_or_create_player("Alice", username="alice")
        bob = db_service.get_or_create_player("Bob", username="bob")

        # Start a game
        game_session_id = db_service.start_new_game(
            game_type_name="301",
            player_ids=[alice.id, bob.id],
            start_score=301,
            double_out=False,
            reset_on_miss=False,
        )

        # Complete the game by setting finished_at
        session = db_service.db_manager.get_session()
        try:
            from src.core.database_models import GameResult

            results = session.query(GameResult).filter_by(game_session_id=game_session_id).all()
            for result in results:
                result.finished_at = datetime.now(timezone.utc)
            session.commit()
        finally:
            session.close()

        # Try to delete the completed game
        response = client.delete(f"/api/game/{game_session_id}")
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert "completed" in data["message"].lower()

    def test_delete_recent_incomplete_game(self, client, db_service):
        """Test that incomplete games less than 1 day old cannot be deleted."""
        # Get test players
        alice = db_service.get_or_create_player("Alice", username="alice")
        bob = db_service.get_or_create_player("Bob", username="bob")

        # Start an incomplete game (no finished_at)
        game_session_id = db_service.start_new_game(
            game_type_name="301",
            player_ids=[alice.id, bob.id],
            start_score=301,
            double_out=False,
            reset_on_miss=False,
        )

        # Try to delete the recent incomplete game
        response = client.delete(f"/api/game/{game_session_id}")
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert "1 day old" in data["message"].lower()

    def test_delete_old_incomplete_game(self, client, db_service):
        """Test that incomplete games older than 1 day can be deleted."""
        from datetime import datetime, timedelta, timezone

        # Get test players
        alice = db_service.get_or_create_player("Alice", username="alice")
        bob = db_service.get_or_create_player("Bob", username="bob")

        # Start an incomplete game
        game_session_id = db_service.start_new_game(
            game_type_name="301",
            player_ids=[alice.id, bob.id],
            start_score=301,
            double_out=False,
            reset_on_miss=False,
        )

        # Modify the game to be older than 1 day
        session = db_service.db_manager.get_session()
        try:
            from src.core.database_models import GameResult

            results = session.query(GameResult).filter_by(game_session_id=game_session_id).all()
            old_date = datetime.now(timezone.utc) - timedelta(days=2)
            for result in results:
                result.started_at = old_date
            session.commit()
        finally:
            session.close()

        # Delete the old incomplete game
        response = client.delete(f"/api/game/{game_session_id}")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"

        # Verify the game was deleted
        game_data = db_service.get_game_replay_data(game_session_id)
        assert game_data is None

    def test_resume_game_not_found(self, client):
        """Test resuming a non-existent game."""
        response = client.post("/api/game/resume/nonexistent-game-id")
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert "not found" in data["message"].lower()

    def test_resume_completed_game(self, client, db_service):
        """Test that completed games cannot be resumed."""
        from datetime import datetime, timezone

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
            from src.core.database_models import GameResult

            results = session.query(GameResult).filter_by(game_session_id=game_session_id).all()
            for result in results:
                result.finished_at = datetime.now(timezone.utc)
            session.commit()
        finally:
            session.close()

        # Try to resume
        response = client.post(f"/api/game/resume/{game_session_id}")
        assert response.status_code == 403
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert "completed" in data["message"].lower()

    def test_resume_incomplete_game(self, client, db_service):
        """Test resuming an incomplete game."""
        # Create an incomplete game
        alice = db_service.get_or_create_player("Alice", username="alice")
        bob = db_service.get_or_create_player("Bob", username="bob")

        game_session_id = db_service.start_new_game(
            game_type_name="cricket",
            player_ids=[alice.id, bob.id],
            start_score=None,
            double_out=False,
            reset_on_miss=False,
        )

        # Resume the game
        response = client.post(f"/api/game/resume/{game_session_id}")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "redirect_url" in data
        assert data["redirect_url"] == "/"

    def test_resume_game_with_throws_301(self, client, db_service):
        """Test resuming a 301 game restores scores correctly."""
        # Create players
        alice = db_service.get_or_create_player("Alice", username="alice")
        bob = db_service.get_or_create_player("Bob", username="bob")

        # Start a 301 game
        game_session_id = db_service.start_new_game(
            game_type_name="301",
            player_ids=[alice.id, bob.id],
            start_score=301,
            double_out=False,
            reset_on_miss=False,
        )

        # Record some throws for Alice (player 0)
        db_service.record_throw(
            player_id=0,
            base_score=20,
            multiplier="TRIPLE",
            multiplier_value=3,
            actual_score=60,
            score_before=301,
            score_after=241,
            turn_number=1,
            throw_in_turn=1,
            dartboard_sends_actual_score=True,
            is_bust=False,
            is_finish=False,
        )

        db_service.record_throw(
            player_id=0,
            base_score=19,
            multiplier="TRIPLE",
            multiplier_value=3,
            actual_score=57,
            score_before=241,
            score_after=184,
            turn_number=1,
            throw_in_turn=2,
            dartboard_sends_actual_score=True,
            is_bust=False,
            is_finish=False,
        )

        # Record throws for Bob (player 1)
        db_service.record_throw(
            player_id=1,
            base_score=20,
            multiplier="SINGLE",
            multiplier_value=1,
            actual_score=20,
            score_before=301,
            score_after=281,
            turn_number=1,
            throw_in_turn=1,
            dartboard_sends_actual_score=True,
            is_bust=False,
            is_finish=False,
        )

        # Resume the game
        response = client.post(f"/api/game/resume/{game_session_id}")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"

        # Get game state
        state = game_manager.get_game_state()

        # Verify game was resumed correctly
        assert state["is_started"] is True
        assert state["game_type"] == "301"
        assert len(state["players"]) == 2

        # Verify scores were restored (in game_data.players)
        game_players = state["game_data"]["players"]
        assert game_players[0]["score"] == 184  # Alice: 301 - 60 - 57 = 184
        assert game_players[1]["score"] == 281  # Bob: 301 - 20 = 281

        # Current player should be Bob (player 1) since Alice threw 2 darts
        assert state["current_player"] == 1
        assert state["current_throw"] == 2

    def test_resume_game_with_throws_cricket(self, client, db_service):
        """Test resuming a Cricket game restores targets correctly."""
        # Create players
        alice = db_service.get_or_create_player("Alice", username="alice")
        bob = db_service.get_or_create_player("Bob", username="bob")

        # Start a Cricket game
        game_session_id = db_service.start_new_game(
            game_type_name="cricket",
            player_ids=[alice.id, bob.id],
            start_score=None,
            double_out=False,
            reset_on_miss=False,
        )

        # Record throws for Alice opening 20 (triple = 3 hits)
        db_service.record_throw(
            player_id=0,
            base_score=20,
            multiplier="TRIPLE",
            multiplier_value=3,
            actual_score=60,
            score_before=0,
            score_after=0,
            turn_number=1,
            throw_in_turn=1,
            dartboard_sends_actual_score=True,
            is_bust=False,
            is_finish=False,
        )

        # Alice scores on 20 (already opened)
        db_service.record_throw(
            player_id=0,
            base_score=20,
            multiplier="SINGLE",
            multiplier_value=1,
            actual_score=20,
            score_before=0,
            score_after=20,
            turn_number=1,
            throw_in_turn=2,
            dartboard_sends_actual_score=True,
            is_bust=False,
            is_finish=False,
        )

        # Resume the game
        response = client.post(f"/api/game/resume/{game_session_id}")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"

        # Get game state
        state = game_manager.get_game_state()

        # Verify game was resumed correctly
        assert state["is_started"] is True
        assert state["game_type"] == "cricket"
        assert len(state["players"]) == 2

        # Verify Cricket state was restored (in game_data.players)
        game_players = state["game_data"]["players"]
        alice_data = game_players[0]
        assert alice_data["score"] == 20  # Scored 20 points
        assert alice_data["targets"][20]["hits"] == 3  # Maxed out at 3 hits (opened)
        assert alice_data["targets"][20]["status"] == 1  # Opened

        # Bob should not have any hits yet
        bob_data = game_players[1]
        assert bob_data["score"] == 0
        assert bob_data["targets"][20]["hits"] == 0

        # Current player should be Alice (player 0) since she threw 2 darts
        assert state["current_player"] == 0
        assert state["current_throw"] == 3
