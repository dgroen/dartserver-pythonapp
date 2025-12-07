"""
Compatibility layer for legacy routes.
This module patches src.app.app to use the new app instance from the factory.
"""

from src.app import app as legacy_app_module


def register_legacy_routes(app, socketio, game_manager):
    """
    Register routes from legacy src/app/app.py with the new app instance.

    Args:
        app: New Flask app instance
        socketio: SocketIO instance
        game_manager: GameManager instance
    """
    # Monkey-patch the legacy module to use our new instances
    legacy_app_module.app = app
    legacy_app_module.socketio = socketio
    legacy_app_module.game_manager = game_manager

    # The routes are already registered via decorators when the module was imported
    # No need to do anything else - the @app.route decorators executed when
    # src.app.app was first imported, and now they're using our app instance

    return app
