"""Unit tests for training mode functionality."""

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from src.core.database_models import GameType, TrainingScore, TrainingSession


class TestTrainingMode:
    """Test training mode functionality."""

    @pytest.fixture
    def mock_session_with_player(self):
        """Create a mock Flask session with player information."""
        return {"player_id": 1, "username": "testuser"}

    @pytest.fixture
    def mock_training_session(self):
        """Create a mock training session."""
        return TrainingSession(
            id=1,
            player_id=1,
            game_type_id=1,
            session_id=str(uuid.uuid4()),
            start_score=301,
            final_score=0,
            double_out_enabled=False,
            completed=True,
            started_at=datetime.now(tz=timezone.utc),
            finished_at=datetime.now(tz=timezone.utc),
        )

    def test_training_route_requires_login(self, app_client):
        """Test that /training route requires login."""
        response = app_client.get("/training", follow_redirects=False)
        # Should redirect to login
        assert response.status_code in [302, 401]

    def test_training_dashboard_route_requires_login(self, app_client):
        """Test that /training/dashboard route requires login."""
        response = app_client.get("/training/dashboard", follow_redirects=False)
        # Should redirect to login
        assert response.status_code in [302, 401]

    @patch("src.app.app.session")
    @patch("src.app.app.game_manager")
    def test_start_training_success(self, mock_game_manager, mock_session, app_client):
        """Test successful training session start."""
        # Setup mocks
        mock_session.get.side_effect = lambda key, default=None: {
            "player_id": 1,
            "username": "testuser",
        }.get(key, default)

        mock_db_session = MagicMock()
        mock_game_type = GameType(id=1, name="301", description="301 game")
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_game_type
        )
        mock_game_manager.db_service.db_manager.get_session.return_value = mock_db_session

        # Make request
        with app_client.application.test_request_context():
            with patch("src.app.app.request") as mock_request:
                mock_request.json = {"game_type": "301", "double_out": False}

                from src.app.app import start_training

                # Mock login_required decorator
                with patch("src.app.app.login_required", lambda f: f):
                    response = start_training()

                # Check response
                assert response is not None

    @patch("src.app.app.session")
    @patch("src.app.app.game_manager")
    def test_start_training_no_player_id(self, mock_game_manager, mock_session, app_client):
        """Test training session start without player ID."""
        # Setup mocks - no player_id
        mock_session.get.return_value = None

        # Make request
        with app_client.application.test_request_context():
            with patch("src.app.app.request") as mock_request:
                mock_request.json = {"game_type": "301", "double_out": False}

                from src.app.app import start_training

                # Mock login_required decorator
                with patch("src.app.app.login_required", lambda f: f):
                    response = start_training()

                # Should return error
                json_response = response[0].get_json()
                assert json_response["success"] is False
                assert "Player ID not available" in json_response["error"]

    @patch("src.app.app.session")
    @patch("src.app.app.game_manager")
    def test_end_training_success(self, mock_game_manager, mock_session, app_client):
        """Test successful training session end."""
        # Setup mocks
        mock_session.get.side_effect = lambda key, default=None: {
            "training_session_id": 1,
        }.get(key, default)
        mock_session.pop = MagicMock()

        mock_db_session = MagicMock()
        mock_training_session = MagicMock()
        mock_training_session.completed = False
        mock_db_session.query.return_value.filter.return_value.first.return_value = (
            mock_training_session
        )
        mock_game_manager.db_service.db_manager.get_session.return_value = mock_db_session
        mock_game_manager.game = MagicMock()
        mock_game_manager.game.get_score.return_value = 100

        # Make request
        with app_client.application.test_request_context():
            from src.app.app import end_training

            # Mock login_required decorator
            with patch("src.app.app.login_required", lambda f: f):
                response = end_training()

            # Check response
            json_response = response.get_json()
            assert json_response["success"] is True

    @patch("src.app.app.session")
    def test_end_training_no_active_session(self, mock_session, app_client):
        """Test ending training with no active session."""
        # Setup mocks - no training_session_id
        mock_session.get.return_value = None

        # Make request
        with app_client.application.test_request_context():
            from src.app.app import end_training

            # Mock login_required decorator
            with patch("src.app.app.login_required", lambda f: f):
                response = end_training()

            # Should return error
            json_response = response[0].get_json()
            assert json_response["success"] is False
            assert "No active training session" in json_response["error"]

    @patch("src.app.app.session")
    @patch("src.app.app.game_manager")
    def test_get_training_history(self, mock_game_manager, mock_session, app_client):
        """Test getting training history."""
        # Setup mocks
        mock_session.get.side_effect = lambda key, default=None: {
            "player_id": 1,
        }.get(key, default)

        mock_db_session = MagicMock()
        mock_training_sessions = []
        mock_game_type = MagicMock()
        mock_game_type.name = "301"

        for i in range(3):
            ts = MagicMock()
            ts.id = i + 1
            ts.session_id = str(uuid.uuid4())
            ts.game_type = mock_game_type
            ts.start_score = 301
            ts.final_score = 0
            ts.double_out_enabled = False
            ts.completed = True
            ts.started_at = datetime.now(tz=timezone.utc)
            ts.finished_at = datetime.now(tz=timezone.utc)
            ts.training_scores = []
            mock_training_sessions.append(ts)

        query_chain = mock_db_session.query.return_value
        query_chain.join.return_value.filter.return_value.order_by.return_value.all.return_value = (
            mock_training_sessions
        )
        mock_game_manager.db_service.db_manager.get_session.return_value = (
            mock_db_session
        )

        # Make request
        with app_client.application.test_request_context():
            from src.app.app import get_training_history

            # Mock login_required decorator
            with patch("src.app.app.login_required", lambda f: f):
                response = get_training_history()

            # Check response
            json_response = response.get_json()
            assert json_response["success"] is True
            assert len(json_response["sessions"]) == 3

    @patch("src.app.app.session")
    @patch("src.app.app.game_manager")
    def test_get_training_statistics(self, mock_game_manager, mock_session, app_client):
        """Test getting training statistics."""
        # Setup mocks
        mock_session.get.side_effect = lambda key, default=None: {
            "player_id": 1,
        }.get(key, default)

        mock_db_session = MagicMock()
        # Mock scalar returns for statistics queries
        query_chain = mock_db_session.query.return_value
        query_chain.filter.return_value.scalar.return_value = 5
        query_chain.join.return_value.filter.return_value.scalar.return_value = 25.5
        mock_game_manager.db_service.db_manager.get_session.return_value = (
            mock_db_session
        )

        # Make request
        with app_client.application.test_request_context():
            from src.app.app import get_training_statistics

            # Mock login_required decorator
            with patch("src.app.app.login_required", lambda f: f):
                response = get_training_statistics()

            # Check response
            json_response = response.get_json()
            assert json_response["success"] is True
            assert "statistics" in json_response
            assert "total_sessions" in json_response["statistics"]


