#!/usr/bin/env python3
"""
Main entry point for the Darts Game Web Application
Imports and runs the Flask app from src.app.app module
"""

import logging
import os
import sys

from src.app.app import app, socketio

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )
    logger = logging.getLogger(__name__)

    try:
        # Run the Flask application with SocketIO support
        # Bind to 0.0.0.0 to make it accessible from nginx on the Docker network
        # This is safe as it's behind a reverse proxy and not exposed directly
        host = os.getenv("FLASK_HOST", "0.0.0.0")  # nosec: B104
        port = int(os.getenv("FLASK_PORT", 5000))
        debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"

        logger.info(f"Starting Flask-SocketIO server on {host}:{port}")
        logger.info(f"Debug mode: {debug}")

        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug,
            allow_unsafe_werkzeug=True,
        )
    except Exception:
        logger.exception("Failed to start application")
        sys.exit(1)
