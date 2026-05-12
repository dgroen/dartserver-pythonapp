"""
Unit tests for API Gateway endpoints
Tests authentication, dartboard endpoints, and game control actions
"""

import json
from unittest.mock import patch

import pytest

import src.api_gateway.app as gateway_module
from src.api_gateway.app import app as gateway_app
from src.api_gateway.app import rabbitmq_publisher


@pytest.fixture
def client():
    """Create test client for API Gateway"""
    gateway_app.config["TESTING"] = True
    with gateway_app.test_client() as client:
        yield client


@pytest.fixture
def mock_rabbitmq():
    """Mock RabbitMQ publisher"""
    with patch.object(rabbitmq_publisher, "publish", return_value=True) as mock:
        yield mock


@pytest.fixture
def mock_jwt_validation():
    """Mock JWT validation to return valid claims"""
    with patch("src.api_gateway.app.validate_jwt_token") as mock:
        mock.return_value = {
            "sub": "test-user",
            "client_id": "dartboard-001",
            "scope": "dartboard:write score:write game:write game:control player:write",
        }
        yield mock


@pytest.fixture
def auth_headers():
    """Return valid authorization headers"""
    return {"Authorization": "Bearer test-token-123"}


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check_no_auth(self, client):
        """Health check should work without authentication"""
        response = client.get("/health")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "healthy"
        assert data["service"] == "darts-api-gateway"
        assert "timestamp" in data


