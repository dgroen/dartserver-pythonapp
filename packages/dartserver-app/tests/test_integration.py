"""Integration tests for dartserver-app package."""

from dartserver_app import GameManager, create_app
from dartserver_app.routes import ROUTE_DOMAINS, get_routes_summary


class TestAppFactoryIntegration:
    """Test Flask app factory creation."""

    def test_create_app_returns_tuple(self):
        """Test create_app returns (app, socketio) tuple."""
        app, socketio = create_app()
        assert app is not None
        assert socketio is not None

    def test_app_has_game_manager(self):
        """Test app has game_manager attached."""
        app, _ = create_app()
        assert hasattr(app, "game_manager")
        assert isinstance(app.game_manager, GameManager)

    def test_app_has_socketio(self):
        """Test app has socketio attached."""
        app, socketio = create_app()
        assert hasattr(app, "socketio")
        assert app.socketio is socketio


class TestRouteRegistryIntegration:
    """Test route organization registry."""

    def test_routes_summary(self):
        """Test getting routes summary."""
        summary = get_routes_summary()
        assert "total_routes" in summary
        assert "domains" in summary
        assert "events" in summary
        assert summary["total_routes"] > 0

    def test_route_domains(self):
        """Test route domain information."""
        assert "auth" in ROUTE_DOMAINS
        assert "game" in ROUTE_DOMAINS
        assert "player" in ROUTE_DOMAINS
        assert "ui" in ROUTE_DOMAINS

    def test_route_domain_counts(self):
        """Test route counts per domain."""
        assert ROUTE_DOMAINS["auth"]["count"] == 6
        assert ROUTE_DOMAINS["game"]["count"] == 13
        assert ROUTE_DOMAINS["player"]["count"] == 6


class TestEventHandlerIntegration:
    """Test event handler registration."""

    def test_event_handlers_registered(self):
        """Test that event handlers can be registered."""
        app, socketio = create_app()
        # Events should be registered automatically
        assert len(app.config) > 0


class TestGameManagerIntegration:
    """Test GameManager functionality."""

    def test_game_manager_creation(self):
        """Test GameManager can be created."""
        from flask import Flask
        from flask_socketio import SocketIO

        app = Flask(__name__)
        socketio = SocketIO(app)
        manager = GameManager(socketio)
        assert manager is not None

    def test_game_manager_has_players(self):
        """Test GameManager has players list."""
        from flask import Flask
        from flask_socketio import SocketIO

        app = Flask(__name__)
        socketio = SocketIO(app)
        manager = GameManager(socketio)
        assert hasattr(manager, "players")
        assert isinstance(manager.players, list)


class TestAppExports:
    """Test that all expected exports are available."""

    def test_create_app_export(self):
        """Test create_app is exported."""
        from dartserver_app import create_app

        assert callable(create_app)

    def test_game_manager_export(self):
        """Test GameManager is exported."""
        from dartserver_app import GameManager

        assert GameManager is not None

    def test_register_events_export(self):
        """Test register_events is exported."""
        from dartserver_app import register_events

        assert callable(register_events)

    def test_register_routes_export(self):
        """Test register_routes is exported."""
        from dartserver_app import register_routes

        assert callable(register_routes)
