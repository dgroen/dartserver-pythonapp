"""
UI and page rendering endpoints
"""

from pathlib import Path

from dartserver_core.auth import login_required, permission_required, role_required
from flask import Blueprint, jsonify, render_template, request, send_from_directory

ui_bp = Blueprint("ui", __name__)

# Get root directory for static files
_app_dir = Path(__file__).resolve().parent
_root_dir = _app_dir.parent.parent


@ui_bp.route("/")
@login_required
def index():
    """Main game board page
    ---
    tags:
      - UI
    summary: Main game board page
    description: Renders the main game board interface for displaying the darts game
    responses:
      200:
        description: HTML page rendered successfully
        content:
          text/html:
            schema:
              type: string
    """
    user_roles = getattr(request, "user_roles", [])
    user_claims = getattr(request, "user_claims", {})
    return render_template("index.html", user_roles=user_roles, user_claims=user_claims)


@ui_bp.route("/service-worker.js")
def serve_service_worker():
    """Serve the service worker file (no authentication required for PWA)
    ---
    tags:
      - UI
    summary: Serve service worker file
    description: Returns the PWA service worker JavaScript file
    responses:
      200:
        description: Service worker JS served successfully
        content:
          application/javascript:
            schema:
              type: string
    """
    return send_from_directory(str(_root_dir / "static"), "service-worker.js")


