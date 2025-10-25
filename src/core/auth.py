"""
Authentication and Authorization Module for Darts Game System
Integrates with WSO2 Identity Server for OAuth2/OIDC authentication
Implements role-based access control (RBAC)
"""

import logging
import os
from functools import wraps
from typing import Any
from urllib.parse import urlencode

import jwt
import requests
from flask import current_app, has_request_context, jsonify, redirect, request, session
from flask import url_for as flask_url_for

from src.core.config import Config

logger = logging.getLogger(__name__)

# WSO2 Identity Server Configuration
# WSO2_IS_URL: Public URL for browser redirects (authorize, logout)
# WSO2_IS_INTERNAL_URL: Internal URL for backend API calls (token, userinfo, introspect)
WSO2_IS_URL = os.getenv("WSO2_IS_URL", "https://localhost:9443")
WSO2_IS_INTERNAL_URL = os.getenv("WSO2_IS_INTERNAL_URL", WSO2_IS_URL)

# Browser-facing URLs (use public URL)
WSO2_IS_AUTHORIZE_URL = f"{WSO2_IS_URL}/oauth2/authorize"
WSO2_IS_LOGOUT_URL = f"{WSO2_IS_URL}/oidc/logout"

# Backend API URLs (use internal URL for server-to-server communication)
WSO2_IS_TOKEN_URL = f"{WSO2_IS_INTERNAL_URL}/oauth2/token"
WSO2_IS_USERINFO_URL = f"{WSO2_IS_INTERNAL_URL}/oauth2/userinfo"
WSO2_IS_JWKS_URL = f"{WSO2_IS_INTERNAL_URL}/oauth2/jwks"
WSO2_IS_INTROSPECT_URL = f"{WSO2_IS_INTERNAL_URL}/oauth2/introspect"
WSO2_IS_SCIM2_ME_URL = f"{WSO2_IS_INTERNAL_URL}/scim2/Me"

# OAuth2 Client Configuration
WSO2_CLIENT_ID = os.getenv("WSO2_CLIENT_ID", "")
WSO2_CLIENT_SECRET = os.getenv("WSO2_CLIENT_SECRET", "")
# Default redirect URI: use Config for environment-aware defaults
WSO2_REDIRECT_URI_DEFAULT = os.getenv("WSO2_REDIRECT_URI", Config.CALLBACK_URL)
WSO2_POST_LOGOUT_REDIRECT_URI_DEFAULT = os.getenv(
    "WSO2_POST_LOGOUT_REDIRECT_URI",
    os.getenv("WSO2_REDIRECT_URI", Config.LOGOUT_REDIRECT_URL),
)


def get_dynamic_redirect_uri() -> str:
    """
    Dynamically build redirect URI based on the current request and configuration.

    Priority:
    1. Use request headers if available (X-Forwarded-Proto, X-Forwarded-Host)
    2. Fall back to request.scheme and request.host
    3. Fall back to configured defaults (Config.CALLBACK_URL)

    Supports multiple domains and schemes:
    - https://letsplaydarts.eu/callback (production)
    - http://dev.letsplaydarts.eu/callback (development)
    - http://localhost:5000/callback (local)
    """
    if not has_request_context():
        logger.debug(f"No active request, using default redirect URI: {WSO2_REDIRECT_URI_DEFAULT}")
        return WSO2_REDIRECT_URI_DEFAULT

    # Try to get scheme from X-Forwarded-Proto header (from reverse proxy like nginx)
    scheme = request.headers.get("X-Forwarded-Proto", request.scheme)

    # Try to get host from X-Forwarded-Host header (from reverse proxy)
    host = request.headers.get("X-Forwarded-Host", request.host)

    # Build the redirect URI
    redirect_uri = f"{scheme}://{host}/callback"

    # Enhanced logging for localhost debugging
    is_localhost = "localhost" in host or "127.0.0.1" in host
    if is_localhost:
        logger.info(
            f"Localhost redirect URI: {redirect_uri} "
            f"(scheme={scheme}, host={host}, "
            f"config_domain={Config.APP_DOMAIN}, "
            f"config_scheme={Config.APP_SCHEME}, "
            f"session_secure={Config.SESSION_COOKIE_SECURE})",
        )
    else:
        logger.debug(
            f"Dynamic redirect URI: {redirect_uri} "
            f"(scheme={scheme}, host={host}, "
            f"config_domain={Config.APP_DOMAIN})",
        )
    return redirect_uri


