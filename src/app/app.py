"""
Darts Game Web Application
Receives scores through RabbitMQ and manages 301 and Cricket games
Includes WSO2 IS authentication and role-based access control
"""

import logging
import os
import secrets
import ssl
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone
from functools import wraps
from pathlib import Path

import requests
from dotenv import load_dotenv
from eventlet import wsgi
from flasgger import Swagger
from flask import (
    Flask,
    Response,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from flask_cors import CORS
from flask_socketio import SocketIO
from sqlalchemy import func
from werkzeug.middleware.proxy_fix import ProxyFix

from src.app.mobile_service import MobileService
from src.app.multi_game_manager import MultiGameManager
from src.core.auth import (
    exchange_code_for_token,
    get_authorization_url,
    get_user_groups_from_scim2,
    get_user_info,
    get_user_roles,
    get_wso2_user_info,
    login_required,
    logout_user,
    permission_required,
    role_required,
    search_wso2_users,
    validate_token,
)
from src.core.config import Config
from src.core.dartboard_service import DartboardMappingError, DartboardService
from src.core.database_models import GameType, Player, TrainingScore, TrainingSession
from src.core.database_service import get_session, set_database_service
from src.core.rabbitmq_consumer import RabbitMQConsumer

# Load environment variables
load_dotenv()

# Configure logging to output to stdout for Docker
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Initialize Flask app with correct template and static folder paths
# Since app.py is in src/app/, we need to go up 2 levels to reach root templates/static
_app_dir = Path(__file__).resolve().parent
_root_dir = _app_dir.parent.parent
app = Flask(
    __name__,
    template_folder=str(_root_dir / "templates"),
    static_folder=str(_root_dir / "static"),
)

# Configure Flask to trust proxy headers from nginx
# This allows Flask to correctly detect the original scheme (https) and host
# when running behind a reverse proxy
app.wsgi_app = ProxyFix(  # type: ignore
    app.wsgi_app,
    x_for=1,  # Trust X-Forwarded-For
    x_proto=1,  # Trust X-Forwarded-Proto
    x_host=1,  # Trust X-Forwarded-Host
    x_prefix=1,  # Trust X-Forwarded-Prefix
)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
# Use Config class for environment-aware SSL settings
app.config["SESSION_COOKIE_SECURE"] = Config.SESSION_COOKIE_SECURE
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = 3600  # 1 hour
# Enable CORS with credentials support - required for session cookies to work
CORS(
    app,
    origins=[Config.APP_URL],
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
)

# Log environment and configuration info
logging.info(f"Application Configuration: {Config}")
logging.info(f"Environment: {Config.get_environment()}")
logging.info(f"App URL: {Config.APP_URL}")
logging.info(f"Callback URL: {Config.CALLBACK_URL}")
logging.info(f"Session Cookie Secure: {app.config['SESSION_COOKIE_SECURE']}")

# Initialize Swagger
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
        },
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api/docs/",
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Darts Game API",
        "description": "API for managing darts games (301, 401, 501, Cricket, Round the Clock) \
        with real-time score tracking",
        "version": "1.0.0",
        "contact": {
            "name": "Darts Game Server",
        },
    },
    "host": Config.SWAGGER_HOST,
    "basePath": "/",
    "schemes": ["http", "https"] if not Config.is_production() else ["https"],
    "tags": [
        {"name": "Game", "description": "Game management endpoints"},
        {"name": "Players", "description": "Player management endpoints"},
        {"name": "Score", "description": "Score submission endpoints"},
        {"name": "TTS", "description": "Text-to-Speech configuration endpoints"},
        {"name": "UI", "description": "User interface endpoints"},
    ],
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

# Initialize Multi-Game Manager
multi_game_manager = MultiGameManager(socketio)

# Create a default game for backward compatibility
default_game_manager = multi_game_manager.create_game("default")
game_manager = default_game_manager  # Keep for backward compatibility with existing code
app.game_manager = game_manager  # Attach to app for access in decorators

# Multi-game management - track all active games
games_store = {}  # Dict[str, dict] - stores game metadata
active_game_id = None  # Current active game

# Initialize global database service for dartboard endpoints
set_database_service(game_manager.db_service)

# Initialize RabbitMQ Consumer
rabbitmq_consumer = None


def on_score_received(score_data):
    """Callback when a score is received from RabbitMQ"""
    print(f"Score received: {score_data}")
    game_manager.process_score(score_data)


@app.route("/")
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


@app.route("/service-worker.js")
def serve_service_worker():
    """Serve the service worker file (no authentication required for PWA)"""
    return send_from_directory(str(_root_dir / "static"), "service-worker.js")


@app.route("/health", methods=["GET"])
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


@app.route("/control")
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


@app.route("/game/create")
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


@app.route("/history")
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


@app.route("/dashboard")
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


@app.route("/training")
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


@app.route("/training/dashboard")
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


def _verify_callback_state():
    """Verify state parameter to prevent CSRF."""
    state = request.args.get("state")
    stored_state = session.get("oauth_state")
    app.logger.info(f"Callback state check: {state}")
    if state != stored_state:
        app.logger.error(f"State mismatch! {state} vs {stored_state}")
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
        player = game_manager.db_service.get_or_create_player(
            username=username,
            email=email,
            name=name,
        )
        if player:
            session["player_id"] = player.id
    except Exception as e:
        app.logger.warning(f"Player creation failed: {e}")


@app.route("/login")
def login():
    """Login page"""
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state
    session.permanent = True  # Make session persistent across requests

    # Store the "next" parameter to redirect after login
    next_url = request.args.get("next")
    if next_url:
        session["login_next_url"] = next_url
        app.logger.info(f"Storing redirect URL in session: {next_url}")
    else:
        app.logger.warning("No 'next' parameter found in login request")

    # Ensure session changes are persisted
    session.modified = True

    # Debug logging
    app.logger.info(f"Login - Generated state: {state}")
    app.logger.info(f"Login - Session ID: {session.get('_id', 'No session ID')}")
    app.logger.info(
        f"Login - Session data: oauth_state={session.get('oauth_state', 'MISSING')}, "
        f"login_next_url={session.get('login_next_url', 'MISSING')}",
    )

    # Get authorization URL
    auth_url = get_authorization_url(state)

    error = request.args.get("error")
    return render_template("login.html", auth_url=auth_url, error=error)


@app.route("/callback")
def callback():
    """OAuth2 callback endpoint"""
    app.logger.info(f"Callback - Session ID: {session.get('_id', 'No session ID')}")

    if not _verify_callback_state():
        return redirect(url_for("login", error="Invalid state parameter"))

    access_token, error = _handle_auth_code_exchange()
    if error:
        return redirect(url_for("login", error=error))

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
    app.logger.info(f"Callback redirecting to: {next_url}")
    return redirect(next_url)


@app.route("/logout")
def logout():
    """Logout endpoint"""
    id_token = session.get("id_token")

    # Clear session
    session.clear()

    # Redirect to WSO2 logout
    logout_url = logout_user(id_token)
    return redirect(logout_url)


@app.route("/profile")
@login_required
def profile():
    """User profile page"""
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


@app.route("/debug/auth")
@login_required
def debug_auth():
    """Debug authentication information"""
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
            app.logger.warning(f"Failed to fetch SCIM2 groups in debug: {e}")

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


@app.route("/test-refresh")
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


@app.route("/api/game/state", methods=["GET"])
@login_required
def get_game_state():
    """Get current game state - all authenticated users
    ---
    tags:
      - Game
    summary: Get current game state
    description: Returns the complete current state including players, scores, and game type
    responses:
      200:
        description: Current game state
        schema:
          type: object
          properties:
            players:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    description: Player ID
                  name:
                    type: string
                    description: Player name
                  score:
                    type: integer
                    description: Current score (for 301/401/501 games)
                  is_turn:
                    type: boolean
                    description: Whether it's this player's turn
            current_player:
              type: integer
              description: Index of the current player
            game_type:
              type: string
              description: Type of game (301, 401, 501, cricket, round_the_clock,
                round_the_clock_double)
              enum: ['301', '401', '501', 'cricket', 'round_the_clock',
                'round_the_clock_double']
            is_started:
              type: boolean
              description: Whether the game has started
            is_paused:
              type: boolean
              description: Whether the game is paused
            is_winner:
              type: boolean
              description: Whether there is a winner
            current_throw:
              type: integer
              description: Current throw number (1-3)
            game_data:
              type: object
              description: Game-specific data
    """
    return jsonify(game_manager.get_game_state())


@app.route("/api/game/new", methods=["POST"])
@login_required
@permission_required("game:create")
def new_game():
    """Start a new game - requires game:create permission
    ---
    tags:
      - Game
    summary: Start a new game
    description: Initializes a new darts game with specified type and players
    parameters:
      - in: body
        name: body
        description: Game configuration
        required: true
        schema:
          type: object
          properties:
            game_type:
              type: string
              description: Type of game to start
              enum: ['301', '401', '501', 'cricket', 'round_the_clock', 'round_the_clock_double']
              default: '301'
              example: '301'
            players:
              type: array
              description: List of player names
              items:
                type: string
              default: ['Player 1', 'Player 2']
              example: ['Alice', 'Bob']
            double_out:
              type: boolean
              description: Whether to require double-out to finish (only for 301/401/501)
              default: false
              example: false
            reset_on_miss:
              type: boolean
              description: Enable hard mode for round_the_clock (reset to 20 after 3 misses)
              default: false
              example: false
    responses:
      200:
        description: Game started successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: New game started
            game_id:
              type: string
              description: The ID of the created game
      400:
        description: Invalid request or player not found
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
    """
    # global games_store
    global active_game_id
    global game_manager

    data = request.json
    game_type = data.get("game_type", "301")
    player_data = data.get("players", [])
    double_out = data.get("double_out", False)
    reset_on_miss = data.get("reset_on_miss", False)

    # Generate game_id if not provided
    game_id = f"game-{uuid.uuid4().hex[:8]}"

    # Convert player names to player objects with database IDs
    db_session = game_manager.db_service.db_manager.get_session()
    try:
        player_ids = []

        for player_name in player_data:
            # Try to find player by name or username
            player = (
                db_session.query(Player)
                .filter(
                    (Player.name == player_name) | (Player.username == player_name),
                )
                .first()
            )
            if player:
                player_ids.append({"db_id": player.id, "name": player.name})
            else:
                # If player not found in database, return an error response
                app.logger.warning(
                    f"Player '{player_name}' not found in database. "
                    "Only registered WSO2 users can play.",
                )
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": (
                                f"Player '{player_name}' not found. "
                                "Only registered WSO2 users allowed."
                            ),
                        },
                    ),
                    400,
                )

        if not player_ids:
            player_ids = [session.get("player_id")]

        # Create a dedicated session and start the game there
        new_game_manager = multi_game_manager.create_game(game_id)
        new_game_manager.new_game(
            game_type,
            player_ids=player_ids,
            double_out=double_out,
            reset_on_miss=reset_on_miss,
        )
        # Set active and update global pointers so main area shows this game
        multi_game_manager.set_active_game(game_id)
        game_manager = new_game_manager
        app.game_manager = game_manager

        # Store game metadata in games_store
        games_store[game_id] = {
            "game_id": game_id,
            "game_type": game_type,
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
            "players": player_ids,
            "double_out": double_out,
            "reset_on_miss": reset_on_miss,
        }
        active_game_id = game_id

        # Game state is automatically emitted by game_manager.new_game()
        return jsonify({"status": "success", "message": "New game started", "game_id": game_id})
    except Exception:
        app.logger.exception("Error starting new game")
        # Don't expose internal error details to clients
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "An error occurred while starting the game. Please try again.",
                },
            ),
            500,
        )
    finally:
        db_session.close()


@app.route("/api/games", methods=["GET"])
@login_required
def list_games():
    """List all active game sessions - all authenticated users
    ---
    tags:
      - Game
    summary: List all active games
    description: Returns a list of all active game sessions with their basic information
    responses:
      200:
        description: List of active games
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            games:
              type: array
              items:
                type: object
                properties:
                  game_id:
                    type: string
                    description: Unique game identifier
                  game_type:
                    type: string
                    description: Type of game
                  is_started:
                    type: boolean
                    description: Whether the game has started
                  is_active:
                    type: boolean
                    description: Whether this is the currently active game
                  player_count:
                    type: integer
                    description: Number of players
                  players:
                    type: array
                    items:
                      type: string
                    description: List of player names
    """
    try:
        games = multi_game_manager.list_games()
        # Hide legacy default session from UI
        games = [g for g in games if g.get("game_id") != "default"]
        active_id = multi_game_manager.get_active_game_id()
        if active_id == "default":
            active_id = None
        return jsonify({"status": "success", "games": games, "active_game_id": active_id})
    except Exception:
        app.logger.exception("Error getting games list")
        return jsonify({"status": "error", "message": "Failed to list games"}), 500