class TestDartboardEndpoint:
    """Test dartboard throw endpoint"""

    def test_dartboard_throw_success(
        self,
        client,
        mock_rabbitmq,
        mock_jwt_validation,
        auth_headers,
    ):
        """Test successful dartboard throw submission"""
        response = client.post(
            "/api/v1/dartboard/throw",
            json={
                "masterPin": 4,
                "slavePin": 13,
                "boardType": "carromco",
            },
            headers=auth_headers,
            content_type="application/json",
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["status"] == "success"
        assert data["message"] == "Throw submitted successfully"

        # Verify RabbitMQ publish was called
        mock_rabbitmq.assert_called_once()
        call_args = mock_rabbitmq.call_args
        assert call_args[0][0] == "darts.dartboard.throw"
        message = call_args[0][1]
        assert message["masterPin"] == 4
        assert message["slavePin"] == 13
        assert message["boardType"] == "carromco"
        assert message["client_id"] == "dartboard-001"

    def test_dartboard_throw_no_auth(self, client):
        """Test dartboard throw without authentication"""
        response = client.post(
            "/api/v1/dartboard/throw",
            json={
                "masterPin": 4,
                "slavePin": 13,
                "boardType": "carromco",
            },
            content_type="application/json",
        )

        assert response.status_code == 401
        data = json.loads(response.data)
        assert "error" in data

    def test_dartboard_throw_missing_fields(
        self,
        client,
        mock_jwt_validation,
        auth_headers,
    ):
        """Test dartboard throw with missing required fields"""
        response = client.post(
            "/api/v1/dartboard/throw",
            json={"masterPin": 4},
            headers=auth_headers,
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "Missing required fields" in data["message"]

    def test_dartboard_throw_invalid_pins(
        self,
        client,
        mock_jwt_validation,
        auth_headers,
    ):
        """Test dartboard throw with invalid pin types"""
        response = client.post(
            "/api/v1/dartboard/throw",
            json={
                "masterPin": "not_a_number",
                "slavePin": 13,
                "boardType": "carromco",
            },
            headers=auth_headers,
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "integer" in data["message"].lower()

    def test_dartboard_throw_empty_board_type(
        self,
        client,
        mock_jwt_validation,
        auth_headers,
    ):
        """Test dartboard throw with empty board type"""
        response = client.post(
            "/api/v1/dartboard/throw",
            json={
                "masterPin": 4,
                "slavePin": 13,
                "boardType": "",
            },
            headers=auth_headers,
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data


class TestScoreEndpoint:
    """Test score submission endpoint"""

    def test_submit_score_success(
        self,
        client,
        mock_rabbitmq,
        mock_jwt_validation,
        auth_headers,
    ):
        """Test successful score submission"""
        response = client.post(
            "/api/v1/scores",
            json={
                "score": 20,
                "multiplier": "TRIPLE",
            },
            headers=auth_headers,
            content_type="application/json",
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["status"] == "success"

        # Verify RabbitMQ publish
        mock_rabbitmq.assert_called_once()
        call_args = mock_rabbitmq.call_args
        assert call_args[0][0] == "darts.scores.api"

    def test_submit_score_invalid_value(
        self,
        client,
        mock_jwt_validation,
        auth_headers,
    ):
        """Test score submission with invalid score value"""
        response = client.post(
            "/api/v1/scores",
            json={
                "score": 100,  # Invalid: max is 60
                "multiplier": "TRIPLE",
            },
            headers=auth_headers,
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_submit_score_invalid_multiplier(
        self,
        client,
        mock_jwt_validation,
        auth_headers,
    ):
        """Test score submission with invalid multiplier"""
        response = client.post(
            "/api/v1/scores",
            json={
                "score": 20,
                "multiplier": "QUADRUPLE",  # Invalid
            },
            headers=auth_headers,
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data


class TestGameEndpoints:
    """Test game management endpoints"""

    def test_create_game_success(
        self,
        client,
        mock_rabbitmq,
        mock_jwt_validation,
        auth_headers,
    ):
        """Test successful game creation"""
        response = client.post(
            "/api/v1/games",
            json={
                "game_type": "301",
                "players": ["Player 1", "Player 2"],
                "double_out": False,
            },
            headers=auth_headers,
            content_type="application/json",
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["status"] == "success"

        # Verify RabbitMQ publish
        mock_rabbitmq.assert_called_once()
        call_args = mock_rabbitmq.call_args
        assert call_args[0][0] == "darts.games.create"

    def test_create_game_invalid_type(
        self,
        client,
        mock_jwt_validation,
        auth_headers,
    ):
        """Test game creation with invalid game type"""
        response = client.post(
            "/api/v1/games",
            json={
                "game_type": "999",  # Invalid
                "players": ["Player 1"],
            },
            headers=auth_headers,
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_create_game_no_players(
        self,
        client,
        mock_jwt_validation,
        auth_headers,
    ):
        """Test game creation with no players"""
        response = client.post(
            "/api/v1/games",
            json={
                "game_type": "301",
                "players": [],
            },
            headers=auth_headers,
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data


class TestGameActions:
    """Test game control action endpoints"""

    def test_end_turn_success(
        self,
        client,
        mock_rabbitmq,
        mock_jwt_validation,
        auth_headers,
    ):
        """Test ending turn successfully"""
        response = client.post(
            "/api/v1/game/actions/end-turn",
            json={"game_id": "test-game-123"},
            headers=auth_headers,
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"

        # Verify RabbitMQ publish
        mock_rabbitmq.assert_called_once()
        call_args = mock_rabbitmq.call_args
        assert call_args[0][0] == "darts.game.action"
        message = call_args[0][1]
        assert message["action"] == "end_turn"

    def test_continue_game_success(
        self,
        client,
        mock_rabbitmq,
        mock_jwt_validation,
        auth_headers,
    ):
        """Test continuing game successfully"""
        response = client.post(
            "/api/v1/game/actions/continue",
            json={"game_id": "test-game-123"},
            headers=auth_headers,
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"

        # Verify action type
        call_args = mock_rabbitmq.call_args
        message = call_args[0][1]
        assert message["action"] == "continue"

    def test_pause_game_success(
        self,
        client,
        mock_rabbitmq,
        mock_jwt_validation,
        auth_headers,
    ):
        """Test pausing game successfully"""
        response = client.post(
            "/api/v1/game/actions/pause",
            json={"game_id": "test-game-123"},
            headers=auth_headers,
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "success"

        # Verify action type
        call_args = mock_rabbitmq.call_args
        message = call_args[0][1]
        assert message["action"] == "pause"

    def test_game_action_no_auth(self, client):
        """Test game actions without authentication"""
        response = client.post(
            "/api/v1/game/actions/end-turn",
            json={"game_id": "test-game-123"},
            content_type="application/json",
        )

        assert response.status_code == 401


class TestPlayerEndpoint:
    """Test player management endpoint"""

    def test_add_player_success(
        self,
        client,
        mock_rabbitmq,
        mock_jwt_validation,
        auth_headers,
    ):
        """Test adding player successfully"""
        response = client.post(
            "/api/v1/players",
            json={"name": "New Player"},
            headers=auth_headers,
            content_type="application/json",
        )

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data["status"] == "success"

    def test_add_player_invalid_name(
        self,
        client,
        mock_jwt_validation,
        auth_headers,
    ):
        """Test adding player with invalid name"""
        response = client.post(
            "/api/v1/players",
            json={"name": 123},  # Invalid: not a string
            headers=auth_headers,
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data


class TestErrorHandlers:
    """Test error handlers"""

    def test_404_handler(self, client):
        """Test 404 error handler"""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
        data = json.loads(response.data)
        assert data["error"] == "Not found"


class TestOpenAPIEndpoints:
    """Test OpenAPI specification endpoints"""

    def test_openapi_yaml(self, client):
        """Test OpenAPI YAML endpoint"""
        response = client.get("/api/v1/openapi.yaml")
        assert response.status_code == 200
        assert "application/x-yaml" in response.content_type

    def test_openapi_json(self, client):
        """Test OpenAPI JSON endpoint"""
        response = client.get("/api/v1/openapi.json")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert "openapi" in data
        assert "paths" in data

    def test_swagger_ui(self, client):
        """Test Swagger UI endpoint"""
        response = client.get("/docs")
        assert response.status_code == 200
        assert b"swagger-ui" in response.data

    def test_api_docs_alias(self, client):
        """Test /api-docs alias for Swagger UI"""
        response = client.get("/api-docs")
        assert response.status_code == 200
        assert b"swagger-ui" in response.data


class TestAuthorizationScopes:
    """Test authorization scope parsing and fallback behavior"""

    def test_submit_score_accepts_comma_separated_scope(self, client, mock_rabbitmq):
        """Token scope provided as comma-separated string should be accepted"""
        with patch("src.api_gateway.app.validate_jwt_token") as mock_validate:
            mock_validate.return_value = {
                "sub": "test-user",
                "client_id": "dartboard-001",
                "scope": "score:write,game:write",
            }

            response = client.post(
                "/api/v1/scores",
                json={"score": 15, "multiplier": "SINGLE"},
                headers={"Authorization": "Bearer test-token-123"},
                content_type="application/json",
            )

        assert response.status_code == 201

    def test_introspection_uses_default_scopes_for_configured_client(self):
        """Configured client should receive default scopes when introspection omits scopes"""

        class MockResponse:
            status_code = 200
            text = '{"active": true, "client_id": "darts_api_gateway"}'

            @staticmethod
            def json():
                return {"active": True, "client_id": "darts_api_gateway"}

        with (
            patch("src.api_gateway.app.JWT_VALIDATION_MODE", "introspection"),
            patch("src.api_gateway.app.WSO2_IS_CLIENT_ID", "darts_api_gateway"),
            patch("src.api_gateway.app.WSO2_IS_DEFAULT_SCOPES", "score:write game:write"),
            patch("src.api_gateway.app.requests.post", return_value=MockResponse()),
        ):
            claims = gateway_module.validate_jwt_token("opaque-test-token")

        assert claims is not None
        assert "score:write" in claims["scope"]
        assert "game:write" in claims["scope"]
