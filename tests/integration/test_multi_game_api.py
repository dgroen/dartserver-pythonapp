"""Integration tests for multi-game functionality"""

import pytest
from unittest.mock import Mock

from multi_game_manager import MultiGameManager


class TestMultiGameIntegration:
    """Integration tests for multi-game manager functionality"""

    @pytest.fixture
    def socketio_mock(self):
        """Mock SocketIO instance"""
        mock = Mock()
        mock.emit = Mock()
        return mock

    @pytest.fixture
    def multi_manager(self, socketio_mock):
        """Create a MultiGameManager instance"""
        return MultiGameManager(socketio_mock)

    def test_create_and_manage_multiple_games(self, multi_manager):
        """Test creating and managing multiple games"""
        # Create first game
        game1 = multi_manager.create_game("game-1")
        game1.new_game("301", ["Alice", "Bob"])

        # Create second game
        game2 = multi_manager.create_game("game-2")
        game2.new_game("501", ["Charlie", "Dave", "Eve"])

        # Verify both games exist
        assert len(multi_manager.list_games()) == 2

        # Verify game states
        state1 = game1.get_game_state()
        assert state1["game_type"] == "301"
        assert len(state1["players"]) == 2

        state2 = game2.get_game_state()
        assert state2["game_type"] == "501"
        assert len(state2["players"]) == 3

    def test_switch_between_games(self, multi_manager):
        """Test switching between different games"""
        # Create two games
        game1 = multi_manager.create_game("game-1")
        game1.new_game("301", ["Alice", "Bob"])

        game2 = multi_manager.create_game("game-2")
        game2.new_game("cricket", ["Charlie", "Dave"])

        # game-1 should be active (first created)
        assert multi_manager.get_active_game_id() == "game-1"

        # Switch to game-2
        multi_manager.set_active_game("game-2")
        assert multi_manager.get_active_game_id() == "game-2"

        # Verify we get the correct game
        active_game = multi_manager.get_game()
        assert active_game == game2

        # Switch back to game-1
        multi_manager.set_active_game("game-1")
        assert multi_manager.get_active_game_id() == "game-1"
        active_game = multi_manager.get_game()
        assert active_game == game1

    def test_games_maintain_independent_state(self, multi_manager):
        """Test that games maintain independent state"""
        # Create two games
        game1 = multi_manager.create_game("game-1")
        game1.new_game("301", ["Alice", "Bob"])

        game2 = multi_manager.create_game("game-2")
        game2.new_game("301", ["Charlie", "Dave"])

        # Process scores in game1
        game1.process_score({"score": 20, "multiplier": "TRIPLE"})

        # Verify game1 state changed
        state1 = game1.get_game_state()
        assert state1["current_throw"] == 2  # Should have incremented

        # Verify game2 state is unchanged
        state2 = game2.get_game_state()
        assert state2["current_throw"] == 1  # Should still be 1

    def test_delete_game_and_switch_active(self, multi_manager):
        """Test deleting a game and automatic active game switching"""
        # Create three games
        multi_manager.create_game("game-1")
        multi_manager.create_game("game-2")
        multi_manager.create_game("game-3")

        # game-1 is active
        assert multi_manager.get_active_game_id() == "game-1"

        # Delete active game
        multi_manager.delete_game("game-1")

        # Should automatically switch to another game
        assert multi_manager.get_active_game_id() in ["game-2", "game-3"]
        assert len(multi_manager.list_games()) == 2

    def test_list_games_with_details(self, multi_manager):
        """Test listing games includes all relevant details"""
        # Create games with different states
        game1 = multi_manager.create_game("game-1")
        game1.new_game("301", ["Alice", "Bob"])

        game2 = multi_manager.create_game("game-2")
        # Don't start game2

        game3 = multi_manager.create_game("game-3")
        game3.new_game("cricket", ["Charlie", "Dave", "Eve", "Frank"])

        # Get games list
        games_list = multi_manager.list_games()

        assert len(games_list) == 3

        # Find each game in list
        game1_info = next(g for g in games_list if g["game_id"] == "game-1")
        game2_info = next(g for g in games_list if g["game_id"] == "game-2")
        game3_info = next(g for g in games_list if g["game_id"] == "game-3")

        # Verify game-1
        assert game1_info["game_type"] == "301"
        assert game1_info["is_started"] is True
        assert game1_info["is_active"] is True  # First created
        assert game1_info["player_count"] == 2
        assert game1_info["players"] == ["Alice", "Bob"]

        # Verify game-2
        assert game2_info["is_started"] is False
        assert game2_info["is_active"] is False

        # Verify game-3
        assert game3_info["game_type"] == "cricket"
        assert game3_info["is_started"] is True
        assert game3_info["player_count"] == 4
        assert game3_info["players"] == ["Charlie", "Dave", "Eve", "Frank"]

    def test_concurrent_gameplay(self, multi_manager):
        """Test that multiple games can have gameplay simultaneously"""
        # Create two games
        game1 = multi_manager.create_game("game-1")
        game1.new_game("301", ["Alice", "Bob"])

        game2 = multi_manager.create_game("game-2")
        game2.new_game("301", ["Charlie", "Dave"])

        # Play in game1
        game1.process_score({"score": 20, "multiplier": "TRIPLE"})
        game1.process_score({"score": 19, "multiplier": "SINGLE"})

        # Play in game2
        game2.process_score({"score": 15, "multiplier": "DOUBLE"})

        # Verify independent scores
        state1 = game1.get_game_state()
        state2 = game2.get_game_state()

        # Game 1: Alice should have score 301 - 60 - 19 = 222
        game1_players = state1["game_data"]["players"]
        assert game1_players[0]["score"] == 222

        # Game 2: Charlie should have score 301 - 30 = 271
        game2_players = state2["game_data"]["players"]
        assert game2_players[0]["score"] == 271

        # Both games should have different throw counts
        assert state1["current_throw"] == 3
        assert state2["current_throw"] == 2

