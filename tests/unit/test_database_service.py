"""Unit tests for database_service module."""

from unittest.mock import patch

import pytest

from src.core.database_models import DatabaseManager
from src.core.database_service import DatabaseService


class TestDatabaseManager:
    """Test DatabaseManager class."""

    def test_initialization(self):
        """Test DatabaseManager initialization."""
        db_manager = DatabaseManager("sqlite:///:memory:")
        assert db_manager.engine is not None
        assert db_manager.Session is not None

    def test_get_session(self):
        """Test getting a database session."""
        db_manager = DatabaseManager("sqlite:///:memory:")
        session = db_manager.get_session()
        assert session is not None
        session.close()

    def test_create_tables(self):
        """Test creating database tables."""
        db_manager = DatabaseManager("sqlite:///:memory:")
        db_manager.create_tables()
        # Should not raise an error


class TestDatabaseService:
    """Test DatabaseService class."""

    @pytest.fixture
    def db_service(self):
        """Create a test database service."""
        service = DatabaseService("sqlite:///:memory:")
        service.initialize_database()
        return service

    def test_initialization_default_url(self):
        """Test initialization with default URL from environment."""
        with patch.dict("os.environ", {"DATABASE_URL": "sqlite:///:memory:"}):
            service = DatabaseService()
            assert service.db_manager is not None

    def test_initialization_custom_url(self):
        """Test initialization with custom URL."""
        service = DatabaseService("sqlite:///:memory:")
        assert service.db_manager is not None

    def test_initialize_database(self, db_service):
        """Test database initialization."""
        # Should not raise an error
        db_service.initialize_database()

    def test_start_new_game(self, db_service):
        """Test starting a new game."""
        session_id = db_service.start_new_game(
            game_type_name="301",
            player_names=["Player 1", "Player 2"],
            start_score=301,
            double_out=False,
        )
        assert session_id is not None
        assert db_service.current_game_session_id == session_id
        assert len(db_service.current_game_results) == 2

    def test_start_new_game_cricket(self, db_service):
        """Test starting a cricket game."""
        session_id = db_service.start_new_game(
            game_type_name="cricket",
            player_names=["Alice", "Bob"],
            start_score=None,
            double_out=False,
        )
        assert session_id is not None
        assert db_service.current_game_session_id == session_id

    def test_start_new_game_creates_game_type(self, db_service):
        """Test that starting a game creates game type if it doesn't exist."""
        session_id = db_service.start_new_game(
            game_type_name="custom_game",
            player_names=["Player 1"],
            start_score=500,
            double_out=True,
        )
        assert session_id is not None

    def test_record_throw(self, db_service):
        """Test recording a throw."""
        # Start a game first
        db_service.start_new_game(
            game_type_name="301",
            player_names=["Player 1", "Player 2"],
            start_score=301,
            double_out=False,
        )

        # Record a throw
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
        # Should not raise an error

    def test_record_throw_without_game(self, db_service):
        """Test recording a throw without starting a game."""
        # Should not raise an error (silently fails)
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
            dartboard_sends_actual_score=True,
            is_bust=False,
            is_finish=False,
        )

    def test_mark_winner(self, db_service):
        """Test marking a player as winner."""
        # Start a game
        db_service.start_new_game(
            game_type_name="301",
            player_names=["Player 1", "Player 2"],
            start_score=301,
            double_out=False,
        )

        # Mark winner
        db_service.mark_winner(player_id=0)
        # Should not raise an error

    def test_mark_winner_without_active_game(self, db_service):
        """Test marking winner when no game is active."""
        # Should not raise an error (silently fails)
        db_service.mark_winner(player_id=0)

    def test_update_player_score(self, db_service):
        """Test updating player score."""
        # Start a game
        db_service.start_new_game(
            game_type_name="301",
            player_names=["Player 1", "Player 2"],
            start_score=301,
            double_out=False,
        )

        # Update score
        db_service.update_player_score(player_id=0, final_score=241)
        # Should not raise an error

    def test_get_recent_games(self, db_service):
        """Test getting recent games."""
        # Start and finish a game
        db_service.start_new_game(
            game_type_name="301",
            player_names=["Player 1", "Player 2"],
            start_score=301,
            double_out=False,
        )
        db_service.mark_winner(player_id=0)

        # Get recent games
        games = db_service.get_recent_games(limit=10)
        assert isinstance(games, list)
        assert len(games) >= 1

    def test_get_recent_games_empty(self, db_service):
        """Test getting recent games when no games exist."""
        games = db_service.get_recent_games(limit=10)
        assert isinstance(games, list)
        assert len(games) == 0

    def test_get_game_replay_data(self, db_service):
        """Test getting game replay data."""
        # Start a game and record some throws
        session_id = db_service.start_new_game(
            game_type_name="301",
            player_names=["Player 1", "Player 2"],
            start_score=301,
            double_out=False,
        )

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

        # Get replay data
        replay_data = db_service.get_game_replay_data(session_id)
        assert replay_data is not None
        assert replay_data["game_session_id"] == session_id
        assert replay_data["game_type"] == "301"
        assert len(replay_data["players"]) == 2
        assert len(replay_data["throws"]) == 1

    def test_get_game_replay_data_nonexistent(self, db_service):
        """Test getting replay data for nonexistent game."""
        replay_data = db_service.get_game_replay_data("nonexistent-id")
        assert replay_data is None

    def test_full_game_workflow(self, db_service):
        """Test a complete game workflow."""
        # Start game
        session_id = db_service.start_new_game(
            game_type_name="301",
            player_names=["Alice", "Bob"],
            start_score=301,
            double_out=False,
        )

        # Record some throws for player 0
        for i in range(3):
            db_service.record_throw(
                player_id=0,
                base_score=20,
                multiplier="SINGLE",
                multiplier_value=1,
                actual_score=20,
                score_before=301 - (i * 20),
                score_after=301 - ((i + 1) * 20),
                turn_number=1,
                throw_in_turn=i + 1,
                dartboard_sends_actual_score=True,
                is_bust=False,
                is_finish=False,
            )

        # Record some throws for player 1
        for i in range(3):
            db_service.record_throw(
                player_id=1,
                base_score=19,
                multiplier="SINGLE",
                multiplier_value=1,
                actual_score=19,
                score_before=301 - (i * 19),
                score_after=301 - ((i + 1) * 19),
                turn_number=1,
                throw_in_turn=i + 1,
                dartboard_sends_actual_score=True,
                is_bust=False,
                is_finish=False,
            )

        # Mark winner
        db_service.mark_winner(player_id=0)

        # Verify game data
        replay_data = db_service.get_game_replay_data(session_id)
        assert replay_data is not None
        assert len(replay_data["throws"]) == 6
        assert replay_data["players"][0]["is_winner"] is True
        assert replay_data["players"][1]["is_winner"] is False

    def test_multiple_games(self, db_service):
        """Test handling multiple games."""
        # Start first game
        db_service.start_new_game(
            game_type_name="301",
            player_names=["Player 1", "Player 2"],
            start_score=301,
            double_out=False,
        )
        db_service.mark_winner(player_id=0)

        # Start second game
        db_service.start_new_game(
            game_type_name="501",
            player_names=["Player 3", "Player 4"],
            start_score=501,
            double_out=True,
        )
        db_service.mark_winner(player_id=1)

        # Verify both games exist
        games = db_service.get_recent_games(limit=10)
        assert len(games) >= 2

    def test_record_bust_throw(self, db_service):
        """Test recording a bust throw."""
        db_service.start_new_game(
            game_type_name="301",
            player_names=["Player 1"],
            start_score=301,
            double_out=False,
        )

        db_service.record_throw(
            player_id=0,
            base_score=20,
            multiplier="TRIPLE",
            multiplier_value=3,
            actual_score=60,
            score_before=50,
            score_after=50,  # Score doesn't change on bust
            turn_number=1,
            throw_in_turn=1,
            dartboard_sends_actual_score=True,
            is_bust=True,
            is_finish=False,
        )
        # Should not raise an error

    def test_record_finish_throw(self, db_service):
        """Test recording a finishing throw."""
        db_service.start_new_game(
            game_type_name="301",
            player_names=["Player 1"],
            start_score=301,
            double_out=False,
        )

        db_service.record_throw(
            player_id=0,
            base_score=20,
            multiplier="SINGLE",
            multiplier_value=1,
            actual_score=20,
            score_before=20,
            score_after=0,
            turn_number=1,
            throw_in_turn=1,
            dartboard_sends_actual_score=True,
            is_bust=False,
            is_finish=True,
        )
        # Should not raise an error

    def test_undo_throws_for_bust(self, db_service):
        """Test undoing throws for a bust."""
        db_service.start_new_game(
            game_type_name="301",
            player_names=["Player 1"],
            start_score=301,
            double_out=False,
        )

        # Record some throws
        for i in range(3):
            db_service.record_throw(
                player_id=0,
                base_score=20,
                multiplier="SINGLE",
                multiplier_value=1,
                actual_score=20,
                score_before=301 - (i * 20),
                score_after=301 - ((i + 1) * 20),
                turn_number=1,
                throw_in_turn=i + 1,
                dartboard_sends_actual_score=True,
                is_bust=False,
                is_finish=False,
            )

        # Undo 2 throws
        db_service.undo_throws_for_bust(player_id=0, throw_count=2)
        # Should not raise an error
