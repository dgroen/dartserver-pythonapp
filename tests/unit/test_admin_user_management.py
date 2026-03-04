"""
Unit tests for admin user management endpoints.
Tests for role assignment, user activation/deactivation.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

# Import modules at top level to avoid PLC0415
from dartserver_core import auth


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Set up mock environment variables"""
    monkeypatch.setenv("WSO2_IS_INTERNAL_URL", "https://test-wso2")
    monkeypatch.setenv("WSO2_IS_INTROSPECT_USER", "admin")
    monkeypatch.setenv("WSO2_IS_INTROSPECT_PASSWORD", "admin_pass")
    monkeypatch.setenv("WSO2_IS_VERIFY_SSL", "false")
    monkeypatch.setenv("AUTH_DISABLED", "true")


@pytest.fixture
def client(flask_app):
    """Create test client with auth disabled."""
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client


class TestUpdateUserRoles:
    """Tests for the update_user_roles endpoint"""

    def test_update_roles_add_and_remove(self, mock_env_vars, client):
        """Test updating user roles with additions and removals"""
        # Mock requests module
        with patch("src.app.app_admin.requests") as mock_requests:
            # Mock user data response
            user_data = {
                "userName": "testuser",
                "groups": [
                    {"display": "PRIMARY/player", "value": "group-player-id"},
                ],
            }
            mock_user_response = MagicMock()
            mock_user_response.status_code = 200
            mock_user_response.json.return_value = user_data

            # Mock groups list response
            groups_data = {
                "Resources": [
                    {"id": "group-admin-id", "displayName": "PRIMARY/admin"},
                    {"id": "group-gamemaster-id", "displayName": "PRIMARY/gamemaster"},
                    {"id": "group-player-id", "displayName": "PRIMARY/player"},
                ],
            }
            mock_groups_response = MagicMock()
            mock_groups_response.status_code = 200
            mock_groups_response.json.return_value = groups_data

            # Mock patch responses (for adding/removing from groups)
            mock_patch_response = MagicMock()
            mock_patch_response.status_code = 200

            # Set up get/patch mock behavior
            mock_requests.get.side_effect = [mock_user_response, mock_groups_response]
            mock_requests.patch.return_value = mock_patch_response

            response = client.put(
                "/api/admin/users/test-user-id/roles",
                json={"roles": ["admin", "gamemaster"]},
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["status"] == "success"

            # Verify that patch was called for adding to new groups
            # Should be called twice: once to add to admin, once to add to gamemaster
            # And once to remove from player
            assert mock_requests.patch.call_count >= 2

    def test_update_roles_no_changes(self, mock_env_vars, client):
        """Test updating user roles when no changes are needed"""
        with patch("src.app.app_admin.requests") as mock_requests:
            # User already has the requested roles
            user_data = {
                "userName": "testuser",
                "groups": [
                    {"display": "PRIMARY/admin", "value": "group-admin-id"},
                ],
            }
            mock_user_response = MagicMock()
            mock_user_response.status_code = 200
            mock_user_response.json.return_value = user_data

            groups_data = {
                "Resources": [
                    {"id": "group-admin-id", "displayName": "PRIMARY/admin"},
                    {"id": "group-player-id", "displayName": "PRIMARY/player"},
                ],
            }
            mock_groups_response = MagicMock()
            mock_groups_response.status_code = 200
            mock_groups_response.json.return_value = groups_data

            mock_requests.get.side_effect = [mock_user_response, mock_groups_response]

            response = client.put(
                "/api/admin/users/test-user-id/roles",
                json={"roles": ["admin"]},
                content_type="application/json",
            )

            assert response.status_code == 200
            # No patch calls should be made if roles don't change
            assert mock_requests.patch.call_count == 0

    def test_update_roles_user_not_found(self, mock_env_vars, client):
        """Test updating roles for non-existent user"""
        with patch("src.app.app_admin.requests") as mock_requests:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_requests.get.return_value = mock_response

            response = client.put(
                "/api/admin/users/nonexistent-id/roles",
                json={"roles": ["admin"]},
                content_type="application/json",
            )

            assert response.status_code == 404


class TestUpdateUserStatus:
    """Tests for the update_user_status endpoint"""

    def test_deactivate_user(self, mock_env_vars, client):
        """Test deactivating a user"""
        with patch("src.app.app_admin.requests") as mock_requests:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_requests.patch.return_value = mock_response

            response = client.put(
                "/api/admin/users/test-user-id/status",
                json={"active": False},
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["status"] == "success"
            assert "deactivated" in data["message"]

            # Verify the PATCH request was made with correct payload
            assert mock_requests.patch.called
            call_args = mock_requests.patch.call_args
            payload = call_args[1]["json"]
            assert payload["Operations"][0]["op"] == "replace"
            assert payload["Operations"][0]["path"] == "active"
            assert payload["Operations"][0]["value"] is False

    def test_activate_user(self, mock_env_vars, client):
        """Test activating a user"""
        with patch("src.app.app_admin.requests") as mock_requests:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_requests.patch.return_value = mock_response

            response = client.put(
                "/api/admin/users/test-user-id/status",
                json={"active": True},
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["status"] == "success"
            assert "activated" in data["message"]

            # Verify the PATCH request was made with correct payload
            call_args = mock_requests.patch.call_args
            payload = call_args[1]["json"]
            assert payload["Operations"][0]["value"] is True

    def test_activate_user_with_fallback(self, mock_env_vars, client):
        """Test activating a user when path-based PATCH fails and fallback succeeds"""
        with patch("src.app.app_admin.requests") as mock_requests:
            # First PATCH (path-based) fails, second (value-based) succeeds
            mock_fail_response = MagicMock()
            mock_fail_response.status_code = 400
            mock_success_response = MagicMock()
            mock_success_response.status_code = 200

            mock_requests.patch.side_effect = [mock_fail_response, mock_success_response]

            response = client.put(
                "/api/admin/users/test-user-id/status",
                json={"active": True},
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["status"] == "success"
            # Should have tried twice
            assert mock_requests.patch.call_count == 2


class TestSearchWso2Users:
    """Tests for search_wso2_users function"""

    def test_search_includes_active_field(self):
        """Test that search_wso2_users includes the active field"""
        with patch.object(auth, "requests") as mock_requests:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "Resources": [
                    {
                        "id": "user-1",
                        "userName": "activeuser",
                        "active": True,
                        "emails": [{"value": "active@test.com"}],
                        "name": {"givenName": "Active", "familyName": "User"},
                    },
                    {
                        "id": "user-2",
                        "userName": "inactiveuser",
                        "active": False,
                        "emails": [{"value": "inactive@test.com"}],
                        "name": {"givenName": "Inactive", "familyName": "User"},
                    },
                ],
            }
            mock_requests.get.return_value = mock_response

            with (
                patch.object(auth, "WSO2_IS_INTROSPECT_USER", "admin"),
                patch.object(auth, "WSO2_IS_INTROSPECT_PASSWORD", "pass"),
                patch.object(auth, "WSO2_IS_INTERNAL_URL", "https://test"),
            ):
                users = auth.search_wso2_users("user")

            assert len(users) == 2
            assert users[0]["active"] is True
            assert users[1]["active"] is False

    def test_search_defaults_active_to_true(self):
        """Test that search_wso2_users defaults active to True when not present"""
        with patch.object(auth, "requests") as mock_requests:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "Resources": [
                    {
                        "id": "user-1",
                        "userName": "testuser",
                        # No 'active' field
                        "emails": [{"value": "test@test.com"}],
                    },
                ],
            }
            mock_requests.get.return_value = mock_response

            with (
                patch.object(auth, "WSO2_IS_INTROSPECT_USER", "admin"),
                patch.object(auth, "WSO2_IS_INTROSPECT_PASSWORD", "pass"),
                patch.object(auth, "WSO2_IS_INTERNAL_URL", "https://test"),
            ):
                users = auth.search_wso2_users("testuser")

            assert len(users) == 1
            assert users[0]["active"] is True  # Should default to True


class TestGetWso2ActiveSessions:
    """Tests for the get_wso2_active_sessions function"""

    @pytest.fixture(autouse=True)
    def mock_wso2_config(self):
        """Patch WSO2 IS connection settings for all tests in this class."""
        with (
            patch.object(auth, "WSO2_IS_INTROSPECT_USER", "admin"),
            patch.object(auth, "WSO2_IS_INTROSPECT_PASSWORD", "pass"),
            patch.object(auth, "WSO2_IS_INTERNAL_URL", "https://test"),
            patch.object(auth, "WSO2_IS_VERIFY_SSL", False),
        ):
            yield

    def test_returns_sessions_on_success(self):
        """Test that active sessions are returned when WSO2 IS responds successfully"""
        with patch.object(auth, "requests") as mock_requests:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "sessions": [
                    {
                        "userId": "admin",
                        "id": "session-abc123",
                        "loginTime": "2024-01-15T10:00:00.000Z",
                        "lastAccessTime": "2024-01-15T10:30:00.000Z",
                        "ip": "192.168.1.1",
                        "userAgent": "Mozilla/5.0",
                        "applications": [
                            {"appName": "Darts App", "appId": "darts-app-id"},
                        ],
                    },
                ],
            }
            mock_requests.get.return_value = mock_response

            sessions = auth.get_wso2_active_sessions()

        assert len(sessions) == 1
        assert sessions[0]["username"] == "admin"
        assert sessions[0]["session_id"] == "session-abc123"
        assert sessions[0]["login_time"] == "2024-01-15T10:00:00.000Z"
        assert sessions[0]["last_activity"] == "2024-01-15T10:30:00.000Z"
        assert sessions[0]["ip"] == "192.168.1.1"
        assert sessions[0]["user_agent"] == "Mozilla/5.0"
        assert sessions[0]["applications"] == ["Darts App"]

    def test_returns_empty_list_on_error_status(self):
        """Test that an empty list is returned when WSO2 IS returns an error status"""
        with patch.object(auth, "requests") as mock_requests:
            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_response.text = "Forbidden"
            mock_requests.get.return_value = mock_response

            sessions = auth.get_wso2_active_sessions()

        assert sessions == []

    def test_returns_empty_list_on_exception(self):
        """Test that an empty list is returned when a network exception occurs"""
        with patch.object(auth, "requests") as mock_requests:
            mock_requests.get.side_effect = ConnectionError("Connection refused")

            sessions = auth.get_wso2_active_sessions()

        assert sessions == []

    def test_uses_correct_endpoint(self):
        """Test that the correct WSO2 IS session management API endpoint is called"""
        with patch.object(auth, "requests") as mock_requests, patch.object(
            auth, "WSO2_IS_INTERNAL_URL", "https://wso2-test"
        ):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"sessions": []}
            mock_requests.get.return_value = mock_response

            auth.get_wso2_active_sessions()

        mock_requests.get.assert_called_once()
        call_args = mock_requests.get.call_args
        assert call_args[0][0] == "https://wso2-test/api/server/v1/sessions"
        assert call_args[1]["auth"] == ("admin", "pass")

    def test_handles_empty_sessions_list(self):
        """Test that an empty sessions list is handled gracefully"""
        with patch.object(auth, "requests") as mock_requests:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"sessions": []}
            mock_requests.get.return_value = mock_response

            sessions = auth.get_wso2_active_sessions()

        assert sessions == []

    def test_handles_missing_optional_fields(self):
        """Test that sessions with missing optional fields are handled gracefully"""
        with patch.object(auth, "requests") as mock_requests:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "sessions": [
                    {
                        "userId": "testuser",
                        # Missing: id, loginTime, lastAccessTime, ip, userAgent, applications
                    },
                ],
            }
            mock_requests.get.return_value = mock_response

            sessions = auth.get_wso2_active_sessions()

        assert len(sessions) == 1
        assert sessions[0]["username"] == "testuser"
        assert sessions[0]["session_id"] == ""
        assert sessions[0]["login_time"] == ""
        assert sessions[0]["last_activity"] == ""
        assert sessions[0]["ip"] == ""
        assert sessions[0]["user_agent"] == ""
        assert sessions[0]["applications"] == []

