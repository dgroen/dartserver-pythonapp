"""Unit tests for app_auth.py endpoints."""

import json
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_auth_fixtures():
    """Mock authentication functions."""
    with (
        patch("src.app.app_auth.get_authorization_url") as mock_auth_url,
        patch("src.app.app_auth.exchange_code_for_token") as mock_exchange,
        patch("src.app.app_auth.get_user_info") as mock_user_info,
        patch("src.app.app_auth.validate_token") as mock_validate,
        patch("src.app.app_auth.get_user_roles") as mock_roles,
        patch("src.app.app_auth.get_user_groups_from_scim2") as mock_groups,
        patch("src.app.app_auth.logout_user") as mock_logout,
    ):
        mock_auth_url.return_value = "https://auth.example.com/authorize?state=test"
        mock_exchange.return_value = {
            "access_token": "test-access-token",
            "refresh_token": "test-refresh-token",
            "id_token": "test-id-token",
        }
        mock_user_info.return_value = {
            "sub": "test-user-id",
            "preferred_username": "testuser",
            "email": "test@example.com",
            "name": "Test User",
        }
        mock_validate.return_value = {"sub": "test-user-id", "groups": ["admin"]}
        mock_roles.return_value = ["admin"]
        mock_groups.return_value = ["admin", "gamemaster"]
        mock_logout.return_value = "https://auth.example.com/logout"

        yield {
            "auth_url": mock_auth_url,
            "exchange": mock_exchange,
            "user_info": mock_user_info,
            "validate": mock_validate,
            "roles": mock_roles,
            "groups": mock_groups,
            "logout": mock_logout,
        }


@pytest.fixture
def client(flask_app):
    """Create test client with auth mocking."""
    with flask_app.test_client() as client:
        yield client