def get_dynamic_post_logout_redirect_uri() -> str:
    """
    Dynamically build post-logout redirect URI based on the current request and configuration.

    Priority:
    1. Use request headers if available (X-Forwarded-Proto, X-Forwarded-Host)
    2. Fall back to request.scheme and request.host
    3. Fall back to configured defaults (Config.LOGOUT_REDIRECT_URL)
    """
    if not request:
        logger.debug(
            f"No active request, using default post-logout redirect URI: "
            f"{WSO2_POST_LOGOUT_REDIRECT_URI_DEFAULT}",
        )
        return WSO2_POST_LOGOUT_REDIRECT_URI_DEFAULT

    # Try to get scheme from X-Forwarded-Proto header
    scheme = request.headers.get("X-Forwarded-Proto", request.scheme)

    # Try to get host from X-Forwarded-Host header
    host = request.headers.get("X-Forwarded-Host", request.host)

    # Build the post-logout redirect URI
    post_logout_uri = f"{scheme}://{host}/"

    # Enhanced logging for localhost debugging
    is_localhost = "localhost" in host or "127.0.0.1" in host
    if is_localhost:
        logger.info(
            f"Localhost post-logout redirect URI: {post_logout_uri} "
            f"(scheme={scheme}, host={host})",
        )
    else:
        logger.debug(
            f"Dynamic post-logout redirect URI: {post_logout_uri} (scheme={scheme}, host={host})",
        )
    return post_logout_uri


def get_current_request_url() -> str:
    """
    Reconstruct the current request URL using X-Forwarded-* headers.

    This ensures that when running behind a reverse proxy, the URL reflects
    the external URL (e.g., https://letsplaydarts.eu) rather than the
    internal address (e.g., http://localhost:5000).

    Priority:
    1. Use X-Forwarded-Proto and X-Forwarded-Host headers (from nginx proxy)
    2. Fall back to request.scheme and request.host
    """
    if not request:
        logger.debug("No active request context, cannot build current URL")
        return ""

    # Get scheme from X-Forwarded-Proto header (set by nginx), fallback to request.scheme
    scheme = request.headers.get("X-Forwarded-Proto", request.scheme)

    # Get host from X-Forwarded-Host header (set by nginx), fallback to request.host
    host = request.headers.get("X-Forwarded-Host", request.host)

    # Build the full URL preserving the path and query string
    current_url = f"{scheme}://{host}{request.full_path}"

    # Remove trailing question mark if no query string
    if current_url.endswith("?"):
        current_url = current_url[:-1]

    logger.debug(
        f"Built current request URL: {current_url} (scheme={scheme}, host={host})",
    )
    return current_url


def url_for(endpoint, **values):
    """
    Enhanced url_for wrapper that ensures URLs use the correct scheme and host
    when behind a reverse proxy (respects X-Forwarded-Proto and X-Forwarded-Host).

    This prevents generating localhost URLs when the app is accessed via a proxy.
    """
    # Get the relative URL from Flask's url_for
    relative_url = flask_url_for(endpoint, **values)

    # If _external is explicitly set to True in values, build the full URL
    # using the proxy headers
    if values.get("_external"):
        # Get scheme and host from proxy headers
        scheme = request.headers.get("X-Forwarded-Proto", request.scheme)
        host = request.headers.get("X-Forwarded-Host", request.host)
        return f"{scheme}://{host}{relative_url}"

    # For relative URLs, return as-is (the browser will use the current scheme/host)
    return relative_url


# Introspection credentials
WSO2_IS_INTROSPECT_USER = os.getenv("WSO2_IS_INTROSPECT_USER", "admin")
WSO2_IS_INTROSPECT_PASSWORD = os.getenv("WSO2_IS_INTROSPECT_PASSWORD", "admin")

