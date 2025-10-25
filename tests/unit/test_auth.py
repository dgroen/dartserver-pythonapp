"""Unit tests for authentication and authorization module."""

import json
from unittest.mock import Mock, patch

import jwt
from flask import Flask, jsonify

from src.core.auth import (
    get_dynamic_post_logout_redirect_uri,
    get_dynamic_redirect_uri,
    get_user_roles,
    has_permission,
    login_required,
    permission_required,
    role_required,
    validate_token,
)


class TestValidateToken:
    """Test token validation functions."""

    @patch("src.core.auth.JWT_VALIDATION_MODE", "jwks")
    @patch("src.core.auth.jwks_client")
    def test_validate_token_jwks_success(self, mock_jwks_client):
        """Test successful token validation using JWKS."""
        # Mock signing key
        mock_signing_key = Mock()
        mock_signing_key.key = "test-key"
        mock_jwks_client.get_signing_key_from_jwt.return_value = mock_signing_key

        # Mock jwt.decode
        expected_claims = {
            "sub": "test-user",
            "username": "testuser",
            "groups": ["admin"],
        }

        with patch("src.core.auth.jwt.decode", return_value=expected_claims):
            result = validate_token("test-token")
            assert result == expected_claims

    @patch("src.core.auth.JWT_VALIDATION_MODE", "jwks")
    @patch("src.core.auth.jwks_client")
    def test_validate_token_jwks_expired(self, mock_jwks_client):
        """Test token validation with expired token."""
        mock_signing_key = Mock()
        mock_signing_key.key = "test-key"
        mock_jwks_client.get_signing_key_from_jwt.return_value = mock_signing_key

        with patch("src.core.auth.jwt.decode", side_effect=jwt.ExpiredSignatureError):
            result = validate_token("expired-token")
            assert result is None

    @patch("src.core.auth.JWT_VALIDATION_MODE", "jwks")
    @patch("src.core.auth.jwks_client")
    def test_validate_token_jwks_invalid(self, mock_jwks_client):
        """Test token validation with invalid token."""
        mock_signing_key = Mock()
        mock_signing_key.key = "test-key"
        mock_jwks_client.get_signing_key_from_jwt.return_value = mock_signing_key

        with patch("src.core.auth.jwt.decode", side_effect=jwt.InvalidTokenError("Invalid")):
            result = validate_token("invalid-token")
            assert result is None

    @patch("src.core.auth.JWT_VALIDATION_MODE", "jwks")
    @patch("src.core.auth.jwks_client")
    def test_validate_token_jwks_exception(self, mock_jwks_client):
        """Test token validation with unexpected exception."""
        mock_signing_key = Mock()
        mock_signing_key.key = "test-key"
        mock_jwks_client.get_signing_key_from_jwt.return_value = mock_signing_key

        with patch("src.core.auth.jwt.decode", side_effect=Exception("Unexpected error")):
            result = validate_token("test-token")
            assert result is None

    @patch("src.core.auth.JWT_VALIDATION_MODE", "introspection")
    @patch("src.core.auth.requests.post")
    def test_validate_token_introspection_success(self, mock_post):
        """Test successful token validation using introspection."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "active": True,
            "sub": "test-user",
            "username": "testuser",
            "groups": ["player"],
        }
        mock_post.return_value = mock_response

        result = validate_token("test-token")
        assert result["sub"] == "test-user"
        assert result["username"] == "testuser"
        assert result["groups"] == ["player"]

    @patch("src.core.auth.JWT_VALIDATION_MODE", "introspection")
    @patch("src.core.auth.requests.post")
    def test_validate_token_introspection_inactive(self, mock_post):
        """Test token validation with inactive token."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"active": False}
        mock_post.return_value = mock_response

        result = validate_token("inactive-token")
        assert result is None

    @patch("src.core.auth.JWT_VALIDATION_MODE", "introspection")
    @patch("src.core.auth.requests.post")
    def test_validate_token_introspection_error(self, mock_post):
        """Test token validation with introspection error."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        result = validate_token("test-token")
        assert result is None

    @patch("src.core.auth.JWT_VALIDATION_MODE", "introspection")
    @patch("src.core.auth.requests.post")
    def test_validate_token_introspection_exception(self, mock_post):
        """Test token validation with request exception."""
        mock_post.side_effect = Exception("Connection error")

        result = validate_token("test-token")
        assert result is None


class TestGetUserRoles:
    """Test user role extraction."""

    def test_get_user_roles_from_groups_list(self):
        """Test extracting roles from groups claim as list."""
        claims = {"groups": ["admin", "player"]}
        roles = get_user_roles(claims)
        assert "admin" in roles
        assert "player" in roles

    def test_get_user_roles_from_groups_string(self):
        """Test extracting roles from groups claim as string."""
        claims = {"groups": "admin"}
        roles = get_user_roles(claims)
        assert "admin" in roles

    def test_get_user_roles_from_roles_list(self):
        """Test extracting roles from roles claim as list."""
        claims = {"roles": ["gamemaster", "player"]}
        roles = get_user_roles(claims)
        assert "gamemaster" in roles
        assert "player" in roles

    def test_get_user_roles_from_roles_string(self):
        """Test extracting roles from roles claim as string."""
        claims = {"roles": "player"}
        roles = get_user_roles(claims)
        assert "player" in roles

    def test_get_user_roles_from_both_claims(self):
        """Test extracting roles from both groups and roles claims."""
        claims = {"groups": ["admin"], "roles": ["player"]}
        roles = get_user_roles(claims)
        assert "admin" in roles
        assert "player" in roles

    def test_get_user_roles_normalize_with_prefix(self):
        """Test role normalization with domain prefix."""
        claims = {"groups": ["Internal/admin", "Application/player"]}
        roles = get_user_roles(claims)
        assert "admin" in roles
        assert "player" in roles

    def test_get_user_roles_empty_claims(self):
        """Test extracting roles from empty claims."""
        claims = {}
        roles = get_user_roles(claims)
        assert roles == []

    def test_get_user_roles_case_normalization(self):
        """Test role name case normalization."""
        claims = {"groups": ["ADMIN", "Player"]}
        roles = get_user_roles(claims)
        assert "admin" in roles
        assert "player" in roles


class TestHasPermission:
    """Test permission checking."""

    def test_has_permission_admin_wildcard(self):
        """Test admin has all permissions."""
        assert has_permission(["admin"], "any:permission")
        assert has_permission(["admin"], "game:create")
        assert has_permission(["admin"], "player:delete")

    def test_has_permission_gamemaster_allowed(self):
        """Test gamemaster has allowed permissions."""
        assert has_permission(["gamemaster"], "game:create")
        assert has_permission(["gamemaster"], "game:manage")
        assert has_permission(["gamemaster"], "player:add")

    def test_has_permission_gamemaster_denied(self):
        """Test gamemaster doesn't have admin permissions."""
        assert not has_permission(["gamemaster"], "system:admin")

    def test_has_permission_player_allowed(self):
        """Test player has allowed permissions."""
        assert has_permission(["player"], "game:view")
        assert has_permission(["player"], "score:submit")

    def test_has_permission_player_denied(self):
        """Test player doesn't have management permissions."""
        assert not has_permission(["player"], "game:create")
        assert not has_permission(["player"], "player:remove")

    def test_has_permission_multiple_roles(self):
        """Test permission check with multiple roles."""
        assert has_permission(["player", "gamemaster"], "game:create")
        assert has_permission(["player", "gamemaster"], "score:submit")

    def test_has_permission_no_roles(self):
        """Test permission check with no roles."""
        assert not has_permission([], "game:view")

    def test_has_permission_unknown_role(self):
        """Test permission check with unknown role."""
        assert not has_permission(["unknown"], "game:view")


