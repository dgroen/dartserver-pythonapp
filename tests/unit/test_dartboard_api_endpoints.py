"""
Unit tests for dartboard API endpoints
Tests both legacy /api/Throw and new /api/Throw/zone endpoints
Also tests dartboard management endpoints including admin endpoints
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from dartserver_services import DartboardMappingError


@pytest.fixture
def client(flask_app):
    """Create test client"""
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client


@pytest.fixture
def mock_game_manager():
    """Mock game manager"""
    mock_app = MagicMock()
    mock_app.game_manager.process_score = MagicMock()
    with patch("src.app.app_services._app", return_value=mock_app):
        yield mock_app.game_manager


@pytest.fixture
def mock_db_session():
    """Create mock database session"""
    with patch("dartserver_core.database_service.get_session") as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        yield mock_session


class TestNewZoneThrowEndpoint:
    """Test new /api/Throw/zone endpoint (generic pin-based format)"""

    @patch("src.app.app_services.DartboardService")
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

    @patch("src.app.app_services.DartboardService")
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

    @patch("src.app.app_services.DartboardService")
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

    @patch("src.app.app_services.DartboardService")
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

    @patch("src.app.app_services.DartboardService")
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

    @patch("src.app.app_services.DartboardService")
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

    @patch("src.app.app_services.DartboardService")
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

    @patch("src.app.app_services.DartboardService")
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

    @patch("src.app.app_services.DartboardService")
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

    @patch("src.app.app_services.DartboardService")
    def test_get_dartboard_types_empty(self, mock_service, client, mock_db_session):
        """Test getting dartboard types when none exist"""
        mock_service.list_dartboard_types.return_value = []

        response = client.get("/api/dartboard/types")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert len(data["types"]) == 0

    @patch("src.app.app_services.DartboardService")
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

    @patch("src.app.app_services.DartboardService")
    def test_get_dartboard_types_exception(self, mock_service, client, mock_db_session):
        """Test exception handling in types endpoint"""
        mock_service.list_dartboard_types.side_effect = Exception("DB error")

        response = client.get("/api/dartboard/types")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"


class TestDartboardMappingsEndpoint:
    """Test /api/dartboard/types/<board_type>/mappings endpoint"""

    @patch("src.app.app_services.DartboardService")
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

    @patch("src.app.app_services.DartboardService")
    def test_get_mappings_type_not_found(self, mock_service, client, mock_db_session):
        """Test getting mappings for non-existent type"""
        mock_service.get_dartboard_type_mappings.return_value = None

        response = client.get("/api/dartboard/types/nonexistent/mappings")

        assert response.status_code == 404
        data = json.loads(response.data)
        assert data["status"] == "error"

    @patch("src.app.app_services.DartboardService")
    def test_get_mappings_exception(self, mock_service, client, mock_db_session):
        """Test exception handling in mappings endpoint"""
        mock_service.get_dartboard_type_mappings.side_effect = Exception("DB error")

        response = client.get("/api/dartboard/types/carromco/mappings")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    @patch("src.app.app_services.DartboardService")
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

    @patch("src.app.app_services.DartboardService")
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


class TestCreateDartboardTypeEndpoint:
    """Test /api/admin/dartboard/type endpoint"""

    @pytest.fixture
    def admin_client(self, flask_app):
        """Create test client with admin authentication"""
        flask_app.config["TESTING"] = True
        with flask_app.test_client() as client:
            with client.session_transaction() as sess:
                sess["access_token"] = "test-admin-token"
            yield client

    @patch("dartserver_core.auth.validate_token")
    @patch("src.app.app_services.DartboardService")
    @patch("dartserver_core.database_service.get_session")
    def test_create_dartboard_type_success(
        self,
        mock_get_session,
        mock_service,
        mock_validate,
        admin_client,
    ):
        """Test successful dartboard type creation"""
        mock_validate.return_value = {
            "sub": "admin-user",
            "username": "admin",
            "groups": ["admin"],
        }

        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_dartboard = MagicMock()
        mock_dartboard.id = 1
        mock_dartboard.name = "granboard"
        mock_dartboard.brand = "Gran Board"
        mock_dartboard.model = "Gran Board 3"
        mock_dartboard.description = "Electronic dartboard"
        mock_service.register_dartboard_type.return_value = mock_dartboard

        response = admin_client.post(
            "/api/admin/dartboard/type",
            json={
                "name": "granboard",
                "brand": "Gran Board",
                "model": "Gran Board 3",
                "description": "Electronic dartboard",
            },
            content_type="application/json",
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "granboard" in data["message"]
        assert data["dartboard_type"]["name"] == "granboard"
        assert data["dartboard_type"]["brand"] == "Gran Board"

    @patch("dartserver_core.auth.validate_token")
    @patch("dartserver_core.database_service.get_session")
    def test_create_dartboard_type_missing_name(
        self,
        mock_get_session,
        mock_validate,
        admin_client,
    ):
        """Test creating dartboard type without name fails"""
        mock_validate.return_value = {
            "sub": "admin-user",
            "username": "admin",
            "groups": ["admin"],
        }

        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        response = admin_client.post(
            "/api/admin/dartboard/type",
            json={"brand": "Some Brand"},
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert "Name is required" in data["message"]

    @patch("dartserver_core.auth.validate_token")
    @patch("dartserver_core.database_service.get_session")
    def test_create_dartboard_type_missing_brand(
        self,
        mock_get_session,
        mock_validate,
        admin_client,
    ):
        """Test creating dartboard type without brand fails"""
        mock_validate.return_value = {
            "sub": "admin-user",
            "username": "admin",
            "groups": ["admin"],
        }

        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        response = admin_client.post(
            "/api/admin/dartboard/type",
            json={"name": "someboard"},
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert "Brand is required" in data["message"]

    @patch("dartserver_core.auth.validate_token")
    @patch("dartserver_core.database_service.get_session")
    def test_create_dartboard_type_invalid_name_format(
        self,
        mock_get_session,
        mock_validate,
        admin_client,
    ):
        """Test creating dartboard type with invalid name format fails"""
        mock_validate.return_value = {
            "sub": "admin-user",
            "username": "admin",
            "groups": ["admin"],
        }

        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        response = admin_client.post(
            "/api/admin/dartboard/type",
            json={"name": "invalid name!", "brand": "Some Brand"},
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert "letters, numbers" in data["message"].lower()

    @patch("dartserver_core.auth.validate_token")
    @patch("src.app.app_services.DartboardService")
    @patch("dartserver_core.database_service.get_session")
    def test_create_dartboard_type_duplicate(
        self,
        mock_get_session,
        mock_service,
        mock_validate,
        admin_client,
    ):
        """Test creating duplicate dartboard type fails"""
        mock_validate.return_value = {
            "sub": "admin-user",
            "username": "admin",
            "groups": ["admin"],
        }

        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_service.register_dartboard_type.side_effect = DartboardMappingError(
            "Dartboard type 'carromco' already exists",
        )

        response = admin_client.post(
            "/api/admin/dartboard/type",
            json={"name": "carromco", "brand": "Carromco"},
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert "already exists" in data["message"]

    @patch("dartserver_core.auth.validate_token")
    def test_create_dartboard_type_non_admin(self, mock_validate, admin_client):
        """Test that non-admin users cannot create dartboard types"""
        mock_validate.return_value = {
            "sub": "regular-user",
            "username": "player",
            "groups": ["player"],
        }

        response = admin_client.post(
            "/api/admin/dartboard/type",
            json={"name": "someboard", "brand": "Some Brand"},
            content_type="application/json",
        )

        assert response.status_code == 403

    def test_create_dartboard_type_unauthenticated(self, client):
        """Test that unauthenticated users cannot create dartboard types"""
        response = client.post(
            "/api/admin/dartboard/type",
            json={"name": "someboard", "brand": "Some Brand"},
            content_type="application/json",
        )

        # Should redirect to login or return 401
        assert response.status_code in [302, 401]

    @patch("dartserver_core.auth.validate_token")
    @patch("src.app.app_services.DartboardService")
    @patch("dartserver_core.database_service.get_session")
    def test_create_dartboard_type_with_hyphens_and_underscores(
        self,
        mock_get_session,
        mock_service,
        mock_validate,
        admin_client,
    ):
        """Test creating dartboard type with valid special characters"""
        mock_validate.return_value = {
            "sub": "admin-user",
            "username": "admin",
            "groups": ["admin"],
        }

        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_dartboard = MagicMock()
        mock_dartboard.id = 2
        mock_dartboard.name = "gran-board_3s"
        mock_dartboard.brand = "Gran Board"
        mock_dartboard.model = "3S"
        mock_dartboard.description = None
        mock_service.register_dartboard_type.return_value = mock_dartboard

        response = admin_client.post(
            "/api/admin/dartboard/type",
            json={"name": "gran-board_3s", "brand": "Gran Board", "model": "3S"},
            content_type="application/json",
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["status"] == "success"

    @patch("dartserver_core.auth.validate_token")
    @patch("src.app.app_services.DartboardService")
    @patch("dartserver_core.database_service.get_session")
    def test_create_dartboard_type_minimal(
        self,
        mock_get_session,
        mock_service,
        mock_validate,
        admin_client,
    ):
        """Test creating dartboard type with only required fields"""
        mock_validate.return_value = {
            "sub": "admin-user",
            "username": "admin",
            "groups": ["admin"],
        }

        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_dartboard = MagicMock()
        mock_dartboard.id = 3
        mock_dartboard.name = "newboard"
        mock_dartboard.brand = "New Brand"
        mock_dartboard.model = None
        mock_dartboard.description = None
        mock_service.register_dartboard_type.return_value = mock_dartboard

        response = admin_client.post(
            "/api/admin/dartboard/type",
            json={"name": "newboard", "brand": "New Brand"},
            content_type="application/json",
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert data["dartboard_type"]["model"] is None
        assert data["dartboard_type"]["description"] is None


class TestUpdateDartboardPinsEndpoint:
    """Test /api/admin/dartboard/type/<board_type>/pins endpoint"""

    @pytest.fixture
    def admin_client(self, flask_app):
        """Create test client with admin authentication"""
        flask_app.config["TESTING"] = True
        with flask_app.test_client() as client:
            with client.session_transaction() as sess:
                sess["access_token"] = "test-admin-token"
            yield client

    @patch("dartserver_core.auth.validate_token")
    @patch("src.app.app_services.DartboardService")
    @patch("dartserver_core.database_service.get_session")
    def test_update_pins_success(
        self,
        mock_get_session,
        mock_service,
        mock_validate,
        admin_client,
    ):
        """Test successfully updating dartboard pins"""
        mock_validate.return_value = {
            "sub": "admin-user",
            "username": "admin",
            "groups": ["admin"],
        }

        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_dartboard = MagicMock()
        mock_dartboard.id = 1
        mock_dartboard.name = "carromco"
        mock_service.update_dartboard_pins.return_value = mock_dartboard

        response = admin_client.put(
            "/api/admin/dartboard/type/carromco/pins",
            json={
                "masterPins": [2, 4, 5, 16, 17, 18, 19],
                "slavePins": [12, 13, 14, 25, 26, 27, 32, 33],
            },
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        mock_service.update_dartboard_pins.assert_called_once()

    @patch("dartserver_core.auth.validate_token")
    @patch("dartserver_core.database_service.get_session")
    def test_update_pins_invalid_master_pins(
        self,
        mock_get_session,
        mock_validate,
        admin_client,
    ):
        """Test updating pins with invalid masterPins type"""
        mock_validate.return_value = {
            "sub": "admin-user",
            "username": "admin",
            "groups": ["admin"],
        }

        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        response = admin_client.put(
            "/api/admin/dartboard/type/carromco/pins",
            json={"masterPins": "not-an-array"},
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "array of integers" in data["message"]

    @patch("dartserver_core.auth.validate_token")
    @patch("src.app.app_services.DartboardService")
    @patch("dartserver_core.database_service.get_session")
    def test_update_pins_not_found(
        self,
        mock_get_session,
        mock_service,
        mock_validate,
        admin_client,
    ):
        """Test updating pins for non-existent dartboard type"""
        mock_validate.return_value = {
            "sub": "admin-user",
            "username": "admin",
            "groups": ["admin"],
        }

        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_service.update_dartboard_pins.side_effect = DartboardMappingError(
            "Dartboard type 'nonexistent' not found",
        )

        response = admin_client.put(
            "/api/admin/dartboard/type/nonexistent/pins",
            json={"masterPins": [2, 4, 5]},
            content_type="application/json",
        )

        assert response.status_code == 404

    @patch("dartserver_core.auth.validate_token")
    def test_update_pins_non_admin(self, mock_validate, admin_client):
        """Test that non-admin users cannot update pins"""
        mock_validate.return_value = {
            "sub": "regular-user",
            "username": "player",
            "groups": ["player"],
        }

        response = admin_client.put(
            "/api/admin/dartboard/type/carromco/pins",
            json={"masterPins": [2, 4, 5]},
            content_type="application/json",
        )

        assert response.status_code == 403


class TestCreateDartboardTypeWithPins:
    """Test creating dartboard types with pin configuration"""

    @pytest.fixture
    def admin_client(self, flask_app):
        """Create test client with admin authentication"""
        flask_app.config["TESTING"] = True
        with flask_app.test_client() as client:
            with client.session_transaction() as sess:
                sess["access_token"] = "test-admin-token"
            yield client

    @patch("dartserver_core.auth.validate_token")
    @patch("src.app.app_services.DartboardService")
    @patch("dartserver_core.database_service.get_session")
    def test_create_with_pins(
        self,
        mock_get_session,
        mock_service,
        mock_validate,
        admin_client,
    ):
        """Test creating dartboard type with pin configuration"""
        mock_validate.return_value = {
            "sub": "admin-user",
            "username": "admin",
            "groups": ["admin"],
        }

        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_dartboard = MagicMock()
        mock_dartboard.id = 1
        mock_dartboard.name = "newboard"
        mock_dartboard.brand = "New Brand"
        mock_dartboard.model = None
        mock_dartboard.description = None
        mock_service.register_dartboard_type.return_value = mock_dartboard

        response = admin_client.post(
            "/api/admin/dartboard/type",
            json={
                "name": "newboard",
                "brand": "New Brand",
                "masterPins": [2, 4, 5, 16, 17, 18, 19],
                "slavePins": [12, 13, 14, 25, 26, 27, 32, 33],
            },
            content_type="application/json",
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["status"] == "success"
        # Verify pins were passed to service
        call_kwargs = mock_service.register_dartboard_type.call_args[1]
        assert call_kwargs["master_pins"] == [2, 4, 5, 16, 17, 18, 19]
        assert call_kwargs["slave_pins"] == [12, 13, 14, 25, 26, 27, 32, 33]


class TestGetAvailablePinsEndpoint:
    """Test /api/admin/dartboard/available-pins endpoint"""

    @pytest.fixture
    def admin_client(self, flask_app):
        """Create test client with admin authentication"""
        flask_app.config["TESTING"] = True
        with flask_app.test_client() as client:
            with client.session_transaction() as sess:
                sess["access_token"] = "test-admin-token"
            yield client

    @patch("dartserver_core.auth.validate_token")
    def test_get_available_pins(self, mock_validate, admin_client):
        """Test getting list of available GPIO pins"""
        mock_validate.return_value = {
            "sub": "admin-user",
            "username": "admin",
            "groups": ["admin"],
        }

        response = admin_client.get("/api/admin/dartboard/available-pins")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "pins" in data
        assert isinstance(data["pins"], list)
        assert 2 in data["pins"]  # Common ESP32 GPIO pin
        assert 4 in data["pins"]


class TestImportDartboardMappingsEndpoint:
    """Test /api/admin/dartboard/import endpoint"""

    @pytest.fixture
    def admin_client(self, flask_app):
        """Create test client with admin authentication"""
        flask_app.config["TESTING"] = True
        with flask_app.test_client() as client:
            with client.session_transaction() as sess:
                sess["access_token"] = "test-admin-token"
            yield client

    @patch("dartserver_core.auth.validate_token")
    def test_import_rejects_placeholder_board_type(self, mock_validate, admin_client):
        """Test that __new__ placeholder board type is rejected"""
        mock_validate.return_value = {
            "sub": "admin-user",
            "username": "admin",
            "groups": ["admin"],
        }

        response = admin_client.post(
            "/api/admin/dartboard/import",
            json={
                "boardType": "__new__",
                "mappings": [
                    {
                        "masterPin": 4,
                        "slavePin": 13,
                        "zoneNumber": 20,
                        "multiplierType": "TRIPLE",
                        "baseValue": 20,
                    },
                ],
            },
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"
        assert "__new__" in data["message"]
        assert "Invalid boardType" in data["message"]
