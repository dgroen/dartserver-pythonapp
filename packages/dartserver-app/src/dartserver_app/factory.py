"""Flask application factory and initialization."""

import logging
import os

from dartserver_core import Config

logger = logging.getLogger(__name__)


def create_app(config=None, debug=False, root_dir=None):
    """
    Create and configure the Flask application.

    For test compatibility we reuse the legacy app instance defined in
    ``src.app.app`` so all routes registered via decorators remain available.
    """

    # Import legacy module once to pick up all route decorators
    from src.app import app as legacy_app_module

    app = legacy_app_module.app
    socketio = legacy_app_module.socketio

    # Ensure config flags align with test expectations
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    app.config["SESSION_COOKIE_SECURE"] = Config.SESSION_COOKIE_SECURE
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["PERMANENT_SESSION_LIFETIME"] = 3600
    app.config["TESTING"] = debug or app.config.get("TESTING", False)

    if config:
        app.config.update(config)

    logger.info(f"Flask app created (debug={debug}) using legacy routes")
    return app, socketio


def get_app_instance():
    """Get or create the application instance."""
    return create_app()
