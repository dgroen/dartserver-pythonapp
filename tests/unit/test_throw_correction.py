"""Unit tests for SCD2 throw correction (issue #209).

Covers the `Score` versioning in `DatabaseService`, the guards in
`GameManager.correct_last_throw`, and the `/api/game/throw/correct` endpoint.
"""

import json
from typing import ClassVar
from unittest.mock import Mock, patch

import pytest
from dartserver_core.database_models import DatabaseManager, Player, Score
from dartserver_core.database_service import DatabaseService
from sqlalchemy import create_engine, inspect, text

from alembic import command
from alembic.config import Config as AlembicConfig
from src.app.multi_game_manager import MultiGameManager


@pytest.fixture
def db_service():
    service = DatabaseService("sqlite:///:memory:?check_same_thread=False")
    service.initialize_database()
    return service


def _create_player(db_service, name="Alice"):
    session = db_service.db_manager.get_session()
    try:
        player = Player(name=name, username=name.lower())
        session.add(player)
        session.commit()
        return player.id
    finally:
        session.close()


def _record(db_service, base_score=20, multiplier="TRIPLE", value=3, before=301, after=241):
    db_service.record_throw(
        player_id=0,
        base_score=base_score,
        multiplier=multiplier,
        multiplier_value=value,
        actual_score=base_score * value,
        score_before=before,
        score_after=after,
        turn_number=1,
        throw_in_turn=1,
        dartboard_sends_actual_score=False,
    )


@pytest.fixture
def game_with_throw(db_service):
    """A started game session with one recorded throw of T20."""
    player_id = _create_player(db_service)
    game_session_id = db_service.start_new_game("301", [{"db_id": player_id}], start_score=301)
    _record(db_service)
    return game_session_id


class TestScoreDefaults:
    """New throws are current version 1."""

    def test_recorded_throw_is_current_version_one(self, db_service, game_with_throw):
        session = db_service.db_manager.get_session()
        try:
            score = session.query(Score).one()
            assert score.is_current is True
            assert score.version == 1
            assert score.valid_from is not None
            assert score.valid_to is None
            assert score.replaces_score_id is None
        finally:
            session.close()

    def test_model_metadata_has_scd2_columns(self):
        columns = {c.name for c in Score.__table__.columns}
        assert columns >= {"is_current", "version", "valid_from", "valid_to", "replaces_score_id"}


class TestGetLastScore:
    """`get_last_score` finds the most recent current throw."""

    def test_returns_none_when_nothing_recorded(self, db_service):
        assert db_service.get_last_score() is None

    def test_returns_the_recorded_throw(self, db_service, game_with_throw):
        last = db_service.get_last_score()
        assert last["base_score"] == 20
        assert last["multiplier"] == "TRIPLE"
        assert last["version"] == 1

    def test_scoped_to_game_session(self, db_service, game_with_throw):
        assert db_service.get_last_score(game_with_throw) is not None
        assert db_service.get_last_score("no-such-game") is None

    def test_ignores_superseded_versions(self, db_service, game_with_throw):
        old_id = db_service.get_last_score()["id"]
        db_service.correct_score(old_id, 20, "DOUBLE", 2, 40, 261)

        last = db_service.get_last_score()
        assert last["id"] != old_id
        assert last["multiplier"] == "DOUBLE"


