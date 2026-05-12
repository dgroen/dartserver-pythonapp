"""Integration tests for dartserver-core package."""

from dartserver_core import Config, Player, get_session


class TestConfigIntegration:
    """Test configuration loading and access."""

    def test_config_app_url(self):
        """Test that APP_URL is properly configured."""
        assert Config.APP_URL is not None
        assert isinstance(Config.APP_URL, str)

    def test_config_callback_url(self):
        """Test that CALLBACK_URL is properly configured."""
        assert Config.CALLBACK_URL is not None
        assert isinstance(Config.CALLBACK_URL, str)

    def test_config_environment_detection(self):
        """Test environment detection."""
        assert hasattr(Config, "is_production")
        assert callable(Config.is_production)


class TestDatabaseIntegration:
    """Test database initialization and operations."""

    def test_get_session(self):
        """Test that database session can be created."""
        session = get_session()
        assert session is not None
        session.close()

    def test_player_model_creation(self):
        """Test Player model can be instantiated."""
        player = Player(username="testuser", email="test@example.com", name="Test User")
        assert player.username == "testuser"
        assert player.email == "test@example.com"


class TestCoreExports:
    """Test that all expected exports are available."""

    def test_config_export(self):
        """Test Config is exported."""
        from dartserver_core import Config

        assert Config is not None

    def test_auth_decorators_export(self):
        """Test auth decorators are exported."""
        from dartserver_core import login_required, permission_required, role_required

        assert callable(login_required)
        assert callable(role_required)
        assert callable(permission_required)

    def test_models_export(self):
        """Test models are exported."""
        from dartserver_core import GameHistory, GameScore, GameSession, Player

        assert Player is not None
        assert GameHistory is not None
        assert GameSession is not None
        assert GameScore is not None
