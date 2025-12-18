"""
Unit tests for /api/Throw/zone endpoint
Tests the new zone-based scoring system that replaces DARTBOARD_SENDS_ACTUAL_SCORE
"""

import json
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture()
def client():
    """Create test client"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture()
def mock_game_manager():
    """Mock game manager"""
    with patch("src.app.app.game_manager") as mock:
        mock.process_score = MagicMock()
        yield mock


@pytest.fixture()
def mock_dartboard_service():
    """Mock dartboard service"""
    with patch("src.app.app.DartboardService") as mock:
        yield mock


@pytest.fixture()
def mock_db_session():
    """Create mock database session"""
    with patch("src.app.app.get_session") as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        yield mock_session


class TestZoneEndpoint:
    """Test /api/Throw/zone endpoint"""

    def test_submit_zone_triple_20(
        self,
        client,
        mock_game_manager,
        mock_dartboard_service,
        mock_db_session,
    ):
        """Test submitting a triple 20 via zone endpoint"""
        mock_dartboard_service.get_zone_from_pins.return_value = {
            "zone_number": 20,
            "multiplier_type": "TRIPLE",
            "base_value": 20,
            "score": 60,
        }

        response = client.post(
            "/api/Throw/zone",
            json={"masterPin": 4, "slavePin": 13, "boardType": "carromco"},
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert data["zone_info"]["multiplier_type"] == "TRIPLE"
        assert data["zone_info"]["base_value"] == 20
        assert data["zone_info"]["score"] == 60

        # Verify game_manager was called with base_value, not calculated score
        mock_game_manager.process_score.assert_called_once_with(
            {
                "score": 20,
                "multiplier": "TRIPLE",
            },
        )

    def test_submit_zone_double_15(
        self,
        client,
        mock_game_manager,
        mock_dartboard_service,
        mock_db_session,
    ):
        """Test submitting a double 15 via zone endpoint"""
        mock_dartboard_service.get_zone_from_pins.return_value = {
            "zone_number": 15,
            "multiplier_type": "DOUBLE",
            "base_value": 15,
            "score": 30,
        }

        response = client.post(
            "/api/Throw/zone",
            json={"masterPin": 5, "slavePin": 10, "boardType": "carromco"},
            content_type="application/json",
        )

        assert response.status_code == 200
        mock_game_manager.process_score.assert_called_once_with(
            {
                "score": 15,
                "multiplier": "DOUBLE",
            },
        )

    def test_submit_zone_bull(
        self,
        client,
        mock_game_manager,
        mock_dartboard_service,
        mock_db_session,
    ):
        """Test submitting a bull (25 BULL)"""
        mock_dartboard_service.get_zone_from_pins.return_value = {
            "zone_number": 25,
            "multiplier_type": "BULL",
            "base_value": 25,
            "score": 25,
        }

        response = client.post(
            "/api/Throw/zone",
            json={"masterPin": 7, "slavePin": 12, "boardType": "carromco"},
            content_type="application/json",
        )

        assert response.status_code == 200
        mock_game_manager.process_score.assert_called_once_with(
            {
                "score": 25,
                "multiplier": "BULL",
            },
        )

    def test_submit_zone_double_bull(
        self,
        client,
        mock_game_manager,
        mock_dartboard_service,
        mock_db_session,
    ):
        """Test submitting a double bull (50)"""
        mock_dartboard_service.get_zone_from_pins.return_value = {
            "zone_number": 25,
            "multiplier_type": "DBLBULL",
            "base_value": 25,
            "score": 50,
        }

        response = client.post(
            "/api/Throw/zone",
            json={"masterPin": 7, "slavePin": 13, "boardType": "carromco"},
            content_type="application/json",
        )

        assert response.status_code == 200
        mock_game_manager.process_score.assert_called_once_with(
            {
                "score": 25,
                "multiplier": "DBLBULL",
            },
        )

    def test_zone_not_found(
        self,
        client,
        mock_dartboard_service,
        mock_db_session,
    ):
        """Test when zone mapping is not found"""
        mock_dartboard_service.get_zone_from_pins.return_value = None

        response = client.post(
            "/api/Throw/zone",
            json={"masterPin": 99, "slavePin": 99, "boardType": "unknown"},
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert "not found" in data["message"].lower()

    def test_invalid_pin_types(self, client, mock_db_session):
        """Test with invalid pin types"""
        response = client.post(
            "/api/Throw/zone",
            json={"masterPin": "not_a_number", "slavePin": 13, "boardType": "carromco"},
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "integer" in data["message"].lower()

    def test_missing_board_type(self, client, mock_db_session):
        """Test with missing boardType"""
        response = client.post(
            "/api/Throw/zone",
            json={"masterPin": 4, "slavePin": 13},
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "boardType" in data["message"]