class TestCorrectScore:
    """The SCD2 invariant: invalidate the old row, insert a new current one."""

    def test_old_row_is_invalidated_not_deleted(self, db_service, game_with_throw):
        old_id = db_service.get_last_score()["id"]

        db_service.correct_score(old_id, 20, "DOUBLE", 2, 40, 261)

        session = db_service.db_manager.get_session()
        try:
            old = session.query(Score).filter_by(id=old_id).one()
            assert old.is_current is False
            assert old.valid_to is not None
            assert old.actual_score == 60  # untouched history
            assert session.query(Score).count() == 2
        finally:
            session.close()

    def test_new_row_is_the_next_version(self, db_service, game_with_throw):
        old = db_service.get_last_score()

        result = db_service.correct_score(old["id"], 20, "DOUBLE", 2, 40, 261)

        assert result["version"] == 2
        assert result["replaces_score_id"] == old["id"]

        session = db_service.db_manager.get_session()
        try:
            new = session.query(Score).filter_by(id=result["id"]).one()
            assert new.is_current is True
            assert new.valid_to is None
            assert new.actual_score == 40
            assert new.score_after == 261
        finally:
            session.close()

    def test_new_row_carries_the_throws_position_over(self, db_service, game_with_throw):
        old = db_service.get_last_score()

        result = db_service.correct_score(old["id"], 20, "DOUBLE", 2, 40, 261)

        session = db_service.db_manager.get_session()
        try:
            new = session.query(Score).filter_by(id=result["id"]).one()
            assert new.game_result_id == old["game_result_id"]
            assert new.player_id == old["player_id"]
            assert new.throw_sequence == old["throw_sequence"]
            assert new.turn_number == old["turn_number"]
            assert new.throw_in_turn == old["throw_in_turn"]
            assert new.score_before == old["score_before"]
        finally:
            session.close()

    def test_correcting_twice_keeps_versioning(self, db_service, game_with_throw):
        first = db_service.get_last_score()["id"]
        second = db_service.correct_score(first, 20, "DOUBLE", 2, 40, 261)
        third = db_service.correct_score(second["id"], 20, "SINGLE", 1, 20, 281)

        assert third["version"] == 3
        assert third["replaces_score_id"] == second["id"]

        session = db_service.db_manager.get_session()
        try:
            assert session.query(Score).filter_by(is_current=True).count() == 1
            assert session.query(Score).count() == 3
        finally:
            session.close()

    def test_correcting_a_superseded_row_is_refused(self, db_service, game_with_throw):
        old_id = db_service.get_last_score()["id"]
        db_service.correct_score(old_id, 20, "DOUBLE", 2, 40, 261)

        assert db_service.correct_score(old_id, 20, "SINGLE", 1, 20, 281) is None

    def test_unknown_score_is_refused(self, db_service):
        assert db_service.correct_score(4242, 20, "SINGLE", 1, 20, 281) is None


class TestExistingReadsIgnoreSupersededRows:
    """Existing `Score` reads must not double-count corrected throws."""

    def test_replay_data_shows_only_the_current_version(self, db_service, game_with_throw):
        old_id = db_service.get_last_score()["id"]
        db_service.correct_score(old_id, 20, "DOUBLE", 2, 40, 261)

        replay = db_service.get_game_replay_data(game_with_throw)
        assert len(replay["throws"]) == 1
        assert replay["throws"][0]["actual_score"] == 40

    def test_statistics_count_only_the_current_version(self, db_service, game_with_throw):
        old_id = db_service.get_last_score()["id"]
        db_service.correct_score(old_id, 20, "DOUBLE", 2, 40, 261)

        session = db_service.db_manager.get_session()
        try:
            alice_id = session.query(Player).filter_by(name="Alice").one().id
        finally:
            session.close()

        stats = db_service.get_player_statistics(alice_id)
        # One turn, one current throw worth 40
        assert stats["average_score"] == 40

    def test_bust_undo_only_removes_current_rows(self, db_service, game_with_throw):
        old_id = db_service.get_last_score()["id"]
        corrected = db_service.correct_score(old_id, 20, "DOUBLE", 2, 40, 261)

        db_service.undo_throws_for_bust(0, 3)

        session = db_service.db_manager.get_session()
        try:
            remaining = {s.id for s in session.query(Score).all()}
            assert corrected["id"] not in remaining
            assert old_id in remaining  # invalidated history survives
        finally:
            session.close()


