"""Pytest configuration and fixtures for dartserver-games."""

import pytest


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