@app.route("/api/games/create", methods=["POST"])
@login_required
@permission_required("game:create")
def create_new_game_session():
    """Create a new game session - requires game:create permission
    ---
    tags:
      - Game
    summary: Create a new game session
    description: Creates a new game session with a unique ID and optionally starts a game
    parameters:
      - in: body
        name: body
        description: Game session configuration
        required: true
        schema:
          type: object
          properties:
            game_id:
              type: string
              description: Unique identifier for the game (optional, will be auto-generated if not
              provided)
              example: game-1
            game_type:
              type: string
              description: Type of game to start
              enum: ['301', '401', '501', 'cricket', 'round_the_clock', 'round_the_clock_double']
              example: '301'
            players:
              type: array
              description: List of player names
              items:
                type: string
              example: ['Alice', 'Bob']
            double_out:
              type: boolean
              description: Whether to require double-out to finish
              default: false
            reset_on_miss:
              type: boolean
              description: Enable hard mode for round_the_clock
              default: false
            set_as_active:
              type: boolean
              description: Whether to set this as the active game
              default: true
    responses:
      200:
        description: Game session created successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: Game session created
            game_id:
              type: string
              description: ID of the created game
      400:
        description: Bad request
    """
    data = request.json or {}
    game_id = data.get("game_id")

    # Auto-generate game ID if not provided
    if not game_id:
        game_id = f"game-{str(uuid.uuid4())[:8]}"

    # Check if game already exists
    if multi_game_manager.has_game(game_id):
        return jsonify({"status": "error", "message": f"Game '{game_id}' already exists"}), 400

    # Create the game session
    try:
        new_game_manager = multi_game_manager.create_game(game_id)

        # Start the game if parameters provided
        game_type = data.get("game_type")
        player_names = data.get("players")
        if game_type and player_names:
            double_out = data.get("double_out", False)
            reset_on_miss = data.get("reset_on_miss", False)

            # Convert player names to player objects with database IDs
            db_session = new_game_manager.db_service.db_manager.get_session()
            try:
                player_ids = []

                for player_name in player_names:
                    # Try to find player by name or username
                    player = (
                        db_session.query(Player)
                        .filter(
                            (Player.name == player_name) | (Player.username == player_name),
                        )
                        .first()
                    )
                    if player:
                        player_ids.append({"db_id": player.id, "name": player.name})
                    else:
                        # If player not found in database, return an error response
                        app.logger.warning(
                            f"Player '{player_name}' not found in database. "
                            "Only registered WSO2 users can play.",
                        )
                        return (
                            jsonify(
                                {
                                    "status": "error",
                                    "message": (
                                        f"Player '{player_name}' not found. "
                                        "Only registered WSO2 users allowed."
                                    ),
                                },
                            ),
                            400,
                        )

                if not player_ids:
                    player_ids = [session.get("player_id")]

                new_game_manager.new_game(
                    game_type,
                    player_ids=player_ids,
                    double_out=double_out,
                    reset_on_miss=reset_on_miss,
                )
            finally:
                db_session.close()

        # Set as active if requested (default: true)
        if data.get("set_as_active", True):
            multi_game_manager.set_active_game(game_id)
            # Update global game_manager reference
            global game_manager
            game_manager = new_game_manager
            app.game_manager = game_manager

        return jsonify(
            {
                "status": "success",
                "message": "Game session created",
                "game_id": game_id,
            },
        )
    except ValueError as e:
        # ValueError is raised with a user-friendly message about duplicate game ID
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception:
        app.logger.exception("Error creating game session")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "An error occurred while creating the game. Please try again.",
                },
            ),
            500,
        )


@app.route("/api/games/<game_id>/activate", methods=["POST"])
@login_required
@permission_required("game:create")
def activate_game_session(game_id):
    """Set a game as the active game session - requires game:create permission
    ---
    tags:
      - Game
    summary: Activate a game session
    description: Sets the specified game as the currently active game
    parameters:
      - in: path
        name: game_id
        type: string
        required: true
        description: ID of the game to activate
    responses:
      200:
        description: Game activated successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: Game activated
            game_id:
              type: string
              description: ID of the activated game
      404:
        description: Game not found
    """
    if not multi_game_manager.has_game(game_id):
        return jsonify({"status": "error", "message": f"Game '{game_id}' not found"}), 404

    multi_game_manager.set_active_game(game_id)

    # Update global game_manager reference
    global game_manager
    game_manager = multi_game_manager.get_game(game_id)
    app.game_manager = game_manager

    return jsonify(
        {
            "status": "success",
            "message": "Game activated",
            "game_id": game_id,
        },
    )


@app.route("/api/games/<game_id>", methods=["DELETE"])
@login_required
@permission_required("game:create")
def delete_game_session(game_id):
    """Delete a game session - requires game:create permission
    ---
    tags:
      - Game
    summary: Delete a game session
    description: Deletes a game session by ID
    parameters:
      - in: path
        name: game_id
        type: string
        required: true
        description: ID of the game to delete
    responses:
      200:
        description: Game deleted successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: Game session deleted
      404:
        description: Game not found
      400:
        description: Cannot delete default game
    """
    # Prevent deletion of default game
    if game_id == "default":
        return jsonify({"status": "error", "message": "Cannot delete default game"}), 400

    if not multi_game_manager.has_game(game_id):
        return jsonify({"status": "error", "message": f"Game '{game_id}' not found"}), 404

    multi_game_manager.delete_game(game_id)

    # Update global game_manager reference if we deleted the active game
    global game_manager
    active_game = multi_game_manager.get_game()
    if active_game:
        game_manager = active_game
        app.game_manager = game_manager

    return jsonify(
        {
            "status": "success",
            "message": "Game session deleted",
        },
    )


@app.route("/api/games/<game_id>/state", methods=["GET"])
@login_required
def get_specific_game_state(game_id):
    """Get state of a specific game - all authenticated users
    ---
    tags:
      - Game
    summary: Get specific game state
    description: Returns the state of a specific game by ID
    parameters:
      - in: path
        name: game_id
        type: string
        required: true
        description: ID of the game
    responses:
      200:
        description: Game state
        schema:
          type: object
      404:
        description: Game not found
    """
    game = multi_game_manager.get_game(game_id)
    if not game:
        return jsonify({"status": "error", "message": f"Game '{game_id}' not found"}), 404

    return jsonify(game.get_game_state())


@app.route("/api/players", methods=["GET"])
@login_required
def get_players():
    """Get all players - all authenticated users
    ---
    tags:
      - Players
    summary: Get all players
    description: Returns a list of all players in the current game or all database players
    parameters:
      - in: query
        name: source
        type: string
        description: Source of players ('game' for current game, 'database' for all users)
        default: game
        enum: [game, database]
    responses:
      200:
        description: List of players or status with players
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            players:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    description: Player ID
                  name:
                    type: string
                    description: Player name
                  username:
                    type: string
                    description: Player username (for database source)
                  email:
                    type: string
                    description: Player email (for database source)
    """
    source = request.args.get("source", "game")

    if source == "database":
        # Return all players from database with usernames
        try:
            players = game_manager.db_service.get_all_players_with_usernames()
            return jsonify({"status": "success", "players": players})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    else:
        # Return current game players
        return jsonify(game_manager.get_players())


@app.route("/api/wso2/users/search", methods=["GET"])
@login_required
def search_wso2_users_endpoint():
    """Search for WSO2 users (autocomplete)
    ---
    tags:
      - WSO2
    summary: Search WSO2 users
    description: Search for users in WSO2 by username, email, or name
    parameters:
      - in: query
        name: q
        type: string
        required: true
        description: Search query (username, email, or name)
    responses:
      200:
        description: List of matching users
        schema:
          type: object
          properties:
            success:
              type: boolean
            users:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: string
                  username:
                    type: string
                  email:
                    type: string
                  name:
                    type: string
    """
    try:
        query = request.args.get("q", "").strip()
        if not query or len(query) < 1:
            return jsonify({"success": False, "error": "Search query too short"}), 400

        users = search_wso2_users(query)
        return jsonify({"success": True, "users": users})
    except Exception as e:
        logger.exception("Error searching WSO2 users")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/players", methods=["POST"])
@login_required
@permission_required("player:add")
def add_player():
    """Add a new player - requires player:add permission
    ---
    tags:
      - Players
    summary: Add a new player
    description: |
      Adds a new WSO2-authenticated player to the current game.
      IMPORTANT: Only players registered in WSO2 can be added.
      Exception: bypass_user for local development/testing.
    parameters:
      - in: body
        name: body
        description: Player information
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              description: WSO2 username (REQUIRED)
              example: charlie
    responses:
      200:
        description: Player added successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: Player added
            player:
              type: object
              properties:
                name:
                  type: string
                email:
                  type: string
                player_id:
                  type: integer
      400:
        description: Invalid input - username required or WSO2 user not found
      500:
        description: Server error
    """
    try:
        data = request.json or {}
        username = data.get("username", "").strip()

        # Username is REQUIRED (WSO2 user lookup)
        if not username:
            return (
                jsonify(
                    {
                        "success": False,
                        "error": (
                            "Username is required. "
                            "Only WSO2-authenticated users can be added to games."
                        ),
                    },
                ),
                400,
            )

        # Lookup WSO2 user
        wso2_user = get_wso2_user_info(username)
        if not wso2_user:
            return (
                jsonify({"success": False, "error": f"User '{username}' not found in WSO2"}),
                404,
            )

        # Use WSO2 user info
        player_name = wso2_user.get("name") or wso2_user.get("username")
        email = wso2_user.get("email")

        # Add to database with email and username (enforces WSO2 users only)
        player = game_manager.db_service.get_or_create_player(
            name=player_name,
            username=username,
            email=email,
        )

        if not player:
            return (
                jsonify({"success": False, "error": "Failed to create/retrieve player"}),
                500,
            )

        # Add to game with player database ID
        game_manager.add_player_with_id(player_name, player.id)

        return jsonify(
            {
                "status": "success",
                "message": f"Player {player_name} added to game",
                "player": {
                    "name": player_name,
                    "email": email,
                    "player_id": player.id,
                },
            },
        )
    except Exception as e:
        logger.exception("Error adding player")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/players/<int:player_id>", methods=["DELETE"])
@login_required
@permission_required("player:remove")
def remove_player(player_id):
    """Remove a player - requires player:remove permission
    ---
    tags:
      - Players
    summary: Remove a player
    description: Removes a player from the current game by player ID
    parameters:
      - in: path
        name: player_id
        type: integer
        required: true
        description: ID of the player to remove
        example: 1
    responses:
      200:
        description: Player removed successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: Player removed
    """
    game_manager.remove_player(player_id)
    # Game state is automatically emitted by game_manager.remove_player()
    return jsonify({"status": "success", "message": "Player removed"})