@ui_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for Docker health monitoring
    ---
    tags:
      - UI
    summary: Health check endpoint
    description: Returns 200 OK if the application is running and healthy
    responses:
      200:
        description: Application is healthy
        schema:
          type: object
          properties:
            status:
              type: string
              example: healthy
    """
    return jsonify({"status": "healthy"}), 200


@ui_bp.route("/control")
@login_required
@role_required("admin", "gamemaster")
def control():
    """Game control panel - requires admin or gamemaster role
    ---
    tags:
      - UI
    summary: Game control panel
    description: Renders the control panel interface for managing the game
    responses:
      200:
        description: HTML page rendered successfully
    """
    user_roles = getattr(request, "user_roles", [])
    user_claims = getattr(request, "user_claims", {})
    return render_template("control.html", user_roles=user_roles, user_claims=user_claims)


@ui_bp.route("/game/create")
@login_required
@permission_required("game:create")
def game_create():
    """Game creation page - requires game:create permission
    ---
    tags:
      - UI
    summary: Game creation page
    description: Renders the game creation interface for starting new games
    responses:
      200:
        description: HTML page rendered successfully
    """
    user_roles = getattr(request, "user_roles", [])
    user_claims = getattr(request, "user_claims", {})
    return render_template("game_create.html", user_roles=user_roles, user_claims=user_claims)


@ui_bp.route("/history")
@login_required
def history():
    """User game history page
    ---
    tags:
      - UI
    summary: Game history page
    description: Renders the user's game history with statistics
    responses:
      200:
        description: HTML page rendered successfully
    """
    user_roles = getattr(request, "user_roles", [])
    user_claims = getattr(request, "user_claims", {})
    return render_template("history.html", user_roles=user_roles, user_claims=user_claims)


@ui_bp.route("/dashboard")
@login_required
def dashboard():
    """Game dashboard page with game history
    ---
    tags:
      - UI
    summary: Game dashboard page
    description: Renders the dashboard with game history, statistics, and game details
    responses:
      200:
        description: HTML page rendered successfully
    """
    user_roles = getattr(request, "user_roles", [])
    user_claims = getattr(request, "user_claims", {})
    return render_template("dashboard.html", user_roles=user_roles, user_claims=user_claims)


@ui_bp.route("/training")
@login_required
def training():
    """Training mode page for single-player practice
    ---
    tags:
      - UI
    summary: Training mode page
    description: Renders the training mode interface for single-player practice
    responses:
      200:
        description: HTML page rendered successfully
    """
    user_roles = getattr(request, "user_roles", [])
    user_claims = getattr(request, "user_claims", {})
    return render_template("training.html", user_roles=user_roles, user_claims=user_claims)


@ui_bp.route("/training/dashboard")
@login_required
def training_dashboard():
    """Training statistics dashboard
    ---
    tags:
      - UI
    summary: Training statistics dashboard
    description: Renders the training statistics and history dashboard
    responses:
      200:
        description: HTML page rendered successfully
    """
    user_roles = getattr(request, "user_roles", [])
    user_claims = getattr(request, "user_claims", {})
    return render_template(
        "training_dashboard.html",
        user_roles=user_roles,
        user_claims=user_claims,
    )


@ui_bp.route("/test-refresh")
def test_refresh():
    """Test page for automatic refresh functionality
    ---
    tags:
      - UI
    summary: Test page for automatic refresh
    description: Test page for verifying automatic refresh functionality
    responses:
      200:
        description: HTML page rendered successfully
    """
    return render_template("test_refresh.html")


@ui_bp.route("/admin")
@login_required
@role_required("admin")
def admin_home():
    """Admin home page - requires admin role
    ---
    tags:
      - Admin
    summary: Admin dashboard home
    description: Renders the admin dashboard with navigation to all admin functions
    responses:
      200:
        description: HTML page rendered successfully
    """
    user_roles = getattr(request, "user_roles", [])
    user_claims = getattr(request, "user_claims", {})
    return render_template(
        "admin_home.html",
        user_roles=user_roles,
        user_claims=user_claims,
    )


@ui_bp.route("/admin/dartboard-testing")
@login_required
@role_required("admin", "gamemaster")
def admin_dartboard_testing():
    """Admin dartboard testing page - requires admin or gamemaster role
    ---
    tags:
      - Admin
    summary: Dartboard testing interface
    description: Renders the dartboard testing and calibration interface
    responses:
      200:
        description: HTML page rendered successfully
    """
    user_roles = getattr(request, "user_roles", [])
    user_claims = getattr(request, "user_claims", {})
    return render_template(
        "admin_dartboard_testing.html",
        user_roles=user_roles,
        user_claims=user_claims,
    )


@ui_bp.route("/admin/tts-testing")
@login_required
@role_required("admin")
def admin_tts_testing():
    """Admin TTS testing page - requires admin role
    ---
    tags:
      - Admin
    summary: TTS testing interface
    description: Renders the TTS testing and configuration interface
    responses:
      200:
        description: HTML page rendered successfully
    """
    user_roles = getattr(request, "user_roles", [])
    user_claims = getattr(request, "user_claims", {})
    return render_template(
        "admin_tts_testing.html",
        user_roles=user_roles,
        user_claims=user_claims,
    )


@ui_bp.route("/admin/users")
@login_required
@role_required("admin")
def admin_users():
    """Admin user management page - requires admin role
    ---
    tags:
      - Admin
    summary: User management interface
    description: Renders the user management interface for creating, updating, and managing users
    responses:
      200:
        description: HTML page rendered successfully
    """
    user_roles = getattr(request, "user_roles", [])
    user_claims = getattr(request, "user_claims", {})
    return render_template(
        "admin_users.html",
        user_roles=user_roles,
        user_claims=user_claims,
    )


@ui_bp.route("/admin/games")
@login_required
@role_required("admin")
def admin_games():
    """Admin game management page - requires admin role
    ---
    tags:
      - Admin
    summary: Game management interface
    description: Renders the game management interface for managing and archiving games
    responses:
      200:
        description: HTML page rendered successfully
    """
    user_roles = getattr(request, "user_roles", [])
    user_claims = getattr(request, "user_claims", {})
    return render_template(
        "admin_games.html",
        user_roles=user_roles,
        user_claims=user_claims,
    )


@ui_bp.route("/admin/active-users")
@login_required
@role_required("admin")
def admin_active_users():
    """Admin active users page - requires admin role
    ---
    tags:
      - Admin
    summary: Active users overview
    description: Renders the active users overview showing logged-in users
    responses:
      200:
        description: HTML page rendered successfully
    """
    user_roles = getattr(request, "user_roles", [])
    user_claims = getattr(request, "user_claims", {})
    return render_template(
        "admin_active_users.html",
        user_roles=user_roles,
        user_claims=user_claims,
    )


@ui_bp.route("/admin/statistics")
@login_required
@role_required("admin")
def admin_statistics():
    """Admin statistics page - requires admin role
    ---
    tags:
      - Admin
    summary: User statistics interface
    description: Renders the statistics interface showing user performance metrics
    responses:
      200:
        description: HTML page rendered successfully
    """
    user_roles = getattr(request, "user_roles", [])
    user_claims = getattr(request, "user_claims", {})
    return render_template(
        "admin_statistics.html",
        user_roles=user_roles,
        user_claims=user_claims,
    )


@ui_bp.route("/profile")
@login_required
def profile():
    """User profile page
    ---
    tags:
      - UI
    summary: User profile page
    description: Renders the user profile page with personal information, statistics, and settings
    responses:
      200:
        description: HTML page rendered successfully
    """
    user_roles = getattr(request, "user_roles", [])
    user_claims = getattr(request, "user_claims", {})
    return render_template("profile.html", user_roles=user_roles, user_claims=user_claims)
