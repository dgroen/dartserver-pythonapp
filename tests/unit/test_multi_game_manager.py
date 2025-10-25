"""Unit tests for MultiGameManager"""

import pytest
from unittest.mock import Mock

from multi_game_manager import MultiGameManager


class TestMultiGameManager:
    """Test cases for MultiGameManager"""

    @pytest.fixture
    def socketio_mock(self):
        """Mock SocketIO instance"""
        return Mock()

    @pytest.fixture
    def multi_manager(self, socketio_mock):
        """Create a MultiGameManager instance"""
        return MultiGameManager(socketio_mock)

    def test_initialization(self, multi_manager):
        """Test MultiGameManager initialization"""
        assert multi_manager.games == {}
        assert multi_manager.active_game_id is None

    def test_create_game(self, multi_manager):
        """Test creating a new game"""
        game = multi_manager.create_game("game-1")

        assert game is not None
        assert "game-1" in multi_manager.games
        assert multi_manager.active_game_id == "game-1"

    def test_create_duplicate_game(self, multi_manager):
        """Test creating a game with duplicate ID raises error"""
        multi_manager.create_game("game-1")

        with pytest.raises(ValueError, match="already exists"):
            multi_manager.create_game("game-1")

    def test_create_multiple_games(self, multi_manager):
        """Test creating multiple games"""
        game1 = multi_manager.create_game("game-1")
        game2 = multi_manager.create_game("game-2")
        game3 = multi_manager.create_game("game-3")

        assert len(multi_manager.games) == 3
        assert multi_manager.active_game_id == "game-1"  # First game is active
        assert game1 != game2
        assert game2 != game3

    def test_get_game_by_id(self, multi_manager):
        """Test getting a game by ID"""
        created_game = multi_manager.create_game("game-1")
        retrieved_game = multi_manager.get_game("game-1")

        assert retrieved_game == created_game

    def test_get_active_game(self, multi_manager):
        """Test getting the active game"""
        game1 = multi_manager.create_game("game-1")
        multi_manager.create_game("game-2")

        # Without ID, should return active game
        active_game = multi_manager.get_game()
        assert active_game == game1

    def test_get_nonexistent_game(self, multi_manager):
        """Test getting a nonexistent game returns None"""
        game = multi_manager.get_game("nonexistent")
        assert game is None

    def test_set_active_game(self, multi_manager):
        """Test setting the active game"""
        multi_manager.create_game("game-1")
        multi_manager.create_game("game-2")

        success = multi_manager.set_active_game("game-2")
        assert success is True
        assert multi_manager.active_game_id == "game-2"

    def test_set_active_nonexistent_game(self, multi_manager):
        """Test setting a nonexistent game as active fails"""
        multi_manager.create_game("game-1")

        success = multi_manager.set_active_game("nonexistent")
        assert success is False
        assert multi_manager.active_game_id == "game-1"  # Unchanged

    def test_delete_game(self, multi_manager):
        """Test deleting a game"""
        multi_manager.create_game("game-1")
        multi_manager.create_game("game-2")

        success = multi_manager.delete_game("game-1")
        assert success is True
        assert "game-1" not in multi_manager.games
        assert "game-2" in multi_manager.games

    def test_delete_active_game(self, multi_manager):
        """Test deleting the active game sets a new active game"""
        multi_manager.create_game("game-1")
        multi_manager.create_game("game-2")

        # game-1 is active
        assert multi_manager.active_game_id == "game-1"

        # Delete active game
        multi_manager.delete_game("game-1")

        # Should set game-2 as active
        assert multi_manager.active_game_id == "game-2"

    def test_delete_last_game(self, multi_manager):
        """Test deleting the last game clears active game"""
        multi_manager.create_game("game-1")

        multi_manager.delete_game("game-1")

        assert len(multi_manager.games) == 0
        assert multi_manager.active_game_id is None

    def test_delete_nonexistent_game(self, multi_manager):
        """Test deleting a nonexistent game returns False"""
        success = multi_manager.delete_game("nonexistent")
        assert success is False

    def test_list_games(self, multi_manager):
        """Test listing all games"""
        multi_manager.create_game("game-1")
        multi_manager.create_game("game-2")

        # Start a game on game-1
        game1 = multi_manager.get_game("game-1")
        game1.new_game("301", ["Alice", "Bob"])

        games_list = multi_manager.list_games()

        assert len(games_list) == 2
        assert any(g["game_id"] == "game-1" for g in games_list)
        assert any(g["game_id"] == "game-2" for g in games_list)

        # Check game-1 details
        game1_info = next(g for g in games_list if g["game_id"] == "game-1")
        assert game1_info["game_type"] == "301"
        assert game1_info["is_started"] is True
        assert game1_info["is_active"] is True
        assert game1_info["player_count"] == 2
        assert game1_info["players"] == ["Alice", "Bob"]

    def test_get_active_game_id(self, multi_manager):
        """Test getting the active game ID"""
        assert multi_manager.get_active_game_id() is None

        multi_manager.create_game("game-1")
        assert multi_manager.get_active_game_id() == "game-1"

        multi_manager.create_game("game-2")
        multi_manager.set_active_game("game-2")
        assert multi_manager.get_active_game_id() == "game-2"

    def test_has_game(self, multi_manager):
        """Test checking if a game exists"""
        assert multi_manager.has_game("game-1") is False

        multi_manager.create_game("game-1")
        assert multi_manager.has_game("game-1") is True

        multi_manager.delete_game("game-1")
        assert multi_manager.has_game("game-1") is False