@app.route("/api/Throw/zone", methods=["POST"])
# @login_required
# @permission_required("score:submit")
def submit_score_zone():
    """Submit a score via dartboard zone mapping (New generic format)
    ---
    tags:
      - Score
    summary: Submit a dart score using zone mapping
    description: |
        Submits a dart throw using GPIO pin combination and dartboard type.
        The server looks up the zone information based on the dartboard type and pin combination.
        This is the preferred format for new dartboards.
    parameters:
      - in: body
        name: body
        description: Pin-based score information
        required: true
        schema:
          type: object
          required:
            - masterPin
            - slavePin
            - boardType
          properties:
            masterPin:
              type: integer
              description: Master (row) GPIO pin number
              example: 4
            slavePin:
              type: integer
              description: Slave (column) GPIO pin number
              example: 13
            boardType:
              type: string
              description: Dartboard type identifier (e.g., 'carromco', 'winmau')
              example: carromco
            user:
              type: string
              description: Optional player identifier
              example: dgroen
    responses:
      200:
        description: Score submitted successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: Score submitted
            zone_info:
              type: object
              properties:
                zone_number:
                  type: integer
                  example: 20
                multiplier_type:
                  type: string
                  example: TRIPLE
                base_value:
                  type: integer
                  example: 20
                score:
                  type: integer
                  example: 60
      400:
        description: Invalid request or zone not found
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
    """
    try:
        data = request.json
        master_pin = data.get("masterPin")
        slave_pin = data.get("slavePin")
        board_type = data.get("boardType", "").lower()

        # Validate input
        if not isinstance(master_pin, int) or not isinstance(slave_pin, int):
            return (
                jsonify({"status": "error", "message": "masterPin and slavePin must be integers"}),
                400,
            )

        if not board_type:
            return jsonify({"status": "error", "message": "boardType is required"}), 400

        # Get database session
        session = get_session()

        try:
            # Look up zone information
            zone_info = DartboardService.get_zone_from_pins(
                session,
                board_type,
                master_pin,
                slave_pin,
            )

            # Emit WebSocket event for admin dartboard testing page (even if zone not found)
            socketio.emit(
                "dartboard_test_received",
                {
                    "masterPin": master_pin,
                    "slavePin": slave_pin,
                    "boardType": board_type,
                    "zoneInfo": zone_info,
                },
                namespace="/",
            )

            if not zone_info:
                logger.warning(
                    f"Zone mapping not found - Received pinout: masterPin={master_pin}, "
                    f"slavePin={slave_pin}, boardType={board_type}",
                )
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": (
                                f"Zone mapping not found for pins ({master_pin}, {slave_pin}) "
                                f"on board type '{board_type}'"
                            ),
                        },
                    ),
                    400,
                )

            # Process the score using the zone information
            # Pass the base_value and multiplier_type - game logic handles the calculation
            game_manager.process_score(
                {
                    "score": zone_info["base_value"],
                    "multiplier": zone_info["multiplier_type"],
                },
            )

            return jsonify(
                {
                    "status": "success",
                    "message": "Score submitted",
                    "zone_info": zone_info,
                },
            )
        finally:
            session.close()

    except Exception as e:
        logger.exception("Error submitting zone-based score")
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/dartboard/types", methods=["GET"])
def get_dartboard_types():
    """Get all registered dartboard types
    ---
    tags:
      - Dartboard
    summary: Get dartboard types
    description: Returns all registered and active dartboard types
    responses:
      200:
        description: List of dartboard types
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            types:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                  name:
                    type: string
                  brand:
                    type: string
                  model:
                    type: string
                  description:
                    type: string
    """
    try:
        session = get_session()
        try:
            types = DartboardService.list_dartboard_types(session)
            return jsonify(
                {
                    "status": "success",
                    "types": [
                        {
                            "id": t.id,
                            "name": t.name,
                            "brand": t.brand,
                            "model": t.model,
                            "description": t.description,
                        }
                        for t in types
                    ],
                },
            )
        finally:
            session.close()
    except Exception as e:
        logger.exception("Error getting dartboard types")
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/dartboard/types/<board_type>/mappings", methods=["GET"])
def get_dartboard_mappings(board_type):
    """Get zone mappings for a dartboard type
    ---
    tags:
      - Dartboard
    summary: Get dartboard zone mappings
    description: Returns all zone mappings for a specific dartboard type
    parameters:
      - in: path
        name: board_type
        type: string
        required: true
        description: Dartboard type name (e.g., 'carromco')
    responses:
      200:
        description: List of zone mappings
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            board_type:
              type: string
            mappings:
              type: array
              items:
                type: object
                properties:
                  master_pin:
                    type: integer
                  slave_pin:
                    type: integer
                  zone_number:
                    type: integer
                  multiplier_type:
                    type: string
                  base_value:
                    type: integer
      404:
        description: Dartboard type not found
    """
    try:
        session = get_session()
        try:
            mappings = DartboardService.get_dartboard_type_mappings(session, board_type.lower())
            if mappings is None:
                return (
                    jsonify(
                        {"status": "error", "message": f"Dartboard type '{board_type}' not found"},
                    ),
                    404,
                )

            return jsonify(
                {
                    "status": "success",
                    "board_type": board_type,
                    "mappings": [
                        {
                            "master_pin": m.master_pin,
                            "slave_pin": m.slave_pin,
                            "zone_number": m.zone_number,
                            "multiplier_type": m.multiplier_type,
                            "base_value": m.base_value,
                        }
                        for m in mappings
                    ],
                },
            )
        finally:
            session.close()
    except Exception as e:
        logger.exception("Error getting dartboard mappings")
        return jsonify({"status": "error", "message": str(e)}), 400


# ==================== ADMIN DARTBOARD TESTING ENDPOINTS ====================


@app.route("/admin/dartboard-testing")
@login_required
@role_required("admin")
def admin_dartboard_testing():
    """Admin page for dartboard testing and calibration"""
    return render_template("admin_dartboard_testing.html")


@app.route("/api/admin/dartboard/matrix/<board_type>", methods=["GET"])
@login_required
@role_required("admin")
def get_dartboard_matrix(board_type):
    """Get matrix visualization for a dartboard type
    ---
    tags:
      - Admin/Dartboard
    summary: Get dartboard matrix visualization
    description: Returns the GPIO pin matrix for a dartboard type with current mappings
    parameters:
      - in: path
        name: board_type
        type: string
        description: Dartboard type name (e.g., 'carromco')
    responses:
      200:
        description: Matrix visualization data
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            dartboard_type:
              type: object
            master_pins:
              type: array
              items:
                type: integer
            slave_pins:
              type: array
              items:
                type: integer
            matrix:
              type: array
      404:
        description: Dartboard type not found
    """
    try:
        session = get_session()
        try:
            result = DartboardService.get_matrix_visualization(session, board_type.lower())
            if not result or result[0] is None:
                return (
                    jsonify(
                        {"status": "error", "message": f"Dartboard type '{board_type}' not found"},
                    ),
                    404,
                )

            dartboard_type_dict, master_pins, slave_pins, matrix = result

            return jsonify(
                {
                    "status": "success",
                    "dartboard_type": dartboard_type_dict,
                    "master_pins": master_pins,
                    "slave_pins": slave_pins,
                    "matrix": matrix,
                },
            )
        finally:
            session.close()
    except Exception as e:
        logger.exception("Error getting dartboard matrix")
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/admin/dartboard/mapping", methods=["POST"])
@login_required
@role_required("admin")
def update_dartboard_mapping():
    """Update or create a dartboard zone mapping
    ---
    tags:
      - Admin/Dartboard
    summary: Update dartboard mapping
    description: Update an existing zone mapping or create a new one
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - boardType
            - masterPin
            - slavePin
            - zoneNumber
            - multiplierType
            - baseValue
          properties:
            boardType:
              type: string
              example: carromco
            masterPin:
              type: integer
              example: 4
            slavePin:
              type: integer
              example: 13
            zoneNumber:
              type: integer
              example: 20
            multiplierType:
              type: string
              enum: ['SINGLE', 'DOUBLE', 'TRIPLE', 'BULL', 'DBLBULL']
              example: TRIPLE
            baseValue:
              type: integer
              example: 20
    responses:
      200:
        description: Mapping updated successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
      400:
        description: Invalid request or validation error
    """
    try:
        data = request.json
        board_type = data.get("boardType", "").lower()
        master_pin = data.get("masterPin")
        slave_pin = data.get("slavePin")
        zone_number = data.get("zoneNumber")
        multiplier_type = data.get("multiplierType", "").upper()
        base_value = data.get("baseValue")

        # Validate input
        if not all(
            [
                board_type,
                master_pin is not None,
                slave_pin is not None,
                zone_number is not None,
                multiplier_type,
                base_value is not None,
            ],
        ):
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        session = get_session()
        try:
            DartboardService.update_zone_mapping(
                session,
                board_type,
                int(master_pin),
                int(slave_pin),
                int(zone_number),
                multiplier_type,
                int(base_value),
            )
            return jsonify(
                {
                    "status": "success",
                    "message": f"Mapping for pins ({master_pin}, {slave_pin}) updated successfully",
                },
            )
        finally:
            session.close()
    except DartboardMappingError as e:
        logger.exception("Dartboard mapping error")
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        logger.exception("Error updating dartboard mapping")
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/admin/dartboard/import", methods=["POST"])
@login_required
@role_required("admin")
def import_dartboard_mappings():
    """Bulk import dartboard mappings from CSV
    ---
    tags:
      - Admin/Dartboard
    summary: Bulk import mappings
    description: Import multiple zone mappings at once
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - boardType
            - mappings
          properties:
            boardType:
              type: string
              example: carromco
            mappings:
              type: array
              items:
                type: object
                required:
                  - masterPin
                  - slavePin
                  - zoneNumber
                  - multiplierType
                  - baseValue
                properties:
                  masterPin:
                    type: integer
                  slavePin:
                    type: integer
                  zoneNumber:
                    type: integer
                  multiplierType:
                    type: string
                  baseValue:
                    type: integer
    responses:
      200:
        description: Mappings imported successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            created:
              type: integer
            updated:
              type: integer
      400:
        description: Invalid request or import error
    """
    try:
        data = request.json
        board_type = data.get("boardType", "").lower()
        mappings = data.get("mappings", [])

        if not board_type or not mappings:
            return (
                jsonify({"status": "error", "message": "boardType and mappings are required"}),
                400,
            )

        session = get_session()
        try:
            # Convert CSV-like format to mapping data format
            mapping_data = []
            for mapping in mappings:
                mapping_data.append(
                    {
                        "master_pin": mapping.get("masterPin"),
                        "slave_pin": mapping.get("slavePin"),
                        "zone_number": mapping.get("zoneNumber"),
                        "multiplier_type": mapping.get("multiplierType"),
                        "base_value": mapping.get("baseValue"),
                    },
                )

            created, updated = DartboardService.bulk_import_mappings(
                session,
                board_type,
                mapping_data,
            )

            return jsonify(
                {
                    "status": "success",
                    "message": (
                        f"Imported {created} new mappings and updated {updated} existing mappings"
                    ),
                    "created": created,
                    "updated": updated,
                },
            )
        finally:
            session.close()
    except DartboardMappingError as e:
        logger.exception("Dartboard import error")
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        logger.exception("Error importing dartboard mappings")
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/admin/dartboard/type", methods=["POST"])
@login_required
@role_required("admin")
def create_dartboard_type():
    """Create a new dartboard type
    ---
    tags:
      - Admin/Dartboard
    summary: Create new dartboard type
    description: Register a new dartboard type that can then be configured with zone mappings
    parameters:
      - in: body
        name: body
        schema:
          type: object
          required:
            - name
            - brand
          properties:
            name:
              type: string
              description: Unique identifier for the dartboard type (lowercase, no spaces)
              example: granboard
            brand:
              type: string
              description: Brand name of the dartboard
              example: Gran Board
            model:
              type: string
              description: Model name or number (optional)
              example: Gran Board 3
            description:
              type: string
              description: Description of the dartboard (optional)
              example: Electronic dartboard with Bluetooth connectivity
            masterPins:
              type: array
              items:
                type: integer
              description: List of GPIO pins for master (row) lines
              example: [2, 4, 5, 16, 17, 18, 19]
            slavePins:
              type: array
              items:
                type: integer
              description: List of GPIO pins for slave (column) lines
              example: [12, 13, 14, 25, 26, 27, 32, 33]
    responses:
      201:
        description: Dartboard type created successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
            dartboard_type:
              type: object
              properties:
                id:
                  type: integer
                name:
                  type: string
                brand:
                  type: string
                model:
                  type: string
                description:
                  type: string
                master_pins:
                  type: array
                  items:
                    type: integer
                slave_pins:
                  type: array
                  items:
                    type: integer
      400:
        description: Invalid request or dartboard type already exists
    """
    try:
        data = request.json or {}
        name = data.get("name", "").lower().strip()
        brand = data.get("brand", "").strip()
        model = data.get("model", "").strip() if data.get("model") else None
        description = data.get("description", "").strip() if data.get("description") else None
        master_pins = data.get("masterPins")
        slave_pins = data.get("slavePins")

        # Validate required fields
        error_msg = None
        status_code = 400

        if not name:
            error_msg = "Name is required"
        elif not brand:
            error_msg = "Brand is required"
        elif not name.replace("_", "").replace("-", "").isalnum():
            error_msg = "Name must contain only letters, numbers, hyphens and underscores"
        elif master_pins is not None and (
            not isinstance(master_pins, list) or not all(isinstance(p, int) for p in master_pins)
        ):
            error_msg = "masterPins must be an array of integers"
        elif slave_pins is not None and (
            not isinstance(slave_pins, list) or not all(isinstance(p, int) for p in slave_pins)
        ):
            error_msg = "slavePins must be an array of integers"

        if error_msg:
            return jsonify({"status": "error", "message": error_msg}), status_code

        session = get_session()
        try:
            dartboard_type = DartboardService.register_dartboard_type(
                session,
                name=name,
                brand=brand,
                model=model,
                description=description,
                master_pins=master_pins,
                slave_pins=slave_pins,
            )
            return (
                jsonify(
                    {
                        "status": "success",
                        "message": f"Dartboard type '{name}' created successfully",
                        "dartboard_type": {
                            "id": dartboard_type.id,
                            "name": dartboard_type.name,
                            "brand": dartboard_type.brand,
                            "model": dartboard_type.model,
                            "description": dartboard_type.description,
                            "master_pins": master_pins,
                            "slave_pins": slave_pins,
                        },
                    },
                ),
                201,
            )
        finally:
            session.close()
    except DartboardMappingError as e:
        logger.warning("Dartboard type creation failed: %s", str(e))
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        logger.exception("Error creating dartboard type")
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/admin/dartboard/type/<board_type>/pins", methods=["PUT"])
@login_required
@role_required("admin")
def update_dartboard_pins(board_type):
    """Update GPIO pin configuration for a dartboard type
    ---
    tags:
      - Admin/Dartboard
    summary: Update dartboard GPIO pins
    description: Update the master and slave GPIO pin configuration for an existing dartboard type
    parameters:
      - in: path
        name: board_type
        type: string
        required: true
        description: Dartboard type name
      - in: body
        name: body
        schema:
          type: object
          properties:
            masterPins:
              type: array
              items:
                type: integer
              description: List of GPIO pins for master (row) lines
              example: [2, 4, 5, 16, 17, 18, 19]
            slavePins:
              type: array
              items:
                type: integer
              description: List of GPIO pins for slave (column) lines
              example: [12, 13, 14, 25, 26, 27, 32, 33]
    responses:
      200:
        description: Pins updated successfully
      400:
        description: Invalid request
      404:
        description: Dartboard type not found
    """
    try:
        data = request.json
        master_pins = data.get("masterPins")
        slave_pins = data.get("slavePins")

        # Validate pin arrays if provided
        if master_pins is not None and (
            not isinstance(master_pins, list) or not all(isinstance(p, int) for p in master_pins)
        ):
            return (
                jsonify({"status": "error", "message": "masterPins must be an array of integers"}),
                400,
            )
        if slave_pins is not None and (
            not isinstance(slave_pins, list) or not all(isinstance(p, int) for p in slave_pins)
        ):
            return (
                jsonify({"status": "error", "message": "slavePins must be an array of integers"}),
                400,
            )

        session = get_session()
        try:
            dartboard_type = DartboardService.update_dartboard_pins(
                session,
                board_type.lower(),
                master_pins=master_pins,
                slave_pins=slave_pins,
            )
            return jsonify(
                {
                    "status": "success",
                    "message": f"Pins updated for '{board_type}'",
                    "dartboard_type": {
                        "id": dartboard_type.id,
                        "name": dartboard_type.name,
                        "master_pins": master_pins,
                        "slave_pins": slave_pins,
                    },
                },
            )
        finally:
            session.close()
    except DartboardMappingError as e:
        logger.warning("Dartboard pin update failed: %s", str(e))
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        logger.exception("Error updating dartboard pins")
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/admin/dartboard/available-pins", methods=["GET"])
@login_required
@role_required("admin")
def get_available_pins():
    """Get list of available GPIO pins for dartboard configuration
    ---
    tags:
      - Admin/Dartboard
    summary: Get available GPIO pins
    description: Returns a list of common ESP32 GPIO pins that can be used for dartboard matrices
    responses:
      200:
        description: List of available pins
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            pins:
              type: array
              items:
                type: integer
              example: [2, 4, 5, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23, 25, 26, 27, 32, 33]
    """
    return jsonify(
        {
            "status": "success",
            "pins": DartboardService.AVAILABLE_GPIO_PINS,
        },
    )


