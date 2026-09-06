"""Unit tests for the board registry (issue #208).

Covers `DatabaseService` board persistence, the in-memory board locking in
`MultiGameManager`, and the Alembic migration round-trip.
"""

from unittest.mock import Mock

import pytest
from dartserver_core.database_models import Board, DatabaseManager, GameResult, Player, Score
from dartserver_core.database_service import DatabaseService
from sqlalchemy import create_engine, inspect

from alembic import command
from alembic.config import Config as AlembicConfig
from src.app.multi_game_manager import MultiGameManager


@pytest.fixture
def db_service():
    """A DatabaseService backed by a shared in-memory SQLite database."""
    service = DatabaseService("sqlite:///:memory:")
    service.initialize_database()
    return service


class TestGetOrCreateBoard:
    """`DatabaseService.get_or_create_board` registers boards on first sight."""

    def test_creates_board_on_first_sight(self, db_service):
        board = db_service.get_or_create_board("cam-garage", kind="vision")

        assert board is not None
        assert board["external_id"] == "cam-garage"
        assert board["kind"] == "vision"
        assert board["is_active"] is True

    def test_is_idempotent(self, db_service):
        first = db_service.get_or_create_board("cam-garage", kind="vision")
        second = db_service.get_or_create_board("cam-garage", kind="vision")

        assert first["id"] == second["id"]

        session = db_service.db_manager.get_session()
        try:
            assert session.query(Board).count() == 1
        finally:
            session.close()

    def test_same_external_id_different_kinds_are_distinct_boards(self, db_service):
        vision = db_service.get_or_create_board("board-1", kind="vision")
        electronic = db_service.get_or_create_board("board-1", kind="electronic")

        assert vision["id"] != electronic["id"]

    def test_updates_last_used_at(self, db_service):
        board = db_service.get_or_create_board("cam-garage", kind="vision")

        session = db_service.db_manager.get_session()
        try:
            stored = session.query(Board).filter_by(id=board["id"]).first()
            assert stored.last_used_at is not None
        finally:
            session.close()

    def test_missing_identity_returns_none(self, db_service):
        assert db_service.get_or_create_board(None, kind="vision") is None
        assert db_service.get_or_create_board("", kind="vision") is None


class TestBoardLookups:
    """Reading boards back out of the registry."""

    def test_get_board(self, db_service):
        created = db_service.get_or_create_board("cam-garage", kind="vision")
        assert db_service.get_board(created["id"])["external_id"] == "cam-garage"

    def test_get_board_missing_returns_none(self, db_service):
        assert db_service.get_board(4242) is None

    def test_list_active_boards(self, db_service):
        db_service.get_or_create_board("cam-garage", kind="vision")
        db_service.get_or_create_board("oauth-client-abc", kind="electronic")

        boards = db_service.list_active_boards()
        assert {b["external_id"] for b in boards} == {"cam-garage", "oauth-client-abc"}

    def test_list_active_boards_skips_inactive(self, db_service):
        created = db_service.get_or_create_board("cam-garage", kind="vision")

        session = db_service.db_manager.get_session()
        try:
            session.query(Board).filter_by(id=created["id"]).first().is_active = False
            session.commit()
        finally:
            session.close()

        assert db_service.list_active_boards() == []


class TestBoardAssociations:
    """Linking boards to players, game results and throws."""

    def _create_player(self, db_service, name="Alice"):
        session = db_service.db_manager.get_session()
        try:
            player = Player(name=name, username=name.lower())
            session.add(player)
            session.commit()
            return player.id
        finally:
            session.close()

    def test_player_last_board_round_trip(self, db_service):
        player_id = self._create_player(db_service)
        board = db_service.get_or_create_board("cam-garage", kind="vision")

        assert db_service.get_player_last_board_id(player_id) is None
        assert db_service.set_player_last_board(player_id, board["id"]) is True
        assert db_service.get_player_last_board_id(player_id) == board["id"]

    def test_set_game_result_board(self, db_service):
        player_id = self._create_player(db_service)
        board = db_service.get_or_create_board("cam-garage", kind="vision")

        game_session_id = db_service.start_new_game("301", [{"db_id": player_id}], start_score=301)

        assert db_service.set_game_result_board(game_session_id, player_id, board["id"]) is True

        session = db_service.db_manager.get_session()
        try:
            result = session.query(GameResult).filter_by(game_session_id=game_session_id).first()
            assert result.board_id == board["id"]
        finally:
            session.close()

    def test_set_game_result_board_unknown_game(self, db_service):
        player_id = self._create_player(db_service)
        board = db_service.get_or_create_board("cam-garage", kind="vision")

        assert db_service.set_game_result_board("no-such-game", player_id, board["id"]) is False

    def test_record_throw_persists_board_id(self, db_service):
        player_id = self._create_player(db_service)
        board = db_service.get_or_create_board("cam-garage", kind="vision")
        db_service.start_new_game("301", [{"db_id": player_id}], start_score=301)

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
            dartboard_sends_actual_score=False,
            board_id=board["id"],
        )

        session = db_service.db_manager.get_session()
        try:
            score = session.query(Score).first()
            assert score.board_id == board["id"]
        finally:
            session.close()

    def test_record_throw_without_board_stays_null(self, db_service):
        """Manual entry is unaffected by the board registry."""
        player_id = self._create_player(db_service)
        db_service.start_new_game("301", [{"db_id": player_id}], start_score=301)

        db_service.record_throw(
            player_id=0,
            base_score=20,
            multiplier="SINGLE",
            multiplier_value=1,
            actual_score=20,
            score_before=301,
            score_after=281,
            turn_number=1,
            throw_in_turn=1,
            dartboard_sends_actual_score=False,
        )

        session = db_service.db_manager.get_session()
        try:
            assert session.query(Score).first().board_id is None
        finally:
            session.close()