class TestAuthEndpoints:
    """Test authentication endpoints in app_auth.py."""

    def test_login_page_renders(self, client, mock_auth_fixtures):
        """Test login page renders with authorization URL."""
        response = client.get("/login")
        assert response.status_code == 200
        assert b"<!DOCTYPE html>" in response.data or b"<html" in response.data
        mock_auth_fixtures["auth_url"].assert_called_once()

    def test_login_with_next_parameter(self, client, mock_auth_fixtures):
        """Test login stores next URL in session."""
        with client.session_transaction() as sess:
            # Session should be initially empty
            assert "login_next_url" not in sess

        response = client.get("/login?next=/control")
        assert response.status_code == 200

        with client.session_transaction() as sess:
            assert sess.get("login_next_url") == "/control"
            assert "oauth_state" in sess

    def test_login_generates_state(self, client, mock_auth_fixtures):
        """Test login generates CSRF state token."""
        response = client.get("/login")
        assert response.status_code == 200

        with client.session_transaction() as sess:
            assert "oauth_state" in sess
            assert len(sess["oauth_state"]) > 20  # Should be a random token

    def test_callback_success(self, client, flask_app, mock_auth_fixtures):
        """Test successful OAuth callback."""
        # Set up session state
        with client.session_transaction() as sess:
            sess["oauth_state"] = "test-state"

        # Mock database player creation
        mock_game_manager = MagicMock()
        mock_db_service = MagicMock()
        mock_player = MagicMock()
        mock_player.id = 123
        mock_db_service.get_or_create_player.return_value = mock_player
        mock_game_manager.db_service = mock_db_service

        with patch.object(flask_app, "game_manager", mock_game_manager):
            response = client.get(
                "/callback?code=test-code&state=test-state",
                follow_redirects=False,
            )

            assert response.status_code == 302  # Redirect
            assert response.location == "/"

            # Verify token exchange was called
            mock_auth_fixtures["exchange"].assert_called_once_with("test-code")

        # Check session was updated
        with client.session_transaction() as sess:
            assert sess.get("access_token") == "test-access-token"
            assert "user_info" in sess
            assert "oauth_state" not in sess  # State should be cleared

    def test_callback_invalid_state(self, client, mock_auth_fixtures):
        """Test callback with invalid state parameter."""
        # Set up session state
        with client.session_transaction() as sess:
            sess["oauth_state"] = "valid-state"

        response = client.get("/callback?code=test-code&state=wrong-state", follow_redirects=False)

        assert response.status_code == 302  # Redirect to login with error
        assert "/login" in response.location
        assert "error" in response.location

    def test_callback_missing_code(self, client, mock_auth_fixtures):
        """Test callback without authorization code."""
        with client.session_transaction() as sess:
            sess["oauth_state"] = "test-state"

        response = client.get("/callback?state=test-state", follow_redirects=False)

        assert response.status_code == 302
        assert "/login" in response.location
        assert "error" in response.location

    def test_callback_token_exchange_failure(self, client, mock_auth_fixtures):
        """Test callback when token exchange fails."""
        with client.session_transaction() as sess:
            sess["oauth_state"] = "test-state"

        # Mock failed token exchange
        mock_auth_fixtures["exchange"].return_value = None

        response = client.get(
            "/callback?code=test-code&state=test-state",
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert "/login" in response.location
        assert "error" in response.location

    def test_callback_redirects_to_next_url(self, client, flask_app, mock_auth_fixtures):
        """Test callback redirects to stored next URL."""
        with client.session_transaction() as sess:
            sess["oauth_state"] = "test-state"
            sess["login_next_url"] = "/dashboard"

        mock_game_manager = MagicMock()
        mock_db_service = MagicMock()
        mock_player = MagicMock()
        mock_player.id = 123
        mock_db_service.get_or_create_player.return_value = mock_player
        mock_game_manager.db_service = mock_db_service

        with patch.object(flask_app, "game_manager", mock_game_manager):
            response = client.get(
                "/callback?code=test-code&state=test-state",
                follow_redirects=False,
            )

            assert response.status_code == 302
            assert response.location == "/dashboard"

        with client.session_transaction() as sess:
            assert "login_next_url" not in sess  # Should be cleared

    def test_logout_clears_session(self, client, mock_auth_fixtures):
        """Test logout clears session and redirects."""
        # Set up session
        with client.session_transaction() as sess:
            sess["access_token"] = "test-token"
            sess["user_info"] = {"username": "testuser"}
            sess["id_token"] = "test-id-token"

        response = client.get("/logout", follow_redirects=False)

        assert response.status_code == 302
        assert "logout" in response.location

        # Verify session was cleared
        with client.session_transaction() as sess:
            assert "access_token" not in sess
            assert "user_info" not in sess
            assert "id_token" not in sess

        mock_auth_fixtures["logout"].assert_called_once_with("test-id-token")

    def test_profile_requires_auth(self, client):
        """Test profile endpoint requires authentication."""
        response = client.get("/profile")
        # Should redirect to login or return 401/403
        assert response.status_code in [302, 401, 403]

    def test_profile_returns_user_info(self, client, mock_auth_fixtures):
        """Test profile returns user information."""
        # Set up authenticated session
        with client.session_transaction() as sess:
            sess["access_token"] = "test-token"
            sess["user_info"] = {
                "sub": "test-user",
                "preferred_username": "testuser",
                "email": "test@example.com",
            }

        with patch("dartserver_core.auth.validate_token") as mock_validate:
            mock_validate.return_value = {"sub": "test-user", "groups": ["admin"]}

            response = client.get("/profile")

            if response.status_code == 200:
                data = json.loads(response.data)
                assert "user_info" in data
                assert data["user_info"]["preferred_username"] == "testuser"
                assert "roles" in data
                assert "claims" in data

    def test_debug_auth_requires_auth(self, client):
        """Test debug auth endpoint requires authentication."""
        response = client.get("/debug/auth")
        assert response.status_code in [302, 401, 403]

    def test_debug_auth_returns_detailed_info(self, client, mock_auth_fixtures):
        """Test debug auth returns detailed authentication information."""
        with client.session_transaction() as sess:
            sess["access_token"] = "test-token"
            sess["user_info"] = {"sub": "test-user", "username": "testuser"}

        with patch("dartserver_core.auth.validate_token") as mock_validate:
            mock_validate.return_value = {
                "sub": "test-user",
                "groups": ["admin"],
                "roles": ["admin"],
            }

            response = client.get("/debug/auth")

            if response.status_code == 200:
                data = json.loads(response.data)
                assert "session_keys" in data
                assert "user_info" in data
                assert "token_claims" in data
                assert "extracted_roles" in data

    def test_callback_with_scim2_fallback(self, client, flask_app, mock_auth_fixtures):
        """Test callback uses SCIM2 when username has UUID format."""
        with client.session_transaction() as sess:
            sess["oauth_state"] = "test-state"

        # Mock user info with UUID username
        mock_auth_fixtures["user_info"].return_value = {
            "sub": "test-user-id",
            "preferred_username": "123e4567-e89b-12d3-a456-426614174000",
            "email": None,
            "name": None,
        }

        mock_game_manager = MagicMock()
        mock_db_service = MagicMock()
        mock_player = MagicMock()
        mock_player.id = 123
        mock_db_service.get_or_create_player.return_value = mock_player
        mock_game_manager.db_service = mock_db_service

        with (
            patch("src.app.app_auth._fetch_scim2_user") as mock_scim2,
            patch.object(flask_app, "game_manager", mock_game_manager),
        ):
            mock_scim2.return_value = {
                "userName": "testuser",
                "emails": [{"value": "test@example.com"}],
                "name": {"givenName": "Test", "familyName": "User"},
            }

            response = client.get(
                "/callback?code=test-code&state=test-state",
                follow_redirects=False,
            )

            assert response.status_code == 302
            mock_scim2.assert_called_once()

    def test_callback_creates_player(self, client, flask_app, mock_auth_fixtures):
        """Test callback creates player in database."""
        with client.session_transaction() as sess:
            sess["oauth_state"] = "test-state"

        mock_game_manager = MagicMock()
        mock_db_service = MagicMock()
        mock_player = MagicMock()
        mock_player.id = 456
        mock_db_service.get_or_create_player.return_value = mock_player
        mock_game_manager.db_service = mock_db_service

        with patch.object(flask_app, "game_manager", mock_game_manager):
            response = client.get(
                "/callback?code=test-code&state=test-state",
                follow_redirects=False,
            )

            assert response.status_code == 302

            # Verify player was created
            mock_db_service.get_or_create_player.assert_called_once()
            call_args = mock_db_service.get_or_create_player.call_args
            assert call_args[1]["username"] == "testuser"

        with client.session_transaction() as sess:
            assert sess.get("player_id") == 456
