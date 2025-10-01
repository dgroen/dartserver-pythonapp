"""Unit tests for GameCricket class."""

from games.game_cricket import GameCricket


class TestGameCricket:
    """Test cases for GameCricket class."""

    def test_initialization(self, sample_players):
        """Test game initialization."""
        game = GameCricket(sample_players)
        assert len(game.players) == 2
        assert game.players[0]["score"] == 0
        assert game.players[1]["score"] == 0
        assert game.players[0]["is_turn"] is True
        assert game.players[1]["is_turn"] is False
        # Check targets are initialized
        for target in GameCricket.CRICKET_TARGETS:
            assert target in game.players[0]["targets"]
            assert game.players[0]["targets"][target]["hits"] == 0

    def test_cricket_targets(self):
        """Test cricket targets are correct."""
        assert GameCricket.CRICKET_TARGETS == [15, 16, 17, 18, 19, 20, 25]

    def test_add_player(self, sample_players):
        """Test adding a player."""
        game = GameCricket(sample_players)
        new_player = {"id": 2, "name": "Player 3"}
        game.add_player(new_player)
        assert len(game.players) == 3
        assert game.players[2]["name"] == "Player 3"
        assert game.players[2]["score"] == 0

    def test_add_player_max_limit(self, sample_players_four):
        """Test adding player beyond max limit."""
        game = GameCricket(sample_players_four)
        assert len(game.players) == 4
        # Try to add 5th player
        game.add_player({"id": 4, "name": "Player 5"})
        assert len(game.players) == 4  # Should still be 4

    def test_remove_player(self, sample_players):
        """Test removing a player."""
        game = GameCricket(sample_players)
        game.add_player({"id": 2, "name": "Player 3"})
        game.remove_player(1)
        assert len(game.players) == 2

    def test_process_throw_single_hit(self, sample_players):
        """Test processing a single hit."""
        game = GameCricket(sample_players)
        result = game.process_throw(0, 20, 1, "SINGLE")
        assert result["target"] == 20
        assert result["hits"] == 1
        assert result["opened"] is False
        assert result["winner"] is False
        assert game.players[0]["targets"][20]["hits"] == 1

    def test_process_throw_double_hit(self, sample_players):
        """Test processing a double hit."""
        game = GameCricket(sample_players)
        result = game.process_throw(0, 20, 2, "DOUBLE")
        assert result["hits"] == 2
        assert game.players[0]["targets"][20]["hits"] == 2

    def test_process_throw_triple_hit(self, sample_players):
        """Test processing a triple hit."""
        game = GameCricket(sample_players)
        result = game.process_throw(0, 20, 3, "TRIPLE")
        assert result["hits"] == 3
        assert result["opened"] is True
        assert game.players[0]["targets"][20]["hits"] == 3
        assert game.players[0]["targets"][20]["status"] == 1

    def test_process_throw_non_cricket_target(self, sample_players):
        """Test processing throw on non-cricket target."""
        game = GameCricket(sample_players)
        result = game.process_throw(0, 10, 1, "SINGLE")
        assert result["target"] == 10
        assert result["points_scored"] == 0

    def test_scoring_after_opening(self, sample_players):
        """Test scoring points after opening a target."""
        game = GameCricket(sample_players)
        # Open target 20 with triple
        game.process_throw(0, 20, 3, "TRIPLE")
        # Hit again to score points
        result = game.process_throw(0, 20, 1, "SINGLE")
        assert result["points_scored"] == 20
        assert game.players[0]["score"] == 20

    def test_closing_target_for_all(self, sample_players):
        """Test closing a target when all players open it."""
        game = GameCricket(sample_players)
        # Player 0 opens 20
        game.process_throw(0, 20, 3, "TRIPLE")
        # Player 1 opens 20
        result = game.process_throw(1, 20, 3, "TRIPLE")
        assert result["closed"] is True
        # Check status is 2 (closed for all)
        assert game.players[0]["targets"][20]["status"] == 2
        assert game.players[1]["targets"][20]["status"] == 2

    def test_no_scoring_on_closed_target(self, sample_players):
        """Test that no points are scored on closed targets."""
        game = GameCricket(sample_players)
        # Both players open 20
        game.process_throw(0, 20, 3, "TRIPLE")
        game.process_throw(1, 20, 3, "TRIPLE")
        # Try to score on closed target
        result = game.process_throw(0, 20, 1, "SINGLE")
        assert result["points_scored"] == 0

    def test_winner_detection(self, sample_players):
        """Test winner detection."""
        game = GameCricket(sample_players)
        # Player 0 opens all targets
        for target in GameCricket.CRICKET_TARGETS:
            result = game.process_throw(0, target, 3, "TRIPLE")
        # Last target should trigger winner
        assert result["winner"] is True

    def test_winner_with_highest_score(self, sample_players):
        """Test winner must have highest score."""
        game = GameCricket(sample_players)
        # Player 0 opens 20 and scores
        game.process_throw(0, 20, 3, "TRIPLE")
        game.process_throw(0, 20, 2, "DOUBLE")  # Score 40 points
        # Player 1 opens 20
        game.process_throw(1, 20, 3, "TRIPLE")
        # Player 0 opens remaining targets
        for target in [15, 16, 17, 18, 19, 25]:
            game.process_throw(0, target, 3, "TRIPLE")
        # Player 0 should win with higher score
        assert game.players[0]["score"] == 40

    def test_get_player_score(self, sample_players):
        """Test getting player score."""
        game = GameCricket(sample_players)
        assert game.get_player_score(0) == 0
        assert game.get_player_score(1) == 0
        assert game.get_player_score(5) == 0  # Invalid player

    def test_get_state(self, sample_players):
        """Test getting game state."""
        game = GameCricket(sample_players)
        state = game.get_state()
        assert state["type"] == "cricket"
        assert state["targets"] == GameCricket.CRICKET_TARGETS
        assert len(state["players"]) == 2

    def test_reset(self, sample_players):
        """Test resetting the game."""
        game = GameCricket(sample_players)
        # Play some throws
        game.process_throw(0, 20, 3, "TRIPLE")
        game.process_throw(0, 20, 2, "DOUBLE")
        # Reset
        game.reset()
        assert game.players[0]["score"] == 0
        assert game.players[0]["targets"][20]["hits"] == 0
        assert game.players[0]["targets"][20]["status"] == 0

    def test_invalid_player_id(self, sample_players):
        """Test processing throw with invalid player ID."""
        game = GameCricket(sample_players)
        result = game.process_throw(5, 20, 1, "SINGLE")
        assert "error" in result

    def test_bull_target(self, sample_players):
        """Test hitting bull (25)."""
        game = GameCricket(sample_players)
        result = game.process_throw(0, 25, 1, "BULL")
        assert result["target"] == 25
        assert game.players[0]["targets"][25]["hits"] == 1

    def test_double_bull_target(self, sample_players):
        """Test hitting double bull."""
        game = GameCricket(sample_players)
        result = game.process_throw(0, 25, 2, "DBLBULL")
        assert result["target"] == 25
        assert game.players[0]["targets"][25]["hits"] == 2

    def test_progressive_opening(self, sample_players):
        """Test progressive opening of a target."""
        game = GameCricket(sample_players)
        # First hit
        result1 = game.process_throw(0, 20, 1, "SINGLE")
        assert result1["opened"] is False
        assert game.players[0]["targets"][20]["hits"] == 1
        # Second hit
        result2 = game.process_throw(0, 20, 1, "SINGLE")
        assert result2["opened"] is False
        assert game.players[0]["targets"][20]["hits"] == 2
        # Third hit - should open
        result3 = game.process_throw(0, 20, 1, "SINGLE")
        assert result3["opened"] is True
        assert game.players[0]["targets"][20]["hits"] == 3
        assert game.players[0]["targets"][20]["status"] == 1

    def test_scoring_multiple_hits_after_opening(self, sample_players):
        """Test scoring multiple points after opening."""
        game = GameCricket(sample_players)
        # Open 20
        game.process_throw(0, 20, 3, "TRIPLE")
        # Hit triple again (should score 3 x 20 = 60)
        result = game.process_throw(0, 20, 3, "TRIPLE")
        assert result["points_scored"] == 60
        assert game.players[0]["score"] == 60
