"""Integration tests for multi-game session functionality."""

import json
from unittest.mock import patch

import pytest

from src.app.app import app, game_session_manager


class TestMultiGameSessions:
    """Integration tests for multiple concurrent game sessions."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup for each test."""
        # Clear all sessions before each test
        game_session_manager.sessions.clear()

    def test_concurrent_games_isolation(self, mock_player_data):
        """Test that concurrent games in different sessions are isolated."""
        # Create two sessions
        session_id1 = game_session_manager.create_session(creator_id="user1")
        session_id2 = game_session_manager.create_session(creator_id="user2")

        # Get game managers
        game_mgr1 = game_session_manager.get_session(session_id1)
        game_mgr2 = game_session_manager.get_session(session_id2)

        # Mock database operations
        with patch.object(game_mgr1.db_service, "start_new_game"):
            with patch.object(game_mgr2.db_service, "start_new_game"):
                # Start different games in each session
                game_mgr1.new_game("301", player_ids=mock_player_data)
                game_mgr2.new_game("cricket", player_ids=mock_player_data)

                # Verify games are different
                assert game_mgr1.game_type == "301"
                assert game_mgr2.game_type == "cricket"

                # Verify they're both running
                assert game_mgr1.is_started is True
                assert game_mgr2.is_started is True

                # Process a score in game 1
                with patch.object(game_mgr1.db_service, "record_throw"):
                    game_mgr1.process_score({"score": 20, "multiplier": "TRIPLE"})

                # Verify game 2 is unaffected
                assert game_mgr2.current_throw == 1  # Still on first throw

    def test_default_session_backward_compatibility(self):
        """Test that default session exists for backward compatibility."""
        default_id = game_session_manager.get_or_create_default_session()
        assert default_id == "default"
        assert default_id in game_session_manager.sessions

        # Second call should return same session
        default_id2 = game_session_manager.get_or_create_default_session()
        assert default_id == default_id2

    def test_session_listing_shows_active_games(self, mock_player_data):
        """Test that session listing includes game information."""
        # Create session and start a game
        session_id = game_session_manager.create_session(creator_id="user1")
        game_mgr = game_session_manager.get_session(session_id)

        with patch.object(game_mgr.db_service, "start_new_game"):
            game_mgr.new_game("501", player_ids=mock_player_data, double_out=True)

        # List sessions
        sessions = game_session_manager.list_sessions()

        assert len(sessions) == 1
        session_info = sessions[0]
        assert session_info["session_id"] == session_id
        assert session_info["game_type"] == "501"
        assert session_info["is_started"] is True
        assert session_info["player_count"] == 2

    def test_multiple_sessions_different_states(self, mock_player_data):
        """Test multiple sessions can have different game states."""
        # Create three sessions
        session_id1 = game_session_manager.create_session(creator_id="user1")
        session_id2 = game_session_manager.create_session(creator_id="user2")
        session_id3 = game_session_manager.create_session(creator_id="user3")

        # Start game only in session 1
        game_mgr1 = game_session_manager.get_session(session_id1)
        with patch.object(game_mgr1.db_service, "start_new_game"):
            game_mgr1.new_game("301", player_ids=mock_player_data)

        # Get all sessions
        sessions = game_session_manager.list_sessions()
        assert len(sessions) == 3

        # Find each session in the list
        session1_info = next(s for s in sessions if s["session_id"] == session_id1)
        session2_info = next(s for s in sessions if s["session_id"] == session_id2)
        session3_info = next(s for s in sessions if s["session_id"] == session_id3)

        # Verify states
        assert session1_info["is_started"] is True
        assert session2_info["is_started"] is False
        assert session3_info["is_started"] is False

    def test_session_isolation_players(self, mock_player_data):
        """Test that players in different sessions are isolated."""
        # Create two sessions
        session_id1 = game_session_manager.create_session(creator_id="user1")
        session_id2 = game_session_manager.create_session(creator_id="user2")

        # Get game managers
        game_mgr1 = game_session_manager.get_session(session_id1)
        game_mgr2 = game_session_manager.get_session(session_id2)

        # Mock database operations
        with patch.object(game_mgr1.db_service, "start_new_game"):
            with patch.object(game_mgr2.db_service, "start_new_game"):
                # Start games with different player counts
                game_mgr1.new_game("301", player_ids=mock_player_data)
                game_mgr2.new_game(
                    "301",
                    player_ids=[{"db_id": 1}, {"db_id": 2}, {"db_id": 3}],
                )

                # Verify player isolation
                assert len(game_mgr1.players) == 2
                assert len(game_mgr2.players) == 3

    def test_session_game_state_isolation(self, mock_player_data):
        """Test that game state is isolated between sessions."""
        # Create two sessions
        session_id1 = game_session_manager.create_session(creator_id="user1")
        session_id2 = game_session_manager.create_session(creator_id="user2")

        # Get game managers
        game_mgr1 = game_session_manager.get_session(session_id1)
        game_mgr2 = game_session_manager.get_session(session_id2)

        # Mock database operations
        with patch.object(game_mgr1.db_service, "start_new_game"):
            with patch.object(game_mgr2.db_service, "start_new_game"):
                with patch.object(game_mgr1.db_service, "record_throw"):
                    # Start both games
                    game_mgr1.new_game("301", player_ids=mock_player_data)
                    game_mgr2.new_game("301", player_ids=mock_player_data)

                    # Process scores in game 1
                    game_mgr1.process_score({"score": 20, "multiplier": "TRIPLE"})
                    game_mgr1.process_score({"score": 20, "multiplier": "TRIPLE"})
                    game_mgr1.process_score({"score": 20, "multiplier": "TRIPLE"})

                    # Game 1 should have progressed
                    assert game_mgr1.current_throw > 3 or game_mgr1.is_paused

                    # Game 2 should be unaffected
                    assert game_mgr2.current_throw == 1
                    assert game_mgr2.is_paused is False
