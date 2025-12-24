"""
Authentication and user management endpoints
"""

import os
import secrets

import requests
from flask import (
    Blueprint,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask import (
    current_app as _flask_current_app,
)

from src.core.auth import (
    exchange_code_for_token,
    get_authorization_url,
    get_user_groups_from_scim2,
    get_user_info,
    get_user_roles,
    login_required,
    logout_user,
    validate_token,
)

auth_bp = Blueprint("auth", __name__)

# Module-level placeholder so tests can patch `src.app.app_auth.current_app`.
current_app = None


def _app():
    return current_app if current_app is not None else _flask_current_app


def _verify_callback_state():
    """Verify state parameter to prevent CSRF.
    ---
    tags:
      - Auth
    summary: Verify OAuth callback state
    description: Checks the `state` query parameter against the session-stored \
      oauth_state to prevent CSRF attacks.
    responses:
      200:
        description: State valid (returns True/False internally)
    """
    state = request.args.get("state")
    stored_state = session.get("oauth_state")
    _app().logger.info(f"Callback state check: {state}")
    if state != stored_state:
        _app().logger.error(f"State mismatch! {state} vs {stored_state}")
        return False
    return True


def _handle_auth_code_exchange():
    """Get code and exchange for tokens."""
    code = request.args.get("code")
    if not code:
        error = request.args.get("error", "Authorization failed")
        return None, error

    token_response = exchange_code_for_token(code)
    if not token_response:
        return None, "Failed to obtain access token"

    session["access_token"] = token_response.get("access_token")
    session["refresh_token"] = token_response.get("refresh_token")
    session["id_token"] = token_response.get("id_token")
    return session["access_token"], None


def _process_scim2_data(scim_data, username, email, name):
    """Extract user data from SCIM2 response."""
    username = scim_data.get("userName") or username
    if not email:
        emails = scim_data.get("emails", [])
        if emails:
            email = emails[0] if isinstance(emails[0], str) else emails[0].get("value")
    if not name:
        name_obj = scim_data.get("name", {})
        if isinstance(name_obj, dict):
            given = name_obj.get("givenName", "")
            family = name_obj.get("familyName", "")
            name = f"{given} {family}".strip()
    return username, email, name


def _fetch_scim2_user(access_token):
    """Fetch user data from SCIM2 /Me endpoint."""
    try:
        wso2_url = os.getenv("WSO2_IS_INTERNAL_URL", "https://wso2is:9443")
        verify_ssl = os.getenv("WSO2_IS_VERIFY_SSL", "false").lower() in ("true", "1", "yes")
        resp = requests.get(
            f"{wso2_url}/scim2/Me",
            headers={"Authorization": f"Bearer {access_token}"},
            verify=verify_ssl,
            timeout=5,
        )
        return resp.json() if resp.status_code == 200 else None
    except Exception:
        return None


def _ensure_player_exists(username, email, name):
    """Create or get player in database."""
    if not username:
        return
    try:
        player = _app().game_manager.db_service.get_or_create_player(
            username=username,
            email=email,
            name=name,
        )
        if player:
            session["player_id"] = player.id
    except Exception as e:
        _app().logger.warning(f"Player creation failed: {e}")


@auth_bp.route("/login")
def login():
    """Login page
    ---
    tags:
      - Auth
    summary: Login page (initiates OAuth2 flow)
    description: Redirects user to OAuth provider to authenticate and stores state in session.
    responses:
      200:
        description: Login page rendered
      302:
        description: Redirect to OAuth provider
    """
    # use _app() for test-friendly current_app
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state
    session.permanent = True  # Make session persistent across requests

    # Store the "next" parameter to redirect after login
    next_url = request.args.get("next")
    if next_url:
        session["login_next_url"] = next_url
        _app().logger.info(f"Storing redirect URL in session: {next_url}")
    else:
        _app().logger.warning("No 'next' parameter found in login request")

    # Ensure session changes are persisted
    session.modified = True

    # Debug logging
    _app().logger.info(f"Login - Generated state: {state}")
    _app().logger.info(f"Login - Session ID: {session.get('_id', 'No session ID')}")
    _app().logger.info(
        f"Login - Session data: oauth_state={session.get('oauth_state', 'MISSING')}, "
        f"login_next_url={session.get('login_next_url', 'MISSING')}",
    )

    # Get authorization URL
    auth_url = get_authorization_url(state)

    error = request.args.get("error")
    return render_template("login.html", auth_url=auth_url, error=error)


@auth_bp.route("/callback")
def callback():
    """OAuth2 callback endpoint
    ---
    tags:
      - Auth
    summary: OAuth2 callback
    description: Handles authorization code exchange and sets session tokens/user info.
    responses:
      302:
        description: Redirects to original requested page after login
      400:
        description: Invalid state or token exchange failed
    """
    _app().logger.info(f"Callback - Session ID: {session.get('_id', 'No session ID')}")
    if not _verify_callback_state():
        return redirect(url_for("auth.login", error="Invalid state parameter"))

    access_token, error = _handle_auth_code_exchange()
    if error:
        return redirect(url_for("auth.login", error=error))

    user_info = get_user_info(access_token)
    if user_info:
        session["user_info"] = user_info
        username = user_info.get("preferred_username") or user_info.get("username")
        email = user_info.get("email")
        name = user_info.get("name") or user_info.get("given_name")

        if not username or "-" in str(username):
            scim_data = _fetch_scim2_user(access_token)
            if scim_data:
                username, email, name = _process_scim2_data(scim_data, username, email, name)

        if username and "@" in username:
            username = username.split("@")[0]

        if not username or "-" in str(username):
            username = user_info.get("sub")
        if not name:
            name = username

        _ensure_player_exists(username, email, name)

    session.pop("oauth_state", None)
    next_url = session.pop("login_next_url", None) or "/"
    session.modified = True
    _app().logger.info(f"Callback redirecting to: {next_url}")
    return redirect(next_url)


@auth_bp.route("/logout")
def logout():
    """Logout endpoint
    ---
    tags:
      - Auth
    summary: Logout user
    description: Clears session and redirects to WSO2 logout endpoint.
    responses:
      302:
        description: Redirect to upstream logout URL
    """
    id_token = session.get("id_token")

    # Clear session
    session.clear()

    # Redirect to WSO2 logout
    logout_url = logout_user(id_token)
    return redirect(logout_url)


@auth_bp.route("/profile")
@login_required
def profile():
    """User profile page
    ---
    tags:
      - User
    summary: Get current user profile
    description: Returns user information stored in session including roles and claims.
    responses:
      200:
        description: User profile JSON
    """
    user_info = session.get("user_info", {})
    user_roles = getattr(request, "user_roles", [])
    user_claims = getattr(request, "user_claims", {})

    return jsonify(
        {
            "user_info": user_info,
            "roles": user_roles,
            "claims": user_claims,
        },
    )


@auth_bp.route("/debug/auth")
@login_required
def debug_auth():
    """Debug authentication information
    ---
    tags:
      - Debug
    summary: Debug auth
    description: Returns token claims, extracted roles, and SCIM2 groups for debugging.
    responses:
      200:
        description: Debug authentication data
    """
    # using _app() instead of local current_app import
    access_token = session.get("access_token")
    user_info = session.get("user_info", {})

    # Validate token and get claims
    token_claims = validate_token(access_token) if access_token else {}

    # Extract roles
    extracted_roles = get_user_roles(token_claims or {}, access_token=access_token)

    # Try to get SCIM2 groups directly
    scim2_groups = []
    if access_token:
        try:
            scim2_groups = get_user_groups_from_scim2(access_token)
        except Exception as e:
            _app().logger.warning(f"Failed to fetch SCIM2 groups in debug: {e}")

    return jsonify(
        {
            "session_keys": list(session.keys()),
            "user_info": user_info,
            "token_claims": token_claims,
            "extracted_roles": extracted_roles,
            "scim2_groups": scim2_groups,
            "request_user_roles": getattr(request, "user_roles", []),
            "request_user_claims": getattr(request, "user_claims", {}),
        },
    )
