"""Integration tests for complete game scenarios."""

from src.app.game_manager import GameManager


class TestGame301Scenarios:
    """Test complete 301 game scenarios."""

    def test_complete_301_game(self, mock_socketio, mock_database_service):
        """Test a complete 301 game from start to finish."""
        manager = GameManager(mock_socketio)
        manager.new_game("301", ["Alice", "Bob"])

        # Alice's turn - score 180 (3x triple 20)
        # When DARTBOARD_SENDS_ACTUAL_SCORE=True, we send actual scores (60, not 20)
        for _ in range(3):
            manager.process_score({"score": 60, "multiplier": "TRIPLE"})
        assert manager.game.players[0]["score"] == 121  # 301 - 180

        # Move to Bob
        manager.next_player()
        assert manager.current_player == 1

        # Bob's turn - score 160 (60 + 60 + 40)
        manager.process_score({"score": 60, "multiplier": "TRIPLE"})
        manager.process_score({"score": 60, "multiplier": "TRIPLE"})
        manager.process_score({"score": 40, "multiplier": "DOUBLE"})
        assert manager.game.players[1]["score"] == 141  # 301 - 160

    def test_301_bust_scenario(self, mock_socketio, mock_database_service):
        """Test bust scenario in 301."""
        manager = GameManager(mock_socketio)
        manager.new_game("301", ["Alice", "Bob"])

        # Score down to 50 properly (301 - 251 = 50)
        # First turn: score 180 (60 triple x 3)
        manager.process_score({"score": 60, "multiplier": "TRIPLE"})  # 301 - 180 = 121
        manager.process_score({"score": 60, "multiplier": "TRIPLE"})
        manager.process_score({"score": 60, "multiplier": "TRIPLE"})
        assert manager.game.players[0]["score"] == 121

        # Next turn: score 71 more (121 - 71 = 50)
        manager.next_player()  # Move to Bob
        manager.next_player()  # Back to Alice
        manager.process_score({"score": 60, "multiplier": "TRIPLE"})  # 60
        manager.process_score({"score": 11, "multiplier": "SINGLE"})  # 11
        assert manager.game.players[0]["score"] == 50

        # Third throw in same turn - try to score 60 (bust - would go negative)
        manager.process_score({"score": 60, "multiplier": "TRIPLE"})  # This should bust

        # Score should be restored to start of turn (121) because bust undoes entire turn
        assert manager.game.players[0]["score"] == 121
        assert manager.is_paused is True

    def test_301_exact_finish(self, mock_socketio, mock_database_service):
        """Test exact finish in 301."""
        manager = GameManager(mock_socketio)
        manager.new_game("301", ["Alice", "Bob"])

        # Set Alice's score to 40
        manager.game.players[0]["score"] = 40

        # Score exactly 40 to win
        manager.process_score({"score": 40, "multiplier": "DOUBLE"})

        # Should be winner
        assert manager.game.players[0]["score"] == 0
        assert manager.is_winner is True

    def test_501_game(self, mock_socketio, mock_database_service):
        """Test 501 game variant."""
        manager = GameManager(mock_socketio)
        manager.new_game("501", ["Alice", "Bob"])

        assert manager.game.start_score == 501
        assert manager.game.players[0]["score"] == 501

        # Score some points
        manager.process_score({"score": 60, "multiplier": "TRIPLE"})
        assert manager.game.players[0]["score"] == 441


