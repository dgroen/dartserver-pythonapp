"""
Tests for login redirect functionality
Ensures that users are redirected back to the page they requested after login
"""

from unittest.mock import patch

import pytest
from flask import session


@pytest.fixture
def app_with_login():
    """Create Flask app with login routes"""
    from src.app.app import app as flask_app

    flask_app.config["TESTING"] = True
    flask_app.config["WTF_CSRF_ENABLED"] = False
    flask_app.config["SESSION_COOKIE_SECURE"] = False

    with flask_app.app_context():
        yield flask_app


@pytest.fixture
def client_with_login(app_with_login):
    """Create test client"""
    return app_with_login.test_client()


class TestLoginRedirectFlow:
    """Test login redirect flow for protected pages"""

    @patch("src.core.auth.get_current_request_url")
    @patch("src.core.auth.validate_token")
    def test_history_page_redirect_to_login(self, mock_validate, mock_get_url, client_with_login):
        """Test that accessing /history without token redirects to login"""
        mock_validate.return_value = None
        mock_get_url.return_value = "https://localhost:5000/history"

        response = client_with_login.get("/history", follow_redirects=False)

        # Should redirect to login
        assert response.status_code == 302
        assert "/login" in response.location
        assert "next=" in response.location

    @patch("src.core.auth.get_current_request_url")
    def test_login_stores_next_url_in_session(
        self,
        mock_get_url,
        client_with_login,
        app_with_login,
    ):
        """Test that login route stores the 'next' parameter in session"""
        with client_with_login:
            # First request to login with next parameter
            client_with_login.get(
                "/login?next=https://localhost:5000/history",
                follow_redirects=False,
            )

            # Check that the session was set with the next URL
            assert session.get("login_next_url") == "https://localhost:5000/history"
            assert session.get("oauth_state") is not None

    @patch("src.core.auth.get_current_request_url")
    def test_login_stores_oauth_state(self, mock_get_url, client_with_login):
        """Test that login route generates and stores OAuth state"""
        with client_with_login:
            client_with_login.get("/login", follow_redirects=False)

            # Check that oauth_state is set
            assert session.get("oauth_state") is not None
            state = session.get("oauth_state")
            # State should be a URL-safe token
            assert len(state) > 20

    @patch("src.app.app.get_user_info")
    @patch("src.app.app.exchange_code_for_token")
    def test_callback_redirect_to_next_url(
        self,
        mock_exchange,
        mock_get_info,
        client_with_login,
        app_with_login,
    ):
        """Test that callback redirects to the 'next' URL stored in session"""
        # Setup mocks
        mock_exchange.return_value = {
            "access_token": "test_token",
            "refresh_token": "test_refresh",
            "id_token": "test_id_token",
        }
        mock_get_info.return_value = {
            "preferred_username": "testuser",
            "email": "test@example.com",
            "name": "Test User",
        }

        with client_with_login:
            # First, set up the session with the next URL and oauth_state
            with client_with_login.session_transaction() as sess:
                sess["login_next_url"] = "https://localhost:5000/history"
                sess["oauth_state"] = "test_state_12345"

            # Now call the callback with the matching state
            response = client_with_login.get(
                "/callback?code=test_code&state=test_state_12345",
                follow_redirects=False,
            )

            # Should redirect to the history page
            assert response.status_code == 302
            assert response.location == "https://localhost:5000/history"

    @patch("src.app.app.get_user_info")
    @patch("src.app.app.exchange_code_for_token")
    def test_callback_redirects_to_home_without_next_url(
        self,
        mock_exchange,
        mock_get_info,
        client_with_login,
    ):
        """Test that callback redirects to home when no 'next' URL is stored"""
        # Setup mocks
        mock_exchange.return_value = {
            "access_token": "test_token",
            "refresh_token": "test_refresh",
            "id_token": "test_id_token",
        }
        mock_get_info.return_value = {
            "preferred_username": "testuser",
            "email": "test@example.com",
            "name": "Test User",
        }

        with client_with_login:
            # Set up the session WITHOUT the next URL
            with client_with_login.session_transaction() as sess:
                sess["oauth_state"] = "test_state_12345"

            # Call the callback with the matching state
            response = client_with_login.get(
                "/callback?code=test_code&state=test_state_12345",
                follow_redirects=False,
            )

            # Should redirect to home page
            assert response.status_code == 302
            assert response.location == "/"

    @patch("src.app.app.get_user_info")
    @patch("src.app.app.exchange_code_for_token")
    def test_callback_clears_login_next_url_from_session(
        self,
        mock_exchange,
        mock_get_info,
        client_with_login,
    ):
        """Test that callback removes 'login_next_url' from session after redirect"""
        # Setup mocks
        mock_exchange.return_value = {
            "access_token": "test_token",
            "refresh_token": "test_refresh",
            "id_token": "test_id_token",
        }
        mock_get_info.return_value = {
            "preferred_username": "testuser",
            "email": "test@example.com",
            "name": "Test User",
        }

        with client_with_login:
            # Set up the session with the next URL
            with client_with_login.session_transaction() as sess:
                sess["login_next_url"] = "https://localhost:5000/history"
                sess["oauth_state"] = "test_state_12345"

            # Call the callback
            client_with_login.get(
                "/callback?code=test_code&state=test_state_12345",
                follow_redirects=False,
            )

            # Check that login_next_url has been removed from session
            with client_with_login.session_transaction() as sess:
                assert "login_next_url" not in sess

    @patch("src.core.auth.get_current_request_url")
    def test_login_session_marked_as_permanent(self, mock_get_url, client_with_login):
        """Test that login route marks session as permanent"""
        with client_with_login:
            client_with_login.get("/login", follow_redirects=False)

            # Check that session is permanent
            with client_with_login.session_transaction() as sess:
                assert sess.permanent is True

    def test_login_route_renders_template(self, client_with_login):
        """Test that login route renders the login template"""
        response = client_with_login.get("/login")

        assert response.status_code == 200
        assert b"Login with WSO2" in response.data
        assert b"Darts Game System" in response.data

    def test_login_displays_error_message(self, client_with_login):
        """Test that login route displays error messages"""
        response = client_with_login.get("/login?error=test_error_message")

        assert response.status_code == 200
        assert b"test_error_message" in response.data
