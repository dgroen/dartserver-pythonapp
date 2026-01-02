"""
Unit tests for OAuth2 proxy endpoints in API Gateway
Tests OAuth2 token proxy and redirect handler
"""

from unittest.mock import MagicMock, patch

import pytest

from src.api_gateway.app import app as gateway_app


@pytest.fixture
def client():
    """Create test client for API Gateway"""
    gateway_app.config["TESTING"] = True
    with gateway_app.test_client() as client:
        yield client


class TestOAuth2TokenProxy:
    """Test OAuth2 token proxy endpoint"""

    def test_oauth2_token_cors_preflight(self, client):
        """Test CORS preflight request"""
        response = client.options(
            "/oauth2/token",
            headers={"Origin": "http://localhost:8080"},
        )
        assert response.status_code == 200
        assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:8080"
        assert "POST" in response.headers["Access-Control-Allow-Methods"]

    @patch("src.api_gateway.app.requests.post")
    def test_oauth2_token_client_credentials(self, mock_post, client):
        """Test OAuth2 client_credentials grant flow"""
        # Mock WSO2 IS token response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "mock-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "dartboard:write score:write",
        }
        mock_post.return_value = mock_response

        # Test client_credentials grant
        response = client.post(
            "/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "scope": "dartboard:write score:write",
            },
            headers={"Origin": "http://localhost:8080"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["access_token"] == "mock-access-token"
        assert data["token_type"] == "Bearer"
        assert "dartboard:write" in data["scope"]

    @patch("src.api_gateway.app.requests.post")
    def test_oauth2_token_authorization_code(self, mock_post, client):
        """Test OAuth2 authorization_code grant flow"""
        # Mock WSO2 IS token response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "mock-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "dartboard:write score:write",
        }
        mock_post.return_value = mock_response

        # Test authorization_code grant
        response = client.post(
            "/oauth2/token",
            data={
                "grant_type": "authorization_code",
                "code": "test-auth-code-123",
                "redirect_uri": "http://localhost:8080/oauth2-redirect",
            },
            headers={"Origin": "http://localhost:8080"},
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["access_token"] == "mock-access-token"
        assert mock_post.called
        # Verify the code was passed to WSO2 IS
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["data"]["code"] == "test-auth-code-123"

    def test_oauth2_token_missing_code(self, client):
        """Test OAuth2 token request with missing authorization code"""
        response = client.post(
            "/oauth2/token",
            data={
                "grant_type": "authorization_code",
                "redirect_uri": "http://localhost:8080/oauth2-redirect",
                # Missing 'code' parameter
            },
            headers={"Origin": "http://localhost:8080"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "invalid_request"

    def test_oauth2_token_unsupported_grant(self, client):
        """Test OAuth2 token request with unsupported grant type"""
        response = client.post(
            "/oauth2/token",
            data={
                "grant_type": "password",  # Unsupported grant type
                "username": "test",
                "password": "test",
            },
            headers={"Origin": "http://localhost:8080"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "unsupported_grant_type"

    @patch("src.api_gateway.app.requests.post")
    def test_oauth2_token_wso2_error(self, mock_post, client):
        """Test OAuth2 token proxy when WSO2 IS returns error"""
        # Mock WSO2 IS error response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "error": "invalid_client",
            "error_description": "Client authentication failed",
        }
        mock_post.return_value = mock_response

        response = client.post(
            "/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "scope": "dartboard:write",
            },
            headers={"Origin": "http://localhost:8080"},
        )

        assert response.status_code == 401
        data = response.get_json()
        assert data["error"] == "invalid_client"


class TestOAuth2RedirectHandler:
    """Test OAuth2 redirect handler endpoint"""

    def test_oauth2_redirect_handler(self, client):
        """Test OAuth2 redirect handler serves HTML"""
        response = client.get("/oauth2-redirect")
        assert response.status_code == 200
        assert b"OAuth2 Redirect" in response.data
        assert b"window.opener.swaggerUIRedirectOauth2" in response.data
        assert b"authorization_code" in response.data

    def test_oauth2_redirect_with_code(self, client):
        """Test OAuth2 redirect handler with authorization code"""
        response = client.get("/oauth2-redirect?code=test-code&state=test-state")
        assert response.status_code == 200
        # JavaScript should be present to handle the code
        assert b"qp.code" in response.data
        assert b"oauth2.callback" in response.data

    def test_oauth2_redirect_with_error(self, client):
        """Test OAuth2 redirect handler with error"""
        response = client.get("/oauth2-redirect?error=access_denied&error_description=User+denied")
        assert response.status_code == 200
        # JavaScript should handle errors
        assert b"qp.error" in response.data
        assert b"oauth2.errCb" in response.data
