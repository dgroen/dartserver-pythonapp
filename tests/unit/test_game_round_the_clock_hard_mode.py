"""Unit tests for GameRoundTheClock hard mode (reset on miss) feature."""

from dartserver_games.game_round_the_clock import GameRoundTheClock


class TestGameRoundTheClockHardMode:
    """Test cases for Round the Clock hard mode with reset on miss."""

    def test_initialization_with_reset_on_miss(self, sample_players):
        """Test game initialization with reset_on_miss enabled."""
        game = GameRoundTheClock(sample_players, reset_on_miss=True)
        assert len(game.players) == 2
        assert game.reset_on_miss is True
        assert game.players[0]["turn_misses"] == 0
        assert game.players[1]["turn_misses"] == 0

    def test_initialization_without_reset_on_miss(self, sample_players):
        """Test game initialization with reset_on_miss disabled (default)."""
        game = GameRoundTheClock(sample_players)
        assert game.reset_on_miss is False

    def test_miss_counter_increments_on_miss(self, sample_players):
        """Test that miss counter increments when player misses target."""
        game = GameRoundTheClock(sample_players, reset_on_miss=True)
        # Player 0 is at target 20, throw 19 (miss)
        result = game.process_throw(0, 19, "SINGLE")
        assert result["hit"] is False
        assert game.players[0]["turn_misses"] == 1

    def test_miss_counter_resets_on_hit(self, sample_players):
        """Test that miss counter resets when player hits target."""
        game = GameRoundTheClock(sample_players, reset_on_miss=True)
        # Miss twice
        game.process_throw(0, 19, "SINGLE")
        game.process_throw(0, 18, "SINGLE")
        assert game.players[0]["turn_misses"] == 2
        # Hit target
        result = game.process_throw(0, 20, "SINGLE")
        assert result["hit"] is True
        assert game.players[0]["turn_misses"] == 0

    def test_reset_after_three_misses(self, sample_players):
        """Test that player resets to 20 after missing 3 darts in hard mode."""
        game = GameRoundTheClock(sample_players, reset_on_miss=True)
        # Advance player to target 15
        game.players[0]["current_target"] = 15
        # Miss 3 times
        game.process_throw(0, 20, "SINGLE")
        game.process_throw(0, 19, "SINGLE")
        game.process_throw(0, 18, "SINGLE")
        assert game.players[0]["turn_misses"] == 3
        # End turn - should trigger reset
        result = game.end_turn(0)
        assert result["reset"] is True
        assert result["message"] == "Missed target! Reset to 20"
        assert game.players[0]["current_target"] == 20
        assert game.players[0]["turn_misses"] == 0

    def test_no_reset_after_three_misses_when_disabled(self, sample_players):
        """Test that reset does not occur when hard mode is disabled."""
        game = GameRoundTheClock(sample_players, reset_on_miss=False)
        # Advance player to target 15
        game.players[0]["current_target"] = 15
        # Miss 3 times
        game.process_throw(0, 20, "SINGLE")
        game.process_throw(0, 19, "SINGLE")
        game.process_throw(0, 18, "SINGLE")
        # End turn - should NOT trigger reset
        result = game.end_turn(0)
        assert result["reset"] is False
        assert game.players[0]["current_target"] == 15  # Still at 15

    def test_no_reset_at_bull_stage(self, sample_players):
        """Test that reset does not occur when player is at bull stage."""
        game = GameRoundTheClock(sample_players, reset_on_miss=True)
        # Set player to bull stage (target 0)
        game.players[0]["current_target"] = 0
        # Miss 3 times (any non-bull throws)
        game.process_throw(0, 20, "SINGLE")
        game.process_throw(0, 19, "SINGLE")
        game.process_throw(0, 18, "SINGLE")
        # Note: misses should NOT increment at bull stage
        assert game.players[0]["turn_misses"] == 0
        # End turn - should NOT trigger reset
        result = game.end_turn(0)
        assert result["reset"] is False
        assert game.players[0]["current_target"] == 0  # Still at bull stage

    def test_partial_misses_no_reset(self, sample_players):
        """Test that reset does not occur with fewer than 3 misses."""
        game = GameRoundTheClock(sample_players, reset_on_miss=True)
        game.players[0]["current_target"] = 15
        # Miss 2 times
        game.process_throw(0, 20, "SINGLE")
        game.process_throw(0, 19, "SINGLE")
        assert game.players[0]["turn_misses"] == 2
        # End turn - should NOT trigger reset
        result = game.end_turn(0)
        assert result["reset"] is False
        assert game.players[0]["current_target"] == 15
        # Miss counter should be reset for next turn
        assert game.players[0]["turn_misses"] == 0

    def test_miss_counter_resets_between_turns(self, sample_players):
        """Test that miss counter resets when turn ends."""
        game = GameRoundTheClock(sample_players, reset_on_miss=True)
        # Miss 2 times
        game.process_throw(0, 19, "SINGLE")
        game.process_throw(0, 18, "SINGLE")
        assert game.players[0]["turn_misses"] == 2
        # End turn
        game.end_turn(0)
        # Miss counter should be reset
        assert game.players[0]["turn_misses"] == 0

    def test_reset_applies_only_to_targets_1_20(self, sample_players):
        """Test that reset only applies to numbered targets 1-20."""
        game = GameRoundTheClock(sample_players, reset_on_miss=True)
        # Test at target 20
        game.players[0]["current_target"] = 20
        game.process_throw(0, 19, "SINGLE")
        game.process_throw(0, 18, "SINGLE")
        game.process_throw(0, 17, "SINGLE")
        result = game.end_turn(0)
        assert result["reset"] is True
        assert game.players[0]["current_target"] == 20

        # Test at target 1
        game.players[0]["current_target"] = 1
        game.players[0]["turn_misses"] = 0
        game.process_throw(0, 20, "SINGLE")
        game.process_throw(0, 19, "SINGLE")
        game.process_throw(0, 18, "SINGLE")
        result = game.end_turn(0)
        assert result["reset"] is True
        assert game.players[0]["current_target"] == 20

    def test_multiple_players_independent_reset(self, sample_players):
        """Test that reset tracking is independent for each player."""
        game = GameRoundTheClock(sample_players, reset_on_miss=True)
        # Player 0 at target 15
        game.players[0]["current_target"] = 15
        # Player 1 at target 10
        game.players[1]["current_target"] = 10

        # Player 0 misses 3 times
        game.process_throw(0, 20, "SINGLE")
        game.process_throw(0, 19, "SINGLE")
        game.process_throw(0, 18, "SINGLE")
        result = game.end_turn(0)
        assert result["reset"] is True
        assert game.players[0]["current_target"] == 20

        # Player 1 should be unaffected
        assert game.players[1]["current_target"] == 10
        assert game.players[1]["turn_misses"] == 0

    def test_hit_then_miss_in_same_turn(self, sample_players):
        """Test scenario where player hits then misses in same turn."""
        game = GameRoundTheClock(sample_players, reset_on_miss=True)
        # Hit target 20
        game.process_throw(0, 20, "SINGLE")
        assert game.players[0]["current_target"] == 19
        assert game.players[0]["turn_misses"] == 0
        # Miss new target 19 twice
        game.process_throw(0, 20, "SINGLE")
        game.process_throw(0, 18, "SINGLE")
        assert game.players[0]["turn_misses"] == 2
        # End turn - should NOT reset (only 2 misses)
        result = game.end_turn(0)
        assert result["reset"] is False
        assert game.players[0]["current_target"] == 19

    def test_reset_message_included(self, sample_players):
        """Test that reset result includes appropriate message."""
        game = GameRoundTheClock(sample_players, reset_on_miss=True)
        game.players[0]["current_target"] = 10
        # Miss 3 times
        game.process_throw(0, 20, "SINGLE")
        game.process_throw(0, 19, "SINGLE")
        game.process_throw(0, 18, "SINGLE")
        result = game.end_turn(0)
        assert result["reset"] is True
        assert "message" in result
        assert "Reset to 20" in result["message"]

    def test_add_player_initializes_turn_misses(self, sample_players):
        """Test that adding a player initializes turn_misses."""
        game = GameRoundTheClock(sample_players, reset_on_miss=True)
        new_player = {"id": 2, "name": "Player 3"}
        game.add_player(new_player)
        assert game.players[2]["turn_misses"] == 0

    def test_reset_game_clears_turn_misses(self, sample_players):
        """Test that resetting the game clears turn_misses."""
        game = GameRoundTheClock(sample_players, reset_on_miss=True)
        # Set up some state
        game.players[0]["turn_misses"] = 2
        game.players[0]["current_target"] = 15
        # Reset game
        game.reset()
        assert game.players[0]["turn_misses"] == 0
        assert game.players[0]["current_target"] == 20

    def test_end_turn_invalid_player(self, sample_players):
        """Test end_turn with invalid player ID."""
        game = GameRoundTheClock(sample_players, reset_on_miss=True)
        result = game.end_turn(99)
        assert "error" in result

    def test_complete_game_scenario_with_reset(self, sample_players):
        """Test a complete game scenario with multiple resets."""
        game = GameRoundTheClock(sample_players, reset_on_miss=True)

        # Turn 1: Player hits 20
        game.process_throw(0, 20, "SINGLE")
        assert game.players[0]["current_target"] == 19
        game.end_turn(0)

        # Turn 2: Player misses all 3 at target 19 - should reset
        game.process_throw(0, 20, "SINGLE")
        game.process_throw(0, 18, "SINGLE")
        game.process_throw(0, 17, "SINGLE")
        assert game.players[0]["turn_misses"] == 3
        result = game.end_turn(0)
        assert result["reset"] is True
        assert game.players[0]["current_target"] == 20

        # Turn 3: Player tries again from 20
        result = game.process_throw(0, 20, "DOUBLE")  # Skip to 18
        assert result["hit"] is True
        assert game.players[0]["current_target"] == 18
        game.end_turn(0)

        # Continue game normally
        assert game.players[0]["turn_misses"] == 0
