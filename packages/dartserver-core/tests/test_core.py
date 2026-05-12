"""
Sample tests for dartserver-core package.
"""

from dartserver_core import Config, Game, Player


def test_config_loading(app_config):
    """Test that Config loads environment variables."""
    assert Config is not None
    assert Config.SECRET_KEY == "test-secret-key"


def test_player_creation(test_db):
    """Test Player model creation."""
    player = Player(name="Test Player", email="test@example.com")
    test_db.add(player)
    test_db.commit()

    assert player.id is not None
    assert player.name == "Test Player"
    assert player.email == "test@example.com"


def test_game_creation(test_db):
    """Test Game model creation."""
    game = Game(game_type="301", status="created")
    test_db.add(game)
    test_db.commit()

    assert game.id is not None
    assert game.game_type == "301"
    assert game.status == "created"


def test_imports():
    """Test that all exports are available."""
    from dartserver_core import (
        Config,
        Game,
        GameHistory,
        Player,
        login_required,
        permission_required,
        role_required,
    )

    assert Config is not None
    assert Player is not None
    assert Game is not None
    assert GameHistory is not None
    assert login_required is not None
    assert role_required is not None
    assert permission_required is not None