class TestCorrectLastThrow:
    """`GameManager.correct_last_throw` guards and recomputation."""

    @pytest.fixture
    def game(self, db_service):
        manager = MultiGameManager(Mock())
        game = manager.create_game("game-1")
        game.db_service = db_service

        player_id = _create_player(db_service)
        game.new_game("301", player_ids=[{"db_id": player_id, "name": "Alice"}])
        game.is_paused = False
        return game

    def _throw(self, game, score=20, multiplier="TRIPLE"):
        game.process_score({"score": score, "multiplier": multiplier})

    def test_corrects_the_last_throw(self, game, db_service):
        self._throw(game)
        assert game.game.get_player_score(0) == 241

        result = game.correct_last_throw(20, "DOUBLE")

        assert result["actual_score"] == 40
        assert result["version"] == 2
        assert game.game.get_player_score(0) == 261

    def test_correction_replaces_rather_than_appends(self, game, db_service):
        self._throw(game)
        game.correct_last_throw(20, "DOUBLE")

        session = db_service.db_manager.get_session()
        try:
            assert session.query(Score).filter_by(is_current=True).count() == 1
        finally:
            session.close()

    def test_only_the_last_throw_is_correctable(self, game):
        self._throw(game, 20, "TRIPLE")
        self._throw(game, 5, "SINGLE")

        # The correction targets the most recent throw (the 5), not the T20
        result = game.correct_last_throw(1, "SINGLE")
        assert result["actual_score"] == 1
        assert game.game.get_player_score(0) == 301 - 60 - 1

    def test_earlier_throws_in_the_turn_are_preserved(self, game, db_service):
        self._throw(game, 20, "TRIPLE")
        self._throw(game, 20, "TRIPLE")
        game.correct_last_throw(1, "SINGLE")

        session = db_service.db_manager.get_session()
        try:
            current = session.query(Score).filter_by(is_current=True).all()
            assert sorted(s.actual_score for s in current) == [1, 60]
        finally:
            session.close()

    def test_refuses_when_no_throw_recorded(self, game):
        with pytest.raises(ValueError, match=r"no longer correctable|No throw"):
            game.correct_last_throw(20, "SINGLE")

    def test_refuses_when_the_turn_has_moved_on(self, game):
        self._throw(game)
        game.next_player()

        with pytest.raises(ValueError, match="turn has already moved on"):
            game.correct_last_throw(20, "DOUBLE")

    def test_refuses_when_the_game_is_not_started(self, game):
        game.is_started = False
        with pytest.raises(ValueError, match="not active"):
            game.correct_last_throw(20, "SINGLE")

    def test_refuses_when_another_game_threw_since(self, game):
        self._throw(game)

        # The globally most recent throw belongs to some other game's results
        foreign_throw = {
            "id": 999,
            "game_result_id": 4242,
            "is_bust": False,
            "is_finish": False,
        }
        with (
            patch.object(game.db_service, "get_last_score", return_value=foreign_throw),
            pytest.raises(ValueError, match="Another throw has been recorded"),
        ):
            game.correct_last_throw(20, "DOUBLE")

    def test_refuses_a_correction_that_would_finish_the_leg(self, game):
        self._throw(game, 20, "TRIPLE")
        # Rewinding to 301 and applying a 301 leaves exactly 0, i.e. a finish
        with pytest.raises(ValueError, match="busts or finishes"):
            game.correct_last_throw(301, "SINGLE")

    def test_refuses_a_correction_that_would_bust(self, game):
        self._throw(game, 20, "TRIPLE")
        with pytest.raises(ValueError, match="busts or finishes"):
            game.correct_last_throw(302, "SINGLE")

    def test_game_state_is_unchanged_after_a_refused_correction(self, game):
        self._throw(game, 20, "TRIPLE")
        before = game.game.get_player_score(0)

        with pytest.raises(ValueError, match="busts or finishes"):
            game.correct_last_throw(301, "SINGLE")

        assert game.game.get_player_score(0) == before

    def test_invalid_multiplier_falls_back_to_single(self, game):
        self._throw(game, 20, "TRIPLE")
        result = game.correct_last_throw(20, "NONSENSE")
        assert result["multiplier"] == "SINGLE"

    def test_invalid_score_is_refused(self, game):
        self._throw(game, 20, "TRIPLE")
        with pytest.raises(ValueError, match="Invalid score"):
            game.correct_last_throw("not-a-number", "SINGLE")


class TestScd2Migration:
    """The versioning columns land on the `scores` table."""

    def test_create_tables_includes_scd2_columns(self):
        db_manager = DatabaseManager("sqlite:///:memory:")
        db_manager.create_tables()
        columns = {c["name"] for c in inspect(db_manager.engine).get_columns("scores")}
        assert columns >= {"is_current", "version", "valid_from", "valid_to", "replaces_score_id"}


