"""
Pytest configuration for dartserver-core tests.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def test_db():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")

    from dartserver_core.database_models import Base

    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


@pytest.fixture
def app_config(monkeypatch):
    """Mock environment variables for testing."""
    test_env = {
        "FLASK_DEBUG": "False",
        "SECRET_KEY": "test-secret-key",
        "WSO2_IS_URL": "https://localhost:9443",
        "WSO2_CLIENT_ID": "test-client",
        "WSO2_CLIENT_SECRET": "test-secret",
        "DATABASE_URL": "sqlite:///:memory:",
    }

    for key, value in test_env.items():
        monkeypatch.setenv(key, value)

    return test_env
