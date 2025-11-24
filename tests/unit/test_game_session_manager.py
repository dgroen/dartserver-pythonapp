"""Unit tests for GameSessionManager class."""

import pytest

from src.app.game_session_manager import GameSessionManager


class TestGameSessionManager:
    """Test cases for GameSessionManager class."""

    def test_initialization(self, mock_socketio):
        """Test session manager initialization."""
        manager = GameSessionManager(mock_socketio)
        assert manager.socketio == mock_socketio
        assert manager.sessions == {}

    def test_create_session(self, mock_socketio):
        """Test creating a new game session."""
        manager = GameSessionManager(mock_socketio)
        session_id = manager.create_session(creator_id="user123")

        assert session_id is not None
        assert session_id in manager.sessions
        assert manager.sessions[session_id].session_id == session_id
        assert manager.sessions[session_id].creator_id == "user123"

    def test_create_multiple_sessions(self, mock_socketio):
        """Test creating multiple game sessions."""
        manager = GameSessionManager(mock_socketio)
        session_id1 = manager.create_session(creator_id="user1")
        session_id2 = manager.create_session(creator_id="user2")

        assert session_id1 != session_id2
        assert session_id1 in manager.sessions
        assert session_id2 in manager.sessions
        assert len(manager.sessions) == 2

    def test_get_session(self, mock_socketio):
        """Test getting a game session by ID."""
        manager = GameSessionManager(mock_socketio)
        session_id = manager.create_session(creator_id="user1")

        game_mgr = manager.get_session(session_id)
        assert game_mgr is not None
        assert game_mgr.session_id == session_id

    def test_get_nonexistent_session(self, mock_socketio):
        """Test getting a nonexistent session returns None."""
        manager = GameSessionManager(mock_socketio)
        game_mgr = manager.get_session("nonexistent")
        assert game_mgr is None

    def test_delete_session(self, mock_socketio):
        """Test deleting a game session."""
        manager = GameSessionManager(mock_socketio)
        session_id = manager.create_session(creator_id="user1")

        assert manager.delete_session(session_id) is True
        assert session_id not in manager.sessions

    def test_delete_nonexistent_session(self, mock_socketio):
        """Test deleting a nonexistent session returns False."""
        manager = GameSessionManager(mock_socketio)
        assert manager.delete_session("nonexistent") is False

    def test_list_sessions(self, mock_socketio):
        """Test listing all active sessions."""
        manager = GameSessionManager(mock_socketio)
        session_id1 = manager.create_session(creator_id="user1")
        session_id2 = manager.create_session(creator_id="user2")

        sessions = manager.list_sessions()
        assert len(sessions) == 2
        assert any(s["session_id"] == session_id1 for s in sessions)
        assert any(s["session_id"] == session_id2 for s in sessions)

    def test_list_sessions_with_game_state(self, mock_socketio, mock_player_data):
        """Test listing sessions includes game state info."""
        manager = GameSessionManager(mock_socketio)
        session_id = manager.create_session(creator_id="user1")

        # Start a game in the session
        game_mgr = manager.get_session(session_id)
        game_mgr.new_game("301", player_ids=mock_player_data)

        sessions = manager.list_sessions()
        assert len(sessions) == 1
        session_info = sessions[0]

        assert session_info["session_id"] == session_id
        assert session_info["creator_id"] == "user1"
        assert session_info["game_type"] == "301"
        assert session_info["is_started"] is True
        assert session_info["player_count"] == 2

    def test_get_or_create_default_session(self, mock_socketio):
        """Test getting or creating default session for backward compatibility."""
        manager = GameSessionManager(mock_socketio)

        # First call creates the session
        session_id1 = manager.get_or_create_default_session()
        assert session_id1 == "default"
        assert "default" in manager.sessions

        # Second call returns the same session
        session_id2 = manager.get_or_create_default_session()
        assert session_id2 == session_id1
        assert len(manager.sessions) == 1

    def test_sessions_are_isolated(self, mock_socketio, mock_player_data):
        """Test that game sessions are isolated from each other."""
        manager = GameSessionManager(mock_socketio)

        # Create two sessions
        session_id1 = manager.create_session(creator_id="user1")
        session_id2 = manager.create_session(creator_id="user2")

        # Start different games in each session
        game_mgr1 = manager.get_session(session_id1)
        game_mgr2 = manager.get_session(session_id2)

        game_mgr1.new_game("301", player_ids=mock_player_data)
        game_mgr2.new_game("cricket", player_ids=mock_player_data)

        # Verify isolation
        assert game_mgr1.game_type == "301"
        assert game_mgr2.game_type == "cricket"
        assert game_mgr1.is_started is True
        assert game_mgr2.is_started is True
        assert game_mgr1 is not game_mgr2

    def test_session_unique_ids(self, mock_socketio):
        """Test that session IDs are unique."""
        manager = GameSessionManager(mock_socketio)
        session_ids = set()

        # Create 20 sessions to validate uniqueness
        for i in range(20):
            session_id = manager.create_session(creator_id=f"user{i}")
            assert session_id not in session_ids
            session_ids.add(session_id)

        assert len(session_ids) == 20
        assert len(manager.sessions) == 20