class TestBoardLocking:
    """Per-(game, player) board exclusivity in MultiGameManager."""

    @pytest.fixture
    def manager(self):
        return MultiGameManager(Mock())

    def test_starts_with_no_locks(self, manager):
        assert manager.board_locks == {}
        assert manager.get_lock_for_board(1) is None

    def test_lock_and_read_back(self, manager):
        manager.lock_board(1, "game-1", 42)
        assert manager.get_lock_for_board(1) == ("game-1", 42)

    def test_relock_same_player_is_allowed(self, manager):
        manager.lock_board(1, "game-1", 42)
        manager.lock_board(1, "game-1", 42)
        assert manager.get_lock_for_board(1) == ("game-1", 42)

    def test_conflicting_player_raises(self, manager):
        manager.lock_board(1, "game-1", 42)
        with pytest.raises(ValueError, match="already in use"):
            manager.lock_board(1, "game-1", 43)

    def test_conflicting_game_raises(self, manager):
        manager.lock_board(1, "game-1", 42)
        with pytest.raises(ValueError, match="already in use"):
            manager.lock_board(1, "game-2", 42)

    def test_one_game_can_hold_several_boards(self, manager):
        """Players in the same game may throw from different physical boards."""
        manager.lock_board(1, "game-1", 42)
        manager.lock_board(2, "game-1", 43)

        assert manager.get_lock_for_board(1) == ("game-1", 42)
        assert manager.get_lock_for_board(2) == ("game-1", 43)

    def test_unlock_for_player_frees_only_that_board(self, manager):
        manager.lock_board(1, "game-1", 42)
        manager.lock_board(2, "game-1", 43)

        assert manager.unlock_board_for_player("game-1", 42) == 1
        assert manager.get_lock_for_board(1) is None
        assert manager.get_lock_for_board(2) == ("game-1", 43)

    def test_unlock_whole_game_frees_every_board(self, manager):
        manager.lock_board(1, "game-1", 42)
        manager.lock_board(2, "game-1", 43)
        manager.lock_board(3, "game-2", 44)

        assert manager.unlock_board_for_player("game-1") == 2
        assert manager.board_locks == {3: ("game-2", 44)}

    def test_unlocked_board_can_be_relocked_by_someone_else(self, manager):
        manager.lock_board(1, "game-1", 42)
        manager.unlock_board_for_player("game-1", 42)

        manager.lock_board(1, "game-2", 43)
        assert manager.get_lock_for_board(1) == ("game-2", 43)

    def test_get_board_for_player(self, manager):
        manager.lock_board(7, "game-1", 42)

        assert manager.get_board_for_player("game-1", 42) == 7
        assert manager.get_board_for_player("game-1", 43) is None

    def test_deleting_a_game_releases_its_boards(self, manager):
        manager.create_game("game-1")
        manager.lock_board(1, "game-1", 42)

        manager.delete_game("game-1")

        assert manager.get_lock_for_board(1) is None

    def test_created_game_knows_how_to_release_its_locks(self, manager):
        game = manager.create_game("game-1")
        manager.lock_board(1, "game-1", 42)

        game._release_board_locks()

        assert manager.get_lock_for_board(1) is None


class TestBoardMigration:
    """The Alembic revision applies and reverses cleanly.

    Earlier revisions in the chain contain raw PostgreSQL, so this runs against
    a throwaway PostgreSQL database and skips when no server is reachable.
    """

    def test_migration_round_trip(self, throwaway_postgres_url, monkeypatch):
        # alembic/env.py takes the URL from DATABASE_URL, ignoring the config
        # value -- without this the migration would run against whatever
        # database this environment points at.
        monkeypatch.setenv("DATABASE_URL", throwaway_postgres_url)

        alembic_cfg = AlembicConfig("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", throwaway_postgres_url)

        command.upgrade(alembic_cfg, "c3d4e5f6a7b8")

        engine = create_engine(throwaway_postgres_url)
        inspector = inspect(engine)
        assert inspector.has_table("board")
        assert "board_id" in {c["name"] for c in inspector.get_columns("scores")}
        assert "board_id" in {c["name"] for c in inspector.get_columns("gameresults")}
        assert "last_board_id" in {c["name"] for c in inspector.get_columns("player")}
        engine.dispose()

        command.downgrade(alembic_cfg, "b2c3d4e5f6a7")

        engine = create_engine(throwaway_postgres_url)
        inspector = inspect(engine)
        assert not inspector.has_table("board")
        assert "board_id" not in {c["name"] for c in inspector.get_columns("scores")}
        assert "board_id" not in {c["name"] for c in inspector.get_columns("gameresults")}
        assert "last_board_id" not in {c["name"] for c in inspector.get_columns("player")}
        engine.dispose()


class TestDatabaseManagerBoard:
    """The ORM metadata creates the board table."""

    def test_create_tables_includes_board(self):
        db_manager = DatabaseManager("sqlite:///:memory:")
        db_manager.create_tables()
        assert "board" in inspect(db_manager.engine).get_table_names()
