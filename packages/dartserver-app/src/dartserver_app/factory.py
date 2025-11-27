"""Flask application factory and initialization."""

import logging
import os
from pathlib import Path

from dartserver_app.events import register_events
from dartserver_app.game_manager import GameManager
from dartserver_app.routes import register_routes
from dartserver_core import Config, set_database_service
from flasgger import Swagger
from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

logger = logging.getLogger(__name__)


def create_app(config=None, debug=False, root_dir=None):
    """
    Create and configure the Flask application.

    Args:
        config: Optional configuration dictionary
        debug: Enable debug mode
        root_dir: Root directory for templates/static (defaults to app directory)

    Returns:
        Tuple of (app, socketio) - Flask app and SocketIO instance
    """
    # Setup paths
    if root_dir is None:
        app_dir = Path(__file__).resolve().parent.parent.parent.parent
        root_dir = app_dir / "src"

    root_dir = Path(root_dir)
    templates_dir = root_dir.parent / "templates"
    static_dir = root_dir.parent / "static"

    # Create Flask app
    app = Flask(
        __name__,
        template_folder=str(templates_dir),
        static_folder=str(static_dir),
    )

    # Configure app
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
    app.config["SESSION_COOKIE_SECURE"] = Config.SESSION_COOKIE_SECURE
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["PERMANENT_SESSION_LIFETIME"] = 3600

    if config:
        app.config.update(config)

    # Enable CORS
    CORS(
        app,
        origins=[Config.APP_URL],
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    )

    # Initialize Swagger
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/apispec.json",
            },
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api/docs/",
    }

    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Darts Game API",
            "description": "API for managing darts games (301, 401, 501, Cricket, Round the Clock) \
                with real-time score tracking",
            "version": "1.0.0",
            "contact": {
                "name": "Darts Game Server",
            },
        },
        "host": Config.SWAGGER_HOST,
        "basePath": "/",
        "schemes": ["http", "https"] if not Config.is_production() else ["https"],
        "tags": [
            {"name": "Game", "description": "Game management endpoints"},
            {"name": "Players", "description": "Player management endpoints"},
            {"name": "Score", "description": "Score submission endpoints"},
            {"name": "TTS", "description": "Text-to-Speech configuration endpoints"},
            {"name": "UI", "description": "User interface endpoints"},
        ],
    }

    Swagger(app, config=swagger_config, template=swagger_template)

    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
    app.socketio = socketio

    # Initialize Game Manager
    game_manager = GameManager(socketio)
    app.game_manager = game_manager

    # Initialize database service
    set_database_service(game_manager.db_service)

    # Register SocketIO event handlers
    register_events(socketio, app)

    # Register routes
    register_routes(app)

    logger.info(f"Flask app created (debug={debug})")
    return app, socketio


def get_app_instance():
    """Get or create the application instance."""
    return create_app()