# JWT validation mode
JWT_VALIDATION_MODE = os.getenv("JWT_VALIDATION_MODE", "introspection")

# SSL verification configuration
WSO2_IS_VERIFY_SSL = os.getenv("WSO2_IS_VERIFY_SSL", "False").lower() == "true"

# Authentication bypass configuration
AUTH_DISABLED = os.getenv("AUTH_DISABLED", "False").lower() == "true"

# Initialize JWKS client
jwks_client = None
if JWT_VALIDATION_MODE == "jwks":
    try:
        # Import PyJWKClient lazily so that importing this module doesn't
        # fail in environments where the installed 'jwt' package/version
        # doesn't provide PyJWKClient (for example, some distributions
        # or a package named 'jwt' that is not PyJWT).
        from jwt import PyJWKClient

        jwks_client = PyJWKClient(WSO2_IS_JWKS_URL)
    except Exception:
        logger.warning(
            "Failed to initialize JWKS client (PyJWKClient may be missing). {e}",
        )

# Role definitions
ROLES = {
    "admin": {
        "name": "Admin",
        "description": "Full system access",
        "permissions": ["*"],
    },
    "gamemaster": {
        "name": "Game Master",
        "description": "Can manage games and players",
        "permissions": [
            "game:create",
            "game:manage",
            "game:delete",
            "player:add",
            "player:remove",
            "score:submit",
            "score:view",
        ],
    },
    "player": {
        "name": "Player",
        "description": "Can view games and submit scores",
        "permissions": ["game:view", "score:submit", "score:view"],
    },
}


def validate_token(token: str) -> dict[str, Any] | None:  # noqa: PLR0911
    """
    Validate JWT/OAuth2 token using JWKS or introspection
    Returns decoded token claims if valid, None otherwise

    When using introspection mode with network issues, falls back to local JWT validation
    to prevent session loss from temporary WSO2 connectivity issues.
    """
    if JWT_VALIDATION_MODE == "jwks" and jwks_client:
        try:
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            decoded = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={"verify_exp": True},
            )
            logger.info(f"Token validated for user: {decoded.get('sub', 'unknown')}")
            return decoded  # type: ignore
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception:
            logger.exception("Error validating token")
            return None
    elif JWT_VALIDATION_MODE == "introspection":
        try:
            response = requests.post(
                WSO2_IS_INTROSPECT_URL,
                auth=(WSO2_IS_INTROSPECT_USER, WSO2_IS_INTROSPECT_PASSWORD),
                data={"token": token},
                verify=WSO2_IS_VERIFY_SSL,
                timeout=5,
            )
            if response.status_code == 200:
                result = response.json()
                if result.get("active"):
                    logger.info(
                        f"Token validated via introspection for user: \
                        {result.get('username', 'unknown')}",
                    )
                    return result  # type: ignore
                logger.warning(f"Token is not active: {result}")
                return None
            logger.warning(
                f"Token introspection failed: status={response.status_code}, "
                f"falling back to local JWT validation",
            )
            # Fall back to local JWT validation if introspection fails
            return _fallback_jwt_validation(token)
        except requests.Timeout:
            logger.warning(
                "Token introspection timed out, falling back to local JWT validation",
            )
            return _fallback_jwt_validation(token)
        except requests.ConnectionError as e:
            logger.warning(
                f"Cannot reach WSO2 for introspection ({e}), "
                f"falling back to local JWT validation",
            )
            return _fallback_jwt_validation(token)
        except Exception as e:
            logger.warning(
                f"Error during token introspection: {e}, falling back to local JWT validation",
            )
            return _fallback_jwt_validation(token)
    else:
        logger.error("No valid JWT validation mode configured")
        return None