class TestCricketScenarios:
    """Test complete cricket game scenarios."""

    def test_complete_cricket_game(self, mock_socketio, mock_database_service):
        """Test a complete cricket game."""
        manager = GameManager(mock_socketio)
        manager.new_game("cricket", ["Alice", "Bob"])

        # Alice opens 20
        manager.process_score({"score": 60, "multiplier": "TRIPLE"})
        assert manager.game.players[0]["targets"][20]["hits"] == 3
        assert manager.game.players[0]["targets"][20]["status"] == 1

        # Alice scores on 20
        manager.process_score({"score": 40, "multiplier": "DOUBLE"})
        assert manager.game.players[0]["score"] == 40

    def test_cricket_closing_target(self, mock_socketio, mock_database_service):
        """Test closing a target in cricket."""
        manager = GameManager(mock_socketio)
        manager.new_game("cricket", ["Alice", "Bob"])

        # Alice opens 20
        manager.process_score({"score": 60, "multiplier": "TRIPLE"})

        # Move to Bob
        manager.next_player()

        # Bob opens 20 (should close it)
        manager.process_score({"score": 60, "multiplier": "TRIPLE"})

        # Target should be closed for both
        assert manager.game.players[0]["targets"][20]["status"] == 2
        assert manager.game.players[1]["targets"][20]["status"] == 2

    def test_cricket_winner(self, mock_socketio, mock_database_service):
        """Test cricket winner detection."""
        manager = GameManager(mock_socketio)
        manager.new_game("cricket", ["Alice", "Bob"])

        # Alice opens all targets (need to handle turn completion)
        targets = [15, 16, 17, 18, 19, 20, 25]
        for i, target in enumerate(targets):
            # After every 3 throws, the turn ends and game pauses
            if i > 0 and i % 3 == 0:
                manager.next_player()  # Move to Bob
                manager.next_player()  # Move back to Alice
            # Send actual score (triple value)
            actual_score = target * 3
            manager.process_score({"score": actual_score, "multiplier": "TRIPLE"})

        # Alice should be winner (all targets opened, Bob has none)
        assert manager.is_winner is True

    def test_cricket_scoring_sequence(self, mock_socketio, mock_database_service):
        """Test cricket scoring sequence."""
        manager = GameManager(mock_socketio)
        manager.new_game("cricket", ["Alice", "Bob"])

        # Alice hits 20 once
        manager.process_score({"score": 20, "multiplier": "SINGLE"})
        assert manager.game.players[0]["targets"][20]["hits"] == 1
        assert manager.game.players[0]["score"] == 0

        # Alice hits 20 twice more (opens)
        manager.process_score({"score": 40, "multiplier": "DOUBLE"})
        assert manager.game.players[0]["targets"][20]["hits"] == 3
        assert manager.game.players[0]["score"] == 0

        # Alice hits 20 again (scores)
        manager.process_score({"score": 20, "multiplier": "SINGLE"})
        assert manager.game.players[0]["score"] == 20


class TestMultiPlayerScenarios:
    """Test multi-player game scenarios."""

    def test_three_player_301(self, mock_socketio):
        """Test 301 game with three players."""
        manager = GameManager(mock_socketio)
        manager.new_game("301", ["Alice", "Bob", "Charlie"])

        assert len(manager.players) == 3

        # Each player takes a turn
        for i in range(3):
            assert manager.current_player == i
            manager.process_score({"score": 20, "multiplier": "TRIPLE"})
            manager.process_score({"score": 20, "multiplier": "TRIPLE"})
            manager.process_score({"score": 20, "multiplier": "TRIPLE"})
            manager.next_player()

    def test_four_player_cricket(self, mock_socketio, mock_database_service):
        """Test cricket game with four players."""
        manager = GameManager(mock_socketio)
        manager.new_game("cricket", ["Alice", "Bob", "Charlie", "Diana"])

        assert len(manager.players) == 4

        # Each player opens 20
        for i in range(4):
            assert manager.current_player == i
            manager.process_score({"score": 60, "multiplier": "TRIPLE"})
            manager.next_player()

        # Target should be closed for all
        for player in manager.game.players:
            assert player["targets"][20]["status"] == 2

    def test_player_rotation(self, mock_socketio):
        """Test player rotation."""
        manager = GameManager(mock_socketio)
        manager.new_game("301", ["Alice", "Bob", "Charlie"])

        # Rotate through all players
        for i in range(6):  # Two full rotations
            expected_player = i % 3
            assert manager.current_player == expected_player
            manager.next_player()


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_score_before_game_start(self, mock_socketio):
        """Test scoring before game starts."""
        manager = GameManager(mock_socketio)
        manager.process_score({"score": 20, "multiplier": "SINGLE"})
        # Should be ignored
        assert manager.current_throw == 1

    def test_invalid_multiplier(self, mock_socketio):
        """Test invalid multiplier."""
        manager = GameManager(mock_socketio)
        manager.new_game("301", ["Alice", "Bob"])
        # Should default to SINGLE
        manager.process_score({"score": 20, "multiplier": "INVALID"})
        # Should process as single
        assert manager.game.players[0]["score"] == 281

    def test_missing_score_data(self, mock_socketio):
        """Test missing score data."""
        manager = GameManager(mock_socketio)
        manager.new_game("301", ["Alice", "Bob"])
        # Should handle gracefully
        manager.process_score({})
        # Should process as 0
        assert manager.game.players[0]["score"] == 301

    def test_remove_current_player(self, mock_socketio):
        """Test removing current player."""
        manager = GameManager(mock_socketio)
        manager.new_game("301", ["Alice", "Bob", "Charlie"])
        manager.current_player = 2
        manager.remove_player(2)
        # Current player should wrap to 0
        assert manager.current_player == 0

    def test_add_player_during_game(self, mock_socketio):
        """Test adding player during active game."""
        manager = GameManager(mock_socketio)
        manager.new_game("301", ["Alice", "Bob"])
        manager.add_player("Charlie")
        assert len(manager.players) == 3
        # New player should have starting score
        assert manager.game.players[2]["score"] == 301