@app.route("/api/tts/config", methods=["GET"])
def get_tts_config():
    """Get TTS configuration
    ---
    tags:
      - TTS
    summary: Get TTS configuration
    description: Returns the current TTS configuration including speed, voice, and enabled status
    responses:
      200:
        description: TTS configuration
        schema:
          type: object
          properties:
            enabled:
              type: boolean
              description: Whether TTS is enabled
            engine:
              type: string
              description: TTS engine name
            speed:
              type: integer
              description: Speech speed (words per minute)
            volume:
              type: number
              description: Volume level (0.0 to 1.0)
            voice:
              type: string
              description: Current voice type
    """
    return jsonify(
        {
            "enabled": game_manager.tts.is_enabled(),
            "engine": game_manager.tts.engine_name,
            "speed": game_manager.tts.speed,
            "volume": game_manager.tts.volume,
            "voice": game_manager.tts.voice_type,
            "language": game_manager.tts.language,
        },
    )


@app.route("/api/tts/config", methods=["POST"])
def update_tts_config():
    """Update TTS configuration
    ---
    tags:
      - TTS
    summary: Update TTS configuration
    description: Updates TTS settings such as speed, voice, and enabled status
    parameters:
      - in: body
        name: body
        description: TTS configuration
        required: true
        schema:
          type: object
          properties:
            enabled:
              type: boolean
              description: Enable or disable TTS
              example: true
            speed:
              type: integer
              description: Speech speed (words per minute, typically 100-200)
              example: 150
            volume:
              type: number
              description: Volume level (0.0 to 1.0)
              example: 1.0
            voice:
              type: string
              description: Voice type identifier
              example: default
    responses:
      200:
        description: Configuration updated successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: TTS configuration updated
    """
    data = request.json

    if "enabled" in data:
        if data["enabled"]:
            game_manager.tts.enable()
        else:
            game_manager.tts.disable()

    if "speed" in data:
        game_manager.tts.set_speed(int(data["speed"]))

    if "volume" in data:
        game_manager.tts.set_volume(float(data["volume"]))

    if "voice" in data:
        game_manager.tts.set_voice(data["voice"])

    if "language" in data:
        game_manager.tts.set_language(data["language"])

    return jsonify({"status": "success", "message": "TTS configuration updated"})


@app.route("/api/tts/voices", methods=["GET"])
def get_tts_voices():
    """Get available TTS voices
    ---
    tags:
      - TTS
    summary: Get available TTS voices
    description: Returns a list of available voices for the current TTS engine
    responses:
      200:
        description: List of available voices
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: string
                description: Voice ID
              name:
                type: string
                description: Voice name
              languages:
                type: array
                items:
                  type: string
                description: Supported languages
              gender:
                type: string
                description: Voice gender
    """
    voices = game_manager.tts.get_available_voices()
    return jsonify(voices)


@app.route("/api/tts/languages", methods=["GET"])
def get_tts_languages():
    """Get supported TTS languages
    ---
    tags:
      - TTS
    summary: Get supported TTS languages
    description: Returns a list of all supported languages for TTS
    responses:
      200:
        description: Dictionary of supported languages
        schema:
          type: object
          additionalProperties:
            type: string
          example:
            en: English
            nl: Dutch
            de: German
            fr: French
            es: Spanish
    """
    from dartserver_services.tts_service import TTSService  # noqa: PLC0415

    languages = TTSService.get_supported_languages()
    return jsonify(languages)


@app.route("/api/tts/test", methods=["POST"])
def test_tts():
    """Test TTS with custom text
    ---
    tags:
      - TTS
    summary: Test TTS
    description: Speaks the provided text using the current TTS configuration
    parameters:
      - in: body
        name: body
        description: Text to speak
        required: true
        schema:
          type: object
          required:
            - text
          properties:
            text:
              type: string
              description: Text to speak
              example: Hello, this is a test
    responses:
      200:
        description: TTS test completed
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: TTS test completed
    """
    data = request.json
    text = data.get("text", "This is a test")

    success = game_manager.tts.speak(text)

    if success:
        return jsonify({"status": "success", "message": "TTS test completed"})
    return jsonify({"status": "error", "message": "TTS test failed"}), 500


@app.route("/api/tts/generate", methods=["POST"])
def generate_tts_audio():
    """Generate TTS audio data
    ---
    tags:
      - TTS
    summary: Generate TTS audio
    description: Generates audio data for the provided text using the current TTS configuration
    parameters:
      - in: body
        name: body
        description: Text to convert to speech
        required: true
        schema:
          type: object
          required:
            - text
          properties:
            text:
              type: string
              description: Text to convert to speech
              example: Hello, this is a test
            lang:
              type: string
              description: Language code (for gTTS)
              example: en
              default: en
    responses:
      200:
        description: Audio data generated successfully
        content:
          audio/mpeg:
            schema:
              type: string
              format: binary
      400:
        description: Bad request
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
              example: Text is required
      500:
        description: TTS generation failed
        schema:
          type: object
          properties:
            status:
              type: string
              example: error
            message:
              type: string
              example: Failed to generate audio
    """
    data = request.json
    text = data.get("text")
    lang = data.get("lang", "en")

    if not text:
        return jsonify({"status": "error", "message": "Text is required"}), 400

    audio_data = game_manager.tts.generate_audio_data(text, lang)

    if audio_data:
        return Response(audio_data, mimetype="audio/mpeg")
    return jsonify({"status": "error", "message": "Failed to generate audio"}), 500


@app.route("/api/admin/tts/player", methods=["GET"])
@role_required("admin")
def tts_player():
    """TTS player UI for testing
    ---
    tags:
      - TTS
    summary: TTS Audio Player
    description: Interactive HTML page for testing TTS with built-in audio player (admin only)
    parameters:
      - in: query
        name: text
        type: string
        description: Text to generate audio for
        example: "Hello, this is a test"
        required: false
    responses:
      200:
        description: HTML page with audio player
        content:
          text/html:
            schema:
              type: string
      403:
        description: Forbidden - admin role required
    """
    text = request.args.get("text", "Hello, this is a test message")
    return render_template(
        "tts_player.html",
        initial_text=text,
    )


# SocketIO Events
@app.route("/api/game/history", methods=["GET"])
@login_required
def get_game_history():
    """Get recent game history
    ---
    tags:
      - Game
    summary: Get recent game history
    description: >
      Returns a list of recent games. Regular users see only their games,
      admins can filter by user.
    parameters:
      - in: query
        name: limit
        type: integer
        description: Maximum number of games to return
        default: 10
        example: 10
      - in: query
        name: user
        type: string
        description: Filter by username (admin only)
        example: john_doe
    responses:
      200:
        description: List of recent games
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            games:
              type: array
              items:
                type: object
                properties:
                  game_session_id:
                    type: string
                    description: Unique game session ID
                  game_type:
                    type: string
                    description: Type of game
                  player_count:
                    type: integer
                    description: Number of players
                  winner:
                    type: string
                    description: Winner name
                  started_at:
                    type: string
                    description: Game start timestamp
                  finished_at:
                    type: string
                    description: Game finish timestamp
    """
    limit = request.args.get("limit", 10, type=int)
    filter_user = request.args.get("user")

    # Get current user info
    user_roles = getattr(request, "user_roles", [])
    user_claims = getattr(request, "user_claims", {})

    # Log all available claims for debugging
    logger.info(f"get_game_history: Available claims: {list(user_claims.keys())}")
    logger.info(
        f"get_game_history: username={user_claims.get('username')}, \
        preferred_username={user_claims.get('preferred_username')}, sub={user_claims.get('sub')}",
    )

    current_username = (
        user_claims.get("username")
        or user_claims.get("preferred_username")
        or user_claims.get("sub")
    )

    # Strip WSO2 tenant suffix (e.g., @carbon.super) from username if present
    if current_username and "@" in current_username:
        current_username = current_username.split("@")[0]

    logger.info(f"get_game_history: current_username={current_username}, user_roles={user_roles}")

    # Determine which username to filter by
    # Admins can filter by specific user or see all games; regular users only see their own
    username_filter = filter_user if "admin" in user_roles else current_username

    logger.info(f"get_game_history: username_filter={username_filter}, limit={limit}")

    try:
        games = game_manager.db_service.get_recent_games(limit=limit, username=username_filter)
        logger.info(f"get_game_history: Found {len(games)} games")
        return jsonify({"status": "success", "games": games})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/game/replay/<game_session_id>", methods=["GET"])
