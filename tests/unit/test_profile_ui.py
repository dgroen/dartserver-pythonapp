"""Unit tests for profile page functionality in app_ui.py."""

from unittest.mock import patch

import pytest


@pytest.fixture
def client(flask_app):
    """Create test client."""
    with flask_app.test_client() as client:
        yield client


@pytest.fixture
def authenticated_client(client):
    """Create authenticated test client with player_id."""
    with client.session_transaction() as sess:
        sess["access_token"] = "test-token"
        sess["user_info"] = {
            "username": "testuser",
            "sub": "test-user",
            "preferred_username": "testuser",
        }
        sess["player_id"] = 1

    with patch("dartserver_core.auth.validate_token") as mock_validate:
        mock_validate.return_value = {
            "sub": "test-user",
            "groups": ["player"],
            "roles": ["player"],
        }
        yield client


class TestProfileRoute:
    """Test profile page route."""

    def test_profile_route_exists(self, authenticated_client):
        """Test profile route is accessible."""
        response = authenticated_client.get("/profile")
        assert response.status_code == 200

    def test_profile_returns_html(self, authenticated_client):
        """Test profile route returns HTML content."""
        response = authenticated_client.get("/profile")
        assert response.status_code == 200
        assert b"<!DOCTYPE html>" in response.data or b"<html" in response.data

    def test_profile_contains_expected_content(self, authenticated_client):
        """Test profile page contains expected elements."""
        response = authenticated_client.get("/profile")
        assert response.status_code == 200
        # Check for key profile elements
        assert b"User Profile" in response.data
        assert b"Personal Information" in response.data
        assert b"Game Statistics" in response.data

    def test_profile_requires_authentication(self, client):
        """Test profile route requires authentication."""
        response = client.get("/profile")
        # Should redirect to login or return 401/403
        assert response.status_code in [302, 401, 403]

    def test_profile_uses_correct_template(self, authenticated_client):
        """Test profile route renders correct template."""
        with patch("src.app.app_ui.render_template") as mock_render:
            mock_render.return_value = "mocked_response"
            authenticated_client.get("/profile")
            # Verify render_template was called with profile.html
            mock_render.assert_called_once()
            args, _kwargs = mock_render.call_args
            assert args[0] == "profile.html"

    def test_profile_passes_user_context(self, authenticated_client):
        """Test profile route passes user roles and claims to template."""
        with patch("src.app.app_ui.render_template") as mock_render:
            mock_render.return_value = "mocked_response"
            authenticated_client.get("/profile")
            # Verify render_template was called with user context
            _args, kwargs = mock_render.call_args
            assert "user_roles" in kwargs
            assert "user_claims" in kwargs


class TestMobileProfileRoute:
    """Test mobile profile page route."""

    def test_mobile_profile_route_exists(self, authenticated_client):
        """Test mobile profile route is accessible."""
        response = authenticated_client.get("/mobile/profile")
        assert response.status_code == 200

    def test_mobile_profile_returns_html(self, authenticated_client):
        """Test mobile profile route returns HTML content."""
        response = authenticated_client.get("/mobile/profile")
        assert response.status_code == 200
        assert b"<!DOCTYPE html>" in response.data or b"<html" in response.data

    def test_mobile_profile_contains_expected_content(self, authenticated_client):
        """Test mobile profile page contains expected elements."""
        response = authenticated_client.get("/mobile/profile")
        assert response.status_code == 200
        # Check for key mobile profile elements
        assert b"Profile" in response.data
        assert b"mobile-app" in response.data or b"mobile-content" in response.data

    def test_mobile_profile_requires_authentication(self, client):
        """Test mobile profile route requires authentication."""
        response = client.get("/mobile/profile")
        # Should redirect to login or return 401/403
        assert response.status_code in [302, 401, 403]

    def test_mobile_profile_uses_correct_template(self, authenticated_client):
        """Test mobile profile route renders correct template."""
        with patch("src.app.app_services.render_template") as mock_render:
            mock_render.return_value = "mocked_response"
            authenticated_client.get("/mobile/profile")
            # Verify render_template was called with mobile_profile.html
            mock_render.assert_called_once()
            args, _kwargs = mock_render.call_args
            assert args[0] == "mobile_profile.html"

    def test_mobile_profile_passes_user_context(self, authenticated_client):
        """Test mobile profile route passes user roles and claims to template."""
        with patch("src.app.app_services.render_template") as mock_render:
            mock_render.return_value = "mocked_response"
            authenticated_client.get("/mobile/profile")
            # Verify render_template was called with user context
            _args, kwargs = mock_render.call_args
            assert "user_roles" in kwargs
            assert "user_claims" in kwargs