class TestLoginRequired:
    """Test login_required decorator."""

    def test_login_required_with_valid_token(self):
        """Test login_required allows access with valid token."""
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"  # pragma: allowlist secret

        @app.route("/protected")
        @login_required
        def protected_route():
            return jsonify({"message": "success"})

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["access_token"] = "test-token"

            with patch("src.core.auth.validate_token") as mock_validate:
                mock_validate.return_value = {
                    "sub": "test-user",
                    "username": "testuser",
                    "groups": ["player"],
                }

                response = client.get("/protected")
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data["message"] == "success"

    def test_login_required_without_token(self):
        """Test login_required redirects without token."""
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"  # pragma: allowlist secret

        @app.route("/login")
        def login():
            return jsonify({"message": "login page"})

        @app.route("/protected")
        @login_required
        def protected_route():
            return jsonify({"message": "success"})

        with app.test_client() as client:
            response = client.get("/protected")
            assert response.status_code == 302
            assert "/login" in response.location

    def test_login_required_with_invalid_token(self):
        """Test login_required redirects with invalid token."""
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"

        @app.route("/login")
        def login():
            return jsonify({"message": "login page"})

        @app.route("/protected")
        @login_required
        def protected_route():
            return jsonify({"message": "success"})

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["access_token"] = "invalid-token"

            with patch("src.core.auth.validate_token", return_value=None):
                response = client.get("/protected")
                assert response.status_code == 302
                assert "/login" in response.location