def get_game_replay(game_session_id):
    """Get game replay data
    ---
    tags:
      - Game
    summary: Get complete game replay data
    description: Returns all data needed to replay a specific game including all throws in sequence
    parameters:
      - in: path
        name: game_session_id
        type: string
        required: true
        description: Game session ID
    responses:
      200:
        description: Complete game replay data
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            game_data:
              type: object
              properties:
                game_session_id:
                  type: string
                  description: Game session ID
                game_type:
                  type: string
                  description: Type of game
                double_out_enabled:
                  type: boolean
                  description: Whether double-out was enabled
                started_at:
                  type: string
                  description: Game start timestamp
                finished_at:
                  type: string
                  description: Game finish timestamp
                players:
                  type: array
                  description: Player information
                throws:
                  type: array
                  description: All throws in chronological order
      404:
        description: Game not found
    """
    try:
        game_data = game_manager.db_service.get_game_replay_data(game_session_id)
        if game_data:
            return jsonify({"status": "success", "game_data": game_data})
        return jsonify({"status": "error", "message": "Game not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/game/current/session_id", methods=["GET"])
def get_current_game_session_id():
    """Get current game session ID
    ---
    tags:
      - Game
    summary: Get current game session ID
    description: Returns the session ID of the currently active game
    responses:
      200:
        description: Current game session ID
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            game_session_id:
              type: string
              description: Current game session ID (null if no active game)
    """
    return jsonify(
        {
            "status": "success",
            "game_session_id": game_manager.db_service.current_game_session_id,
        },
    )


# ============================================================================
# Mobile App API Endpoints
# ============================================================================


def get_mobile_service():
    """Helper function to get MobileService instance with database session"""
    db_session = game_manager.db_service.db_manager.get_session()
    return MobileService(db_session)


def api_key_required(f):
    """Decorator to require API key authentication"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return jsonify({"success": False, "error": "API key required"}), 401

        mobile_service = get_mobile_service()
        player_info = mobile_service.validate_api_key(api_key)

        if not player_info:
            return jsonify({"success": False, "error": "Invalid API key"}), 401

        # Add player info to request context
        request.player_info = player_info  # type: ignore
        return f(*args, **kwargs)

    return decorated_function


@app.route("/mobile")
@login_required
def mobile_app():
    """Mobile app main page
    ---
    tags:
      - UI
    summary: Mobile app interface
    description: Mobile-optimized PWA interface for dartboard management
    responses:
      200:
        description: Mobile app HTML page
    """
    return render_template("mobile.html")


@app.route("/mobile/gameplay")
@login_required
def mobile_gameplay():
    """Mobile gameplay page
    ---
    tags:
      - UI
    summary: Mobile gameplay interface
    description: Mobile interface for active gameplay
    responses:
      200:
        description: Mobile gameplay HTML page
    """
    return render_template("mobile_gameplay.html")


@app.route("/mobile/gamemaster")
@login_required
@role_required("gamemaster")
def mobile_gamemaster():
    """Mobile game master control page
    ---
    tags:
      - UI
    summary: Mobile game master interface
    description: Mobile interface for game master controls
    responses:
      200:
        description: Mobile game master HTML page
    """
    return render_template("mobile_gamemaster.html")


@app.route("/mobile/dartboard-setup")
@login_required
def mobile_dartboard_setup():
    """Mobile dartboard setup page
    ---
    tags:
      - UI
    summary: Mobile dartboard setup interface
    description: Mobile interface for dartboard configuration
    responses:
      200:
        description: Mobile dartboard setup HTML page
    """
    return render_template("mobile_dartboard_setup.html")


@app.route("/mobile/results")
@login_required
def mobile_results():
    """Mobile game results page
    ---
    tags:
      - UI
    summary: Mobile game results interface
    description: Mobile interface for viewing game history
    responses:
      200:
        description: Mobile game results HTML page
    """
    return render_template("mobile_results.html")


@app.route("/mobile/account")
@login_required
def mobile_account():
    """Mobile account management page
    ---
    tags:
      - UI
    summary: Mobile account management interface
    description: Mobile interface for account settings, API keys, and dartboards
    responses:
      200:
        description: Mobile account management HTML page
    """
    return render_template("mobile_account.html")


@app.route("/mobile/hotspot")
@login_required
def mobile_hotspot():
    """Mobile hotspot control page
    ---
    tags:
      - UI
    summary: Mobile hotspot control interface
    description: Mobile interface for managing dartboard hotspot connections
    responses:
      200:
        description: Mobile hotspot control HTML page
    """
    return render_template("mobile_hotspot.html")


# API Key Management Endpoints


@app.route("/api/mobile/apikeys", methods=["GET"])
@login_required
def get_api_keys():
    """Get user's API keys
    ---
    tags:
      - Mobile
    summary: Get API keys
    description: Returns all API keys for the authenticated user
    responses:
      200:
        description: List of API keys
        schema:
          type: object
          properties:
            success:
              type: boolean
            api_keys:
              type: array
              items:
                type: object
    """
    mobile_service = get_mobile_service()
    player_id = session.get("player_id")
    if not player_id:
        return jsonify({"success": False, "error": "Player ID not available"}), 401
    api_keys = mobile_service.get_user_api_keys(player_id)
    return jsonify({"success": True, "api_keys": api_keys})


@app.route("/api/mobile/apikeys", methods=["POST"])
@login_required
def create_api_key():
    """Create new API key
    ---
    tags:
      - Mobile
    summary: Create API key
    description: Creates a new API key for the authenticated user
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            key_name:
              type: string
              description: Friendly name for the API key
    responses:
      200:
        description: API key created
        schema:
          type: object
          properties:
            success:
              type: boolean
            api_key:
              type: object
    """
    data = request.json
    key_name = data.get("key_name", "Default Key")
    player_id = session.get("player_id")
    if not player_id:
        return jsonify({"success": False, "error": "Player ID not available"}), 401

    mobile_service = get_mobile_service()
    result = mobile_service.create_api_key(player_id, key_name)
    return jsonify(result)


@app.route("/api/mobile/apikeys/<int:key_id>", methods=["DELETE"])
@login_required
def revoke_api_key(key_id):
    """Revoke API key
    ---
    tags:
      - Mobile
    summary: Revoke API key
    description: Revokes (deactivates) an API key
    parameters:
      - in: path
        name: key_id
        type: integer
        required: true
    responses:
      200:
        description: API key revoked
        schema:
          type: object
          properties:
            success:
              type: boolean
    """
    player_id = session.get("player_id")
    if not player_id:
        return jsonify({"success": False, "error": "Player ID not available"}), 401
    mobile_service = get_mobile_service()
    result = mobile_service.revoke_api_key(key_id, player_id)
    return jsonify(result)


# Dartboard Management Endpoints


@app.route("/api/mobile/dartboards", methods=["GET"])
@login_required
def get_dartboards():
    """Get user's dartboards
    ---
    tags:
      - Mobile
    summary: Get dartboards
    description: Returns all dartboards for the authenticated user
    responses:
      200:
        description: List of dartboards
        schema:
          type: object
          properties:
            success:
              type: boolean
            dartboards:
              type: array
              items:
                type: object
    """
    mobile_service = get_mobile_service()
    player_id = session.get("player_id")
    if not player_id:
        return jsonify({"success": False, "error": "Player ID not available"}), 401
    dartboards = mobile_service.get_user_dartboards(player_id)
    return jsonify({"success": True, "dartboards": dartboards})


@app.route("/api/mobile/dartboards", methods=["POST"])
@login_required
def register_dartboard():
    """Register new dartboard
    ---
    tags:
      - Mobile
    summary: Register dartboard
    description: Registers a new dartboard for the authenticated user
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            dartboard_id:
              type: string
              description: Unique dartboard identifier
            name:
              type: string
              description: Friendly name for the dartboard
            wpa_key:
              type: string
              description: WPA key for hotspot connection
    responses:
      200:
        description: Dartboard registered
        schema:
          type: object
          properties:
            success:
              type: boolean
            dartboard:
              type: object
    """
    data = request.json
    dartboard_id = data.get("dartboard_id")
    name = data.get("name")
    wpa_key = data.get("wpa_key")
    player_id = session.get("player_id")
    if not player_id:
        return jsonify({"success": False, "error": "Player ID not available"}), 401

    if not all([dartboard_id, name, wpa_key]):
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    mobile_service = get_mobile_service()
    result = mobile_service.register_dartboard(player_id, dartboard_id, name, wpa_key)
    return jsonify(result)


@app.route("/api/mobile/dartboards/<int:dartboard_id>", methods=["DELETE"])
@login_required
def delete_dartboard(dartboard_id):
    """Delete dartboard
    ---
    tags:
      - Mobile
    summary: Delete dartboard
    description: Deletes a dartboard
    parameters:
      - in: path
        name: dartboard_id
        type: integer
        required: true
    responses:
      200:
        description: Dartboard deleted
        schema:
          type: object
          properties:
            success:
              type: boolean
    """
    player_id = session.get("player_id")
    if not player_id:
        return jsonify({"success": False, "error": "Player ID not available"}), 401
    mobile_service = get_mobile_service()
    result = mobile_service.delete_dartboard(dartboard_id, player_id)
    return jsonify(result)


# Hotspot Configuration Endpoints


@app.route("/api/mobile/hotspot", methods=["GET"])
@login_required
def get_hotspot_configs():
    """Get hotspot configurations
    ---
    tags:
      - Mobile
    summary: Get hotspot configurations
    description: Returns all hotspot configurations for the authenticated user
    responses:
      200:
        description: List of hotspot configurations
        schema:
          type: object
          properties:
            success:
              type: boolean
            configs:
              type: array
              items:
                type: object
    """
    mobile_service = get_mobile_service()
    player_id = session.get("player_id")
    if not player_id:
        return jsonify({"success": False, "error": "Player ID not available"}), 401
    configs = mobile_service.get_hotspot_configs(player_id)
    return jsonify({"success": True, "configs": configs})


@app.route("/api/mobile/hotspot", methods=["POST"])
@login_required
def create_hotspot_config():
    """Create hotspot configuration
    ---
    tags:
      - Mobile
    summary: Create hotspot configuration
    description: Creates or updates hotspot configuration for a dartboard
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            dartboard_id:
              type: integer
              description: Dartboard database ID
            ssid:
              type: string
              description: Hotspot SSID
            password:
              type: string
              description: Hotspot password
    responses:
      200:
        description: Hotspot configuration created
        schema:
          type: object
          properties:
            success:
              type: boolean
            config:
              type: object
    """
    data = request.json
    dartboard_id = data.get("dartboard_id")
    ssid = data.get("ssid")
    password = data.get("password")
    player_id = session.get("player_id")
    if not player_id:
        return jsonify({"success": False, "error": "Player ID not available"}), 401

    if not all([dartboard_id, ssid, password]):
        return jsonify({"success": False, "error": "Missing required fields"}), 400

    mobile_service = get_mobile_service()
    result = mobile_service.create_hotspot_config(player_id, dartboard_id, ssid, password)
    return jsonify(result)


@app.route("/api/mobile/hotspot/<int:config_id>/toggle", methods=["POST"])
@login_required
def toggle_hotspot(config_id):
    """Toggle hotspot on/off
    ---
    tags:
      - Mobile
    summary: Toggle hotspot
    description: Enables or disables a hotspot configuration
    parameters:
      - in: path
        name: config_id
        type: integer
        required: true
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            enabled:
              type: boolean
              description: True to enable, False to disable
    responses:
      200:
        description: Hotspot toggled
        schema:
          type: object
          properties:
            success:
              type: boolean
            is_enabled:
              type: boolean
    """
    data = request.json
    enabled = data.get("enabled", False)
    player_id = session.get("player_id")
    if not player_id:
        return jsonify({"success": False, "error": "Player ID not available"}), 401

    mobile_service = get_mobile_service()
    result = mobile_service.toggle_hotspot(config_id, player_id, enabled)
    return jsonify(result)


# Dartboard API Endpoints (authenticated with API key)


@app.route("/api/dartboard/connect", methods=["POST"])
@api_key_required
def dartboard_connect():
    """Dartboard connection endpoint
    ---
    tags:
      - Mobile
    summary: Dartboard connect
    description: Called by dartboard when it connects (requires API key)
    parameters:
      - in: header
        name: X-API-Key
        type: string
        required: true
        description: API key for authentication
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            dartboard_id:
              type: string
              description: Dartboard identifier
    responses:
      200:
        description: Connection acknowledged
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
    """
    data = request.json
    dartboard_id = data.get("dartboard_id")

    if not dartboard_id:
        return jsonify({"success": False, "error": "Missing dartboard_id"}), 400

    mobile_service = get_mobile_service()
    success = mobile_service.update_dartboard_connection(dartboard_id)

    if success:
        return jsonify({"success": True, "message": "Connection acknowledged"})
    return jsonify({"success": False, "error": "Dartboard not found"}), 404


@app.route("/api/dartboard/score", methods=["POST"])
@api_key_required
def dartboard_submit_score():
    """Dartboard score submission endpoint
    ---
    tags:
      - Mobile
    summary: Submit score from dartboard
    description: Called by dartboard to submit scores (requires API key)
    parameters:
      - in: header
        name: X-API-Key
        type: string
        required: true
        description: API key for authentication
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            score:
              type: integer
              description: Base score value
            multiplier:
              type: string
              description: Multiplier type
    responses:
      200:
        description: Score submitted
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
    """
    data = request.json
    # Process score through game manager
    game_manager.process_score(data)
    return jsonify({"success": True, "message": "Score submitted"})


# Mobile Game Management API Endpoints (aliases for existing endpoints)


@app.route("/api/game/current", methods=["GET"])
@login_required
def get_current_game():
    """Get current game state (mobile alias)
    ---
    tags:
      - Mobile
    summary: Get current game state
    description: "Returns the complete current state including players,
    scores,
    and game type (mobile-friendly endpoint)"
    responses:
      200:
        description: Current game state
        schema:
          type: object
          properties:
            success:
              type: boolean
            game:
              type: object
              description: Current game state
    """
    game_state = game_manager.get_game_state()
    return jsonify({"success": True, "game": game_state})


@app.route("/api/user/current", methods=["GET"])
@login_required
def get_current_user():
    """Get current user information
    ---
    tags:
      - User
    summary: Get current user info
    description: Returns the current authenticated user's username, roles, and player ID
    responses:
      200:
        description: Current user information
        schema:
          type: object
          properties:
            success:
              type: boolean
            username:
              type: string
              description: User's username
            roles:
              type: array
              items:
                type: string
              description: User's roles (admin, gamemaster, player, etc.)
            player_id:
              type: integer
              description: User's player database ID
    """
    user_info = session.get("user_info", {})
    user_roles = getattr(request, "user_roles", [])
    username = user_info.get("preferred_username") or user_info.get("username")
    player_id = session.get("player_id")

    return jsonify(
        {
            "success": True,
            "username": username,
            "roles": user_roles,
            "player_id": player_id,
        },
    )


@app.route("/api/game/types", methods=["GET"])
def get_game_types():
    """Get available game types
    ---
    tags:
      - Game
    summary: Get all available game types
    description: Returns a list of all game types available in the system
    responses:
      200:
        description: List of game types
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            game_types:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    description: Game type ID
                  name:
                    type: string
                    description: Game type name (e.g., '301', '501', 'cricket')
                  description:
                    type: string
                    description: Game type description
    """
    try:
        session = game_manager.db_service.db_manager.get_session()
        try:
            game_types = session.query(GameType).order_by(GameType.name).all()
            game_types_list = [
                {"id": gt.id, "name": gt.name, "description": gt.description} for gt in game_types
            ]
            return jsonify({"status": "success", "game_types": game_types_list})
        finally:
            session.close()
    except Exception as e:
        logger.exception("Error fetching game types")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/game/start", methods=["POST"])
@login_required
@permission_required("game:create")
def start_game():
    """Start a new game (mobile alias)
    ---
    tags:
      - Mobile
    summary: Start a new game
    description: "Initializes a new darts game with specified type and
    players (mobile-friendly endpoint)"
    parameters:
      - in: body
        name: body
        description: Game configuration
        required: true
        schema:
          type: object
          properties:
            game_type:
              type: string
              description: Type of game to start
              enum: ['301', '401', '501', 'cricket', 'round_the_clock', 'round_the_clock_double']
              default: '301'
            players:
              type: array
              description: List of player names
              items:
                type: string
            double_out:
              type: boolean
              description: Whether to require double-out to finish
              default: false
            reset_on_miss:
              type: boolean
              description: Enable hard mode for round_the_clock (reset to 20 after 3 misses)
              default: false
            show_throwout_advice:
              type: boolean
              description: Whether to show throw-out advice during the game
              default: false
            game_id:
              type: string
              description: Optional game ID (auto-generated if not provided)
              default: null
    responses:
      200:
        description: Game started successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            game:
              type: object
            game_id:
              type: string
              description: The ID of the created game
      400:
        description: Invalid request or player not found
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
    """
    # global games_store
    global active_game_id
    global game_manager

    data = request.json
    game_type = data.get("game_type", "301")
    player_data = data.get("players", [])
    double_out = data.get("double_out", False)
    reset_on_miss = data.get("reset_on_miss", False)
    show_throwout_advice = data.get("show_throwout_advice", False)
    game_id = data.get("game_id")

    # Generate game_id if not provided
    if not game_id:
        game_id = f"game-{uuid.uuid4().hex[:8]}"

    # Convert player names to player objects with database IDs
    db_session = game_manager.db_service.db_manager.get_session()
    try:
        player_ids = []

        for player_name in player_data:
            # Try to find player by name or username
            player = (
                db_session.query(Player)
                .filter(
                    (Player.name == player_name) | (Player.username == player_name),
                )
                .first()
            )
            if player:
                player_ids.append({"db_id": player.id, "name": player.name})
            else:
                # If player not found in database, return an error response
                app.logger.warning(
                    f"Player '{player_name}' not found in database. "
                    "Only registered WSO2 users can play.",
                )
                return (
                    jsonify(
                        {
                            "success": False,
                            "message": (
                                f"Player '{player_name}' not found. "
                                "Only registered WSO2 users allowed."
                            ),
                        },
                    ),
                    400,
                )

        if not player_ids:
            player_ids = [session.get("player_id")]

        # Create a dedicated session and start the game there
        new_game_manager = multi_game_manager.create_game(game_id)
        new_game_manager.new_game(
            game_type,
            player_ids=player_ids,
            double_out=double_out,
            reset_on_miss=reset_on_miss,
        )
        # Set active and update global pointers so main area shows this game
        multi_game_manager.set_active_game(game_id)
        game_manager = new_game_manager
        app.game_manager = game_manager

        # Store game metadata in games_store
        games_store[game_id] = {
            "game_id": game_id,
            "game_type": game_type,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "players": player_ids,
            "double_out": double_out,
            "reset_on_miss": reset_on_miss,
        }
        active_game_id = game_id

        # Set throwout advice if requested on the newly active session
        if show_throwout_advice:
            game_manager.set_show_throwout_advice(True)

        game_state = game_manager.get_game_state()

        return jsonify(
            {
                "success": True,
                "message": "Game started successfully",
                "game": game_state,
                "game_id": game_id,
            },
        )
    except Exception:
        app.logger.exception("Error starting game")
        # Don't expose internal error details to clients
        return (
            jsonify(
                {
                    "success": False,
                    "message": "An error occurred while starting the game. Please try again.",
                },
            ),
            500,
        )
    finally:
        db_session.close()


# ============================================================================
# Multi-Game Management API Endpoints
# ============================================================================


@app.route("/api/games", methods=["GET"])
@login_required
def get_games_list():
    """Get all games
    ---
    tags:
      - Multi-Game
    summary: List all games
    description: Returns all active game sessions with their current state
    responses:
      200:
        description: List of all games
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            games:
              type: array
              items:
                type: object
            active_game_id:
              type: string
              nullable: true
    """
    try:
        # Use MultiGameManager to retrieve live state for all sessions
        games = multi_game_manager.list_games()
        # Filter out the legacy "default" session from UI
        games = [g for g in games if g.get("game_id") != "default"]
        active_id = multi_game_manager.get_active_game_id()
        # If the active session is default, treat as no active selection
        if active_id == "default":
            active_id = None

        return jsonify(
            {
                "status": "success",
                "games": games,
                "active_game_id": active_id,
            },
        )
    except Exception:
        app.logger.exception("Error getting games list")
        return jsonify({"status": "error", "message": "Failed to list games"}), 500


@app.route("/api/games/<game_id>/activate", methods=["POST"])
@login_required
def activate_game(game_id):
    """Activate a specific game
    ---
    tags:
      - Multi-Game
    summary: Activate a game
    description: Sets the specified game as the active game
    parameters:
      - in: path
        name: game_id
        type: string
        required: true
        description: Game ID to activate
    responses:
      200:
        description: Game activated successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
      404:
        description: Game not found
    """
    # Ensure the session exists in MultiGameManager
    if not multi_game_manager.has_game(game_id):
        return jsonify({"status": "error", "message": f"Game '{game_id}' not found"}), 404

    # Switch active session and update global game_manager reference
    multi_game_manager.set_active_game(game_id)
    global game_manager
    game_manager = multi_game_manager.get_game(game_id)
    app.game_manager = game_manager

    return jsonify(
        {
            "status": "success",
            "message": "Game activated",
            "game_id": game_id,
        },
    )


@app.route("/api/games/<game_id>/state", methods=["GET"])
@login_required
def get_game_state_by_id(game_id):
    """Get state of a specific game
    ---
    tags:
      - Multi-Game
    summary: Get game state
    description: Returns the complete state of a specific game
    parameters:
      - in: path
        name: game_id
        type: string
        required: true
        description: Game ID
    responses:
      200:
        description: Game state retrieved
      404:
        description: Game not found
    """
    game = multi_game_manager.get_game(game_id)
    if not game:
        return jsonify({"status": "error", "message": f"Game '{game_id}' not found"}), 404
    return jsonify(game.get_game_state())


@app.route("/api/mobile/game/start-single-player", methods=["POST"])
@login_required
def start_single_player_game():
    """Start a new single-player game with the current user
    ---
    tags:
      - Mobile
    summary: Start a single-player game
    description: |
      Starts a new single-player game with the currently logged-in user as the only player.
      Any authenticated user can start a single-player game.
      Training modes (bull_practice) require gamemaster or admin role.
    parameters:
      - in: body
        name: body
        description: Game configuration
        required: true
        schema:
          type: object
          properties:
            game_type:
              type: string
              description: Type of game to start
              enum: ['170', '301', '401', '501', 'cricket', 'round_the_clock',
                'round_the_clock_double', 'bull_practice']
              default: '301'
            double_out:
              type: boolean
              description: Whether to require double-out to finish (only for 170/301/401/501)
              default: false
            reset_on_miss:
              type: boolean
              description: Enable hard mode for round_the_clock (reset after 3 misses)
              default: false
    responses:
      200:
        description: Game started successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            game:
              type: object
      401:
        description: Player ID not available
      403:
        description: Training mode requires gamemaster or admin role
      500:
        description: Failed to start game
    """
    try:
        data = request.json or {}
        game_type = data.get("game_type", "301")
        double_out = data.get("double_out", False)
        reset_on_miss = data.get("reset_on_miss", False)

        # Get current player's ID and info from session
        player_id = session.get("player_id")
        if not player_id:
            return jsonify({"success": False, "error": "Player ID not available"}), 401

        # Get user roles for training mode access check
        user_roles = getattr(request, "user_roles", [])

        # Training modes (bull_practice) require gamemaster or admin role
        training_modes = ["bull_practice"]
        if (
            game_type in training_modes
            and "admin" not in user_roles
            and "gamemaster" not in user_roles
        ):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": (f"Training mode '{game_type}' requires gamemaster or admin role"),
                    },
                ),
                403,
            )

        # Get player name from session
        user_info = session.get("user_info", {})
        player_name = (
            user_info.get("name")
            or user_info.get("preferred_username")
            or user_info.get("username")
            or "Player"
        )

        # Start single-player game with current user
        player_ids = [{"db_id": player_id, "name": player_name}]

        game_manager.new_game(
            game_type=game_type,
            player_ids=player_ids,
            double_out=double_out,
            reset_on_miss=reset_on_miss,
        )

        game_state = game_manager.get_game_state()

        return jsonify(
            {
                "success": True,
                "message": f"Single-player {game_type} game started",
                "game": game_state,
            },
        )
    except Exception as e:
        app.logger.exception("Failed to start single-player game")
        return (
            jsonify({"success": False, "error": str(e)}),
            500,
        )


@app.route("/api/game/end", methods=["POST"])
@login_required
@permission_required("game:create")
def end_game():
    """End the current game
    ---
    tags:
      - Mobile
    summary: End current game
    description: Ends the current game and saves results
    parameters:
      - in: body
        name: body
        required: false
        schema:
          type: object
          properties:
            save_results:
              type: boolean
              description: Whether to save game results
              default: true
    responses:
      200:
        description: Game ended successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
    """

    # Reset the game state
    game_manager.reset_game()

    return jsonify(
        {
            "success": True,
            "message": "Game ended successfully",
        },
    )


@app.route("/api/game/<game_session_id>", methods=["DELETE"])
@login_required
@permission_required("game:create")
def delete_game(game_session_id):
    """Delete a game - requires game:create permission
    ---
    tags:
      - Game
    summary: Delete a game
    description: >
      Deletes a game and all associated data (game results and scores).
      Only incomplete games older than 1 day can be deleted.
    parameters:
      - in: path
        name: game_session_id
        type: string
        required: true
        description: The game session ID to delete
    responses:
      200:
        description: Game deleted successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: Game deleted successfully
      403:
        description: Game cannot be deleted (too recent or already completed)
      404:
        description: Game not found
      500:
        description: Error deleting game
    """
    try:
        # Get the game to check if it can be deleted
        game_data = game_manager.db_service.get_game_replay_data(game_session_id)

        if not game_data:
            return jsonify({"status": "error", "message": "Game not found"}), 404

        # Check if game is completed
        if game_data["finished_at"]:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Cannot delete completed games",
                    },
                ),
                403,
            )

        # Check if game is older than 1 day
        started_at_str = game_data["started_at"]
        # Parse the ISO format datetime string
        if started_at_str.endswith("Z"):
            started_at_str = started_at_str.replace("Z", "+00:00")
        started_at = datetime.fromisoformat(started_at_str)

        # Ensure both datetimes are timezone-aware for comparison
        if started_at.tzinfo is None:
            started_at = started_at.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        age = now - started_at

        if age < timedelta(days=1):
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Game must be at least 1 day old to be deleted",
                    },
                ),
                403,
            )

        # Delete the game
        success = game_manager.db_service.delete_game(game_session_id)

        if success:
            return jsonify({"status": "success", "message": "Game deleted successfully"})

        return jsonify({"status": "error", "message": "Failed to delete game"}), 500

    except Exception as e:
        logger.exception(f"Error deleting game {game_session_id}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/game/resume/<game_session_id>", methods=["POST"])
@login_required
@permission_required("game:create")
def resume_game(game_session_id):
    """Resume an incomplete game - requires game:create permission
    ---
    tags:
      - Game
    summary: Resume an incomplete game
    description: >
      Starts a new game with the same settings as the incomplete game.
      The original incomplete game data is preserved in the database.
      Redirects to the game board to continue playing.
    parameters:
      - in: path
        name: game_session_id
        type: string
        required: true
        description: The game session ID to resume
    responses:
      200:
        description: Game setup for resumption
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            message:
              type: string
              example: Starting new game with same settings
            game_id:
              type: string
              description: The ID of the resumed game
            redirect_url:
              type: string
              example: /
      403:
        description: Game cannot be resumed (already completed)
      404:
        description: Game not found
      500:
        description: Error resuming game
    """
    global active_game_id, game_manager

    try:
        # Get the game data
        game_data = game_manager.db_service.get_game_replay_data(game_session_id)

        if not game_data:
            return jsonify({"status": "error", "message": "Game not found"}), 404

        # Check if game is already completed
        if game_data["finished_at"]:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Cannot resume a completed game",
                    },
                ),
                403,
            )

        # Generate game_id for resumed game and create a dedicated session
        game_id = f"game-{uuid.uuid4().hex[:8]}"

        new_game_manager = multi_game_manager.create_game(game_id)

        # Resume the game by replaying all throws to restore state in the new session
        success = new_game_manager.resume_game_from_replay_data(game_data)

        if not success:
            return jsonify({"status": "error", "message": "Failed to resume game"}), 500

        # Store game metadata in games_store
        games_store[game_id] = {
            "game_id": game_id,
            "game_type": game_data.get("game_type", "301"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "players": game_data.get("players", []),
            "double_out": game_data.get("double_out", False),
            "reset_on_miss": game_data.get("reset_on_miss", False),
            "resumed_from": game_session_id,
        }
        # Set active and update global pointers so UI shows resumed session
        multi_game_manager.set_active_game(game_id)
        game_manager = new_game_manager
        app.game_manager = game_manager
        active_game_id = game_id

        # Emit game state to all clients
        socketio.emit("game_state", new_game_manager.get_game_state(), namespace="/")

        return jsonify(
            {
                "status": "success",
                "message": f"Game resumed with {len(game_data['throws'])} throws replayed",
                "game_id": game_id,
                "redirect_url": "/",
            },
        )

    except Exception as e:
        logger.exception(f"Error resuming game {game_session_id}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/game/results", methods=["GET"])
@login_required
def get_game_results():
    """Get game results (mobile alias)
    ---
    tags:
      - Mobile
    summary: Get game results
    description: "Returns a list of recent games with results (mobile-friendly endpoint)"
    parameters:
      - in: query
        name: limit
        type: integer
        description: Maximum number of games to return
        default: 10
      - in: query
        name: game_type
        type: string
        description: Filter by game type
    responses:
      200:
        description: List of game results
        schema:
          type: object
          properties:
            success:
              type: boolean
            results:
              type: array
              items:
                type: object
    """
    limit = request.args.get("limit", 10, type=int)
    game_type = request.args.get("game_type")

    try:
        games = game_manager.db_service.get_recent_games(limit=limit)

        # Filter by game type if specified
        if game_type:
            games = [g for g in games if g.get("game_type") == game_type]

        return jsonify({"success": True, "results": games})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/player/history", methods=["GET"])
@login_required
def get_player_history():
    """Get current player's game history
    ---
    tags:
      - Player
    summary: Get player game history
    description: Returns the logged-in player's game history with statistics
    parameters:
      - in: query
        name: game_type
        type: string
        description: Filter by game type (301, 401, 501, cricket)
      - in: query
        name: limit
        type: integer
        description: Maximum number of games to return
        default: 50
    responses:
      200:
        description: Player game history
        schema:
          type: object
          properties:
            success:
              type: boolean
            games:
              type: array
              items:
                type: object
      401:
        description: Unauthorized - player ID not available
    """
    try:
        player_id = session.get("player_id")
        if not player_id:
            return jsonify({"success": False, "error": "Player ID not available"}), 401

        game_type = request.args.get("game_type")
        limit = request.args.get("limit", 50, type=int)

        games = game_manager.db_service.get_player_game_history(
            player_id=player_id,
            game_type=game_type,
            limit=limit,
        )

        return jsonify({"success": True, "games": games})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/player/statistics", methods=["GET"])
@login_required
def get_player_statistics():
    """Get current player's statistics
    ---
    tags:
      - Player
    summary: Get player statistics
    description: Returns the logged-in player's overall statistics
    responses:
      200:
        description: Player statistics
        schema:
          type: object
          properties:
            success:
              type: boolean
            statistics:
              type: object
      401:
        description: Unauthorized - player ID not available
    """
    try:
        player_id = session.get("player_id")
        if not player_id:
            return jsonify({"success": False, "error": "Player ID not available"}), 401

        stats = game_manager.db_service.get_player_statistics(player_id=player_id)

        if stats:
            return jsonify({"success": True, "statistics": stats})
        return jsonify({"success": False, "error": "Player not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/active-games", methods=["GET"])
@login_required
def get_active_games():
    """Get active games with current state
    ---
    tags:
      - Game
    summary: Get active games
    description: Returns all currently active games with their current state and player scores
    responses:
      200:
        description: List of active games
        schema:
          type: object
          properties:
            success:
              type: boolean
            games:
              type: array
              items:
                type: object
    """
    try:
        games = game_manager.db_service.get_active_games()
        return jsonify({"success": True, "games": games})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/debug/session", methods=["GET"])
def debug_session():
    """Debug endpoint - returns session and player info"""
    return jsonify(
        {
            "player_id": session.get("player_id"),
            "username": session.get("username"),
            "session_keys": list(session.keys()),
            "auth_disabled": os.getenv("AUTH_DISABLED") == "true",
        },
    )


@app.route("/api/training/start", methods=["POST"])
@login_required
def start_training():
    """Start a new training session
    ---
    tags:
      - Training
    summary: Start training session
    description: Initializes a new single-player training session
    parameters:
      - in: body
        name: body
        description: Training configuration
        required: true
        schema:
          type: object
          properties:
            game_type:
              type: string
              description: Type of game to practice
              enum: ['170', '301', '401', '501', 'cricket', 'round_the_clock',
                'round_the_clock_double', 'bull_practice']
              default: '301'
            double_out:
              type: boolean
              description: Whether to require double-out to finish
              default: false
    responses:
      200:
        description: Training session started successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
            session_id:
              type: string
    """
    try:
        data = request.json
        game_type = data.get("game_type", "301")
        double_out = data.get("double_out", False)

        player_id = session.get("player_id")
        if not player_id:
            return jsonify({"success": False, "error": "Player ID not available"}), 401

        # Start training session using database service
        db_session = game_manager.db_service.db_manager.get_session()

        # Get or create game type
        game_type_obj = db_session.query(GameType).filter(GameType.name == game_type).first()
        if not game_type_obj:
            game_type_obj = GameType(name=game_type, description=f"{game_type} game")
            db_session.add(game_type_obj)
            db_session.commit()

        # Create training session
        session_id = str(uuid.uuid4())
        start_score_map = {"170": 170, "301": 301, "401": 401, "501": 501}
        start_score = start_score_map.get(game_type)

        training_session = TrainingSession(
            player_id=player_id,
            game_type_id=game_type_obj.id,
            session_id=session_id,
            start_score=start_score,
            double_out_enabled=double_out,
            completed=False,
        )
        db_session.add(training_session)
        db_session.commit()

        # Store training session ID in session
        session["training_session_id"] = training_session.id

        # Start game in game manager with single player
        game_manager.new_game(
            game_type=game_type,
            player_ids=[{"db_id": player_id, "name": session.get("username", "Player")}],
            double_out=double_out,
        )

        # Set training mode flags in game manager
        game_manager.is_training_mode = True
        game_manager.training_session_id = training_session.id

        db_session.close()

        return jsonify(
            {
                "success": True,
                "message": "Training session started",
                "session_id": session_id,
                "training_session_id": training_session.id,
            },
        )
    except Exception:
        app.logger.exception("Failed to start training session")
        return (
            jsonify({"success": False, "error": "Failed to start training session"}),
            500,
        )


@app.route("/api/training/end", methods=["POST"])
@login_required
def end_training():
    """End the current training session
    ---
    tags:
      - Training
    summary: End training session
    description: Ends the current training session and saves results
    responses:
      200:
        description: Training session ended successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
            message:
              type: string
    """
    try:
        training_session_id = session.get("training_session_id")
        if not training_session_id:
            return jsonify({"success": False, "error": "No active training session"}), 400

        db_session = game_manager.db_service.db_manager.get_session()
        training_session = (
            db_session.query(TrainingSession)
            .filter(TrainingSession.id == training_session_id)
            .first()
        )

        if training_session:
            training_session.completed = True
            training_session.finished_at = datetime.now(tz=timezone.utc)
            training_session.final_score = (
                game_manager.game.get_player_score(0) if game_manager.game else 0
            )
            db_session.commit()

        db_session.close()

        # Clear training mode flags
        game_manager.is_training_mode = False
        game_manager.training_session_id = None

        # Reset game manager
        game_manager.reset_game()

        # Clear training session from session
        session.pop("training_session_id", None)

        return jsonify({"success": True, "message": "Training session ended"})
    except Exception:
        app.logger.exception("Failed to end training session")
        return (
            jsonify({"success": False, "error": "Failed to end training session"}),
            500,
        )


@app.route("/api/training/history", methods=["GET"])
@login_required
def get_training_history():
    """Get training session history for current player
    ---
    tags:
      - Training
    summary: Get training history
    description: Returns the training session history for the logged-in player
    responses:
      200:
        description: Training history retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
            sessions:
              type: array
              items:
                type: object
    """
    try:
        player_id = session.get("player_id")
        if not player_id:
            return jsonify({"success": False, "error": "Player ID not available"}), 401

        db_session = game_manager.db_service.db_manager.get_session()
        training_sessions = (
            db_session.query(TrainingSession)
            .join(GameType, TrainingSession.game_type_id == GameType.id)
            .filter(TrainingSession.player_id == player_id)
            .order_by(TrainingSession.started_at.desc())
            .all()
        )

        sessions_data = []
        for ts in training_sessions:
            sessions_data.append(
                {
                    "id": ts.id,
                    "session_id": ts.session_id,
                    "game_type": ts.game_type.name,
                    "start_score": ts.start_score,
                    "final_score": ts.final_score,
                    "double_out_enabled": ts.double_out_enabled,
                    "completed": ts.completed,
                    "started_at": ts.started_at.isoformat() if ts.started_at else None,
                    "finished_at": ts.finished_at.isoformat() if ts.finished_at else None,
                    "throws_count": len(ts.training_scores),
                },
            )

        db_session.close()

        return jsonify({"success": True, "sessions": sessions_data})
    except Exception:
        app.logger.exception("Failed to get training history")
        return (
            jsonify({"success": False, "error": "Failed to retrieve training history"}),
            500,
        )


@app.route("/api/training/statistics", methods=["GET"])
@login_required
def get_training_statistics():
    """Get training statistics for current player
    ---
    tags:
      - Training
    summary: Get training statistics
    description: Returns aggregated training statistics for the logged-in player
    responses:
      200:
        description: Training statistics retrieved successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
            statistics:
              type: object
    """
    try:
        player_id = session.get("player_id")
        if not player_id:
            return jsonify({"success": False, "error": "Player ID not available"}), 401

        db_session = game_manager.db_service.db_manager.get_session()

        # Count total sessions
        total_sessions = (
            db_session.query(func.count(TrainingSession.id))
            .filter(TrainingSession.player_id == player_id)
            .scalar()
        )

        # Count completed sessions
        completed_sessions = (
            db_session.query(func.count(TrainingSession.id))
            .filter(
                TrainingSession.player_id == player_id,
                TrainingSession.completed.is_(True),
            )
            .scalar()
        )

        # Calculate average score
        avg_score = (
            db_session.query(func.avg(TrainingScore.actual_score))
            .join(TrainingSession, TrainingScore.training_session_id == TrainingSession.id)
            .filter(TrainingSession.player_id == player_id)
            .scalar()
        )

        # Count total throws
        total_throws = (
            db_session.query(func.count(TrainingScore.id))
            .join(TrainingSession, TrainingScore.training_session_id == TrainingSession.id)
            .filter(TrainingSession.player_id == player_id)
            .scalar()
        )

        db_session.close()

        statistics = {
            "total_sessions": total_sessions or 0,
            "completed_sessions": completed_sessions or 0,
            "average_score_per_throw": round(avg_score, 2) if avg_score else 0,
            "total_throws": total_throws or 0,
        }

        return jsonify({"success": True, "statistics": statistics})
    except Exception:
        app.logger.exception("Failed to get training statistics")
        return (
            jsonify({"success": False, "error": "Failed to retrieve training statistics"}),
            500,
        )


@socketio.on("connect", namespace="/")
def handle_connect():
    """Handle client connection"""
    print("Client connected")
    # Use socketio.emit to ensure the message reaches the test client
    socketio.emit(
        "game_state",
        game_manager.get_game_state(),
        namespace="/",
        to=request.sid,  # type: ignore[attr-defined]
    )


@socketio.on("disconnect", namespace="/")
def handle_disconnect():
    """Handle client disconnection"""
    print("Client disconnected")


@socketio.on("new_game", namespace="/")
def handle_new_game(data):
    """Handle new game request"""
    game_type = data.get("game_type", "301")
    player_data = data.get("players", [])
    double_out = data.get("double_out", False)
    reset_on_miss = data.get("reset_on_miss", False)

    # Convert player names to player objects with database IDs
    db_session = game_manager.db_service.db_manager.get_session()
    try:
        player_ids = []

        for player_name in player_data:
            # Try to find player by name or username
            player = (
                db_session.query(Player)
                .filter(
                    (Player.name == player_name) | (Player.username == player_name),
                )
                .first()
            )
            if player:
                player_ids.append({"db_id": player.id, "name": player.name})
            else:
                # If player not found in database, emit error and return
                app.logger.warning(
                    f"Player '{player_name}' not found in database. "
                    "Only registered WSO2 users can play.",
                )
                socketio.emit(
                    "error",
                    {
                        "message": (
                            f"Player '{player_name}' not found. Only registered WSO2 users allowed."
                        ),
                    },
                    namespace="/",
                )
                return

        if not player_ids:
            player_ids = [session.get("player_id")]

        game_manager.new_game(
            game_type,
            player_ids=player_ids,
            double_out=double_out,
            reset_on_miss=reset_on_miss,
        )
    except Exception:
        app.logger.exception("Error starting new game via WebSocket")
        # Don't expose internal error details to clients
        socketio.emit(
            "error",
            {"message": "An error occurred while starting the game. Please try again."},
            namespace="/",
        )
    finally:
        db_session.close()


@socketio.on("add_player", namespace="/")
def handle_add_player(data):
    """Handle add player request"""
    player_name = data.get("name", f"Player {len(game_manager.players) + 1}")
    game_manager.add_player(player_name)


@socketio.on("remove_player", namespace="/")
def handle_remove_player(data):
    """Handle remove player request"""
    player_id = data.get("player_id")
    if player_id is not None:
        game_manager.remove_player(player_id)


@socketio.on("next_player", namespace="/")
def handle_next_player():
    """Handle next player request"""
    game_manager.next_player()


@socketio.on("skip_to_player", namespace="/")
def handle_skip_to_player(data):
    """Handle skip to specific player"""
    player_id = data.get("player_id")
    if player_id is not None:
        game_manager.skip_to_player(player_id)


@socketio.on("end_turn_early", namespace="/")
def handle_end_turn_early():
    """Handle end turn early request - records remaining throws as misses"""
    game_manager.end_turn_early()


@socketio.on("manual_score", namespace="/")
def handle_manual_score(data):
    """Handle manual score entry"""
    game_manager.process_score(data)


@socketio.on("set_throwout_advice", namespace="/")
def handle_set_throwout_advice(data):
    """Handle toggle of throwout advice"""
    enabled = data.get("enabled", False)
    game_manager.set_show_throwout_advice(enabled)


@socketio.on("dartboard_test_message", namespace="/")
def handle_dartboard_test_message(data):
    """Handle raw dartboard test messages for admin calibration"""
    # Broadcast to all admin clients for real-time testing feedback
    socketio.emit("dartboard_test_received", data, namespace="/")


def start_rabbitmq_consumer():
    """Start RabbitMQ consumer in a separate thread"""
    global rabbitmq_consumer

    rabbitmq_config = {
        "host": os.getenv("RABBITMQ_HOST", "localhost"),
        "port": int(os.getenv("RABBITMQ_PORT", 5672)),
        "user": os.getenv("RABBITMQ_USER", "guest"),
        "password": os.getenv("RABBITMQ_PASSWORD", "guest"),
        "vhost": os.getenv("RABBITMQ_VHOST", "/"),
        "exchange": os.getenv("RABBITMQ_EXCHANGE", "darts_exchange"),
        "topic": os.getenv("RABBITMQ_TOPIC", "darts.scores.#"),
    }

    try:
        rabbitmq_consumer = RabbitMQConsumer(rabbitmq_config, on_score_received)
        consumer_thread = threading.Thread(target=rabbitmq_consumer.start, daemon=True)
        consumer_thread.start()
        print("RabbitMQ consumer started")
    except Exception as e:
        print(f"Failed to start RabbitMQ consumer: {e}")
        print("Application will continue without RabbitMQ integration")


def patch_eventlet_ssl_error_handling():
    """
    Monkey-patch eventlet's WSGI handler to suppress SSL protocol errors

    This prevents stack traces from flooding the console when clients attempt
    to connect using HTTP to an HTTPS server. Instead, it logs a concise,
    user-friendly message with rate limiting.
    """
    # Store original handler
    original_handle = wsgi.HttpProtocol.handle

    # Rate limiting state
    ssl_error_state = {"count": 0, "last_logged": 0.0}

    def custom_handle(self):
        """Handle requests with special treatment for SSL protocol errors"""
        try:
            # Call the original handle method
            original_handle(self)
        except ssl.SSLError as e:
            error_msg = str(e)
            if "HTTP_REQUEST" in error_msg or "http request" in error_msg.lower():
                # Rate limit the logging (only log every 10 seconds)
                current_time = time.time()
                ssl_error_state["count"] += 1

                if current_time - ssl_error_state["last_logged"] >= 10:
                    print("")
                    print("⚠️  SSL Protocol Mismatch Detected")
                    print(
                        f"   {ssl_error_state['count']} HTTP request(s) to HTTPS server (rejected)",
                    )
                    print("   Clients must use HTTPS URLs to connect")
                    print("")
                    ssl_error_state["last_logged"] = current_time
                    ssl_error_state["count"] = 0

                # Suppress the stack trace by not re-raising
                return
            # Re-raise other SSL errors
            raise
        except Exception:
            # Re-raise all other exceptions
            raise

    # Apply the monkey-patch
    wsgi.HttpProtocol.handle = custom_handle


if __name__ == "__main__":
    # Start RabbitMQ consumer
    start_rabbitmq_consumer()

    # Start Flask app
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    use_ssl = os.getenv("FLASK_USE_SSL", "False").lower() == "true"

    # SSL Configuration
    ssl_args = {}
    protocol = "http"

    if use_ssl:
        from pathlib import Path

        ssl_dir = Path(__file__).parent / "ssl"
        cert_file = ssl_dir / "cert.pem"
        key_file = ssl_dir / "key.pem"

        if cert_file.exists() and key_file.exists():
            # For eventlet, pass certfile and keyfile directly
            ssl_args = {"certfile": str(cert_file), "keyfile": str(key_file)}
            protocol = "https"

            # Apply SSL error handling patch
            patch_eventlet_ssl_error_handling()
            print("✅ SSL error handling patch applied")

            print("=" * 80)
            print("🔒 Starting Darts Game Server with SSL/HTTPS")
            print(f"   URL: {protocol}://{host}:{port}")
            print("=" * 80)
            print("⚠️  IMPORTANT: Using self-signed SSL certificate")
            print("   - Your browser will show a security warning")
            print("   - This is expected for self-signed certificates")
            print("   - Click 'Advanced' and 'Proceed' to continue")
            print("")
            print("⚠️  SSL ERROR TROUBLESHOOTING:")
            print("   - If you see 'SSL: HTTP_REQUEST' errors, clients are")
            print("     using HTTP instead of HTTPS")
            print("   - Make sure to access the application using: https://")
            print(f"   - Correct URL: {protocol}://{host}:{port}")
            print(f"   - Wrong URL:   http://{host}:{port}")
            print("")
            print("   To disable SSL for development:")
            print("   - Set FLASK_USE_SSL=False in .env file")
            print("=" * 80)
        else:
            print("=" * 80)
            print("⚠️  SSL CONFIGURATION ERROR")
            print("=" * 80)
            print("SSL is enabled but certificates not found!")
            print("Expected files:")
            print(f"  - Certificate: {cert_file}")
            print(f"  - Private Key: {key_file}")
            print("")
            print("To generate SSL certificates, run:")
            print("  ./helpers/generate_ssl_certs.sh letsplaydarts.eu")
            print("")
            print("Falling back to HTTP (insecure)...")
            print("=" * 80)
            use_ssl = False

    if not use_ssl:
        print("=" * 80)
        print("🌐 Starting Darts Game Server (HTTP - No SSL)")
        print(f"   URL: {protocol}://{host}:{port}")
        print("=" * 80)
        print("⚠️  Running without SSL encryption")
        print("   For production, enable SSL by:")
        print("   1. Set FLASK_USE_SSL=True in .env")
        print("   2. Generate certificates: ./helpers/generate_ssl_certs.sh letsplaydarts.eu")
        print("=" * 80)

    try:
        socketio.run(app, host=host, port=port, debug=debug, **ssl_args)
    except Exception as e:
        print("")
        print("=" * 80)
        print("❌ SERVER ERROR")
        print("=" * 80)
        print(f"Failed to start server: {e}")
        if use_ssl and "SSL" in str(e):
            print("")
            print("SSL-related error detected. Possible solutions:")
            print("1. Regenerate SSL certificates:")
            print("   ./helpers/generate_ssl_certs.sh letsplaydarts.eu")
            print("2. Disable SSL for development:")
            print("   Set FLASK_USE_SSL=False in .env")
            print("3. Check certificate permissions:")
            print(f"   ls -la {ssl_dir}/")
        print("=" * 80)
        raise
