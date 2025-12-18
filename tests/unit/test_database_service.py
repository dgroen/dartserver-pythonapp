"""Unit tests for database_service module."""

from unittest.mock import patch

import pytest
from dartserver_core.database_models import DatabaseManager, Player
from dartserver_core.database_service import DatabaseService


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

    @pytest.fixture()
    def db_service(self):
        """Create a test database service."""
        service = DatabaseService("sqlite:///:memory:")
        service.initialize_database()
        return service

    def _create_test_players(self, db_service, names):
        """Helper to create test player records in the database."""
        session = db_service.db_manager.get_session()
        player_ids = []
        for name in names:
            player = Player(
                name=name,
                username=name.replace(" ", "_").lower(),
                email=f"{name.replace(' ', '_').lower()}@test.local",
            )
            session.add(player)
            session.flush()
            player_ids.append(player.id)
        session.commit()
        session.close()
        return player_ids

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
        player_ids = self._create_test_players(db_service, ["Player 1", "Player 2"])
        session_id = db_service.start_new_game(
            game_type_name="301",
            player_ids=player_ids,
            start_score=301,
            double_out=False,
        )
        assert session_id is not None
        assert db_service.current_game_session_id == session_id
        assert len(db_service.current_game_results) == 2

    def test_start_new_game_cricket(self, db_service):
        """Test starting a cricket game."""
        player_ids = self._create_test_players(db_service, ["Alice", "Bob"])
        session_id = db_service.start_new_game(
            game_type_name="cricket",
            player_ids=player_ids,
            start_score=None,
            double_out=False,
        )
        assert session_id is not None
        assert db_service.current_game_session_id == session_id

    def test_start_new_game_creates_game_type(self, db_service):
        """Test that starting a game creates game type if it doesn't exist."""
        player_ids = self._create_test_players(db_service, ["Player 1"])
        session_id = db_service.start_new_game(
            game_type_name="custom_game",
            player_ids=player_ids,
            start_score=500,
            double_out=True,
        )
        assert session_id is not None

    def test_record_throw(self, db_service):
        """Test recording a throw."""
        # Start a game first
        db_service.start_new_game(
            game_type_name="301",
            player_ids=self._create_test_players(db_service, ["Player 1", "Player 2"]),
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
            player_ids=self._create_test_players(db_service, ["Player 1", "Player 2"]),
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
            player_ids=self._create_test_players(db_service, ["Player 1", "Player 2"]),
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
            player_ids=self._create_test_players(db_service, ["Player 1", "Player 2"]),
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

    def test_get_recent_games_with_username_filter(self, db_service):
        """Test getting recent games filtered by username."""
        # Create players with usernames
        session = db_service.db_manager.get_session()
        try:
            player1 = Player(name="Alice", username="alice")
            player2 = Player(name="Bob", username="bob")
            session.add(player1)
            session.add(player2)
            session.commit()

            player1_id = player1.id
            player2_id = player2.id
        finally:
            session.close()

        # Start a game with both players
        db_service.start_new_game(
            game_type_name="301",
            player_ids=[player1_id, player2_id],
            start_score=301,
            double_out=False,
        )

        # Start another game with only player1
        db_service.start_new_game(
            game_type_name="301",
            player_ids=[player1_id],
            start_score=301,
            double_out=False,
        )

        # Get all games (no filter)
        all_games = db_service.get_recent_games(limit=10)
        assert len(all_games) == 2

        # Get games for alice only
        alice_games = db_service.get_recent_games(limit=10, username="alice")
        assert len(alice_games) == 2  # Alice played in both games

        # Get games for bob only
        bob_games = db_service.get_recent_games(limit=10, username="bob")
        assert len(bob_games) == 1  # Bob only played in the first game

    def test_get_all_players_with_usernames(self, db_service):
        """Test getting all players with usernames."""
        # Create players
        session = db_service.db_manager.get_session()
        try:
            player1 = Player(name="Alice", username="alice", email="alice@example.com")
            player2 = Player(name="Bob", username="bob", email="bob@example.com")
            player3 = Player(name="Charlie")  # No username
            session.add(player1)
            session.add(player2)
            session.add(player3)
            session.commit()
        finally:
            session.close()

        # Get all players with usernames
        players = db_service.get_all_players_with_usernames()
        assert len(players) == 2  # Only Alice and Bob have usernames

        usernames = [p["username"] for p in players]
        assert "alice" in usernames
        assert "bob" in usernames

        # Verify structure
        for player in players:
            assert "id" in player
            assert "name" in player
            assert "username" in player
            assert "email" in player

    def test_get_game_replay_data(self, db_service):
        """Test getting game replay data."""
        # Start a game and record some throws
        session_id = db_service.start_new_game(
            game_type_name="301",
            player_ids=self._create_test_players(db_service, ["Player 1", "Player 2"]),
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
            player_ids=self._create_test_players(db_service, ["Alice", "Bob"]),
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
            player_ids=self._create_test_players(db_service, ["Player 1", "Player 2"]),
            start_score=301,
            double_out=False,
        )
        db_service.mark_winner(player_id=0)

        # Start second game
        db_service.start_new_game(
            game_type_name="501",
            player_ids=self._create_test_players(db_service, ["Player 3", "Player 4"]),
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
            player_ids=self._create_test_players(db_service, ["Player 1"]),
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
            player_ids=self._create_test_players(db_service, ["Player 1"]),
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
            player_ids=self._create_test_players(db_service, ["Player 1"]),
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

    def test_get_or_create_player_new_player(self, db_service):
        """Test creating a new player via get_or_create_player."""
        player = db_service.get_or_create_player(
            name="Test Player",
            username="testuser",
            email="test@example.com",
        )

        assert player is not None
        assert player.name == "Test Player"
        assert player.username == "testuser"
        assert player.email == "test@example.com"
        assert player.id is not None
        # Ensure the player object is accessible after session closure
        player_id = player.id
        assert player_id > 0

    def test_get_or_create_player_existing_by_username(self, db_service):
        """Test retrieving an existing player by username."""
        # Create a player first
        player1 = db_service.get_or_create_player(
            name="Test Player",
            username="testuser",
            email="test@example.com",
        )
        player1_id = player1.id

        # Get the same player using username
        player2 = db_service.get_or_create_player(
            name="Updated Name",
            username="testuser",
            email="newemail@example.com",
        )

        assert player2 is not None
        assert player2.id == player1_id
        assert player2.name == "Updated Name"  # Name should be updated
        assert player2.email == "newemail@example.com"  # Email should be updated

    def test_get_or_create_player_existing_by_email(self, db_service):
        """Test retrieving an existing player by email."""
        # Create a player first
        player1 = db_service.get_or_create_player(
            name="Test Player",
            username="testuser1",
            email="test@example.com",
        )
        player1_id = player1.id

        # Get the same player using email (different username)
        player2 = db_service.get_or_create_player(
            name="Updated Name",
            username="testuser2",
            email="test@example.com",
        )

        assert player2 is not None
        assert player2.id == player1_id
        assert player2.name == "Updated Name"
        assert player2.username == "testuser2"

    def test_get_or_create_player_no_username_no_email(self, db_service):
        """Test that creating a player without username is rejected (WSO2 requirement)."""
        # Players without a username cannot be created due to WSO2 authentication requirement
        player = db_service.get_or_create_player(name="Name Only")

        # Should return None since no username provided
        assert player is None

    def test_get_or_create_player_multiple_separate_players(self, db_service):
        """Test creating multiple separate players."""
        player1 = db_service.get_or_create_player(
            name="Player 1",
            username="user1",
            email="user1@example.com",
        )
        player2 = db_service.get_or_create_player(
            name="Player 2",
            username="user2",
            email="user2@example.com",
        )

        assert player1.id != player2.id
        assert player1.username == "user1"
        assert player2.username == "user2"