class TestCorrectThrowEndpoint:
    """`POST /api/game/throw/correct`"""

    @pytest.fixture
    def client(self, flask_app, db_service):
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

    def _post(self, client, **payload):
        return client.post(
            "/api/game/throw/correct",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_requires_auth(self, flask_app):
        with flask_app.test_client() as unauthenticated:
            response = unauthenticated.post("/api/game/throw/correct", json={"score": 20})
        assert response.status_code in (302, 401, 403)

    def test_score_is_required(self, client):
        assert self._post(client, mode="replace").status_code == 400

    def test_unknown_mode_is_rejected(self, client):
        assert self._post(client, score=20, mode="sideways").status_code == 400

    def test_unknown_game_is_404(self, client):
        assert self._post(client, score=20, game_id="no-such-game").status_code == 404

    def test_mode_new_goes_through_the_plain_score_path(self, client, flask_app):
        with patch.object(flask_app.game_manager, "process_score") as process_score:
            response = self._post(client, score=20, multiplier="TRIPLE", mode="new")

        assert response.status_code == 200
        assert json.loads(response.data)["mode"] == "new"
        process_score.assert_called_once_with({"score": 20, "multiplier": "TRIPLE"})

    def test_mode_replace_calls_correct_last_throw(self, client, flask_app):
        with patch.object(
            flask_app.game_manager,
            "correct_last_throw",
            return_value={"version": 2},
        ) as correct:
            response = self._post(client, score=20, multiplier="DOUBLE", mode="replace")

        assert response.status_code == 200
        body = json.loads(response.data)
        assert body["mode"] == "replace"
        assert body["correction"]["version"] == 2
        correct.assert_called_once_with(20, "DOUBLE")

    def test_replace_defaults_when_mode_omitted(self, client, flask_app):
        with patch.object(
            flask_app.game_manager,
            "correct_last_throw",
            return_value={"version": 2},
        ) as correct:
            self._post(client, score=20, multiplier="DOUBLE")
        correct.assert_called_once()

    def test_uncorrectable_throw_is_409(self, client, flask_app):
        with patch.object(
            flask_app.game_manager,
            "correct_last_throw",
            side_effect=ValueError("the turn has already moved on"),
        ):
            response = self._post(client, score=20, mode="replace")

        assert response.status_code == 409
        assert "turn has already moved on" in json.loads(response.data)["message"]


class TestScd2MigrationRoundTrip:
    """The SCD2 Alembic revision applies and reverses cleanly on PostgreSQL."""

    SCD2_COLUMNS: ClassVar[set[str]] = {
        "is_current",
        "version",
        "valid_from",
        "valid_to",
        "replaces_score_id",
    }

    def test_migration_round_trip(self, throwaway_postgres_url, monkeypatch):
        # alembic/env.py takes the URL from DATABASE_URL, ignoring the config
        # value -- without this the migration would run against whatever
        # database this environment points at.
        monkeypatch.setenv("DATABASE_URL", throwaway_postgres_url)

        alembic_cfg = AlembicConfig("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", throwaway_postgres_url)

        command.upgrade(alembic_cfg, "d4e5f6a7b8c9")

        engine = create_engine(throwaway_postgres_url)
        columns = {c["name"] for c in inspect(engine).get_columns("scores")}
        assert columns >= self.SCD2_COLUMNS
        engine.dispose()

        command.downgrade(alembic_cfg, "c3d4e5f6a7b8")

        engine = create_engine(throwaway_postgres_url)
        columns = {c["name"] for c in inspect(engine).get_columns("scores")}
        assert not self.SCD2_COLUMNS & columns
        engine.dispose()

    def test_existing_rows_are_backfilled_as_current(self, throwaway_postgres_url, monkeypatch):
        """A throw recorded before the migration must stay visible afterwards."""
        monkeypatch.setenv("DATABASE_URL", throwaway_postgres_url)
        alembic_cfg = AlembicConfig("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", throwaway_postgres_url)

        command.upgrade(alembic_cfg, "c3d4e5f6a7b8")

        engine = create_engine(throwaway_postgres_url)
        with engine.begin() as conn:
            conn.execute(
                text(
                    "INSERT INTO player (id, name, username) VALUES (1, 'Alice', 'alice')",
                ),
            )
            conn.execute(
                text(
                    "INSERT INTO gametype (id, name) VALUES (1, '301')",
                ),
            )
            conn.execute(
                text(
                    "INSERT INTO gameresults "
                    "(id, game_type_id, player_id, player_order, game_session_id) "
                    "VALUES (1, 1, 1, 0, 'session-1')",
                ),
            )
            conn.execute(
                text(
                    "INSERT INTO scores (id, game_result_id, player_id, throw_sequence, "
                    "turn_number, throw_in_turn, base_score, multiplier, multiplier_value, "
                    "actual_score, score_before, score_after, dartboard_sends_actual_score, "
                    "thrown_at) VALUES (1, 1, 1, 1, 1, 1, 20, 'TRIPLE', 3, 60, 301, 241, "
                    "false, now())",
                ),
            )
        engine.dispose()

        command.upgrade(alembic_cfg, "d4e5f6a7b8c9")

        engine = create_engine(throwaway_postgres_url)
        with engine.connect() as conn:
            row = conn.execute(
                text("SELECT is_current, version, valid_from FROM scores WHERE id = 1"),
            ).one()
        engine.dispose()

        assert row.is_current is True
        assert row.version == 1
        assert row.valid_from is not None
