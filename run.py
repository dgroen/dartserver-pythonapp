#!/usr/bin/env python3
"""
Main entry point for the Darts Game Web Application
Imports and runs the Flask app from src.app.app module
"""

from src.app.app import app, socketio

if __name__ == "__main__":
    # Run the Flask application with SocketIO support
    socketio.run(app)
