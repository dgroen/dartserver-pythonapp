"""Unit tests for 170 game type and Bull Practice game."""


from src.games.game_301 import Game301
from src.games.game_bull_practice import GameBullPractice


class TestGame170:
    """Test cases for 170 game type (using Game301 class)."""

    def test_initialization_170(self, sample_players):
        """Test game initialization with 170 score."""
        game = Game301(sample_players, start_score=170)
        assert game.start_score == 170
        assert len(game.players) == 2
        assert game.players[0]["score"] == 170
        assert game.players[1]["score"] == 170
        assert game.players[0]["is_turn"] is True
        assert game.players[1]["is_turn"] is False

    def test_process_throw_170(self, sample_players):
        """Test processing a throw in 170 game."""
        game = Game301(sample_players, start_score=170)
        result = game.process_throw(0, 20, 3, "TRIPLE")
        assert result["score"] == 60
        assert result["new_total"] == 110
        assert result["bust"] is False
        assert result["winner"] is False

    def test_winner_170(self, sample_players):
        """Test winner detection in 170 game."""
        game = Game301(sample_players, start_score=170)
        # Set player score to 60
        game.players[0]["score"] = 60
        # Score exactly 60 to win
        result = game.process_throw(0, 20, 3, "TRIPLE")
        assert result["winner"] is True
        assert result["new_total"] == 0
        assert game.players[0]["score"] == 0