class TestTrainingDatabaseModels:
    """Test training database models."""

    def test_training_session_creation(self):
        """Test creating a TrainingSession model."""
        session = TrainingSession(
            player_id=1,
            game_type_id=1,
            session_id=str(uuid.uuid4()),
            start_score=301,
            double_out_enabled=False,
            completed=False,
        )
        assert session.player_id == 1
        assert session.game_type_id == 1
        assert session.start_score == 301
        assert session.completed is False

    def test_training_score_creation(self):
        """Test creating a TrainingScore model."""
        score = TrainingScore(
            training_session_id=1,
            player_id=1,
            throw_sequence=1,
            turn_number=1,
            throw_in_turn=1,
            base_score=20,
            multiplier="TRIPLE",
            multiplier_value=3,
            actual_score=60,
            score_before=301,
            score_after=241,
            dartboard_sends_actual_score=False,
            is_bust=False,
            is_finish=False,
        )
        assert score.training_session_id == 1
        assert score.base_score == 20
        assert score.multiplier == "TRIPLE"
        assert score.actual_score == 60


class TestGameManagerTrainingMode:
    """Test GameManager training mode functionality."""

    @pytest.fixture
    def mock_game_manager(self, mock_socketio):
        """Create a mock game manager."""
        from src.app.game_manager import GameManager

        with patch("src.app.game_manager.DatabaseService"):
            return GameManager(mock_socketio)

    def test_training_mode_flags(self, mock_game_manager):
        """Test that training mode flags are initialized."""
        assert hasattr(mock_game_manager, "is_training_mode")
        assert hasattr(mock_game_manager, "training_session_id")
        assert mock_game_manager.is_training_mode is False
        assert mock_game_manager.training_session_id is None

    def test_training_mode_activation(self, mock_game_manager):
        """Test activating training mode."""
        mock_game_manager.is_training_mode = True
        mock_game_manager.training_session_id = 123

        assert mock_game_manager.is_training_mode is True
        assert mock_game_manager.training_session_id == 123

    @patch("src.app.game_manager.func")
    def test_record_throw_training_mode(self, mock_func, mock_game_manager):
        """Test recording throws in training mode."""
        # Setup
        mock_game_manager.is_training_mode = True
        mock_game_manager.training_session_id = 1
        mock_game_manager.players = [{"db_id": 1, "name": "Test Player"}]
        mock_game_manager.current_player = 0
        mock_game_manager.current_throw = 1
        mock_game_manager.turn_number = {0: 1}

        mock_db_session = MagicMock()
        mock_db_session.query.return_value.filter.return_value.scalar.return_value = 0
        mock_game_manager.db_service.db_manager.get_session.return_value = mock_db_session

        # Call _record_throw_in_db
        with patch("src.app.game_manager.app"):
            mock_game_manager._record_throw_in_db(
                base_score=20,
                multiplier="TRIPLE",
                multiplier_value=3,
                actual_score=60,
                score_before=301,
                score_after=241,
                is_bust=False,
                is_finish=False,
            )

        # Verify training score was added
        assert mock_db_session.add.called
        assert mock_db_session.commit.called
        assert mock_db_session.close.called