def _fallback_jwt_validation(token: str) -> dict[str, Any] | None:
    """
    Fallback local JWT validation without connecting to WSO2
    Validates JWT structure and expiration without signature verification
    (since we can't verify without JWKS endpoint)

    This prevents session loss during temporary WSO2 connectivity issues
    """
    try:
        # Decode without verification to check structure and expiration
        # We skip verification because we can't access JWKS during connectivity issues
        decoded = jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": True},
        )

        logger.info(
            f"Token passed local JWT validation (fallback mode) for user: "
            f"{decoded.get('preferred_username', decoded.get('sub', 'unknown'))}",
        )
        return decoded  # type: ignore
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired (detected in fallback validation)")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token format (fallback validation): {e}")
        return None
    except Exception as e:
        logger.warning(f"Error in fallback JWT validation: {e}")
        return None


def get_user_roles(token_claims: dict, access_token: str | None = None) -> list[str]:
    """
    Extract user roles from token claims using multi-tier approach.

    WSO2 IS stores roles in 'groups' or 'roles' claim.
    Extraction strategy:
    1. Check token claims for role information
    2. If not found, try userinfo endpoint
    3. If still not found, fallback to SCIM2 /Me endpoint

    Args:
        token_claims: Decoded JWT token claims
        access_token: OAuth2 access token for API calls

    Returns:
        List of normalized role names (lowercase, without domain prefixes)
    """
    logger.debug(f"Extracting roles from token claims: {list(token_claims.keys())}")

    roles = []

    # Check for roles in different claim formats that WSO2 might use
    possible_role_claims = ["groups", "roles", "role", "group", "realm_roles"]

    for claim_name in possible_role_claims:
        if claim_name in token_claims:
            claim_value = token_claims[claim_name]
            logger.debug(f"Found claim '{claim_name}': {claim_value}")

            if isinstance(claim_value, list):
                roles.extend(claim_value)
            elif isinstance(claim_value, str):
                roles.append(claim_value)
            elif isinstance(claim_value, dict) and "roles" in claim_value:
                # Handle nested role structures (e.g., realm_access.roles)
                nested_roles = claim_value["roles"]
                if isinstance(nested_roles, list):
                    roles.extend(nested_roles)
                elif isinstance(nested_roles, str):
                    roles.append(nested_roles)

    # If no roles found in token claims and we have an access token, try userinfo endpoint
    if not roles and access_token:
        logger.info("No roles in token claims, trying userinfo endpoint")
        try:
            userinfo = get_user_info(access_token)
            if userinfo:
                logger.info(f"UserInfo response: {userinfo}")

                # Check for roles in userinfo using the same claim names
                for claim_name in possible_role_claims:
                    if claim_name in userinfo:
                        claim_value = userinfo[claim_name]
                        logger.debug(f"Found claim '{claim_name}' in userinfo: {claim_value}")

                        if isinstance(claim_value, list):
                            roles.extend(claim_value)
                        elif isinstance(claim_value, str):
                            roles.append(claim_value)
                        elif isinstance(claim_value, dict) and "roles" in claim_value:
                            nested_roles = claim_value["roles"]
                            if isinstance(nested_roles, list):
                                roles.extend(nested_roles)
                            elif isinstance(nested_roles, str):
                                roles.append(nested_roles)
        except Exception as e:
            logger.warning(f"Failed to fetch roles from userinfo: {e}")

    # If still no roles found, try SCIM2 /Me endpoint as last resort
    if not roles and access_token:
        logger.info("No roles in userinfo, trying SCIM2 /Me endpoint")
        try:
            scim_groups = get_user_groups_from_scim2(access_token)
            if scim_groups:
                roles.extend(scim_groups)
                logger.info(f"SCIM2 returned groups: {scim_groups}")
        except Exception as e:
            logger.warning(f"Failed to fetch roles from SCIM2: {e}")

    # Normalize role names (remove domain prefixes if present)
    normalized_roles = []
    for role in roles:
        # WSO2 roles might be in format "Internal/player" or "Application/player"
        normalized_role = role.split("/")[-1] if "/" in role else role
        normalized_roles.append(normalized_role.lower())

    logger.info(f"Extracted and normalized roles: {normalized_roles}")
    return normalized_roles


