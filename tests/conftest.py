"""Pytest configuration and fixtures."""

import builtins
import importlib
import importlib.util
import logging
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import dartserver_core.auth as core_auth
import pytest
from dartserver_app import create_app
from dartserver_core.database_service import DatabaseService
from sqlalchemy import create_engine, text

# Expose frequently used auth helpers as builtins for tests that reference
# them directly without importing. These reference the implementation
# in `packages/dartserver-core/src/dartserver_core/auth.py` but tests
# patch `dartserver_core.auth` during collection; keep references aligned.
builtins.get_user_roles = core_auth.get_user_roles
builtins.has_permission = core_auth.has_permission
builtins.search_wso2_users = core_auth.search_wso2_users

# Default test environment values. These will be set again inside the
# `flask_app` fixture prior to creating the app so the app reads them
# correctly at creation time.
DEFAULT_TEST_ENV = {
    "ENVIRONMENT": "test",
    "APP_DOMAIN": "test.letsplaydarts.eu",
    "APP_SCHEME": "https",
    "SECRET_KEY": "test-secret-key-for-automated-testing",
    "RABBITMQ_EXCHANGE": "darts_exchange_test",
    "WSO2_IS_URL": "https://test.letsplaydarts.eu/auth",
    "TTS_ENABLED": "false",
    # Use a file-based sqlite by default (will be created in the fixture)
    "DATABASE_URL": None,
    "AUTH_DISABLED": "false",
}


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

# Keep dartserver_core auth functions in sync with dartserver_core.auth so test patches
# against the src.core path affect the implementation used by decorators.
dart_core_auth.validate_token = core_auth.validate_token
dart_core_auth.get_user_roles = core_auth.get_user_roles
dart_core_auth.has_permission = core_auth.has_permission
dart_core_auth.search_wso2_users = core_auth.search_wso2_users
dart_core_auth.get_wso2_user_info = core_auth.get_wso2_user_info

# Create a module-global app for tests that reference `flask_app` at import time.
# Some older tests expect a global `flask_app` variable; create a lightweight
# app here using a predictable file-based SQLite DB under /tmp so tests that
# access the global app before fixtures run will not fail.
try:
    # Only create once
    if not getattr(builtins, "flask_app", None):
        os.environ.update({k: v for k, v in DEFAULT_TEST_ENV.items() if v is not None})
        os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/dartserver_test_sqlite.db")
        _app_instance, _socketio_instance = create_app(debug=True)
        builtins.flask_app = _app_instance
        builtins.app = _app_instance
        builtins.socketio = _socketio_instance
        builtins.game_manager = _app_instance.game_manager
except Exception:
    # Best-effort — if early creation fails, the session fixture will create the app.
    logging.exception("Failed to create early app instance: %s")


@pytest.fixture
def mock_socketio():
    """Mock SocketIO instance."""
    mock = MagicMock()
    mock.emit = MagicMock()
    return mock


@pytest.fixture(scope="session")
def flask_app(tmp_path_factory):
    """Create a single Flask app/socketio for the test session.

    This fixture sets up a temporary file-based SQLite database to avoid
    the per-connection isolation issues of in-memory SQLite, and exposes
    `flask_app`, `app`, `socketio` and `game_manager` on the builtins for
    legacy tests that import them directly.
    """
    # Create a temp DB file
    db_file = tmp_path_factory.mktemp("test_db") / "test_sqlite.db"

    # Set environment values BEFORE creating the app so create_app reads them
    for k, v in DEFAULT_TEST_ENV.items():
        if v is not None:
            os.environ[k] = v
    os.environ["DATABASE_URL"] = f"sqlite:///{db_file}"

    app_instance, socketio_instance = create_app(debug=True)
    app_instance.config["TESTING"] = True

    # Expose builtins for tests that rely on global names
    builtins.flask_app = app_instance
    builtins.app = app_instance
    builtins.socketio = socketio_instance
    builtins.game_manager = app_instance.game_manager

    yield app_instance

    # Teardown: remove DB file if present
    try:
        if db_file.exists():
            db_file.unlink()
    except Exception:  # noqa: S110
        pass


@pytest.fixture
def sample_players():
    """Sample player data for testing."""
    return [
        {"id": 0, "name": "Player 1"},
        {"id": 1, "name": "Player 2"},
    ]


@pytest.fixture
def sample_players_four():
    """Sample player data with four players."""
    return [
        {"id": 0, "name": "Alice"},
        {"id": 1, "name": "Bob"},
        {"id": 2, "name": "Charlie"},
        {"id": 3, "name": "Diana"},
    ]


@pytest.fixture
def sample_score_data():
    """Sample score data for testing."""
    return {
        "score": 20,
        "multiplier": "TRIPLE",
        "user": "Player 1",
    }


@pytest.fixture
def app(flask_app):
    """Flask app fixture for pytest-flask and tests."""
    return flask_app


@pytest.fixture
def socketio(flask_app):
    """Provide SocketIO instance from the created app."""
    return builtins.socketio


@pytest.fixture
def game_manager(flask_app):
    """Expose GameManager for tests that reference game_manager directly."""
    return flask_app.game_manager


@pytest.fixture
def app_client(flask_app):
    """Flask test client."""
    with flask_app.test_client() as client:
        yield client


@pytest.fixture
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


@pytest.fixture
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


@pytest.fixture
def in_memory_db():
    """Create an in-memory database for testing."""
    db_service = DatabaseService("sqlite:///:memory:")
    db_service.initialize_database()
    return db_service


@pytest.fixture
def player_ids_with_db():
    """Helper to create player dicts with database IDs."""

    def _create_players(names):
        """Create player objects with db_ids for testing."""
        return [{"db_id": i + 1, "name": name} for i, name in enumerate(names)]

    return _create_players


@pytest.fixture
def throwaway_postgres_url():
    """A freshly created, disposable PostgreSQL database.

    Migration round-trips need a real PostgreSQL server: earlier revisions in
    the chain contain raw PostgreSQL that SQLite cannot execute. Skips when no
    server is reachable.
    """
    admin_url = os.getenv(
        "TEST_POSTGRES_ADMIN_URL",
        "postgresql://postgres:postgres@localhost:5432/postgres",
    )
    db_name = f"test_migration_{uuid4().hex[:12]}"

    admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    try:
        connection = admin_engine.connect()
    except Exception as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"No PostgreSQL server available for migration test: {exc}")

    with connection:
        connection.execute(text(f'CREATE DATABASE "{db_name}"'))
    try:
        yield admin_url.rsplit("/", 1)[0] + f"/{db_name}"
    finally:
        with admin_engine.connect() as connection:
            connection.execute(
                text(
                    "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
                    "WHERE datname = :name",
                ),
                {"name": db_name},
            )
            connection.execute(text(f'DROP DATABASE IF EXISTS "{db_name}"'))
        admin_engine.dispose()
