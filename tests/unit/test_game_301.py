"""Unit tests for Game301 class."""

from games.game_301 import Game301


class TestGame301:
    """Test cases for Game301 class."""

    def test_initialization_default(self, sample_players):
        """Test game initialization with default score."""
        game = Game301(sample_players)
        assert game.start_score == 301
        assert len(game.players) == 2
        assert game.players[0]["score"] == 301
        assert game.players[1]["score"] == 301
        assert game.players[0]["is_turn"] is True
        assert game.players[1]["is_turn"] is False

    def test_initialization_custom_score(self, sample_players):
        """Test game initialization with custom score."""
        game = Game301(sample_players, start_score=501)
        assert game.start_score == 501
        assert game.players[0]["score"] == 501
        assert game.players[1]["score"] == 501

    def test_add_player(self, sample_players):
        """Test adding a player."""
        game = Game301(sample_players)
        new_player = {"id": 2, "name": "Player 3"}
        game.add_player(new_player)
        assert len(game.players) == 3
        assert game.players[2]["name"] == "Player 3"
        assert game.players[2]["score"] == 301

    def test_remove_player(self, sample_players):
        """Test removing a player."""
        game = Game301(sample_players)
        game.add_player({"id": 2, "name": "Player 3"})
        game.remove_player(1)
        assert len(game.players) == 2
        assert game.players[0]["id"] == 0
        assert game.players[1]["id"] == 1

    def test_process_throw_single(self, sample_players):
        """Test processing a single throw."""
        game = Game301(sample_players)
        result = game.process_throw(0, 20, 1, "SINGLE")
        assert result["score"] == 20
        assert result["new_total"] == 281
        assert result["bust"] is False
        assert result["winner"] is False

    def test_process_throw_double(self, sample_players):
        """Test processing a double throw."""
        game = Game301(sample_players)
        result = game.process_throw(0, 20, 2, "DOUBLE")
        assert result["score"] == 40
        assert result["new_total"] == 261
        assert result["bust"] is False
        assert result["winner"] is False

    def test_process_throw_triple(self, sample_players):
        """Test processing a triple throw."""
        game = Game301(sample_players)
        result = game.process_throw(0, 20, 3, "TRIPLE")
        assert result["score"] == 60
        assert result["new_total"] == 241
        assert result["bust"] is False
        assert result["winner"] is False

    def test_process_throw_bust(self, sample_players):
        """Test bust detection."""
        game = Game301(sample_players)
        # Set player score to 50
        game.players[0]["score"] = 50
        # Try to score 60 (would go to -10)
        result = game.process_throw(0, 20, 3, "TRIPLE")
        assert result["bust"] is True
        assert result["new_total"] == 50  # Score should remain unchanged
        assert game.players[0]["score"] == 50

    def test_process_throw_winner(self, sample_players):
        """Test winner detection."""
        game = Game301(sample_players)
        # Set player score to 60
        game.players[0]["score"] = 60
        # Score exactly 60 to win
        result = game.process_throw(0, 20, 3, "TRIPLE")
        assert result["winner"] is True
        assert result["new_total"] == 0
        assert game.players[0]["score"] == 0

    def test_process_throw_invalid_player(self, sample_players):
        """Test processing throw with invalid player ID."""
        game = Game301(sample_players)
        result = game.process_throw(5, 20, 1, "SINGLE")
        assert "error" in result

    def test_get_player_score(self, sample_players):
        """Test getting player score."""
        game = Game301(sample_players)
        assert game.get_player_score(0) == 301
        assert game.get_player_score(1) == 301
        assert game.get_player_score(5) == 0  # Invalid player

    def test_get_state(self, sample_players):
        """Test getting game state."""
        game = Game301(sample_players)
        state = game.get_state()
        assert state["type"] == "301"
        assert state["start_score"] == 301
        assert len(state["players"]) == 2

    def test_reset(self, sample_players):
        """Test resetting the game."""
        game = Game301(sample_players)
        # Play some throws
        game.process_throw(0, 20, 3, "TRIPLE")
        game.process_throw(1, 15, 2, "DOUBLE")
        # Reset
        game.reset()
        assert game.players[0]["score"] == 301
        assert game.players[1]["score"] == 301

    def test_game_401(self, sample_players):
        """Test 401 game variant."""
        game = Game301(sample_players, start_score=401)
        assert game.start_score == 401
        assert game.players[0]["score"] == 401

    def test_game_501(self, sample_players):
        """Test 501 game variant."""
        game = Game301(sample_players, start_score=501)
        assert game.start_score == 501
        assert game.players[0]["score"] == 501

    def test_multiple_throws_sequence(self, sample_players):
        """Test a sequence of multiple throws."""
        game = Game301(sample_players)
        # Player 0 throws
        result1 = game.process_throw(0, 20, 3, "TRIPLE")  # 301 - 60 = 241
        assert result1["new_total"] == 241
        result2 = game.process_throw(0, 19, 3, "TRIPLE")  # 241 - 57 = 184
        assert result2["new_total"] == 184
        result3 = game.process_throw(0, 18, 3, "TRIPLE")  # 184 - 54 = 130
        assert result3["new_total"] == 130
        assert game.players[0]["score"] == 130

    def test_exact_finish(self, sample_players):
        """Test exact finish scenarios."""
        game = Game301(sample_players)
        # Set score to exactly double 20
        game.players[0]["score"] = 40
        result = game.process_throw(0, 20, 2, "DOUBLE")
        assert result["winner"] is True
        assert result["new_total"] == 0

    def test_bust_on_negative_one(self, sample_players):
        """Test bust when going to -1."""
        game = Game301(sample_players)
        game.players[0]["score"] = 1
        result = game.process_throw(0, 1, 2, "DOUBLE")
        assert result["bust"] is True
        assert game.players[0]["score"] == 1

    def test_zero_score_throw(self, sample_players):
        """Test throwing zero (miss)."""
        game = Game301(sample_players)
        initial_score = game.players[0]["score"]
        result = game.process_throw(0, 0, 1, "SINGLE")
        assert result["score"] == 0
        assert result["new_total"] == initial_score
        assert game.players[0]["score"] == initial_score
