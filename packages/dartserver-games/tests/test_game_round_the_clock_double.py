"""Tests for Round the Clock Double game variant"""

from dartserver_games import GameRoundTheClockDouble


class TestGameRoundTheClockDouble:
    """Test suite for GameRoundTheClockDouble"""

    def test_initialization(self):
        """Test game initializes correctly"""
        players = [{"id": 0, "name": "Player 1"}, {"id": 1, "name": "Player 2"}]
        game = GameRoundTheClockDouble(players)

        assert len(game.players) == 2
        assert game.players[0]["current_target"] == 20
        assert game.players[0]["is_turn"] is True
        assert game.players[1]["is_turn"] is False

    def test_single_hit_advances_by_one(self):
        """Test single hit advances target by one"""
        players = [{"id": 0, "name": "Player 1"}]
        game = GameRoundTheClockDouble(players)

        result = game.process_throw(0, 20, 1, "SINGLE")
        assert result["hit"] is True
        assert result["new_target"] == 19

    def test_double_hit_skips_one(self):
        """Test double hit skips one number"""
        players = [{"id": 0, "name": "Player 1"}]
        game = GameRoundTheClockDouble(players)

        result = game.process_throw(0, 20, 2, "DOUBLE")
        assert result["hit"] is True
        assert result["new_target"] == 18

    def test_triple_hit_skips_two(self):
        """Test triple hit skips two numbers"""
        players = [{"id": 0, "name": "Player 1"}]
        game = GameRoundTheClockDouble(players)

        result = game.process_throw(0, 20, 3, "TRIPLE")
        assert result["hit"] is True
        assert result["new_target"] == 17

    def test_miss_does_not_advance(self):
        """Test miss does not advance target"""
        players = [{"id": 0, "name": "Player 1"}]
        game = GameRoundTheClockDouble(players)

        result = game.process_throw(0, 10, 1, "SINGLE")
        assert result["hit"] is False
        assert result["new_target"] == 20

    def test_double_bull_wins(self):
        """Test double bull wins when sequence is complete"""
        players = [{"id": 0, "name": "Player 1"}]
        game = GameRoundTheClockDouble(players)

        # Skip to target 0 (bull needed)
        game.players[0]["current_target"] = 0

        result = game.process_throw(0, 25, 2, "DBLBULL")
        assert result["hit"] is True
        assert result["winner"] is True

    def test_single_bull_not_valid(self):
        """Test single bull is NOT a valid target (key difference from base variant)"""
        players = [{"id": 0, "name": "Player 1"}]
        game = GameRoundTheClockDouble(players)

        # Skip to target 0 (bull needed)
        game.players[0]["current_target"] = 0

        result = game.process_throw(0, 25, 1, "BULL")
        assert result["hit"] is False
        assert result["winner"] is False

    def test_bull_before_sequence_complete_does_not_count(self):
        """Test bull hit doesn't count before sequence is complete"""
        players = [{"id": 0, "name": "Player 1"}]
        game = GameRoundTheClockDouble(players)

        # Current target is 20, not 0
        result = game.process_throw(0, 25, 2, "DBLBULL")
        assert result["hit"] is False

    def test_multi_player_independent_progress(self):
        """Test multiple players have independent progress"""
        players = [{"id": 0, "name": "Player 1"}, {"id": 1, "name": "Player 2"}]
        game = GameRoundTheClockDouble(players)

        # Player 1 hits 20
        game.process_throw(0, 20, 1, "SINGLE")
        # Player 2 hits 20 twice (double)
        game.process_throw(1, 20, 2, "DOUBLE")

        assert game.players[0]["current_target"] == 19
        assert game.players[1]["current_target"] == 18

    def test_target_does_not_go_below_zero(self):
        """Test target doesn't go below 0"""
        players = [{"id": 0, "name": "Player 1"}]
        game = GameRoundTheClockDouble(players)

        game.players[0]["current_target"] = 1
        result = game.process_throw(0, 1, 3, "TRIPLE")
        assert result["new_target"] == 0

    def test_sequence_progression(self):
        """Test complete sequence progression (shortened for testing)"""
        players = [{"id": 0, "name": "Player 1"}]
        game = GameRoundTheClockDouble(players)

        # Quickly progress through sequence
        targets = [20, 19, 18, 17, 16]
        for target in targets:
            result = game.process_throw(0, target, 1, "SINGLE")
            assert result["hit"] is True
            assert result["current_target"] == target

    def test_invalid_player_id(self):
        """Test handling of invalid player ID"""
        players = [{"id": 0, "name": "Player 1"}]
        game = GameRoundTheClockDouble(players)

        result = game.process_throw(5, 20, 1, "SINGLE")
        assert "error" in result

    def test_get_player_score(self):
        """Test getting player's current progress"""
        players = [{"id": 0, "name": "Player 1"}]
        game = GameRoundTheClockDouble(players)

        assert game.get_player_score(0) == 20
        game.players[0]["current_target"] = 15
        assert game.get_player_score(0) == 15

    def test_get_state(self):
        """Test getting game state"""
        players = [{"id": 0, "name": "Player 1"}]
        game = GameRoundTheClockDouble(players)

        state = game.get_state()
        assert state["type"] == "round_the_clock_double"
        assert len(state["players"]) == 1

    def test_reset(self):
        """Test resetting game"""
        players = [{"id": 0, "name": "Player 1"}]
        game = GameRoundTheClockDouble(players)

        game.players[0]["current_target"] = 5
        game.reset()
        assert game.players[0]["current_target"] == 20

    def test_set_current_player(self):
        """Test setting current player"""
        players = [{"id": 0, "name": "Player 1"}, {"id": 1, "name": "Player 2"}]
        game = GameRoundTheClockDouble(players)

        game.set_current_player(1)
        assert game.players[0]["is_turn"] is False
        assert game.players[1]["is_turn"] is True

    def test_add_player(self):
        """Test adding a player"""
        players = [{"id": 0, "name": "Player 1"}]
        game = GameRoundTheClockDouble(players)

        game.add_player({"id": 1, "name": "Player 2"})
        assert len(game.players) == 2
        assert game.players[1]["current_target"] == 20

    def test_remove_player(self):
        """Test removing a player"""
        players = [{"id": 0, "name": "Player 1"}, {"id": 1, "name": "Player 2"}]
        game = GameRoundTheClockDouble(players)

        game.remove_player(0)
        assert len(game.players) == 1
        assert game.players[0]["name"] == "Player 2"

    def test_process_score_wrapper(self):
        """Test process_score wrapper method"""
        players = [{"id": 0, "name": "Player 1"}]
        game = GameRoundTheClockDouble(players)

        result = game.process_score(20, "SINGLE")
        assert result["hit"] is True
        assert result["new_target"] == 19

    def test_complete_game_scenario(self):
        """Test a complete game scenario from start to finish"""
        players = [{"id": 0, "name": "Player 1"}]
        game = GameRoundTheClockDouble(players)

        # Simulate quick progression (hitting all singles to finish quickly)
        # With singles, we progress one at a time, so it's predictable
        current_target = 20
        while current_target > 0:
            result = game.process_throw(0, current_target, 1, "SINGLE")
            assert result["hit"] is True
            current_target -= 1

        # Now at target 0, need double bull to win
        assert game.players[0]["current_target"] == 0

        # Try single bull - should NOT work (key difference from base variant)
        result = game.process_throw(0, 25, 1, "BULL")
        assert result["winner"] is False
        assert result["hit"] is False
        assert game.players[0]["current_target"] == 0

        # Try double bull - should win
        result = game.process_throw(0, 25, 2, "DBLBULL")
        assert result["winner"] is True
        assert result["hit"] is True
