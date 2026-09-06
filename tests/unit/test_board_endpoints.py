"""Unit tests for the board picker/confirmation endpoints (issue #208)."""

import json
from unittest.mock import patch

import pytest
from dartserver_core.database_models import GameResult
from dartserver_core.database_service import DatabaseService


@pytest.fixture
def db_service():
    """In-memory database with a couple of players and two registered boards."""
    db = DatabaseService("sqlite:///:memory:?check_same_thread=False")
    db.initialize_database()
    db.get_or_create_player("Alice", username="alice")
    db.get_or_create_player("Bob", username="bob")
    return db


@pytest.fixture
def boards(db_service):
    return {
        "vision": db_service.get_or_create_board("cam-garage", kind="vision"),
        "electronic": db_service.get_or_create_board("oauth-client-abc", kind="electronic"),
    }


@pytest.fixture
def client(flask_app, db_service):
    """Authenticated test client with a clean board-lock table."""
    flask_app.multi_game_manager.board_locks.clear()
    with flask_app.test_client() as client:
        with client.session_transaction() as sess:
            sess["access_token"] = "test-token"
            sess["user_info"] = {"username": "alice", "sub": "test-user"}
            sess["player_id"] = 1

        flask_app.game_manager.db_service = db_service

        with patch("dartserver_core.auth.validate_token") as mock_validate:
            mock_validate.return_value = {
                "sub": "test-user",
                "groups": ["admin"],
                "roles": ["admin"],
            }
            yield client

    flask_app.multi_game_manager.board_locks.clear()


class TestListBoards:
    """`GET /api/boards`"""

    def test_requires_auth(self, flask_app):
        with flask_app.test_client() as unauthenticated:
            response = unauthenticated.get("/api/boards")
        assert response.status_code in (302, 401, 403)

    def test_lists_registered_boards(self, client, boards):
        response = client.get("/api/boards")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["status"] == "success"
        assert {b["external_id"] for b in data["boards"]} == {
            "cam-garage",
            "oauth-client-abc",
        }

    def test_empty_registry_is_not_an_error(self, client):
        response = client.get("/api/boards")
        assert response.status_code == 200
        assert json.loads(response.data)["boards"] == []

    def test_reports_boards_locked_by_others(self, client, flask_app, boards):
        flask_app.multi_game_manager.lock_board(boards["vision"]["id"], "default", 99)

        data = json.loads(client.get("/api/boards").data)
        vision = next(b for b in data["boards"] if b["external_id"] == "cam-garage")
        assert vision["in_use"] is True
        assert vision["in_use_by_me"] is False

    def test_reports_own_lock_separately(self, client, flask_app, boards):
        flask_app.multi_game_manager.lock_board(boards["vision"]["id"], "default", 1)

        data = json.loads(client.get("/api/boards").data)
        vision = next(b for b in data["boards"] if b["external_id"] == "cam-garage")
        assert vision["in_use_by_me"] is True

    def test_returns_last_board_for_prefill(self, client, db_service, boards):
        db_service.set_player_last_board(1, boards["vision"]["id"])

        data = json.loads(client.get("/api/boards").data)
        assert data["last_board_id"] == boards["vision"]["id"]


class TestConfirmBoard:
    """`POST /api/game/board-confirm`"""

    def _confirm(self, client, board_id, **extra):
        payload = {"board_id": board_id, **extra}
        return client.post(
            "/api/game/board-confirm",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_requires_auth(self, flask_app):
        with flask_app.test_client() as unauthenticated:
            response = unauthenticated.post("/api/game/board-confirm", json={"board_id": 1})
        assert response.status_code in (302, 401, 403)

    def test_board_id_is_required(self, client):
        response = client.post(
            "/api/game/board-confirm",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_unknown_board_is_404(self, client):
        assert self._confirm(client, 4242).status_code == 404

    def test_confirm_locks_the_board(self, client, flask_app, boards):
        response = self._confirm(client, boards["vision"]["id"])
        assert response.status_code == 200

        lock = flask_app.multi_game_manager.get_lock_for_board(boards["vision"]["id"])
        assert lock == (flask_app.multi_game_manager.get_active_game_id(), 1)

    def test_confirm_remembers_board_for_next_time(self, client, db_service, boards):
        self._confirm(client, boards["vision"]["id"])
        assert db_service.get_player_last_board_id(1) == boards["vision"]["id"]

    def test_confirm_stores_choice_in_session(self, client, boards):
        self._confirm(client, boards["vision"]["id"])

        with client.session_transaction() as sess:
            assert sess["board_confirmed"] is True
            assert sess["confirmed_board_id"] == boards["vision"]["id"]

    def test_confirming_same_board_twice_is_fine(self, client, boards):
        assert self._confirm(client, boards["vision"]["id"]).status_code == 200
        assert self._confirm(client, boards["vision"]["id"]).status_code == 200

    def test_board_held_by_another_player_is_409(self, client, flask_app, boards):
        flask_app.multi_game_manager.lock_board(boards["vision"]["id"], "default", 99)

        response = self._confirm(client, boards["vision"]["id"])
        assert response.status_code == 409
        assert "already in use" in json.loads(response.data)["message"]

    def test_unknown_game_is_404(self, client, boards):
        response = self._confirm(client, boards["vision"]["id"], game_id="no-such-game")
        assert response.status_code == 404

    def test_changing_board_before_start_releases_the_old_one(self, client, flask_app, boards):
        flask_app.multi_game_manager.get_game().is_started = False
        self._confirm(client, boards["vision"]["id"])
        assert self._confirm(client, boards["electronic"]["id"]).status_code == 200

        manager = flask_app.multi_game_manager
        assert manager.get_lock_for_board(boards["vision"]["id"]) is None
        assert manager.get_lock_for_board(boards["electronic"]["id"]) is not None

    def test_changing_board_during_an_active_game_is_refused(self, client, flask_app, boards):
        self._confirm(client, boards["vision"]["id"])

        game = flask_app.multi_game_manager.get_game()
        game.is_started = True
        try:
            response = self._confirm(client, boards["electronic"]["id"])
        finally:
            game.is_started = False

        assert response.status_code == 409
        assert "End that game" in json.loads(response.data)["message"]

    def test_confirm_records_board_on_the_players_game_result(
        self,
        client,
        flask_app,
        db_service,
        boards,
    ):
        game_session_id = db_service.start_new_game("301", [{"db_id": 1}], start_score=301)
        flask_app.multi_game_manager.get_game().db_service = db_service

        assert self._confirm(client, boards["vision"]["id"]).status_code == 200

        session = db_service.db_manager.get_session()
        try:
            result = session.query(GameResult).filter_by(game_session_id=game_session_id).first()
            assert result.board_id == boards["vision"]["id"]
        finally:
            session.close()
