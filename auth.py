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
from flask import jsonify, redirect, request, session, url_for
from jwt import PyJWKClient

logger = logging.getLogger(__name__)

# WSO2 Identity Server Configuration
WSO2_IS_URL = os.getenv("WSO2_IS_URL", "https://localhost:9443")
WSO2_IS_AUTHORIZE_URL = f"{WSO2_IS_URL}/oauth2/authorize"
WSO2_IS_TOKEN_URL = f"{WSO2_IS_URL}/oauth2/token"
WSO2_IS_USERINFO_URL = f"{WSO2_IS_URL}/oauth2/userinfo"
WSO2_IS_LOGOUT_URL = f"{WSO2_IS_URL}/oidc/logout"
WSO2_IS_JWKS_URL = f"{WSO2_IS_URL}/oauth2/jwks"
WSO2_IS_INTROSPECT_URL = f"{WSO2_IS_URL}/oauth2/introspect"

# OAuth2 Client Configuration
WSO2_CLIENT_ID = os.getenv("WSO2_CLIENT_ID", "")
WSO2_CLIENT_SECRET = os.getenv("WSO2_CLIENT_SECRET", "")
WSO2_REDIRECT_URI = os.getenv("WSO2_REDIRECT_URI", "http://localhost:5000/callback")
WSO2_POST_LOGOUT_REDIRECT_URI = os.getenv(
    "WSO2_POST_LOGOUT_REDIRECT_URI",
    os.getenv("WSO2_REDIRECT_URI", "http://localhost:5000/callback").replace("/callback", "/"),
)

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
        jwks_client = PyJWKClient(WSO2_IS_JWKS_URL)
    except Exception as e:
        logger.warning(f"Failed to initialize JWKS client: {e}")

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
            return decoded
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
                    return result
                logger.warning(f"Token is not active: {result}")
            else:
                logger.warning(
                    f"Token introspection failed: status={response.status_code}",
                )
            return None
        except Exception:
            logger.exception("Error during token introspection")
            return None
    else:
        logger.error("No valid JWT validation mode configured")
        return None


def get_user_roles(token_claims: dict, access_token: str | None = None) -> list[str]:
    """
    Extract user roles from token claims
    WSO2 IS stores roles in 'groups' or 'roles' claim
    If not found in token claims, try fetching from userinfo endpoint
    """
    # Debug: Log all token claims to see what's available
    print(f"[DEBUG] Token claims for role extraction: {token_claims}")
    logger.info(f"Token claims for role extraction: {token_claims}")

    roles = []

    # Check for roles in different claim formats
    if "groups" in token_claims:
        groups = token_claims["groups"]
        if isinstance(groups, list):
            roles.extend(groups)
        elif isinstance(groups, str):
            roles.append(groups)

    if "roles" in token_claims:
        token_roles = token_claims["roles"]
        if isinstance(token_roles, list):
            roles.extend(token_roles)
        elif isinstance(token_roles, str):
            roles.append(token_roles)

    # If no roles found in token claims and we have an access token, try userinfo endpoint
    if not roles and access_token:
        print("[DEBUG] No roles in token claims, trying userinfo endpoint...")
        logger.info("No roles in token claims, trying userinfo endpoint")
        try:
            userinfo = get_user_info(access_token)
            if userinfo:
                print(f"[DEBUG] UserInfo response: {userinfo}")
                logger.info(f"UserInfo response: {userinfo}")

                # Check for roles in userinfo
                if "groups" in userinfo:
                    groups = userinfo["groups"]
                    if isinstance(groups, list):
                        roles.extend(groups)
                    elif isinstance(groups, str):
                        roles.append(groups)

                if "roles" in userinfo:
                    userinfo_roles = userinfo["roles"]
                    if isinstance(userinfo_roles, list):
                        roles.extend(userinfo_roles)
                    elif isinstance(userinfo_roles, str):
                        roles.append(userinfo_roles)
        except Exception as e:
            logger.warning(f"Failed to fetch roles from userinfo: {e}")

    # Normalize role names (remove domain prefixes if present)
    normalized_roles = []
    for role in roles:
        # WSO2 roles might be in format "Internal/player" or "Application/player"
        normalized_role = role.split("/")[-1] if "/" in role else role
        normalized_roles.append(normalized_role.lower())

    print(f"[DEBUG] Extracted and normalized roles: {normalized_roles}")
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
            request.user_claims = {"sub": "bypass_user", "username": "bypass_user"}
            request.user_roles = ["admin"]  # Grant admin role in bypass mode
            logger.info("Authentication bypassed - AUTH_DISABLED is true")
            return f(*args, **kwargs)

        if "access_token" not in session:
            return redirect(url_for("login", next=request.url))

        # Validate token
        token = session.get("access_token")
        claims = validate_token(token)

        if not claims:
            # Token is invalid or expired, clear session and redirect to login
            session.clear()
            return redirect(url_for("login", next=request.url))

        # Store user info in request context
        request.user_claims = claims
        request.user_roles = get_user_roles(claims, access_token=token)

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
    """
    params = {
        "response_type": "code",
        "client_id": WSO2_CLIENT_ID,
        "redirect_uri": WSO2_REDIRECT_URI,
        "scope": "openid profile email groups",
    }

    if state:
        params["state"] = state

    # Debug logging
    logger.info(f"Generating authorization URL with params: {params}")
    logger.info(f"WSO2_CLIENT_ID value: '{WSO2_CLIENT_ID}'")
    logger.info(f"WSO2_REDIRECT_URI value: '{WSO2_REDIRECT_URI}'")

    query_string = urlencode(params)
    auth_url = f"{WSO2_IS_AUTHORIZE_URL}?{query_string}"

    logger.info(f"Generated authorization URL: {auth_url}")

    return auth_url


def exchange_code_for_token(code: str) -> dict | None:
    """
    Exchange authorization code for access token
    """
    try:
        response = requests.post(
            WSO2_IS_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": WSO2_REDIRECT_URI,
                "client_id": WSO2_CLIENT_ID,
                "client_secret": WSO2_CLIENT_SECRET,
            },
            verify=WSO2_IS_VERIFY_SSL,
            timeout=10,
        )

        if response.status_code == 200:
            return response.json()
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
            return response.json()
        logger.exception(
            f"Failed to get user info: status={response.status_code}",
        )
        return None
    except Exception:
        logger.exception("Error getting user info")
        return None


def logout_user(id_token: str | None = None) -> str:
    """
    Generate logout URL for WSO2 IS
    """
    params = {
        "post_logout_redirect_uri": WSO2_POST_LOGOUT_REDIRECT_URI,
    }

    if id_token:
        params["id_token_hint"] = id_token

    query_string = "&".join([f"{k}={v}" for k, v in params.items()])
    return f"{WSO2_IS_LOGOUT_URL}?{query_string}"
