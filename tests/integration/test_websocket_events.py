"""Integration tests for WebSocket events."""

import time
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
    client = socketio.test_client(app, flask_test_client=app.test_client(), namespace="/")
    # Give the client time to connect and receive initial messages
    time.sleep(0.2)
    return client


def wait_for_events(client, timeout=1.0):
    """Wait for events to be received by the client."""
    import eventlet

    eventlet.sleep(0.1)  # Allow eventlet to process events
    return client.get_received(namespace="/")


class TestWebSocketEvents:
    """Test WebSocket event handlers."""

    def test_connect_event(self, socketio_client):
        """Test client connection event."""
        assert socketio_client.is_connected(namespace="/")
        # Should receive game_state on connect
        received = socketio_client.get_received(namespace="/")
        assert len(received) > 0
        assert received[0]["name"] == "game_state"
        assert "players" in received[0]["args"][0]

    def test_disconnect_event(self, socketio_client):
        """Test client disconnection event."""
        assert socketio_client.is_connected(namespace="/")
        socketio_client.disconnect(namespace="/")
        assert not socketio_client.is_connected(namespace="/")

    def test_new_game_event(self, socketio_client):
        """Test new_game WebSocket event."""
        socketio_client.get_received(namespace="/")  # Clear initial messages

        # Emit new_game event
        socketio_client.emit(
            "new_game",
            {"game_type": "301", "players": ["Alice", "Bob"]},
            namespace="/",
        )

        # Should receive game_state update
        received = wait_for_events(socketio_client)
        assert any(msg["name"] == "game_state" for msg in received)

        # Verify game state
        game_state_msg = next(msg for msg in received if msg["name"] == "game_state")
        state = game_state_msg["args"][0]
        assert state["game_type"] == "301"
        assert state["is_started"] is True

    def test_new_game_event_default_values(self, socketio_client):
        """Test new_game event with default values."""
        socketio_client.get_received(namespace="/")  # Clear initial messages

        # Emit new_game event without parameters
        socketio_client.emit("new_game", {}, namespace="/")

        # Should receive game_state update
        received = wait_for_events(socketio_client)
        assert any(msg["name"] == "game_state" for msg in received)

    def test_new_game_cricket(self, socketio_client):
        """Test new_game event for cricket."""
        socketio_client.get_received(namespace="/")  # Clear initial messages

        # Emit new_game event
        socketio_client.emit(
            "new_game",
            {"game_type": "cricket", "players": ["Player1", "Player2"]},
            namespace="/",
        )

        # Should receive game_state update
        received = wait_for_events(socketio_client)
        game_state_msg = next(msg for msg in received if msg["name"] == "game_state")
        state = game_state_msg["args"][0]
        assert state["game_type"] == "cricket"

    def test_add_player_event(self, socketio_client):
        """Test add_player WebSocket event."""
        socketio_client.get_received(namespace="/")  # Clear initial messages

        # Start a game first
        socketio_client.emit("new_game", {"game_type": "301", "players": ["Alice"]}, namespace="/")
        wait_for_events(socketio_client)  # Clear messages

        # Add a player
        socketio_client.emit("add_player", {"name": "Bob"}, namespace="/")

        # Should receive game_state update
        received = wait_for_events(socketio_client)
        assert any(msg["name"] == "game_state" for msg in received)

    def test_add_player_event_default_name(self, socketio_client):
        """Test add_player event with default name."""
        socketio_client.get_received(namespace="/")  # Clear initial messages

        # Start a game first
        socketio_client.emit("new_game", {"game_type": "301", "players": ["Alice"]}, namespace="/")
        wait_for_events(socketio_client)  # Clear messages

        # Add a player without name
        socketio_client.emit("add_player", {}, namespace="/")

        # Should receive game_state update
        received = wait_for_events(socketio_client)
        assert any(msg["name"] == "game_state" for msg in received)

    def test_remove_player_event(self, socketio_client):
        """Test remove_player WebSocket event."""
        socketio_client.get_received(namespace="/")  # Clear initial messages

        # Start a game with 3 players
        socketio_client.emit(
            "new_game",
            {"game_type": "301", "players": ["Alice", "Bob", "Charlie"]},
            namespace="/",
        )
        wait_for_events(socketio_client)  # Clear messages

        # Remove a player
        socketio_client.emit("remove_player", {"player_id": 1}, namespace="/")

        # Should receive game_state update
        received = wait_for_events(socketio_client)
        assert any(msg["name"] == "game_state" for msg in received)

    def test_remove_player_event_no_id(self, socketio_client):
        """Test remove_player event without player_id."""
        socketio_client.get_received(namespace="/")  # Clear initial messages

        # Start a game
        socketio_client.emit(
            "new_game",
            {"game_type": "301", "players": ["Alice", "Bob"]},
            namespace="/",
        )
        socketio_client.get_received(namespace="/")  # Clear messages

        # Try to remove without player_id
        socketio_client.emit("remove_player", {}, namespace="/")

        # Should not crash, just ignore
        socketio_client.get_received(namespace="/")
        # May or may not receive updates, but shouldn't crash

    def test_next_player_event(self, socketio_client):
        """Test next_player WebSocket event."""
        socketio_client.get_received(namespace="/")  # Clear initial messages

        # Start a game
        socketio_client.emit(
            "new_game",
            {"game_type": "301", "players": ["Alice", "Bob"]},
            namespace="/",
        )
        wait_for_events(socketio_client)  # Clear messages

        # Move to next player
        socketio_client.emit("next_player", namespace="/")

        # Should receive game_state update
        received = wait_for_events(socketio_client)
        assert any(msg["name"] == "game_state" for msg in received)

    def test_skip_to_player_event(self, socketio_client):
        """Test skip_to_player WebSocket event."""
        socketio_client.get_received(namespace="/")  # Clear initial messages

        # Start a game
        socketio_client.emit(
            "new_game",
            {"game_type": "301", "players": ["Alice", "Bob", "Charlie"]},
            namespace="/",
        )
        wait_for_events(socketio_client)  # Clear messages

        # Skip to specific player
        socketio_client.emit("skip_to_player", {"player_id": 2}, namespace="/")

        # Should receive game_state update
        received = wait_for_events(socketio_client)
        assert any(msg["name"] == "game_state" for msg in received)

    def test_skip_to_player_event_no_id(self, socketio_client):
        """Test skip_to_player event without player_id."""
        socketio_client.get_received(namespace="/")  # Clear initial messages

        # Start a game
        socketio_client.emit(
            "new_game",
            {"game_type": "301", "players": ["Alice", "Bob"]},
            namespace="/",
        )
        socketio_client.get_received(namespace="/")  # Clear messages

        # Try to skip without player_id
        socketio_client.emit("skip_to_player", {}, namespace="/")

        # Should not crash, just ignore
        socketio_client.get_received(namespace="/")
        # May or may not receive updates, but shouldn't crash

    def test_manual_score_event(self, socketio_client):
        """Test manual_score WebSocket event."""
        socketio_client.get_received(namespace="/")  # Clear initial messages

        # Start a game
        socketio_client.emit(
            "new_game",
            {"game_type": "301", "players": ["Alice", "Bob"]},
            namespace="/",
        )
        wait_for_events(socketio_client)  # Clear messages

        # Submit a score
        socketio_client.emit("manual_score", {"score": 20, "multiplier": "TRIPLE"}, namespace="/")

        # Should receive game_state update
        received = wait_for_events(socketio_client)
        assert any(msg["name"] == "game_state" for msg in received)

    def test_manual_score_multiple_throws(self, socketio_client):
        """Test multiple manual score submissions."""
        socketio_client.get_received(namespace="/")  # Clear initial messages

        # Start a game
        socketio_client.emit(
            "new_game",
            {"game_type": "301", "players": ["Alice", "Bob"]},
            namespace="/",
        )
        socketio_client.get_received(namespace="/")  # Clear messages

        # Submit multiple scores
        scores = [
            {"score": 20, "multiplier": "TRIPLE"},
            {"score": 19, "multiplier": "DOUBLE"},
            {"score": 18, "multiplier": "SINGLE"},
        ]

        for score in scores:
            socketio_client.emit("manual_score", score, namespace="/")
            socketio_client.get_received(namespace="/")  # Clear messages after each

        # Should have processed all scores
        socketio_client.get_received(namespace="/")
        # Game should still be running

    def test_complete_game_via_websocket(self, socketio_client):
        """Test complete game flow via WebSocket."""
        socketio_client.get_received(namespace="/")  # Clear initial messages

        # Start a game
        socketio_client.emit(
            "new_game",
            {"game_type": "301", "players": ["Alice", "Bob"]},
            namespace="/",
        )
        wait_for_events(socketio_client)  # Clear messages

        # Play some throws
        socketio_client.emit("manual_score", {"score": 20, "multiplier": "TRIPLE"}, namespace="/")
        wait_for_events(socketio_client)

        socketio_client.emit("manual_score", {"score": 20, "multiplier": "TRIPLE"}, namespace="/")
        wait_for_events(socketio_client)

        socketio_client.emit("manual_score", {"score": 20, "multiplier": "TRIPLE"}, namespace="/")
        received = wait_for_events(socketio_client)

        # Should have received updates
        assert len(received) > 0
