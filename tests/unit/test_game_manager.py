"""Unit tests for GameManager class."""

from game_manager import GameManager


class TestGameManager:
    """Test cases for GameManager class."""

    def test_initialization(self, mock_socketio):
        """Test game manager initialization."""
        manager = GameManager(mock_socketio)
        assert manager.socketio == mock_socketio
        assert manager.players == []
        assert manager.current_player == 0
        assert manager.game_type == "301"
        assert manager.game is None
        assert manager.is_started is False
        assert manager.is_paused is True

    def test_new_game_301(self, mock_socketio):
        """Test starting a new 301 game."""
        manager = GameManager(mock_socketio)
        manager.new_game("301", ["Alice", "Bob"])
        assert manager.game_type == "301"
        assert len(manager.players) == 2
        assert manager.is_started is True
        assert manager.is_paused is False
        assert manager.game is not None

    def test_new_game_cricket(self, mock_socketio):
        """Test starting a new cricket game."""
        manager = GameManager(mock_socketio)
        manager.new_game("cricket", ["Alice", "Bob"])
        assert manager.game_type == "cricket"
        assert manager.game is not None

    def test_new_game_501(self, mock_socketio):
        """Test starting a new 501 game."""
        manager = GameManager(mock_socketio)
        manager.new_game("501", ["Alice", "Bob"])
        assert manager.game_type == "501"

    def test_new_game_default_players(self, mock_socketio):
        """Test starting game with default players."""
        manager = GameManager(mock_socketio)
        manager.new_game("301")
        assert len(manager.players) == 2
        assert manager.players[0]["name"] == "Player 1"
        assert manager.players[1]["name"] == "Player 2"

    def test_add_player(self, mock_socketio):
        """Test adding a player."""
        manager = GameManager(mock_socketio)
        manager.new_game("301", ["Alice"])
        manager.add_player("Bob")
        assert len(manager.players) == 2
        assert manager.players[1]["name"] == "Bob"

    def test_add_player_cricket_max_limit(self, mock_socketio):
        """Test adding player to cricket beyond max limit."""
        manager = GameManager(mock_socketio)
        manager.new_game("cricket", ["Alice", "Bob", "Charlie", "Diana"])
        initial_count = len(manager.players)
        manager.add_player("Eve")
        assert len(manager.players) == initial_count  # Should not add

    def test_remove_player(self, mock_socketio):
        """Test removing a player."""
        manager = GameManager(mock_socketio)
        manager.new_game("301", ["Alice", "Bob", "Charlie"])
        manager.remove_player(1)
        assert len(manager.players) == 2
        assert manager.players[0]["name"] == "Alice"
        assert manager.players[1]["name"] == "Charlie"

    def test_remove_player_minimum(self, mock_socketio):
        """Test cannot remove player below minimum."""
        manager = GameManager(mock_socketio)
        manager.new_game("301", ["Alice", "Bob"])
        manager.remove_player(0)
        assert len(manager.players) == 1  # Should allow single player
        # Try to remove the last player
        manager.remove_player(0)
        assert len(manager.players) == 1  # Should not remove last player

    def test_process_score_single(self, mock_socketio):
        """Test processing a single score."""
        manager = GameManager(mock_socketio)
        manager.new_game("301", ["Alice", "Bob"])
        score_data = {"score": 20, "multiplier": "SINGLE"}
        manager.process_score(score_data)
        assert manager.current_throw == 2

    def test_process_score_triple(self, mock_socketio):
        """Test processing a triple score."""
        manager = GameManager(mock_socketio)
        manager.new_game("301", ["Alice", "Bob"])
        score_data = {"score": 20, "multiplier": "TRIPLE"}
        manager.process_score(score_data)
        # Check that game state was updated
        assert mock_socketio.emit.called

    def test_process_score_not_started(self, mock_socketio):
        """Test processing score when game not started."""
        manager = GameManager(mock_socketio)
        score_data = {"score": 20, "multiplier": "SINGLE"}
        manager.process_score(score_data)
        # Should be ignored
        assert manager.current_throw == 1

    def test_process_score_paused(self, mock_socketio):
        """Test processing score when game is paused."""
        manager = GameManager(mock_socketio)
        manager.new_game("301", ["Alice", "Bob"])
        manager.is_paused = True
        score_data = {"score": 20, "multiplier": "SINGLE"}
        initial_throw = manager.current_throw
        manager.process_score(score_data)
        assert manager.current_throw == initial_throw

    def test_next_player(self, mock_socketio):
        """Test moving to next player."""
        manager = GameManager(mock_socketio)
        manager.new_game("301", ["Alice", "Bob"])
        assert manager.current_player == 0
        manager.next_player()
        assert manager.current_player == 1
        assert manager.current_throw == 1
        assert manager.is_paused is False

    def test_next_player_wrap_around(self, mock_socketio):
        """Test next player wraps around."""
        manager = GameManager(mock_socketio)
        manager.new_game("301", ["Alice", "Bob"])
        manager.current_player = 1
        manager.next_player()
        assert manager.current_player == 0

    def test_skip_to_player(self, mock_socketio):
        """Test skipping to specific player."""
        manager = GameManager(mock_socketio)
        manager.new_game("301", ["Alice", "Bob", "Charlie"])
        manager.skip_to_player(2)
        assert manager.current_player == 2
        assert manager.current_throw == 1

    def test_skip_to_invalid_player(self, mock_socketio):
        """Test skipping to invalid player."""
        manager = GameManager(mock_socketio)
        manager.new_game("301", ["Alice", "Bob"])
        initial_player = manager.current_player
        manager.skip_to_player(5)
        assert manager.current_player == initial_player

    def test_get_game_state(self, mock_socketio):
        """Test getting game state."""
        manager = GameManager(mock_socketio)
        manager.new_game("301", ["Alice", "Bob"])
        state = manager.get_game_state()
        assert "players" in state
        assert "current_player" in state
        assert "game_type" in state
        assert "is_started" in state
        assert state["game_type"] == "301"

    def test_get_players(self, mock_socketio):
        """Test getting players."""
        manager = GameManager(mock_socketio)
        manager.new_game("301", ["Alice", "Bob"])
        players = manager.get_players()
        assert len(players) == 2
        assert players[0]["name"] == "Alice"

    def test_emit_game_state(self, mock_socketio):
        """Test emitting game state."""
        manager = GameManager(mock_socketio)
        manager.new_game("301", ["Alice", "Bob"])
        mock_socketio.emit.reset_mock()
        manager._emit_game_state()
        mock_socketio.emit.assert_called_once()
        args = mock_socketio.emit.call_args
        assert args[0][0] == "game_state"

    def test_emit_sound(self, mock_socketio):
        """Test emitting sound."""
        manager = GameManager(mock_socketio)
        manager._emit_sound("test_sound")
        mock_socketio.emit.assert_called_with("play_sound", {"sound": "test_sound"}, namespace="/")

    def test_emit_video(self, mock_socketio):
        """Test emitting video."""
        manager = GameManager(mock_socketio)
        manager._emit_video("test.mp4", 90)
        mock_socketio.emit.assert_called_with(
            "play_video",
            {"video": "test.mp4", "angle": 90},
            namespace="/",
        )

    def test_emit_message(self, mock_socketio):
        """Test emitting message."""
        manager = GameManager(mock_socketio)
        manager._emit_message("Test message")
        mock_socketio.emit.assert_called_with("message", {"text": "Test message"}, namespace="/")

    def test_get_angle(self, mock_socketio):
        """Test getting angle for score."""
        manager = GameManager(mock_socketio)
        angle = manager._get_angle(20)
        assert angle == 0  # 20 is at index 0
        angle = manager._get_angle(1)
        assert angle == 18  # 1 is at index 1

    def test_get_angle_invalid_score(self, mock_socketio):
        """Test getting angle for invalid score."""
        manager = GameManager(mock_socketio)
        angle = manager._get_angle(99)
        assert angle == 0  # Default for invalid score

    def test_turn_completion(self, mock_socketio):
        """Test turn completion after 3 throws."""
        manager = GameManager(mock_socketio)
        manager.new_game("301", ["Alice", "Bob"])
        # Throw 3 darts
        for _ in range(3):
            score_data = {"score": 20, "multiplier": "SINGLE"}
            manager.process_score(score_data)
        # Should be paused after 3 throws
        assert manager.is_paused is True

    def test_bust_handling(self, mock_socketio):
        """Test bust handling."""
        manager = GameManager(mock_socketio)
        manager.new_game("301", ["Alice", "Bob"])
        # Set player score low
        manager.game.players[0]["score"] = 10
        # Try to score more than remaining
        score_data = {"score": 20, "multiplier": "SINGLE"}
        manager.process_score(score_data)
        # Should be paused due to bust
        assert manager.is_paused is True

    def test_winner_handling(self, mock_socketio):
        """Test winner handling."""
        manager = GameManager(mock_socketio)
        manager.new_game("301", ["Alice", "Bob"])
        # Set player score to exact winning amount
        manager.game.players[0]["score"] = 20
        score_data = {"score": 20, "multiplier": "SINGLE"}
        manager.process_score(score_data)
        # Should detect winner
        assert manager.is_winner is True
        assert manager.is_paused is True
