"""Integration tests for WebSocket events."""

from unittest.mock import patch

import pytest

from app import app as flask_app
from app import socketio


@pytest.fixture
def app():
    """Create Flask app for testing."""
    with patch("app.start_rabbitmq_consumer"):
        flask_app.config["TESTING"] = True
        yield flask_app


@pytest.fixture
def socketio_client(app):
    """Create SocketIO test client."""
    return socketio.test_client(app, flask_test_client=app.test_client())


class TestWebSocketEvents:
    """Test WebSocket event handlers."""

    def test_connect_event(self, socketio_client):
        """Test client connection event."""
        assert socketio_client.is_connected()
        # Should receive game_state on connect
        received = socketio_client.get_received()
        assert len(received) > 0
        assert received[0]["name"] == "game_state"
        assert "players" in received[0]["args"][0]

    def test_disconnect_event(self, socketio_client):
        """Test client disconnection event."""
        assert socketio_client.is_connected()
        socketio_client.disconnect()
        assert not socketio_client.is_connected()

    def test_new_game_event(self, socketio_client):
        """Test new_game WebSocket event."""
        socketio_client.get_received()  # Clear initial messages

        # Emit new_game event
        socketio_client.emit("new_game", {"game_type": "301", "players": ["Alice", "Bob"]})

        # Should receive game_state update
        received = socketio_client.get_received()
        assert any(msg["name"] == "game_state" for msg in received)

        # Verify game state
        game_state_msg = next(msg for msg in received if msg["name"] == "game_state")
        state = game_state_msg["args"][0]
        assert state["game_type"] == "301"
        assert state["is_started"] is True

    def test_new_game_event_default_values(self, socketio_client):
        """Test new_game event with default values."""
        socketio_client.get_received()  # Clear initial messages

        # Emit new_game event without parameters
        socketio_client.emit("new_game", {})

        # Should receive game_state update
        received = socketio_client.get_received()
        assert any(msg["name"] == "game_state" for msg in received)

    def test_new_game_cricket(self, socketio_client):
        """Test new_game event for cricket."""
        socketio_client.get_received()  # Clear initial messages

        # Emit new_game event
        socketio_client.emit(
            "new_game",
            {"game_type": "cricket", "players": ["Player1", "Player2"]},
        )

        # Should receive game_state update
        received = socketio_client.get_received()
        game_state_msg = next(msg for msg in received if msg["name"] == "game_state")
        state = game_state_msg["args"][0]
        assert state["game_type"] == "cricket"

    def test_add_player_event(self, socketio_client):
        """Test add_player WebSocket event."""
        socketio_client.get_received()  # Clear initial messages

        # Start a game first
        socketio_client.emit("new_game", {"game_type": "301", "players": ["Alice"]})
        socketio_client.get_received()  # Clear messages

        # Add a player
        socketio_client.emit("add_player", {"name": "Bob"})

        # Should receive game_state update
        received = socketio_client.get_received()
        assert any(msg["name"] == "game_state" for msg in received)

    def test_add_player_event_default_name(self, socketio_client):
        """Test add_player event with default name."""
        socketio_client.get_received()  # Clear initial messages

        # Start a game first
        socketio_client.emit("new_game", {"game_type": "301", "players": ["Alice"]})
        socketio_client.get_received()  # Clear messages

        # Add a player without name
        socketio_client.emit("add_player", {})

        # Should receive game_state update
        received = socketio_client.get_received()
        assert any(msg["name"] == "game_state" for msg in received)

    def test_remove_player_event(self, socketio_client):
        """Test remove_player WebSocket event."""
        socketio_client.get_received()  # Clear initial messages

        # Start a game with 3 players
        socketio_client.emit(
            "new_game",
            {"game_type": "301", "players": ["Alice", "Bob", "Charlie"]},
        )
        socketio_client.get_received()  # Clear messages

        # Remove a player
        socketio_client.emit("remove_player", {"player_id": 1})

        # Should receive game_state update
        received = socketio_client.get_received()
        assert any(msg["name"] == "game_state" for msg in received)

    def test_remove_player_event_no_id(self, socketio_client):
        """Test remove_player event without player_id."""
        socketio_client.get_received()  # Clear initial messages

        # Start a game
        socketio_client.emit("new_game", {"game_type": "301", "players": ["Alice", "Bob"]})
        socketio_client.get_received()  # Clear messages

        # Try to remove without player_id
        socketio_client.emit("remove_player", {})

        # Should not crash, just ignore
        socketio_client.get_received()
        # May or may not receive updates, but shouldn't crash

    def test_next_player_event(self, socketio_client):
        """Test next_player WebSocket event."""
        socketio_client.get_received()  # Clear initial messages

        # Start a game
        socketio_client.emit("new_game", {"game_type": "301", "players": ["Alice", "Bob"]})
        socketio_client.get_received()  # Clear messages

        # Move to next player
        socketio_client.emit("next_player")

        # Should receive game_state update
        received = socketio_client.get_received()
        assert any(msg["name"] == "game_state" for msg in received)

    def test_skip_to_player_event(self, socketio_client):
        """Test skip_to_player WebSocket event."""
        socketio_client.get_received()  # Clear initial messages

        # Start a game
        socketio_client.emit(
            "new_game",
            {"game_type": "301", "players": ["Alice", "Bob", "Charlie"]},
        )
        socketio_client.get_received()  # Clear messages

        # Skip to specific player
        socketio_client.emit("skip_to_player", {"player_id": 2})

        # Should receive game_state update
        received = socketio_client.get_received()
        assert any(msg["name"] == "game_state" for msg in received)

    def test_skip_to_player_event_no_id(self, socketio_client):
        """Test skip_to_player event without player_id."""
        socketio_client.get_received()  # Clear initial messages

        # Start a game
        socketio_client.emit("new_game", {"game_type": "301", "players": ["Alice", "Bob"]})
        socketio_client.get_received()  # Clear messages

        # Try to skip without player_id
        socketio_client.emit("skip_to_player", {})

        # Should not crash, just ignore
        socketio_client.get_received()
        # May or may not receive updates, but shouldn't crash

    def test_manual_score_event(self, socketio_client):
        """Test manual_score WebSocket event."""
        socketio_client.get_received()  # Clear initial messages

        # Start a game
        socketio_client.emit("new_game", {"game_type": "301", "players": ["Alice", "Bob"]})
        socketio_client.get_received()  # Clear messages

        # Submit a score
        socketio_client.emit("manual_score", {"score": 20, "multiplier": "TRIPLE"})

        # Should receive game_state update
        received = socketio_client.get_received()
        assert any(msg["name"] == "game_state" for msg in received)

    def test_manual_score_multiple_throws(self, socketio_client):
        """Test multiple manual score submissions."""
        socketio_client.get_received()  # Clear initial messages

        # Start a game
        socketio_client.emit("new_game", {"game_type": "301", "players": ["Alice", "Bob"]})
        socketio_client.get_received()  # Clear messages

        # Submit multiple scores
        scores = [
            {"score": 20, "multiplier": "TRIPLE"},
            {"score": 19, "multiplier": "DOUBLE"},
            {"score": 18, "multiplier": "SINGLE"},
        ]

        for score in scores:
            socketio_client.emit("manual_score", score)
            socketio_client.get_received()  # Clear messages after each

        # Should have processed all scores
        socketio_client.get_received()
        # Game should still be running

    def test_complete_game_via_websocket(self, socketio_client):
        """Test complete game flow via WebSocket."""
        socketio_client.get_received()  # Clear initial messages

        # Start a game
        socketio_client.emit("new_game", {"game_type": "301", "players": ["Alice", "Bob"]})
        socketio_client.get_received()  # Clear messages

        # Play some throws
        socketio_client.emit("manual_score", {"score": 20, "multiplier": "TRIPLE"})
        socketio_client.get_received()

        socketio_client.emit("manual_score", {"score": 20, "multiplier": "TRIPLE"})
        socketio_client.get_received()

        socketio_client.emit("manual_score", {"score": 20, "multiplier": "TRIPLE"})
        received = socketio_client.get_received()

        # Should have received updates
        assert len(received) > 0