class TestGameBullPractice:
    """Test cases for Bull Practice game."""

    def test_initialization(self, sample_players):
        """Test game initialization."""
        game = GameBullPractice(sample_players)
        assert len(game.players) == 2
        assert game.players[0]["score"] == 0
        assert game.players[0]["current_turn_bull_hits"] == 0
        assert game.players[0]["current_turn_score"] == 0
        assert game.players[0]["throws_in_turn"] == 0
        assert game.players[0]["game_ended"] is False
        assert game.players[0]["is_turn"] is True
        assert game.players[1]["is_turn"] is False

    def test_single_player(self):
        """Test with single player (typical training mode)."""
        players = [{"id": 0, "name": "Player 1"}]
        game = GameBullPractice(players)
        assert len(game.players) == 1
        assert game.players[0]["is_turn"] is True

    def test_process_bull_hit(self):
        """Test processing a bull hit."""
        players = [{"id": 0, "name": "Player 1"}]
        game = GameBullPractice(players)

        # Hit a single bull (25 points)
        result = game.process_throw(0, 25, "BULL")
        assert result["bull_hit"] is True
        assert result["score_added"] == 25
        assert result["current_turn_score"] == 25
        assert result["game_ended"] is False
        assert game.players[0]["current_turn_bull_hits"] == 1

    def test_process_double_bull_hit(self):
        """Test processing a double bull hit."""
        players = [{"id": 0, "name": "Player 1"}]
        game = GameBullPractice(players)

        # Hit a double bull (50 points)
        result = game.process_throw(0, 25, "DBLBULL")
        assert result["bull_hit"] is True
        assert result["score_added"] == 50
        assert result["current_turn_score"] == 50
        assert result["game_ended"] is False

    def test_process_non_bull_hit(self):
        """Test processing a non-bull hit."""
        players = [{"id": 0, "name": "Player 1"}]
        game = GameBullPractice(players)

        # Hit 20 (not a bull)
        result = game.process_throw(0, 20, "SINGLE")
        assert result["bull_hit"] is False
        assert result["score_added"] == 0
        assert result["current_turn_score"] == 0
        assert result["game_ended"] is False

    def test_turn_with_bulls(self):
        """Test a complete turn with bull hits."""
        players = [{"id": 0, "name": "Player 1"}]
        game = GameBullPractice(players)

        # First throw: bull (25)
        result1 = game.process_throw(0, 25, "BULL")
        assert result1["current_turn_score"] == 25
        assert result1["game_ended"] is False

        # Second throw: double bull (50)
        result2 = game.process_throw(0, 25, "DBLBULL")
        assert result2["current_turn_score"] == 75
        assert result2["game_ended"] is False

        # Third throw: bull (25)
        result3 = game.process_throw(0, 25, "BULL")
        assert result3["current_turn_score"] == 100
        assert result3["total_score"] == 100  # Turn complete, score added
        assert result3["game_ended"] is False
        assert game.players[0]["score"] == 100
        assert game.players[0]["throws_in_turn"] == 0  # Reset for next turn

    def test_turn_without_bulls_ends_game(self):
        """Test that a turn without bulls ends the game."""
        players = [{"id": 0, "name": "Player 1"}]
        game = GameBullPractice(players)

        # First turn with bulls
        game.process_throw(0, 25, "BULL")
        game.process_throw(0, 25, "BULL")
        game.process_throw(0, 25, "BULL")
        assert game.players[0]["score"] == 75

        # Second turn without bulls
        result1 = game.process_throw(0, 20, "SINGLE")
        assert result1["game_ended"] is False

        result2 = game.process_throw(0, 20, "DOUBLE")
        assert result2["game_ended"] is False

        result3 = game.process_throw(0, 20, "TRIPLE")
        assert result3["game_ended"] is True
        assert result3["auto_restart"] is True
        assert result3["total_score"] == 75  # Score from first turn only

    def test_mixed_turn_with_some_bulls(self):
        """Test a turn with both bull hits and misses."""
        players = [{"id": 0, "name": "Player 1"}]
        game = GameBullPractice(players)

        # First throw: bull (25)
        result1 = game.process_throw(0, 25, "BULL")
        assert result1["current_turn_score"] == 25

        # Second throw: miss (20)
        result2 = game.process_throw(0, 20, "SINGLE")
        assert result2["current_turn_score"] == 25  # Still has first bull

        # Third throw: double bull (50)
        result3 = game.process_throw(0, 25, "DBLBULL")
        assert result3["current_turn_score"] == 75
        assert result3["total_score"] == 75
        assert result3["game_ended"] is False
        assert game.players[0]["score"] == 75

    def test_restart_game(self):
        """Test restarting the game."""
        players = [{"id": 0, "name": "Player 1"}]
        game = GameBullPractice(players)

        # Play a turn
        game.process_throw(0, 25, "BULL")
        game.process_throw(0, 25, "BULL")
        game.process_throw(0, 25, "BULL")
        assert game.players[0]["score"] == 75

        # End game
        game.process_throw(0, 20, "SINGLE")
        game.process_throw(0, 20, "SINGLE")
        game.process_throw(0, 20, "SINGLE")
        assert game.players[0]["game_ended"] is True

        # Restart
        game.restart_game(0)
        assert game.players[0]["score"] == 0
        assert game.players[0]["current_turn_bull_hits"] == 0
        assert game.players[0]["current_turn_score"] == 0
        assert game.players[0]["throws_in_turn"] == 0
        assert game.players[0]["game_ended"] is False

    def test_get_player_score(self):
        """Test getting player score."""
        players = [{"id": 0, "name": "Player 1"}]
        game = GameBullPractice(players)

        assert game.get_player_score(0) == 0

        # Add some score
        game.process_throw(0, 25, "BULL")
        game.process_throw(0, 25, "BULL")
        game.process_throw(0, 25, "BULL")

        assert game.get_player_score(0) == 75

    def test_get_state(self):
        """Test getting game state."""
        players = [{"id": 0, "name": "Player 1"}]
        game = GameBullPractice(players)

        state = game.get_state()
        assert state["type"] == "bull_practice"
        assert len(state["players"]) == 1

    def test_reset(self):
        """Test resetting the game."""
        players = [{"id": 0, "name": "Player 1"}]
        game = GameBullPractice(players)

        # Play a turn
        game.process_throw(0, 25, "BULL")
        game.process_throw(0, 25, "BULL")
        game.process_throw(0, 25, "BULL")

        # Reset
        game.reset()
        assert game.players[0]["score"] == 0
        assert game.players[0]["current_turn_bull_hits"] == 0
        assert game.players[0]["current_turn_score"] == 0
        assert game.players[0]["throws_in_turn"] == 0
        assert game.players[0]["game_ended"] is False

    def test_add_player(self):
        """Test adding a player."""
        players = [{"id": 0, "name": "Player 1"}]
        game = GameBullPractice(players)

        new_player = {"id": 1, "name": "Player 2"}
        game.add_player(new_player)

        assert len(game.players) == 2
        assert game.players[1]["name"] == "Player 2"
        assert game.players[1]["score"] == 0

    def test_remove_player(self):
        """Test removing a player."""
        players = [{"id": 0, "name": "Player 1"}, {"id": 1, "name": "Player 2"}]
        game = GameBullPractice(players)

        game.remove_player(1)
        assert len(game.players) == 1
        assert game.players[0]["name"] == "Player 1"
