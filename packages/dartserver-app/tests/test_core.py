"""Integration tests for dartserver_app package."""


def test_import_create_app():
    """Test that create_app can be imported."""
    from dartserver_app import create_app

    assert create_app is not None


def test_import_game_manager():
    """Test that GameManager can be imported."""
    from dartserver_app import GameManager

    assert GameManager is not None


def test_app_factory_returns_tuple():
    """Test that create_app returns a tuple of (app, socketio)."""
    from dartserver_app import create_app

    result = create_app()
    assert isinstance(result, tuple)
    assert len(result) == 2

    app, socketio = result
    assert app is not None
    assert socketio is not None


def test_app_has_game_manager():
    """Test that the app has game_manager attached."""
    from dartserver_app import create_app

    app, _ = create_app()
    assert hasattr(app, "game_manager")
    assert app.game_manager is not None


def test_app_has_socketio():
    """Test that the app has socketio attached."""
    from dartserver_app import create_app

    app, socketio = create_app()
    assert hasattr(app, "socketio")
    assert app.socketio is socketio


def test_app_configuration():
    """Test that app is configured correctly."""
    from dartserver_app import create_app

    app, _ = create_app()

    assert app.config["SESSION_COOKIE_HTTPONLY"] is True
    assert app.config["SESSION_COOKIE_SAMESITE"] == "Lax"
    assert app.config["PERMANENT_SESSION_LIFETIME"] == 3600


def test_routes_registration():
    """Test that routes can be registered."""
    from dartserver_app import create_app
    from dartserver_app.routes import register_routes

    app, _ = create_app()
    register_routes(app)  # Should not raise


def test_events_registration():
    """Test that events can be registered."""
    from dartserver_app import create_app
    from dartserver_app.events import register_events

    app, socketio = create_app()
    register_events(socketio, app)  # Should not raise


def test_get_app_instance():
    """Test getting app instance."""
    from dartserver_app import get_app_instance

    result = get_app_instance()
    assert isinstance(result, tuple)
    assert len(result) == 2


def test_game_manager_initialization():
    """Test that GameManager initializes properly."""
    from unittest.mock import Mock

    from dartserver_app import GameManager

    socketio = Mock()
    manager = GameManager(socketio)

    assert manager.socketio is socketio
    assert manager.players == []
    assert manager.is_started is False
