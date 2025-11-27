"""Integration tests for dartserver-games package."""

from dartserver_games import BaseGame, Game301, GameFactory


class TestGameFactoryIntegration:
    """Test game factory creation of all game types."""

    def test_create_301_game(self):
        """Test creating a 301 game."""
        game = GameFactory.create("301", num_players=2)
        assert game is not None
        assert isinstance(game, BaseGame)

    def test_create_cricket_game(self):
        """Test creating a Cricket game."""
        game = GameFactory.create("cricket", num_players=2)
        assert game is not None
        assert isinstance(game, BaseGame)

    def test_create_round_the_clock_game(self):
        """Test creating a Round the Clock game."""
        game = GameFactory.create("round_the_clock", num_players=2)
        assert game is not None
        assert isinstance(game, BaseGame)


class TestGamePlayIntegration:
    """Test basic game play mechanics."""

    def test_add_player(self):
        """Test adding players to game."""
        game = Game301(num_players=2)
        game.add_player("Alice", 1)
        game.add_player("Bob", 2)
        assert len(game.players) == 2

    def test_get_game_state(self):
        """Test retrieving game state."""
        game = Game301(num_players=2)
        game.add_player("Alice", 1)
        state = game.get_game_state()
        assert state is not None
        assert isinstance(state, dict)

    def test_process_score(self):
        """Test processing a score."""
        game = Game301(num_players=2)
        game.add_player("Alice", 1)
        game.add_player("Bob", 2)

        # Should not raise
        game.process_score({"zone": 20, "modifier": 1})


class TestGameRulesIntegration:
    """Test configurable game rules."""

    def test_double_out_rule(self):
        """Test double-out rule configuration."""
        game = Game301(num_players=2, double_out=True)
        assert game.double_out is True

    def test_reset_on_miss_rule(self):
        """Test reset-on-miss rule configuration."""
        game = Game301(num_players=2, reset_on_miss=True)
        assert game.reset_on_miss is True


class TestGamesExports:
    """Test that all expected exports are available."""

    def test_base_game_export(self):
        """Test BaseGame is exported."""
        from dartserver_games import BaseGame

        assert BaseGame is not None

    def test_game_implementations_export(self):
        """Test game implementations are exported."""
        from dartserver_games import Game301, GameCricket, GameRoundTheClock

        assert Game301 is not None
        assert GameCricket is not None
        assert GameRoundTheClock is not None

    def test_game_factory_export(self):
        """Test GameFactory is exported."""
        from dartserver_games import GameFactory

        assert GameFactory is not None
