"""Pytest configuration and fixtures."""

import builtins
import importlib
import importlib.util
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import dartserver_core.auth as core_auth
import pytest
from dartserver_app import create_app

# Eagerly create a single test app/socketio/game_manager for fixtures that
# reference these names as globals (many tests import flask_app directly).
flask_app, socketio = create_app(debug=True)
flask_app.config["TESTING"] = True
game_manager = flask_app.game_manager

# Expose frequently used auth helpers as builtins for tests that reference
# them directly without importing.
builtins.get_user_roles = core_auth.get_user_roles
builtins.has_permission = core_auth.has_permission
builtins.search_wso2_users = core_auth.search_wso2_users
builtins.flask_app = flask_app
builtins.app = flask_app
builtins.socketio = socketio
builtins.game_manager = game_manager

os.environ["ENVIRONMENT"] = "test"
os.environ["APP_DOMAIN"] = "test.letsplaydarts.eu"
os.environ["APP_SCHEME"] = "https"
os.environ["SECRET_KEY"] = "test-secret-key-for-automated-testing"
os.environ["RABBITMQ_EXCHANGE"] = "darts_exchange_test"
os.environ["WSO2_IS_URL"] = "https://test.letsplaydarts.eu/auth"

# Disable TTS during tests to avoid timing issues
os.environ["TTS_ENABLED"] = "false"
# Use in-memory SQLite for tests
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
# Enable authentication for tests to verify auth decorators work correctly
os.environ["AUTH_DISABLED"] = "false"


# Add project root and package sources to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent / "packages" / "dartserver-core" / "src"),
)

for mod in ["dartserver_core", "dartserver_services"]:
    sys.modules.pop(mod, None)
importlib.invalidate_caches()


def _load_local_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)


_load_local_module(
    "dartserver_core",
    Path(__file__).resolve().parent.parent
    / "packages"
    / "dartserver-core"
    / "src"
    / "dartserver_core"
    / "__init__.py",
)
_load_local_module(
    "dartserver_services",
    Path(__file__).resolve().parent.parent
    / "packages"
    / "dartserver-services"
    / "src"
    / "dartserver_services"
    / "__init__.py",
)

import dartserver_core.auth as dart_core_auth  # noqa: E402

# Keep dartserver_core auth functions in sync with src.core.auth so test patches
# against the src.core path affect the implementation used by decorators.
dart_core_auth.validate_token = core_auth.validate_token
dart_core_auth.get_user_roles = core_auth.get_user_roles
dart_core_auth.has_permission = core_auth.has_permission
dart_core_auth.search_wso2_users = core_auth.search_wso2_users


@pytest.fixture()
def mock_socketio():
    """Mock SocketIO instance."""
    mock = MagicMock()
    mock.emit = MagicMock()
    return mock


@pytest.fixture()
def sample_players():
    """Sample player data for testing."""
    return [
        {"id": 0, "name": "Player 1"},
        {"id": 1, "name": "Player 2"},
    ]


@pytest.fixture()
def sample_players_four():
    """Sample player data with four players."""
    return [
        {"id": 0, "name": "Alice"},
        {"id": 1, "name": "Bob"},
        {"id": 2, "name": "Charlie"},
        {"id": 3, "name": "Diana"},
    ]


@pytest.fixture()
def sample_score_data():
    """Sample score data for testing."""
    return {
        "score": 20,
        "multiplier": "TRIPLE",
        "user": "Player 1",
    }


@pytest.fixture()
def app():
    """Flask app fixture for pytest-flask and tests."""
    return flask_app


@pytest.fixture()
def flask_app(app):
    """Alias fixture to satisfy tests expecting flask_app."""
    return app


@pytest.fixture()
def socketio(app):
    """Provide SocketIO instance from the created app."""
    return socketio


@pytest.fixture()
def game_manager(app):
    """Expose GameManager for tests that reference game_manager directly."""
    return game_manager


@pytest.fixture()
def app_client():
    """Flask test client."""
    with flask_app.test_client() as client:
        yield client


@pytest.fixture()
def mock_rabbitmq_config():
    """Mock RabbitMQ configuration."""
    return {
        "host": "localhost",
        "port": 5672,
        "user": "guest",
        "password": "guest",
        "vhost": "/",
        "exchange": "darts_exchange",
        "topic": "darts.scores.#",
    }


@pytest.fixture()
def mock_database_service():
    """Mock DatabaseService for testing."""
    with patch("dartserver_app.game_manager.DatabaseService") as mock_db:
        mock_instance = MagicMock()
        mock_instance.initialize_database = MagicMock()
        mock_instance.start_new_game = MagicMock()
        mock_instance.record_throw = MagicMock()
        mock_instance.end_game = MagicMock()
        mock_instance.get_game_history = MagicMock(return_value=[])
        mock_instance.get_game_replay_data = MagicMock(return_value=None)
        mock_instance.current_game_session_id = "test-session-id"
        mock_db.return_value = mock_instance
        yield mock_instance


@pytest.fixture()
def in_memory_db():
    """Create an in-memory database for testing."""
    from dartserver_core.database_service import DatabaseService

    db_service = DatabaseService("sqlite:///:memory:")
    db_service.initialize_database()
    return db_service


@pytest.fixture()
def player_ids_with_db():
    """Helper to create player dicts with database IDs."""

    def _create_players(names):
        """Create player objects with db_ids for testing."""
        return [{"db_id": i + 1, "name": name} for i, name in enumerate(names)]

    return _create_players