class TestRoleRequired:
    """Test role_required decorator."""

    def test_role_required_with_correct_role(self):
        """Test role_required allows access with correct role."""
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"

        @app.route("/admin")
        @role_required("admin")
        def admin_route():
            return jsonify({"message": "admin access"})

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["access_token"] = "test-token"

            with patch("src.core.auth.validate_token") as mock_validate:
                mock_validate.return_value = {
                    "sub": "test-user",
                    "username": "testuser",
                    "groups": ["admin"],
                }

                response = client.get("/admin")
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data["message"] == "admin access"

    def test_role_required_with_wrong_role(self):
        """Test role_required denies access with wrong role."""
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"

        @app.route("/admin")
        @role_required("admin")
        def admin_route():
            return jsonify({"message": "admin access"})

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["access_token"] = "test-token"

            with patch("src.core.auth.validate_token") as mock_validate:
                mock_validate.return_value = {
                    "sub": "test-user",
                    "username": "testuser",
                    "groups": ["player"],
                }

                response = client.get("/admin")
                assert response.status_code == 403
                data = json.loads(response.data)
                assert "error" in data

    def test_role_required_multiple_roles(self):
        """Test role_required with multiple allowed roles."""
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"

        @app.route("/manage")
        @role_required("admin", "gamemaster")
        def manage_route():
            return jsonify({"message": "management access"})

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["access_token"] = "test-token"

            with patch("src.core.auth.validate_token") as mock_validate:
                mock_validate.return_value = {
                    "sub": "test-user",
                    "username": "testuser",
                    "groups": ["gamemaster"],
                }

                response = client.get("/manage")
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data["message"] == "management access"


class TestPermissionRequired:
    """Test permission_required decorator."""

    def test_permission_required_with_permission(self):
        """Test permission_required allows access with permission."""
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"

        @app.route("/create-game")
        @permission_required("game:create")
        def create_game():
            return jsonify({"message": "game created"})

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["access_token"] = "test-token"

            with patch("src.core.auth.validate_token") as mock_validate:
                mock_validate.return_value = {
                    "sub": "test-user",
                    "username": "testuser",
                    "groups": ["gamemaster"],
                }

                response = client.get("/create-game")
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data["message"] == "game created"

    def test_permission_required_without_permission(self):
        """Test permission_required denies access without permission."""
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"

        @app.route("/create-game")
        @permission_required("game:create")
        def create_game():
            return jsonify({"message": "game created"})

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["access_token"] = "test-token"

            with patch("src.core.auth.validate_token") as mock_validate:
                mock_validate.return_value = {
                    "sub": "test-user",
                    "username": "testuser",
                    "groups": ["player"],
                }

                response = client.get("/create-game")
                assert response.status_code == 403
                data = json.loads(response.data)
                assert "error" in data

    def test_permission_required_admin_wildcard(self):
        """Test permission_required allows admin with wildcard."""
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"

        @app.route("/any-action")
        @permission_required("any:permission")
        def any_action():
            return jsonify({"message": "action performed"})

        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["access_token"] = "test-token"

            with patch("src.core.auth.validate_token") as mock_validate:
                mock_validate.return_value = {
                    "sub": "test-user",
                    "username": "testuser",
                    "groups": ["admin"],
                }

                response = client.get("/any-action")
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data["message"] == "action performed"


