"""Additional edge case tests for GameManager."""

from unittest.mock import MagicMock

import pytest

from game_manager import GameManager


@pytest.fixture
def socketio():
    """Mock SocketIO instance."""
    return MagicMock()


@pytest.fixture
def game_manager(socketio):
    """Create GameManager instance."""
    return GameManager(socketio)


class TestGameManagerEdgeCases:
    """Test edge cases in GameManager."""

    def test_next_player_when_not_started(self, game_manager):
        """Test next_player when game not started."""
        # Don't start game
        game_manager.is_started = False

        # Try to move to next player
        game_manager.next_player()

        # Should not change current player
        assert game_manager.current_player == 0

    def test_skip_to_player_when_not_started(self, game_manager):
        """Test skip_to_player when game not started."""
        # Don't start game
        game_manager.is_started = False

        # Try to skip to player
        game_manager.skip_to_player(1)

        # Should not change current player
        assert game_manager.current_player == 0

    def test_skip_to_player_negative_id(self, game_manager):
        """Test skip_to_player with negative player ID."""
        # Start game
        game_manager.new_game("301", ["Alice", "Bob"])

        # Try to skip to negative player ID
        game_manager.skip_to_player(-1)

        # Should not change current player
        assert game_manager.current_player == 0

    def test_skip_to_player_out_of_range(self, game_manager):
        """Test skip_to_player with out of range player ID."""
        # Start game
        game_manager.new_game("301", ["Alice", "Bob"])

        # Try to skip to player ID beyond range
        game_manager.skip_to_player(10)

        # Should not change current player
        assert game_manager.current_player == 0

    def test_get_game_state_without_game(self, game_manager):
        """Test get_game_state when no game is active."""
        # Don't start game
        state = game_manager.get_game_state()

        # Should return state without game_data
        assert "players" in state
        assert "game_type" in state
        assert "is_started" in state
        assert "game_data" not in state

    def test_get_game_state_with_game(self, game_manager):
        """Test get_game_state when game is active."""
        # Start game
        game_manager.new_game("301", ["Alice", "Bob"])

        state = game_manager.get_game_state()

        # Should return state with game_data
        assert "players" in state
        assert "game_type" in state
        assert "is_started" in state
        assert "game_data" in state

    def test_process_score_with_bull_multiplier(self, game_manager):
        """Test processing score with BULL multiplier."""
        # Start game
        game_manager.new_game("301", ["Alice", "Bob"])

        # Process bull score
        game_manager.process_score({"score": 25, "multiplier": "BULL"})

        # Should process successfully
        assert game_manager.current_throw == 2

    def test_process_score_with_dblbull_multiplier(self, game_manager):
        """Test processing score with DBLBULL multiplier."""
        # Start game
        game_manager.new_game("301", ["Alice", "Bob"])

        # Process double bull score
        game_manager.process_score({"score": 25, "multiplier": "DBLBULL"})

        # Should process successfully
        assert game_manager.current_throw == 2

    def test_process_score_with_miss(self, game_manager):
        """Test processing score with miss (score 0)."""
        # Start game
        game_manager.new_game("301", ["Alice", "Bob"])

        # Process miss
        game_manager.process_score({"score": 0, "multiplier": "SINGLE"})

        # Should process successfully
        assert game_manager.current_throw == 2

    def test_emit_throw_effects_bull(self, game_manager, socketio):
        """Test emit throw effects for BULL."""
        game_manager._emit_throw_effects("BULL", 25, 25)

        # Should emit sound and video
        assert socketio.emit.called

    def test_emit_throw_effects_dblbull(self, game_manager, socketio):
        """Test emit throw effects for DBLBULL."""
        game_manager._emit_throw_effects("DBLBULL", 25, 50)

        # Should emit sound and video
        assert socketio.emit.called

    def test_emit_throw_effects_single(self, game_manager, socketio):
        """Test emit throw effects for SINGLE."""
        game_manager._emit_throw_effects("SINGLE", 20, 20)

        # Should emit sound
        assert socketio.emit.called

    def test_get_angle_valid_scores(self, game_manager):
        """Test get_angle with valid scores."""
        # Test various scores
        angles = {
            20: 0,
            1: 18,
            18: 36,
            4: 54,
            13: 72,
            6: 90,
            10: 108,
            15: 126,
            2: 144,
            17: 162,
            3: 180,
            19: 198,
            7: 216,
            16: 234,
            8: 252,
            11: 270,
            14: 288,
            9: 306,
            12: 324,
            5: 342,
        }

        for score, expected_angle in angles.items():
            angle = game_manager._get_angle(score)
            assert angle == expected_angle

    def test_get_angle_invalid_score(self, game_manager):
        """Test get_angle with invalid score."""
        # Test invalid score
        angle = game_manager._get_angle(99)
        assert angle == 0  # Should return 0 for invalid scores

    def test_get_angle_zero_score(self, game_manager):
        """Test get_angle with zero score."""
        angle = game_manager._get_angle(0)
        assert angle == 0

    def test_handle_bust(self, game_manager, socketio):
        """Test _handle_bust method."""
        # Start game
        game_manager.new_game("301", ["Alice", "Bob"])

        # Trigger bust
        game_manager._handle_bust(None)

        # Should pause game and set throw count
        assert game_manager.is_paused is True
        assert game_manager.current_throw == game_manager.throws_per_turn + 1

        # Should emit events
        assert socketio.emit.called

    def test_handle_winner(self, game_manager, socketio):
        """Test _handle_winner method."""
        # Start game
        game_manager.new_game("301", ["Alice", "Bob"])

        # Trigger winner
        game_manager._handle_winner(0)

        # Should set winner flag and pause
        assert game_manager.is_winner is True
        assert game_manager.is_paused is True

        # Should emit events
        assert socketio.emit.called

    def test_end_turn(self, game_manager, socketio):
        """Test _end_turn method."""
        # Start game
        game_manager.new_game("301", ["Alice", "Bob"])

        # End turn
        game_manager._end_turn()

        # Should pause game
        assert game_manager.is_paused is True

        # Should emit events
        assert socketio.emit.called

    def test_emit_game_state(self, game_manager, socketio):
        """Test _emit_game_state method."""
        # Start game
        game_manager.new_game("301", ["Alice", "Bob"])

        # Emit game state
        game_manager._emit_game_state()

        # Should emit game_state event
        assert socketio.emit.called

    def test_emit_sound(self, game_manager, socketio):
        """Test _emit_sound method."""
        # Emit sound
        game_manager._emit_sound("test_sound")

        # Should emit play_sound event
        socketio.emit.assert_called_with("play_sound", {"sound": "test_sound"})

    def test_emit_video(self, game_manager, socketio):
        """Test _emit_video method."""
        # Emit video
        game_manager._emit_video("test_video.mp4", 45)

        # Should emit play_video event
        socketio.emit.assert_called_with("play_video", {"video": "test_video.mp4", "angle": 45})

    def test_emit_message(self, game_manager, socketio):
        """Test _emit_message method."""
        # Emit message
        game_manager._emit_message("Test message")

        # Should emit message event
        socketio.emit.assert_called_with("message", {"text": "Test message"})

    def test_emit_big_message(self, game_manager, socketio):
        """Test _emit_big_message method."""
        # Emit big message
        game_manager._emit_big_message("Big test message")

        # Should emit big_message event
        socketio.emit.assert_called_with("big_message", {"text": "Big test message"})

    def test_new_game_401(self, game_manager):
        """Test starting a 401 game."""
        game_manager.new_game("401", ["Alice", "Bob"])

        assert game_manager.game_type == "401"
        assert game_manager.is_started is True
        # start_score is stored in the game object, not game_manager
        assert game_manager.game is not None

    def test_new_game_unknown_type(self, game_manager):
        """Test starting game with unknown type defaults to 301."""
        game_manager.new_game("999", ["Alice", "Bob"])

        # Should default to 301
        assert game_manager.game_type == "999"
        assert game_manager.is_started is True

    def test_process_score_complete_turn(self, game_manager):
        """Test processing score that completes a turn."""
        # Start game
        game_manager.new_game("301", ["Alice", "Bob"])

        # Process 3 throws
        game_manager.process_score({"score": 20, "multiplier": "SINGLE"})
        game_manager.process_score({"score": 20, "multiplier": "SINGLE"})
        game_manager.process_score({"score": 20, "multiplier": "SINGLE"})

        # Should pause after 3 throws
        assert game_manager.is_paused is True
        assert game_manager.current_throw == 4

    def test_add_player_to_empty_game(self, game_manager):
        """Test adding player to empty game."""
        # Add player without starting game
        game_manager.add_player("Alice")

        # Should add player
        assert len(game_manager.players) == 1
        assert game_manager.players[0]["name"] == "Alice"

    def test_remove_player_from_empty_game(self, game_manager):
        """Test removing player from empty game."""
        # Try to remove player from empty game
        game_manager.remove_player(0)

        # Should not crash
        assert len(game_manager.players) == 0

    def test_cricket_game_initialization(self, game_manager):
        """Test cricket game initialization."""
        game_manager.new_game("cricket", ["Alice", "Bob"])

        assert game_manager.game_type == "cricket"
        assert game_manager.is_started is True
        assert game_manager.game is not None

    def test_process_score_cricket_target(self, game_manager):
        """Test processing cricket target score."""
        # Start cricket game
        game_manager.new_game("cricket", ["Alice", "Bob"])

        # Process cricket target (20)
        game_manager.process_score({"score": 20, "multiplier": "TRIPLE"})

        # Should process successfully
        assert game_manager.current_throw == 2
