"""
Dartserver App - Flask Web Application for Darts Game Management

Provides Flask application factory, route registration, SocketIO event handlers,
and game management utilities.
"""

from dartserver_app.events import register_events
from dartserver_app.factory import create_app, get_app_instance
from dartserver_app.game_manager import GameManager
from dartserver_app.routes import register_routes

__version__ = "1.0.0"
__all__ = [
    "create_app",
    "get_app_instance",
    "GameManager",
    "register_events",
    "register_routes",
]