class TestAuthDisabled:
    """Test authentication bypass functionality."""

    @patch("src.core.auth.AUTH_DISABLED", True)
    def test_login_required_bypassed(self):
        """Test login_required decorator bypassed when AUTH_DISABLED is True."""
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"

        @app.route("/protected")
        @login_required
        def protected():
            return jsonify({"message": "success"})

        with app.test_client() as client:
            # No session token, but should still work
            response = client.get("/protected")
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["message"] == "success"

    @patch("src.core.auth.AUTH_DISABLED", True)
    def test_role_required_bypassed(self):
        """Test role_required decorator bypassed when AUTH_DISABLED is True."""
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"

        @app.route("/admin-only")
        @role_required("admin")
        def admin_only():
            return jsonify({"message": "admin access"})

        with app.test_client() as client:
            # No session token or roles, but should still work
            response = client.get("/admin-only")
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["message"] == "admin access"

    @patch("src.core.auth.AUTH_DISABLED", True)
    def test_permission_required_bypassed(self):
        """Test permission_required decorator bypassed when AUTH_DISABLED is True."""
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"

        @app.route("/create-game")
        @permission_required("game:create")
        def create_game():
            return jsonify({"message": "game created"})

        with app.test_client() as client:
            # No session token or permissions, but should still work
            response = client.get("/create-game")
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["message"] == "game created"

    @patch("src.core.auth.AUTH_DISABLED", True)
    def test_multiple_decorators_bypassed(self):
        """Test multiple auth decorators bypassed when AUTH_DISABLED is True."""
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"

        @app.route("/complex")
        @role_required("admin", "gamemaster")
        @permission_required("game:manage")
        def complex_endpoint():
            return jsonify({"message": "complex access granted"})

        with app.test_client() as client:
            # No session token, roles, or permissions, but should still work
            response = client.get("/complex")
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["message"] == "complex access granted"

    @patch("src.core.auth.AUTH_DISABLED", False)
    def test_auth_not_bypassed_when_disabled_false(self):
        """Test authentication is enforced when AUTH_DISABLED is False."""
        app = Flask(__name__)
        app.config["SECRET_KEY"] = "test-secret"

        @app.route("/login")
        def login():
            return jsonify({"message": "login page"})

        @app.route("/protected")
        @login_required
        def protected():
            return jsonify({"message": "success"})

        with app.test_client() as client:
            # No session token, should redirect to login
            response = client.get("/protected")
            assert response.status_code == 302  # Redirect
            assert "/login" in response.location


class TestDynamicRedirectUri:
    """Test dynamic redirect URI generation for localhost and other domains."""

    def test_localhost_http_redirect_uri(self):
        """Test redirect URI for localhost with HTTP."""
        app = Flask(__name__)

        with app.test_request_context("http://localhost:5000/login"):
            uri = get_dynamic_redirect_uri()
            assert uri == "http://localhost:5000/callback"

    def test_localhost_https_redirect_uri(self):
        """Test redirect URI for localhost with HTTPS."""
        app = Flask(__name__)

        with app.test_request_context("https://localhost:5000/login"):
            uri = get_dynamic_redirect_uri()
            assert uri == "https://localhost:5000/callback"

    def test_localhost_with_forwarded_headers(self):
        """Test redirect URI respects X-Forwarded-Proto header."""
        app = Flask(__name__)

        with app.test_request_context(
            "http://localhost:5000/login",
            headers={"X-Forwarded-Proto": "https", "X-Forwarded-Host": "localhost:5000"},
        ):
            uri = get_dynamic_redirect_uri()
            assert uri == "https://localhost:5000/callback"

    def test_localhost_post_logout_redirect_uri(self):
        """Test post-logout redirect URI for localhost."""
        app = Flask(__name__)

        with app.test_request_context("http://localhost:5000/login"):
            uri = get_dynamic_post_logout_redirect_uri()
            assert uri == "http://localhost:5000/"

    def test_remote_domain_redirect_uri(self):
        """Test redirect URI for remote domain."""
        app = Flask(__name__)

        with app.test_request_context("https://letsplaydarts.eu/login"):
            uri = get_dynamic_redirect_uri()
            assert uri == "https://letsplaydarts.eu/callback"

    def test_localhost_127_0_0_1_redirect_uri(self):
        """Test redirect URI for 127.0.0.1."""
        app = Flask(__name__)

        with app.test_request_context("http://127.0.0.1:5000/login"):
            uri = get_dynamic_redirect_uri()
            assert uri == "http://127.0.0.1:5000/callback"
