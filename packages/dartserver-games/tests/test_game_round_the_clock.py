"""Unit tests for GameRoundTheClock class."""

from dartserver_games import GameRoundTheClock


class TestGameRoundTheClock:
    """Test cases for GameRoundTheClock class."""

    def test_initialization(self, sample_players):
        """Test game initialization."""
        game = GameRoundTheClock(sample_players)
        assert len(game.players) == 2
        assert game.players[0]["current_target"] == 20
        assert game.players[1]["current_target"] == 20
        assert game.players[0]["is_turn"] is True
        assert game.players[1]["is_turn"] is False
        assert game.players[0]["bull_hits"] == 0

    def test_add_player(self, sample_players):
        """Test adding a player."""
        game = GameRoundTheClock(sample_players)
        new_player = {"id": 2, "name": "Player 3"}
        game.add_player(new_player)
        assert len(game.players) == 3
        assert game.players[2]["name"] == "Player 3"
        assert game.players[2]["current_target"] == 20

    def test_remove_player(self, sample_players):
        """Test removing a player."""
        game = GameRoundTheClock(sample_players)
        game.add_player({"id": 2, "name": "Player 3"})
        game.remove_player(1)
        assert len(game.players) == 2

    def test_single_hit_advances_by_one(self, sample_players):
        """Test that hitting target with single advances by 1."""
        game = GameRoundTheClock(sample_players)
        result = game.process_throw(0, 20, "SINGLE")
        assert result["hit"] is True
        assert result["current_target"] == 20
        assert result["new_target"] == 19
        assert result["skipped"] == 0
        assert game.players[0]["current_target"] == 19

    def test_double_hit_skips_one(self, sample_players):
        """Test that hitting target with double skips 1 number."""
        game = GameRoundTheClock(sample_players)
        result = game.process_throw(0, 20, "DOUBLE")
        assert result["hit"] is True
        assert result["current_target"] == 20
        assert result["new_target"] == 18  # Skip 19
        assert result["skipped"] == 1
        assert game.players[0]["current_target"] == 18

    def test_triple_hit_skips_two(self, sample_players):
        """Test that hitting target with triple skips 2 numbers."""
        game = GameRoundTheClock(sample_players)
        result = game.process_throw(0, 20, "TRIPLE")
        assert result["hit"] is True
        assert result["current_target"] == 20
        assert result["new_target"] == 17  # Skip 19 and 18
        assert result["skipped"] == 2
        assert game.players[0]["current_target"] == 17

    def test_miss_does_not_advance(self, sample_players):
        """Test that missing target does not advance."""
        game = GameRoundTheClock(sample_players)
        result = game.process_throw(0, 19, "SINGLE")  # Hit 19 instead of 20
        assert result["hit"] is False
        assert result["current_target"] == 20
        assert result["new_target"] == 20
        assert game.players[0]["current_target"] == 20

    def test_sequence_progression(self, sample_players):
        """Test full sequence progression from 20 to 1."""
        game = GameRoundTheClock(sample_players)
        # Hit 20, 19, 18, 17... down to 1
        for expected_target in range(20, 0, -1):
            assert game.players[0]["current_target"] == expected_target
            result = game.process_throw(0, expected_target, "SINGLE")
            assert result["hit"] is True
        # After hitting 1, should be at target 0 (ready for bull)
        assert game.players[0]["current_target"] == 0

    def test_double_bull_wins(self, sample_players):
        """Test that double bull wins after completing sequence."""
        game = GameRoundTheClock(sample_players)
        # Complete the sequence
        for target in range(20, 0, -1):
            game.process_throw(0, target, "SINGLE")
        # Hit double bull
        result = game.process_throw(0, 25, "DBLBULL")
        assert result["hit"] is True
        assert result["winner"] is True

    def test_five_single_bulls_wins(self, sample_players):
        """Test that 5 single bulls win after completing sequence."""
        game = GameRoundTheClock(sample_players)
        # Complete the sequence
        for target in range(20, 0, -1):
            game.process_throw(0, target, "SINGLE")
        # Hit 4 single bulls - should not win yet
        for i in range(4):
            result = game.process_throw(0, 25, "BULL")
            assert result["hit"] is True
            assert result["winner"] is False
            assert result["bull_hits"] == i + 1
        # Hit 5th single bull - should win
        result = game.process_throw(0, 25, "BULL")
        assert result["hit"] is True
        assert result["winner"] is True
        assert result["bull_hits"] == 5

    def test_bull_before_sequence_complete_does_not_count(self, sample_players):
        """Test that hitting bull before completing sequence doesn't count."""
        game = GameRoundTheClock(sample_players)
        # Still at target 20
        result = game.process_throw(0, 25, "BULL")
        assert result["hit"] is False
        assert result["winner"] is False
        assert game.players[0]["current_target"] == 20

    def test_bull_hits_reset_on_target_advance(self, sample_players):
        """Test that bull hits reset when advancing to new target."""
        game = GameRoundTheClock(sample_players)
        # Complete sequence
        for target in range(20, 0, -1):
            game.process_throw(0, target, "SINGLE")
        # Hit 2 bulls
        game.process_throw(0, 25, "BULL")
        game.process_throw(0, 25, "BULL")
        assert game.players[0]["bull_hits"] == 2
        # This shouldn't happen in normal game, but test the reset logic
        # by manually setting target back
        game.players[0]["current_target"] = 1
        game.process_throw(0, 1, "SINGLE")
        assert game.players[0]["bull_hits"] == 0

    def test_multi_player_independent_progress(self, sample_players):
        """Test that multiple players have independent progress."""
        game = GameRoundTheClock(sample_players)
        # Player 0 hits 20
        game.process_throw(0, 20, "SINGLE")
        assert game.players[0]["current_target"] == 19
        assert game.players[1]["current_target"] == 20  # Still at 20
        # Player 1 hits 20 with double
        game.process_throw(1, 20, "DOUBLE")
        assert game.players[0]["current_target"] == 19
        assert game.players[1]["current_target"] == 18  # Skipped 19

    def test_target_does_not_go_below_zero(self, sample_players):
        """Test that target stops at 0."""
        game = GameRoundTheClock(sample_players)
        # Manually set to target 2
        game.players[0]["current_target"] = 2
        # Hit with triple (would try to go to -1)
        result = game.process_throw(0, 2, "TRIPLE")
        assert result["hit"] is True
        assert game.players[0]["current_target"] == 0  # Stops at 0, not negative

    def test_invalid_player_id(self, sample_players):
        """Test processing throw with invalid player ID."""
        game = GameRoundTheClock(sample_players)
        result = game.process_throw(5, 20, "SINGLE")
        assert "error" in result

    def test_get_player_score(self, sample_players):
        """Test getting player score (current target)."""
        game = GameRoundTheClock(sample_players)
        assert game.get_player_score(0) == 20
        game.process_throw(0, 20, "SINGLE")
        assert game.get_player_score(0) == 19
        assert game.get_player_score(5) == 20  # Invalid player returns 20

    def test_get_state(self, sample_players):
        """Test getting game state."""
        game = GameRoundTheClock(sample_players)
        state = game.get_state()
        assert state["type"] == "round_the_clock"
        assert len(state["players"]) == 2

    def test_reset(self, sample_players):
        """Test resetting the game."""
        game = GameRoundTheClock(sample_players)
        # Play some throws
        game.process_throw(0, 20, "TRIPLE")
        game.process_throw(0, 17, "DOUBLE")
        # Reset
        game.reset()
        assert game.players[0]["current_target"] == 20
        assert game.players[0]["bull_hits"] == 0

    def test_set_current_player(self, sample_players):
        """Test setting current player."""
        game = GameRoundTheClock(sample_players)
        assert game.players[0]["is_turn"] is True
        assert game.players[1]["is_turn"] is False
        game.set_current_player(1)
        assert game.players[0]["is_turn"] is False
        assert game.players[1]["is_turn"] is True

    def test_process_score_wrapper(self, sample_players):
        """Test process_score wrapper function."""
        game = GameRoundTheClock(sample_players)
        # Player 0 is current
        result = game.process_score(20, "DOUBLE")
        assert result["hit"] is True
        assert result["new_target"] == 18

    def test_complete_game_scenario(self, sample_players):
        """Test a complete game scenario with winner."""
        game = GameRoundTheClock(sample_players)
        # Player 0 completes sequence with mix of singles, doubles, and triples
        game.process_throw(0, 20, "TRIPLE")  # 20 -> 17
        assert game.players[0]["current_target"] == 17

        game.process_throw(0, 17, "DOUBLE")  # 17 -> 15
        assert game.players[0]["current_target"] == 15

        # Continue with singles
        for target in range(15, 0, -1):
            game.process_throw(0, target, "SINGLE")

        assert game.players[0]["current_target"] == 0

        # Win with double bull
        result = game.process_throw(0, 25, "DBLBULL")
        assert result["winner"] is True
