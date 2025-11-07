"""
Unit tests for dartboard API endpoints
Tests both legacy /api/Throw and new /api/Throw/zone endpoints
Also tests dartboard management endpoints
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.app.app import app


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
def mock_db_session():
    """Create mock database session"""
    with patch("src.app.app.get_session") as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        yield mock_session


class TestLegacyThrowEndpoint:
    """Test legacy /api/Throw endpoint (backwards compatibility)"""

    def test_submit_score_triple_20(self, client, mock_game_manager):
        """Test submitting a triple 20 score via legacy endpoint"""
        response = client.post(
            "/api/Throw",
            json={"score": 20, "multiplier": "TRIPLE"},
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert data["message"] == "Score submitted"
        mock_game_manager.process_score.assert_called_once_with(
            {"score": 20, "multiplier": "TRIPLE"},
        )

    def test_submit_score_single_1(self, client, mock_game_manager):
        """Test submitting a single 1 score"""
        response = client.post(
            "/api/Throw",
            json={"score": 1, "multiplier": "SINGLE"},
            content_type="application/json",
        )

        assert response.status_code == 200
        mock_game_manager.process_score.assert_called_once_with(
            {"score": 1, "multiplier": "SINGLE"},
        )

    def test_submit_score_double_bull(self, client, mock_game_manager):
        """Test submitting a double bull (50) score"""
        response = client.post(
            "/api/Throw",
            json={"score": 25, "multiplier": "DBLBULL"},
            content_type="application/json",
        )

        assert response.status_code == 200

    def test_submit_score_bull(self, client, mock_game_manager):
        """Test submitting a bull (25) score"""
        response = client.post(
            "/api/Throw",
            json={"score": 25, "multiplier": "BULL"},
            content_type="application/json",
        )

        assert response.status_code == 200

    def test_submit_score_with_user(self, client, mock_game_manager):
        """Test submitting score with user field (optional)"""
        response = client.post(
            "/api/Throw",
            json={"score": 20, "multiplier": "TRIPLE", "user": "Alice"},
            content_type="application/json",
        )

        assert response.status_code == 200

    def test_submit_score_invalid_type_score(self, client):
        """Test that non-integer score is rejected"""
        response = client.post(
            "/api/Throw",
            json={"score": "20", "multiplier": "TRIPLE"},
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"

    def test_submit_score_invalid_type_multiplier(self, client):
        """Test that non-string multiplier is rejected"""
        response = client.post(
            "/api/Throw",
            json={"score": 20, "multiplier": 123},
            content_type="application/json",
        )

        assert response.status_code == 400

    def test_submit_score_missing_fields(self, client, mock_game_manager):
        """Test missing fields uses defaults"""
        response = client.post(
            "/api/Throw",
            json={},
            content_type="application/json",
        )

        # Should use defaults: score=0, multiplier="SINGLE"
        assert response.status_code == 200
        mock_game_manager.process_score.assert_called_once_with(
            {"score": 0, "multiplier": "SINGLE"},
        )

    def test_submit_score_exception_handling(self, client, mock_game_manager):
        """Test exception handling in legacy endpoint"""
        mock_game_manager.process_score.side_effect = Exception("Game error")

        response = client.post(
            "/api/Throw",
            json={"score": 20, "multiplier": "TRIPLE"},
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"


class TestNewZoneThrowEndpoint:
    """Test new /api/Throw/zone endpoint (generic pin-based format)"""

    @patch("src.app.app.DartboardService")
    def test_submit_score_zone_triple_20(
        self,
        mock_service,
        client,
        mock_game_manager,
        mock_db_session,
    ):
        """Test submitting zone-based score for triple 20"""
        # Mock the dartboard service
        mock_service.get_zone_from_pins.return_value = {
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
        assert data["zone_info"]["zone_number"] == 20
        assert data["zone_info"]["multiplier_type"] == "TRIPLE"
        assert data["zone_info"]["score"] == 60
        mock_game_manager.process_score.assert_called_once()

    @patch("src.app.app.DartboardService")
    def test_submit_score_zone_triple_4(
        self,
        mock_service,
        client,
        mock_game_manager,
        mock_db_session,
    ):
        """Test submitting zone-based score for triple 4 (was problematic)"""
        mock_service.get_zone_from_pins.return_value = {
            "zone_number": 4,
            "multiplier_type": "TRIPLE",
            "base_value": 4,
            "score": 12,
        }

        response = client.post(
            "/api/Throw/zone",
            json={"masterPin": 2, "slavePin": 4, "boardType": "carromco"},
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["zone_info"]["zone_number"] == 4
        assert data["zone_info"]["score"] == 12

    @patch("src.app.app.DartboardService")
    def test_submit_score_zone_triple_13(
        self,
        mock_service,
        client,
        mock_game_manager,
        mock_db_session,
    ):
        """Test submitting zone-based score for triple 13 (was problematic)"""
        mock_service.get_zone_from_pins.return_value = {
            "zone_number": 13,
            "multiplier_type": "TRIPLE",
            "base_value": 13,
            "score": 39,
        }

        response = client.post(
            "/api/Throw/zone",
            json={"masterPin": 17, "slavePin": 5, "boardType": "carromco"},
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["zone_info"]["zone_number"] == 13
        assert data["zone_info"]["score"] == 39

    @patch("src.app.app.DartboardService")
    def test_submit_score_zone_bull(self, mock_service, client, mock_game_manager, mock_db_session):
        """Test submitting bull score"""
        mock_service.get_zone_from_pins.return_value = {
            "zone_number": 25,
            "multiplier_type": "BULL",
            "base_value": 25,
            "score": 25,
        }

        response = client.post(
            "/api/Throw/zone",
            json={"masterPin": 15, "slavePin": 2, "boardType": "carromco"},
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["zone_info"]["multiplier_type"] == "BULL"

    @patch("src.app.app.DartboardService")
    def test_submit_score_zone_dblbull(
        self,
        mock_service,
        client,
        mock_game_manager,
        mock_db_session,
    ):
        """Test submitting double bull score"""
        mock_service.get_zone_from_pins.return_value = {
            "zone_number": 25,
            "multiplier_type": "DBLBULL",
            "base_value": 25,
            "score": 50,
        }

        response = client.post(
            "/api/Throw/zone",
            json={"masterPin": 15, "slavePin": 4, "boardType": "carromco"},
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["zone_info"]["score"] == 50

    def test_submit_score_zone_invalid_pins(self, client, mock_game_manager, mock_db_session):
        """Test that non-integer pins are rejected"""
        response = client.post(
            "/api/Throw/zone",
            json={"masterPin": "4", "slavePin": 13, "boardType": "carromco"},
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"

    def test_submit_score_zone_missing_board_type(self, client, mock_game_manager, mock_db_session):
        """Test that missing boardType is rejected"""
        response = client.post(
            "/api/Throw/zone",
            json={"masterPin": 4, "slavePin": 13},
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert "boardType" in data["message"]

    def test_submit_score_zone_empty_board_type(self, client, mock_game_manager, mock_db_session):
        """Test that empty boardType is rejected"""
        response = client.post(
            "/api/Throw/zone",
            json={"masterPin": 4, "slavePin": 13, "boardType": ""},
            content_type="application/json",
        )

        assert response.status_code == 400

    @patch("src.app.app.DartboardService")
    def test_submit_score_zone_not_found(
        self,
        mock_service,
        client,
        mock_game_manager,
        mock_db_session,
    ):
        """Test handling of unmapped pin combination"""
        mock_service.get_zone_from_pins.return_value = None

        response = client.post(
            "/api/Throw/zone",
            json={"masterPin": 99, "slavePin": 99, "boardType": "carromco"},
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert "Zone mapping not found" in data["message"]

    @patch("src.app.app.DartboardService")
    def test_submit_score_zone_exception_handling(
        self,
        mock_service,
        client,
        mock_game_manager,
        mock_db_session,
    ):
        """Test exception handling in zone endpoint"""
        mock_service.get_zone_from_pins.side_effect = Exception("Service error")

        response = client.post(
            "/api/Throw/zone",
            json={"masterPin": 4, "slavePin": 13, "boardType": "carromco"},
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"

    @patch("src.app.app.DartboardService")
    def test_submit_score_zone_with_user(
        self,
        mock_service,
        client,
        mock_game_manager,
        mock_db_session,
    ):
        """Test zone submission with optional user field"""
        mock_service.get_zone_from_pins.return_value = {
            "zone_number": 20,
            "multiplier_type": "TRIPLE",
            "base_value": 20,
            "score": 60,
        }

        response = client.post(
            "/api/Throw/zone",
            json={
                "masterPin": 4,
                "slavePin": 13,
                "boardType": "carromco",
                "user": "dgroen",
            },
            content_type="application/json",
        )

        assert response.status_code == 200

    @patch("src.app.app.DartboardService")
    def test_submit_score_zone_case_insensitive_board_type(
        self,
        mock_service,
        client,
        mock_game_manager,
        mock_db_session,
    ):
        """Test that boardType is case-insensitive"""
        mock_service.get_zone_from_pins.return_value = {
            "zone_number": 20,
            "multiplier_type": "TRIPLE",
            "base_value": 20,
            "score": 60,
        }

        response = client.post(
            "/api/Throw/zone",
            json={"masterPin": 4, "slavePin": 13, "boardType": "CARROMCO"},
            content_type="application/json",
        )

        assert response.status_code == 200


class TestDartboardTypesEndpoint:
    """Test /api/dartboard/types endpoint"""

    @patch("src.app.app.DartboardService")
    def test_get_dartboard_types_empty(self, mock_service, client, mock_db_session):
        """Test getting dartboard types when none exist"""
        mock_service.list_dartboard_types.return_value = []

        response = client.get("/api/dartboard/types")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert len(data["types"]) == 0

    @patch("src.app.app.DartboardService")
    def test_get_dartboard_types_multiple(self, mock_service, client, mock_db_session):
        """Test getting multiple dartboard types"""
        mock_board1 = MagicMock()
        mock_board1.id = 1
        mock_board1.name = "carromco"
        mock_board1.brand = "Carromco"
        mock_board1.model = "Striker"
        mock_board1.description = "Carromco Striker board"

        mock_board2 = MagicMock()
        mock_board2.id = 2
        mock_board2.name = "winmau"
        mock_board2.brand = "Winmau"
        mock_board2.model = "Blade 6"
        mock_board2.description = "Winmau Blade 6 board"

        mock_service.list_dartboard_types.return_value = [mock_board1, mock_board2]

        response = client.get("/api/dartboard/types")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert len(data["types"]) == 2
        assert data["types"][0]["name"] == "carromco"
        assert data["types"][1]["name"] == "winmau"

    @patch("src.app.app.DartboardService")
    def test_get_dartboard_types_exception(self, mock_service, client, mock_db_session):
        """Test exception handling in types endpoint"""
        mock_service.list_dartboard_types.side_effect = Exception("DB error")

        response = client.get("/api/dartboard/types")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"


class TestDartboardMappingsEndpoint:
    """Test /api/dartboard/types/<board_type>/mappings endpoint"""

    @patch("src.app.app.DartboardService")
    def test_get_mappings_for_type(self, mock_service, client, mock_db_session):
        """Test getting mappings for a dartboard type"""
        mock_mapping1 = MagicMock()
        mock_mapping1.master_pin = 4
        mock_mapping1.slave_pin = 13
        mock_mapping1.zone_number = 20
        mock_mapping1.multiplier_type = "TRIPLE"
        mock_mapping1.base_value = 20

        mock_mapping2 = MagicMock()
        mock_mapping2.master_pin = 4
        mock_mapping2.slave_pin = 12
        mock_mapping2.zone_number = 20
        mock_mapping2.multiplier_type = "DOUBLE"
        mock_mapping2.base_value = 20

        mock_service.get_dartboard_type_mappings.return_value = [mock_mapping1, mock_mapping2]

        response = client.get("/api/dartboard/types/carromco/mappings")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert data["board_type"] == "carromco"
        assert len(data["mappings"]) == 2
        assert data["mappings"][0]["master_pin"] == 4
        assert data["mappings"][0]["zone_number"] == 20

    @patch("src.app.app.DartboardService")
    def test_get_mappings_type_not_found(self, mock_service, client, mock_db_session):
        """Test getting mappings for non-existent type"""
        mock_service.get_dartboard_type_mappings.return_value = None

        response = client.get("/api/dartboard/types/nonexistent/mappings")

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data["status"] == "error"

    @patch("src.app.app.DartboardService")
    def test_get_mappings_exception(self, mock_service, client, mock_db_session):
        """Test exception handling in mappings endpoint"""
        mock_service.get_dartboard_type_mappings.side_effect = Exception("DB error")

        response = client.get("/api/dartboard/types/carromco/mappings")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"


class TestBackwardsCompatibility:
    """Test backwards compatibility between old and new endpoints"""

    @patch("src.app.app.DartboardService")
    def test_legacy_endpoint_still_works(self, mock_service, client, mock_game_manager):
        """Test that legacy endpoint still works with old boards"""
        response = client.post(
            "/api/Throw",
            json={"score": 20, "multiplier": "TRIPLE"},
            content_type="application/json",
        )

        assert response.status_code == 200
        mock_game_manager.process_score.assert_called_once()

    @patch("src.app.app.DartboardService")
    def test_both_endpoints_work_simultaneously(
        self,
        mock_service,
        client,
        mock_game_manager,
        mock_db_session,
    ):
        """Test that both old and new endpoints can be used simultaneously"""
        # Legacy endpoint
        response1 = client.post(
            "/api/Throw",
            json={"score": 20, "multiplier": "TRIPLE"},
            content_type="application/json",
        )
        assert response1.status_code == 200

        # New endpoint
        mock_service.get_zone_from_pins.return_value = {
            "zone_number": 20,
            "multiplier_type": "TRIPLE",
            "base_value": 20,
            "score": 60,
        }

        response2 = client.post(
            "/api/Throw/zone",
            json={"masterPin": 4, "slavePin": 13, "boardType": "carromco"},
            content_type="application/json",
        )
        assert response2.status_code == 200

        # Both should have called process_score
        assert mock_game_manager.process_score.call_count == 2


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_submit_zero_score_legacy(self, client, mock_game_manager):
        """Test submitting zero score"""
        response = client.post(
            "/api/Throw",
            json={"score": 0, "multiplier": "SINGLE"},
            content_type="application/json",
        )

        assert response.status_code == 200

    def test_submit_max_score_legacy(self, client, mock_game_manager):
        """Test submitting maximum score (20 x TRIPLE = 60)"""
        response = client.post(
            "/api/Throw",
            json={"score": 20, "multiplier": "TRIPLE"},
            content_type="application/json",
        )

        assert response.status_code == 200

    @patch("src.app.app.DartboardService")
    def test_submit_negative_pins(self, mock_service, client, mock_game_manager, mock_db_session):
        """Test submitting negative GPIO pin numbers (should fail validation)"""
        response = client.post(
            "/api/Throw/zone",
            json={"masterPin": -1, "slavePin": 13, "boardType": "carromco"},
            content_type="application/json",
        )

        # The endpoint will still accept negative numbers in the validation
        # but the dartboard service should not find a mapping
        mock_service.get_zone_from_pins.return_value = None

        response = client.post(
            "/api/Throw/zone",
            json={"masterPin": -1, "slavePin": 13, "boardType": "carromco"},
            content_type="application/json",
        )

        assert response.status_code == 400

    @patch("src.app.app.DartboardService")
    def test_submit_large_pin_numbers(
        self,
        mock_service,
        client,
        mock_game_manager,
        mock_db_session,
    ):
        """Test submitting very large GPIO pin numbers"""
        mock_service.get_zone_from_pins.return_value = {
            "zone_number": 20,
            "multiplier_type": "TRIPLE",
            "base_value": 20,
            "score": 60,
        }

        response = client.post(
            "/api/Throw/zone",
            json={"masterPin": 9999, "slavePin": 9999, "boardType": "carromco"},
            content_type="application/json",
        )

        # Should work if service has the mapping
        assert response.status_code == 200
