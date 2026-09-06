"""Unit tests for routing board throws to the right (game, player) - issue #208."""

from unittest.mock import MagicMock, patch

import pytest

from src.app import app as app_module


@pytest.fixture
def board():
    return {"id": 7, "external_id": "cam-garage", "kind": "vision"}


@pytest.fixture
def locked_game(flask_app, board):
    """A started game whose current player owns board 7."""
    manager = flask_app.multi_game_manager
    manager.board_locks.clear()

    game = MagicMock()
    game.players = [{"name": "Alice", "db_id": 42}, {"name": "Bob", "db_id": 43}]
    game.current_player = 0

    with patch.object(manager, "get_game", return_value=game):
        manager.lock_board(board["id"], "game-1", 42)
        yield game

    manager.board_locks.clear()


class TestResolveBoard:
    """`_resolve_board` registers the board an incoming throw claims to be from."""

    def test_registers_board(self, flask_app):
        with patch.object(flask_app.game_manager, "db_service") as db_service:
            db_service.get_or_create_board.return_value = {"id": 7}
            result = app_module._resolve_board("cam-garage", kind="vision")

        assert result == {"id": 7}
        db_service.get_or_create_board.assert_called_once_with("cam-garage", kind="vision")

    @pytest.mark.parametrize("external_id", [None, "", "unknown"])
    def test_missing_identity_returns_none(self, external_id):
        assert app_module._resolve_board(external_id, kind="vision") is None


class TestRouteThrowToGame:
    """`_route_throw_to_game` only delivers throws it can attribute confidently."""

    def test_delivers_throw_on_the_owning_players_turn(self, locked_game, board):
        score_data = {"score": 20, "multiplier": "TRIPLE"}

        assert app_module._route_throw_to_game(board, score_data, kind="vision") is True
        locked_game.process_score.assert_called_once_with(score_data, board_id=7)

    def test_drops_throw_from_unlocked_board(self, flask_app, board):
        flask_app.multi_game_manager.board_locks.clear()

        assert app_module._route_throw_to_game(board, {}, kind="vision") is False

    def test_drops_throw_when_it_is_another_players_turn(self, locked_game, board):
        locked_game.current_player = 1  # Bob's turn, but the board is Alice's

        assert app_module._route_throw_to_game(board, {}, kind="vision") is False
        locked_game.process_score.assert_not_called()

    def test_drops_throw_when_game_has_no_players(self, locked_game, board):
        locked_game.players = []

        assert app_module._route_throw_to_game(board, {}, kind="vision") is False
        locked_game.process_score.assert_not_called()

    def test_drops_throw_and_frees_board_when_game_is_gone(self, flask_app, board):
        manager = flask_app.multi_game_manager
        manager.board_locks.clear()
        manager.lock_board(board["id"], "vanished-game", 42)

        with patch.object(manager, "get_game", return_value=None):
            assert app_module._route_throw_to_game(board, {}, kind="vision") is False

        assert manager.get_lock_for_board(board["id"]) is None


class TestVisionThrowHandler:
    """`on_vision_throw_received` prefers boardId over the OAuth client_id."""

    def test_uses_board_id_when_present(self, flask_app):
        with (
            patch.object(app_module, "_resolve_board", return_value={"id": 7}) as resolve,
            patch.object(app_module, "_route_throw_to_game") as route,
        ):
            app_module.on_vision_throw_received(
                {
                    "score": 20,
                    "multiplier": "TRIPLE",
                    "boardId": "cam-garage",
                    "client_id": "oauth-abc",
                },
            )

        resolve.assert_called_once_with("cam-garage", kind="vision")
        route.assert_called_once()

    def test_falls_back_to_client_id(self, flask_app):
        with (
            patch.object(app_module, "_resolve_board", return_value={"id": 7}) as resolve,
            patch.object(app_module, "_route_throw_to_game"),
        ):
            app_module.on_vision_throw_received(
                {"score": 20, "multiplier": "TRIPLE", "client_id": "oauth-abc"},
            )

        resolve.assert_called_once_with("oauth-abc", kind="vision")

    def test_unidentified_board_still_scores_on_the_active_game(self, flask_app):
        """Backwards compatibility: publishers without a board identity keep working."""
        with (
            patch.object(app_module, "_resolve_board", return_value=None),
            patch.object(flask_app.game_manager, "process_score") as process_score,
        ):
            app_module.on_vision_throw_received({"score": 20, "multiplier": "TRIPLE"})

        process_score.assert_called_once_with({"score": 20, "multiplier": "TRIPLE"})
