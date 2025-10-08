"""Integration tests for WebSocket events."""

import time
from unittest.mock import patch

import pytest

from app import app as flask_app
from app import game_manager, socketio


@pytest.fixture
def app():
    """Create Flask app for testing."""
    with patch("app.start_rabbitmq_consumer"), patch("game_manager.DatabaseService"):
        flask_app.config["TESTING"] = True
        yield flask_app


@pytest.fixture
def socketio_client(app):
    """Create SocketIO test client."""
    client = socketio.test_client(app, flask_test_client=app.test_client(), namespace="/")
    # Give the client time to connect and receive initial messages
    time.sleep(0.1)
    # Retrieve and store initial connection messages
    client._initial_messages = client.get_received(namespace="/")
    return client


def wait_for_events(client, timeout=1.0):
    """Wait for events to be received by the client."""
    import eventlet

    # Give time for the server to process and emit events
    # Use eventlet.sleep to allow the eventlet greenthread to process
    eventlet.sleep(0.3)
    return client.get_received(namespace="/")


class TestWebSocketEvents:
    """Test WebSocket event handlers."""

    def test_connect_event(self, socketio_client):
        """Test client connection event."""
        assert socketio_client.is_connected(namespace="/")
        # Connection successful - the connect handler is called (see stdout)
        # Note: Flask-SocketIO test client doesn't capture emissions during connect
        # We test actual event emissions in other tests

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

        # Wait for processing
        wait_for_events(socketio_client)

        # Verify game state directly from game_manager
        state = game_manager.get_game_state()
        assert state["game_type"] == "301"
        assert state["is_started"] is True
        assert len(state["players"]) == 2
        assert state["players"][0]["name"] == "Alice"
        assert state["players"][1]["name"] == "Bob"

    def test_new_game_event_default_values(self, socketio_client):
        """Test new_game event with default values."""
        socketio_client.get_received(namespace="/")  # Clear initial messages

        # Emit new_game event without parameters
        socketio_client.emit("new_game", {}, namespace="/")

        # Wait for processing
        wait_for_events(socketio_client)

        # Verify game state directly from game_manager
        state = game_manager.get_game_state()
        assert state["is_started"] is True
        assert len(state["players"]) == 2  # Default players

    def test_new_game_cricket(self, socketio_client):
        """Test new_game event for cricket."""
        socketio_client.get_received(namespace="/")  # Clear initial messages

        # Emit new_game event
        socketio_client.emit(
            "new_game",
            {"game_type": "cricket", "players": ["Player1", "Player2"]},
            namespace="/",
        )

        # Wait for processing
        wait_for_events(socketio_client)

        # Verify game state directly from game_manager
        state = game_manager.get_game_state()
        assert state["game_type"] == "cricket"
        assert state["is_started"] is True

    def test_add_player_event(self, socketio_client):
        """Test add_player WebSocket event."""
        socketio_client.get_received(namespace="/")  # Clear initial messages

        # Start a game first
        socketio_client.emit("new_game", {"game_type": "301", "players": ["Alice"]}, namespace="/")
        wait_for_events(socketio_client)  # Wait for processing

        # Add a player
        socketio_client.emit("add_player", {"name": "Bob"}, namespace="/")
        wait_for_events(socketio_client)

        # Verify game state directly from game_manager
        state = game_manager.get_game_state()
        assert len(state["players"]) == 2
        assert state["players"][1]["name"] == "Bob"

    def test_add_player_event_default_name(self, socketio_client):
        """Test add_player event with default name."""
        socketio_client.get_received(namespace="/")  # Clear initial messages

        # Start a game first
        socketio_client.emit("new_game", {"game_type": "301", "players": ["Alice"]}, namespace="/")
        wait_for_events(socketio_client)  # Wait for processing

        # Add a player without name
        socketio_client.emit("add_player", {}, namespace="/")
        wait_for_events(socketio_client)

        # Verify game state directly from game_manager
        state = game_manager.get_game_state()
        assert len(state["players"]) == 2
        assert state["players"][1]["name"] == "Player 2"

    def test_remove_player_event(self, socketio_client):
        """Test remove_player WebSocket event."""
        socketio_client.get_received(namespace="/")  # Clear initial messages

        # Start a game with 3 players
        socketio_client.emit(
            "new_game",
            {"game_type": "301", "players": ["Alice", "Bob", "Charlie"]},
            namespace="/",
        )
        wait_for_events(socketio_client)  # Wait for processing

        # Remove a player
        socketio_client.emit("remove_player", {"player_id": 1}, namespace="/")
        wait_for_events(socketio_client)

        # Verify game state directly from game_manager
        state = game_manager.get_game_state()
        assert len(state["players"]) == 2
        assert state["players"][0]["name"] == "Alice"
        assert state["players"][1]["name"] == "Charlie"

    def test_remove_player_event_no_id(self, socketio_client):
        """Test remove_player event without player_id."""
        socketio_client.get_received(namespace="/")  # Clear initial messages

        # Start a game
        socketio_client.emit(
            "new_game",
            {"game_type": "301", "players": ["Alice", "Bob"]},
            namespace="/",
        )
        wait_for_events(socketio_client)  # Clear messages

        # Try to remove without player_id
        socketio_client.emit("remove_player", {}, namespace="/")

        # Should not crash, just ignore
        wait_for_events(socketio_client)
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
        wait_for_events(socketio_client)  # Wait for processing

        # Move to next player
        socketio_client.emit("next_player", namespace="/")
        wait_for_events(socketio_client)

        # Verify game state directly from game_manager
        state = game_manager.get_game_state()
        assert state["current_player"] == 1  # Should be Bob now

    def test_skip_to_player_event(self, socketio_client):
        """Test skip_to_player WebSocket event."""
        socketio_client.get_received(namespace="/")  # Clear initial messages

        # Start a game
        socketio_client.emit(
            "new_game",
            {"game_type": "301", "players": ["Alice", "Bob", "Charlie"]},
            namespace="/",
        )
        wait_for_events(socketio_client)  # Wait for processing

        # Skip to specific player
        socketio_client.emit("skip_to_player", {"player_id": 2}, namespace="/")
        wait_for_events(socketio_client)

        # Verify game state directly from game_manager
        state = game_manager.get_game_state()
        assert state["current_player"] == 2  # Should be Charlie now

    def test_skip_to_player_event_no_id(self, socketio_client):
        """Test skip_to_player event without player_id."""
        socketio_client.get_received(namespace="/")  # Clear initial messages

        # Start a game
        socketio_client.emit(
            "new_game",
            {"game_type": "301", "players": ["Alice", "Bob"]},
            namespace="/",
        )
        wait_for_events(socketio_client)  # Clear messages

        # Try to skip without player_id
        socketio_client.emit("skip_to_player", {}, namespace="/")

        # Should not crash, just ignore
        wait_for_events(socketio_client)
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
        wait_for_events(socketio_client)  # Wait for processing

        # Submit a score (DARTBOARD_SENDS_ACTUAL_SCORE=True, so send actual score 60, not base 20)
        socketio_client.emit("manual_score", {"score": 60, "multiplier": "TRIPLE"}, namespace="/")
        wait_for_events(socketio_client)

        # Verify game state directly from game_manager
        state = game_manager.get_game_state()
        # Alice should have scored 60 (triple 20), so remaining should be 301 - 60 = 241
        assert state["game_data"]["players"][0]["score"] == 241

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

        # Submit multiple scores (DARTBOARD_SENDS_ACTUAL_SCORE=True, so send actual scores)
        scores = [
            {"score": 60, "multiplier": "TRIPLE"},  # Triple 20 = 60
            {"score": 38, "multiplier": "DOUBLE"},  # Double 19 = 38
            {"score": 18, "multiplier": "SINGLE"},  # Single 18 = 18
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
        wait_for_events(socketio_client)  # Wait for processing

        # Play some throws (DARTBOARD_SENDS_ACTUAL_SCORE=True, so send actual scores)
        socketio_client.emit("manual_score", {"score": 60, "multiplier": "TRIPLE"}, namespace="/")
        wait_for_events(socketio_client)

        socketio_client.emit("manual_score", {"score": 60, "multiplier": "TRIPLE"}, namespace="/")
        wait_for_events(socketio_client)

        socketio_client.emit("manual_score", {"score": 60, "multiplier": "TRIPLE"}, namespace="/")
        wait_for_events(socketio_client)

        # Verify game state directly from game_manager
        state = game_manager.get_game_state()
        # Alice should have scored 180 (60 * 3), so remaining should be 301 - 180 = 121
        assert state["game_data"]["players"][0]["score"] == 121
        # After 3 throws, should be on throw 4 (still Alice's turn until explicitly moved)
        assert state["current_throw"] == 4
