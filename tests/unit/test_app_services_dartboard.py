"""Unit tests for app_services.py endpoints (Part 1: Dartboard and Score submission)."""

import json
from unittest.mock import MagicMock, patch

import pytest
from dartserver_core.database_service import DatabaseService


@pytest.fixture
def db_service():
    """Create in-memory database service for testing."""
    db = DatabaseService("sqlite:///:memory:?check_same_thread=False")
    db.initialize_database()
    return db


@pytest.fixture
def client(flask_app, db_service):
    """Create authenticated test client."""
    with flask_app.test_client() as client:
        with client.session_transaction() as sess:
            sess["access_token"] = "test-token"
            sess["user_info"] = {"username": "testuser", "sub": "test-user"}
            sess["player_id"] = 1

        flask_app.game_manager.db_service = db_service

        with patch("src.core.auth.validate_token") as mock_validate:
            mock_validate.return_value = {
                "sub": "test-user",
                "groups": ["admin"],
                "roles": ["admin"],
            }
            yield client


class TestScoreSubmission:
    """Test score submission endpoints."""

    def test_submit_score_zone_valid(self, client):
        """Test submitting valid score via zone."""
        with (
            patch("src.app.app_services.get_session") as mock_get_session,
            patch("src.app.app_services.DartboardService.get_zone_from_pins") as mock_get_zone,
            patch("src.app.app_services.current_app") as mock_app,
        ):
            # Mock database session
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session

            # Mock zone lookup
            mock_get_zone.return_value = {
                "zone_number": 20,
                "multiplier_type": "TRIPLE",
                "base_value": 20,
                "score": 60,
            }

            # Mock game manager
            mock_game_manager = MagicMock()
            mock_socketio = MagicMock()
            mock_app.game_manager = mock_game_manager
            mock_app.socketio = mock_socketio

            response = client.post(
                "/api/Throw/zone",
                data=json.dumps({
                    "masterPin": 4,
                    "slavePin": 13,
                    "boardType": "carromco",
                }),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["status"] == "success"
            assert "zone_info" in data

            # Verify score was processed
            mock_game_manager.process_score.assert_called_once()

    def test_submit_score_zone_invalid_pins(self, client):
        """Test submitting score with invalid pin types."""
        response = client.post(
            "/api/Throw/zone",
            data=json.dumps({
                "masterPin": "invalid",
                "slavePin": 13,
                "boardType": "carromco",
            }),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"

    def test_submit_score_zone_missing_board_type(self, client):
        """Test submitting score without board type."""
        response = client.post(
            "/api/Throw/zone",
            data=json.dumps({
                "masterPin": 4,
                "slavePin": 13,
            }),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"

    def test_submit_score_zone_not_found(self, client):
        """Test submitting score with unmapped zone."""
        with (
            patch("src.app.app_services.get_session") as mock_get_session,
            patch("src.app.app_services.DartboardService.get_zone_from_pins") as mock_get_zone,
            patch("src.app.app_services.current_app") as mock_app,
        ):
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session
            mock_get_zone.return_value = None
            mock_socketio = MagicMock()
            mock_app.socketio = mock_socketio

            response = client.post(
                "/api/Throw/zone",
                data=json.dumps({
                    "masterPin": 99,
                    "slavePin": 99,
                    "boardType": "unknown",
                }),
                content_type="application/json",
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert data["status"] == "error"
            assert "not found" in data["message"].lower()


class TestDartboardTypesEndpoints:
    """Test dartboard types endpoints."""

    def test_get_dartboard_types(self, client):
        """Test getting all dartboard types."""
        with (
            patch("src.app.app_services.get_session") as mock_get_session,
            patch("src.app.app_services.DartboardService.list_dartboard_types") as mock_list,
        ):
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session

            mock_type = MagicMock()
            mock_type.id = 1
            mock_type.name = "carromco"
            mock_type.brand = "Carromco"
            mock_type.model = "Striker 601"
            mock_type.description = "Electronic dartboard"

            mock_list.return_value = [mock_type]

            response = client.get("/api/dartboard/types")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["status"] == "success"
            assert len(data["types"]) == 1
            assert data["types"][0]["name"] == "carromco"

    def test_get_dartboard_mappings_valid_type(self, client):
        """Test getting dartboard mappings for valid type."""
        with (
            patch("src.app.app_services.get_session") as mock_get_session,
            patch("src.app.app_services.DartboardService.get_dartboard_type_mappings") as mock_get,
        ):
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session

            mock_mapping = MagicMock()
            mock_mapping.master_pin = 4
            mock_mapping.slave_pin = 13
            mock_mapping.zone_number = 20
            mock_mapping.multiplier_type = "TRIPLE"
            mock_mapping.base_value = 20

            mock_get.return_value = [mock_mapping]

            response = client.get("/api/dartboard/types/carromco/mappings")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["status"] == "success"
            assert data["board_type"] == "carromco"
            assert len(data["mappings"]) == 1

    def test_get_dartboard_mappings_invalid_type(self, client):
        """Test getting mappings for non-existent type."""
        with (
            patch("src.app.app_services.get_session") as mock_get_session,
            patch("src.app.app_services.DartboardService.get_dartboard_type_mappings") as mock_get,
        ):
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session
            mock_get.return_value = None

            response = client.get("/api/dartboard/types/nonexistent/mappings")

            assert response.status_code == 404
            data = json.loads(response.data)
            assert data["status"] == "error"


class TestAdminDartboardEndpoints:
    """Test admin dartboard management endpoints."""

    def test_get_dartboard_matrix_requires_auth(self, flask_app):
        """Test getting dartboard matrix requires authentication."""
        with flask_app.test_client() as client:
            response = client.get("/api/admin/dartboard/matrix/carromco")
            assert response.status_code in [302, 401, 403]

    def test_get_dartboard_matrix_requires_admin_role(self, flask_app, db_service):
        """Test getting dartboard matrix requires admin role."""
        with flask_app.test_client() as client:
            with client.session_transaction() as sess:
                sess["access_token"] = "test-token"
                sess["user_info"] = {"username": "testuser"}

            flask_app.game_manager.db_service = db_service

            with patch("src.core.auth.validate_token") as mock_validate:
                mock_validate.return_value = {"sub": "test-user", "groups": []}

                response = client.get("/api/admin/dartboard/matrix/carromco")
                assert response.status_code in [302, 401, 403]

    def test_get_dartboard_matrix_valid_type(self, client):
        """Test getting dartboard matrix for valid type."""
        with (
            patch("src.app.app_services.get_session") as mock_get_session,
            patch("src.app.app_services.DartboardService.get_matrix_visualization") as mock_get,
        ):
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session

            mock_get.return_value = (
                {"id": 1, "name": "carromco"},
                [2, 4, 5],
                [12, 13, 14],
                [[{"zone": 20}]],
            )

            response = client.get("/api/admin/dartboard/matrix/carromco")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["status"] == "success"
            assert "dartboard_type" in data
            assert "master_pins" in data
            assert "slave_pins" in data
            assert "matrix" in data

    def test_update_dartboard_mapping_requires_admin(self, flask_app):
        """Test updating dartboard mapping requires admin role."""
        with flask_app.test_client() as client:
            response = client.post(
                "/api/admin/dartboard/mapping",
                data=json.dumps({
                    "boardType": "carromco",
                    "masterPin": 4,
                    "slavePin": 13,
                    "zoneNumber": 20,
                    "multiplierType": "TRIPLE",
                    "baseValue": 20,
                }),
                content_type="application/json",
            )
            assert response.status_code in [302, 401, 403]

    def test_update_dartboard_mapping_valid(self, client):
        """Test updating dartboard mapping with valid data."""
        with (
            patch("src.app.app_services.get_session") as mock_get_session,
            patch("src.app.app_services.DartboardService.update_zone_mapping") as mock_update,
        ):
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session

            response = client.post(
                "/api/admin/dartboard/mapping",
                data=json.dumps({
                    "boardType": "carromco",
                    "masterPin": 4,
                    "slavePin": 13,
                    "zoneNumber": 20,
                    "multiplierType": "TRIPLE",
                    "baseValue": 20,
                }),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["status"] == "success"

            mock_update.assert_called_once()

    def test_update_dartboard_mapping_missing_fields(self, client):
        """Test updating dartboard mapping with missing fields."""
        response = client.post(
            "/api/admin/dartboard/mapping",
            data=json.dumps({
                "boardType": "carromco",
                "masterPin": 4,
                # Missing slavePin and other required fields
            }),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"

    def test_import_dartboard_mappings_requires_admin(self, flask_app):
        """Test importing dartboard mappings requires admin role."""
        with flask_app.test_client() as client:
            response = client.post(
                "/api/admin/dartboard/import",
                data=json.dumps({
                    "boardType": "test",
                    "mappings": [],
                }),
                content_type="application/json",
            )
            assert response.status_code in [302, 401, 403]

    def test_import_dartboard_mappings_valid(self, client):
        """Test importing dartboard mappings with valid data."""
        with (
            patch("src.app.app_services.get_session") as mock_get_session,
            patch("src.app.app_services.DartboardService.bulk_import_mappings") as mock_import,
        ):
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session
            mock_import.return_value = (5, 3)  # created, updated

            response = client.post(
                "/api/admin/dartboard/import",
                data=json.dumps({
                    "boardType": "carromco",
                    "mappings": [
                        {
                            "masterPin": 4,
                            "slavePin": 13,
                            "zoneNumber": 20,
                            "multiplierType": "TRIPLE",
                            "baseValue": 20,
                        },
                    ],
                }),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["status"] == "success"
            assert data["created"] == 5
            assert data["updated"] == 3

    def test_create_dartboard_type_requires_admin(self, flask_app):
        """Test creating dartboard type requires admin role."""
        with flask_app.test_client() as client:
            response = client.post(
                "/api/admin/dartboard/type",
                data=json.dumps({
                    "name": "test",
                    "brand": "Test Brand",
                }),
                content_type="application/json",
            )
            assert response.status_code in [302, 401, 403]

    def test_create_dartboard_type_valid(self, client):
        """Test creating dartboard type with valid data."""
        with (
            patch("src.app.app_services.get_session") as mock_get_session,
            patch("src.app.app_services.DartboardService.register_dartboard_type") as mock_register,
        ):
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session

            mock_type = MagicMock()
            mock_type.id = 2
            mock_type.name = "granboard"
            mock_type.brand = "Gran Board"
            mock_type.model = "Gran Board 3"
            mock_type.description = "Bluetooth dartboard"

            mock_register.return_value = mock_type

            response = client.post(
                "/api/admin/dartboard/type",
                data=json.dumps({
                    "name": "granboard",
                    "brand": "Gran Board",
                    "model": "Gran Board 3",
                    "description": "Bluetooth dartboard",
                    "masterPins": [2, 4, 5],
                    "slavePins": [12, 13, 14],
                }),
                content_type="application/json",
            )

            assert response.status_code == 201
            data = json.loads(response.data)
            assert data["status"] == "success"
            assert data["dartboard_type"]["name"] == "granboard"

    def test_create_dartboard_type_missing_name(self, client):
        """Test creating dartboard type without name."""
        response = client.post(
            "/api/admin/dartboard/type",
            data=json.dumps({
                "brand": "Test Brand",
            }),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data["status"] == "error"

    def test_update_dartboard_pins_requires_admin(self, flask_app):
        """Test updating dartboard pins requires admin role."""
        with flask_app.test_client() as client:
            response = client.put(
                "/api/admin/dartboard/type/carromco/pins",
                data=json.dumps({
                    "masterPins": [2, 4, 5],
                    "slavePins": [12, 13, 14],
                }),
                content_type="application/json",
            )
            assert response.status_code in [302, 401, 403]

    def test_update_dartboard_pins_valid(self, client):
        """Test updating dartboard pins with valid data."""
        with (
            patch("src.app.app_services.get_session") as mock_get_session,
            patch("src.app.app_services.DartboardService.update_dartboard_pins") as mock_update,
        ):
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session

            mock_type = MagicMock()
            mock_type.id = 1
            mock_type.name = "carromco"

            mock_update.return_value = mock_type

            response = client.put(
                "/api/admin/dartboard/type/carromco/pins",
                data=json.dumps({
                    "masterPins": [2, 4, 5],
                    "slavePins": [12, 13, 14],
                }),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["status"] == "success"

    def test_get_available_pins(self, client):
        """Test getting available GPIO pins."""
        response = client.get("/api/admin/dartboard/available-pins")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert "pins" in data
        assert isinstance(data["pins"], list)
