"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def app():
    """Create application for testing."""
    from dartserver_app import create_app

    app, socketio = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Create Flask test client."""
    return app.test_client()


@pytest.fixture
def socketio_client(app):
    """Create SocketIO test client."""
    from unittest.mock import Mock

    return Mock()
