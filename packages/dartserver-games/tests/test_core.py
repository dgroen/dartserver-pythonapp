"""Core integration tests for dartserver-games."""

from dartserver_games import (
    BaseGame,
    Game301,
    GameBullPractice,
    GameCricket,
    GameRoundTheClock,
    GameRoundTheClockDouble,
)


class TestGamePackageImports:
    """Test that all game classes are properly exported."""

    def test_all_games_importable(self):
        """Test that all game classes can be imported."""
        assert Game301 is not None
        assert GameCricket is not None
        assert GameRoundTheClock is not None
        assert GameRoundTheClockDouble is not None
        assert GameBullPractice is not None
        assert BaseGame is not None

    def test_game_301_instantiation(self, sample_players):
        """Test Game301 can be instantiated."""
        game = Game301(sample_players)
        assert game is not None
        assert len(game.players) == 2

    def test_game_cricket_instantiation(self, sample_players):
        """Test GameCricket can be instantiated."""
        game = GameCricket(sample_players)
        assert game is not None
        assert len(game.players) == 2

    def test_game_round_the_clock_instantiation(self, sample_players):
        """Test GameRoundTheClock can be instantiated."""
        game = GameRoundTheClock(sample_players)
        assert game is not None
        assert len(game.players) == 2

    def test_game_round_the_clock_double_instantiation(self, sample_players):
        """Test GameRoundTheClockDouble can be instantiated."""
        game = GameRoundTheClockDouble(sample_players)
        assert game is not None
        assert len(game.players) == 2

    def test_game_bull_practice_instantiation(self, sample_players):
        """Test GameBullPractice can be instantiated."""
        game = GameBullPractice(sample_players)
        assert game is not None
        assert len(game.players) == 2