def has_permission(user_roles: list[str], required_permission: str) -> bool:
    """
    Check if user has required permission based on their roles
    """
    # Admin has all permissions
    if "admin" in user_roles:
        return True

    # Check each role's permissions
    for role in user_roles:
        if role in ROLES:
            role_permissions = ROLES[role]["permissions"]
            if "*" in role_permissions or required_permission in role_permissions:
                return True

    return False


def login_required(f):
    """
    Decorator to require authentication
    Redirects to login page if user is not authenticated
    Can be bypassed by setting AUTH_DISABLED=true in environment
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Bypass authentication if disabled
        if AUTH_DISABLED:
            # Set default user info for bypass mode
            request.user_claims = {"sub": "bypass_user", "username": "bypass_user"}  # type: ignore
            request.user_roles = ["admin"]  # type: ignore  # Grant admin role in bypass mode

            # Create/get bypass player in database if not already done
            if "player_id" not in session:
                try:
                    # Access game_manager from Flask app context
                    game_manager = current_app.game_manager
                    player = game_manager.db_service.get_or_create_player(
                        username="bypass_user",
                        email="bypass@local.dev",
                        name="Bypass User",
                    )
                    if player:
                        session["player_id"] = player.id
                        logger.info(f"Bypass player created/retrieved: {player.id}")
                except Exception as e:
                    logger.warning(f"Failed to create/get bypass player: {e}")
                    # Continue anyway to avoid breaking the app

            logger.info("Authentication bypassed - AUTH_DISABLED is true")
            return f(*args, **kwargs)

        if "access_token" not in session:
            current_url = get_current_request_url()
            logger.info(
                f"login_required: No access token, "
                f"redirecting to login. Current URL: {current_url}",
            )
            return redirect(url_for("login", next=current_url))

        # Validate token
        token = session.get("access_token")
        claims = validate_token(token)

        if not claims:
            # Token is invalid or expired, clear session and redirect to login
            session.clear()
            current_url = get_current_request_url()
            logger.info(
                f"login_required: Token validation failed, "
                f"redirecting to login. Current URL: {current_url}",
            )
            return redirect(url_for("login", next=current_url))

        # Store user info in request context
        request.user_claims = claims  # type: ignore
        request.user_roles = get_user_roles(claims, access_token=token)  # type: ignore

        return f(*args, **kwargs)

    return decorated_function


def role_required(*required_roles):
    """
    Decorator to require specific roles
    Returns 403 if user doesn't have required role
    Can be bypassed by setting AUTH_DISABLED=true in environment
    """

    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            # Bypass role check if authentication is disabled
            if AUTH_DISABLED:
                logger.info(
                    f"Role check bypassed - AUTH_DISABLED is true (required: {required_roles})",
                )
                return f(*args, **kwargs)

            user_roles = getattr(request, "user_roles", [])

            # Debug: Log role check
            logger.info(f"Role check - User roles: {user_roles}, Required roles: {required_roles}")

            # Check if user has any of the required roles
            if not any(role in user_roles for role in required_roles):
                logger.warning(
                    f"""
                    Access denied - User roles {user_roles} do not match
                    required roles {required_roles}
                    """,
                )
                return (
                    jsonify(
                        {
                            "error": "Forbidden",
                            "message": f"Required role: {', '.join(required_roles)}",
                            "user_roles": user_roles,
                        },
                    ),
                    403,
                )

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def permission_required(permission: str):
    """
    Decorator to require specific permission
    Returns 403 if user doesn't have required permission
    Can be bypassed by setting AUTH_DISABLED=true in environment
    """

    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            # Bypass permission check if authentication is disabled
            if AUTH_DISABLED:
                logger.info(
                    f"Permission check bypassed - AUTH_DISABLED is true (required: {permission})",
                )
                return f(*args, **kwargs)

            user_roles = getattr(request, "user_roles", [])

            if not has_permission(user_roles, permission):
                return (
                    jsonify(
                        {
                            "error": "Forbidden",
                            "message": f"Required permission: {permission}",
                        },
                    ),
                    403,
                )

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def get_authorization_url(state: str | None = None) -> str:
    """
    Generate OAuth2 authorization URL for WSO2 IS
    Uses dynamic redirect URI based on the current request
    """
    redirect_uri = get_dynamic_redirect_uri()

    params = {
        "response_type": "code",
        "client_id": WSO2_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": "openid profile email groups internal_login",
    }

    if state:
        params["state"] = state

    # Debug logging
    logger.info(f"Generating authorization URL with params: {params}")
    logger.info(f"WSO2_CLIENT_ID value: '{WSO2_CLIENT_ID}'")
    logger.info(f"Dynamic redirect_uri value: '{redirect_uri}'")

    query_string = urlencode(params)
    auth_url = f"{WSO2_IS_AUTHORIZE_URL}?{query_string}"

    logger.info(f"Generated authorization URL: {auth_url}")

    return auth_url


def exchange_code_for_token(code: str) -> dict | None:
    """
    Exchange authorization code for access token
    Uses dynamic redirect URI based on the current request
    """
    redirect_uri = get_dynamic_redirect_uri()

    try:
        response = requests.post(
            WSO2_IS_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": WSO2_CLIENT_ID,
                "client_secret": WSO2_CLIENT_SECRET,
            },
            verify=WSO2_IS_VERIFY_SSL,
            timeout=10,
        )

        if response.status_code == 200:
            return response.json()  # type: ignore
        logger.exception(
            f"Token exchange failed: status={response.status_code}, body={response.text}",
        )
        return None
    except Exception:
        logger.exception("Error exchanging code for token")
        return None


def get_user_info(access_token: str) -> dict | None:
    """
    Get user information from WSO2 IS userinfo endpoint
    """
    try:
        response = requests.get(
            WSO2_IS_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            verify=WSO2_IS_VERIFY_SSL,
            timeout=5,
        )

        if response.status_code == 200:
            return response.json()  # type: ignore
        logger.exception(
            f"Failed to get user info: status={response.status_code}",
        )
        return None
    except Exception:
        logger.exception("Error getting user info")
        return None


def get_user_groups_from_scim2(access_token: str) -> list[str]:
    """
    Get user groups from WSO2 IS SCIM2 /Me endpoint
    This is a fallback when groups are not included in the token or userinfo
    """
    try:
        logger.info("Fetching user groups from SCIM2 /Me endpoint")

        response = requests.get(
            WSO2_IS_SCIM2_ME_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            verify=WSO2_IS_VERIFY_SSL,
            timeout=5,
        )

        if response.status_code == 200:
            scim_data = response.json()
            logger.info(f"SCIM2 /Me response: {scim_data}")

            groups = []
            # SCIM2 groups are in the 'groups' array
            if "groups" in scim_data and isinstance(scim_data["groups"], list):
                for group in scim_data["groups"]:
                    # Each group has 'display' and 'value' fields
                    if isinstance(group, dict):
                        group_name = group.get("display") or group.get("value")
                        if group_name:
                            groups.append(group_name)
                    elif isinstance(group, str):
                        groups.append(group)

            logger.info(f"Extracted groups from SCIM2: {groups}")
            return groups

        logger.warning(
            f"Failed to get user groups from SCIM2: status={response.status_code}, "
            f"response={response.text}",
        )
        return []
    except Exception as e:
        logger.warning(f"Error getting user groups from SCIM2: {e}")
        return []


def search_wso2_users(query: str, access_token: str | None = None) -> list[dict]:
    """
    Search for users in WSO2 using SCIM2 API.
    Returns list of users matching the query with username and email.

    Args:
        query: Search term (username, email, or name)
        access_token: Access token for authentication (admin credentials used if not provided)

    Returns:
        List of user dictionaries with id, username, email, and name
    """
    try:
        # Use admin credentials if no access token provided
        auth = None
        if not access_token:
            auth = (WSO2_IS_INTROSPECT_USER, WSO2_IS_INTROSPECT_PASSWORD)

        # Build SCIM2 filter - search by username, email, or name
        filter_param = (
            f'(username co "{query}" or emails co "{query}" or name.familyName co "{query}" '
            f'or name.givenName co "{query}")'
        )

        scim_users_url = f"{WSO2_IS_INTERNAL_URL}/scim2/Users"

        response = requests.get(
            scim_users_url,
            params={"filter": filter_param, "count": "100"},
            headers={
                "Authorization": f"Bearer {access_token}" if access_token else None,
                "Content-Type": "application/scim+json",
            },
            auth=auth if not access_token else None,
            verify=WSO2_IS_VERIFY_SSL,
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()
            users = []

            if "Resources" in data:
                for user in data["Resources"]:
                    user_info = {
                        "id": user.get("id"),
                        "username": user.get("userName"),
                        "email": None,
                        "name": None,
                    }

                    # Extract email
                    if (
                        "emails" in user
                        and isinstance(user["emails"], list)
                        and len(user["emails"]) > 0
                    ):
                        user_info["email"] = user["emails"][0].get("value")

                    # Extract name
                    if "name" in user:
                        name_parts = []
                        if user["name"].get("givenName"):
                            name_parts.append(user["name"]["givenName"])
                        if user["name"].get("familyName"):
                            name_parts.append(user["name"]["familyName"])
                        if name_parts:
                            user_info["name"] = " ".join(name_parts)

                    users.append(user_info)

            logger.info(f"Found {len(users)} users matching query '{query}'")
            return users

        logger.warning(
            f"WSO2 user search failed: status={response.status_code}, response={response.text}",
        )
        return []
    except Exception:
        logger.exception("Error searching WSO2 users:")
        return []


def get_wso2_user_info(username: str, access_token: str | None = None) -> dict | None:
    """
    Get detailed information for a specific WSO2 user by username.

    Args:
        username: Username to look up
        access_token: Access token for authentication

    Returns:
        Dictionary with user details (id, username, email, name) or None if not found
    """
    try:
        auth = None
        if not access_token:
            auth = (WSO2_IS_INTROSPECT_USER, WSO2_IS_INTROSPECT_PASSWORD)

        # Filter by exact username match
        filter_param = f'(userName eq "{username}")'

        scim_users_url = f"{WSO2_IS_INTERNAL_URL}/scim2/Users"

        response = requests.get(
            scim_users_url,
            params={"filter": filter_param},
            headers={
                "Authorization": f"Bearer {access_token}" if access_token else None,
                "Content-Type": "application/scim+json",
            },
            auth=auth if not access_token else None,
            verify=WSO2_IS_VERIFY_SSL,
            timeout=10,
        )

        if response.status_code == 200:
            data = response.json()

            if "Resources" in data and len(data["Resources"]) > 0:
                user = data["Resources"][0]
                user_info = {
                    "id": user.get("id"),
                    "username": user.get("userName"),
                    "email": None,
                    "name": None,
                }

                if (
                    "emails" in user
                    and isinstance(user["emails"], list)
                    and len(user["emails"]) > 0
                ):
                    user_info["email"] = user["emails"][0].get("value")

                if "name" in user:
                    name_parts = []
                    if user["name"].get("givenName"):
                        name_parts.append(user["name"]["givenName"])
                    if user["name"].get("familyName"):
                        name_parts.append(user["name"]["familyName"])
                    if name_parts:
                        user_info["name"] = " ".join(name_parts)

                logger.info(f"Found WSO2 user: {username}")
                return user_info

            logger.warning(f"User '{username}' not found in WSO2")
            return None

        logger.warning(f"WSO2 user lookup failed: status={response.status_code}")
        return None
    except Exception:
        logger.exception(f"Error looking up WSO2 user '{username}'")
        return None


def logout_user(id_token: str | None = None) -> str:
    """
    Generate logout URL for WSO2 IS
    Uses dynamic post-logout redirect URI based on the current request
    """
    post_logout_uri = get_dynamic_post_logout_redirect_uri()

    params = {
        "post_logout_redirect_uri": post_logout_uri,
    }

    if id_token:
        params["id_token_hint"] = id_token

    query_string = urlencode(params)
    return f"{WSO2_IS_LOGOUT_URL}?{query_string}"
