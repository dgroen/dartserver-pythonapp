"""
Darts Game Web Application
Receives scores through RabbitMQ and manages 301 and Cricket games
Includes WSO2 IS authentication and role-based access control
"""

import logging
import os
import secrets
import threading
from pathlib import Path

from dotenv import load_dotenv
from flasgger import Swagger
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_cors import CORS
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix

from src.app.game_manager import GameManager
from src.app.mobile_service import MobileService
from src.core.auth import (
    exchange_code_for_token,
    get_authorization_url,
    get_user_info,
    login_required,
    logout_user,
    permission_required,
    role_required,
)
from src.core.config import Config
from src.core.rabbitmq_consumer import RabbitMQConsumer

# Load environment variables
load_dotenv()

# Configure logging to output to stdout for Docker
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

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
app.wsgi_app = ProxyFix(
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
_dsas = os.getenv("DARTBOARD_SENDS_ACTUAL_SCORE", "false")
app.config["DARTBOARD_SENDS_ACTUAL_SCORE"] = _dsas.lower() == "true"
CORS(app)

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
        "description": "API for managing darts games (301, 401, 501, Cricket) \
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
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# Initialize Game Manager
game_manager = GameManager(socketio)
app.game_manager = game_manager  # Attach to app for access in decorators

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


@app.route("/login")
def login():
    """Login page"""
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state
    session.permanent = True  # Make session persistent across requests

    # Debug logging
    app.logger.info(f"Login - Generated state: {state}")
    app.logger.info(f"Login - Session ID: {session.get('_id', 'No session ID')}")

    # Get authorization URL
    auth_url = get_authorization_url(state)

    error = request.args.get("error")
    return render_template("login.html", auth_url=auth_url, error=error)


@app.route("/callback")
def callback():
    """OAuth2 callback endpoint"""
    # Verify state to prevent CSRF
    state = request.args.get("state")
    stored_state = session.get("oauth_state")

    # Debug logging
    app.logger.info(f"Callback received - State from request: {state}")
    app.logger.info(f"Callback received - State from session: {stored_state}")
    app.logger.info(f"Session ID: {session.get('_id', 'No session ID')}")

    if state != stored_state:
        app.logger.error(f"State mismatch! Request: {state}, Session: {stored_state}")
        return redirect(url_for("login", error="Invalid state parameter"))

    # Get authorization code
    code = request.args.get("code")
    if not code:
        error = request.args.get("error", "Authorization failed")
        return redirect(url_for("login", error=error))

    # Exchange code for token
    token_response = exchange_code_for_token(code)
    if not token_response:
        return redirect(url_for("login", error="Failed to obtain access token"))

    # Store tokens in session
    session["access_token"] = token_response.get("access_token")
    session["refresh_token"] = token_response.get("refresh_token")
    session["id_token"] = token_response.get("id_token")

    # Get user info
    user_info = get_user_info(session["access_token"])
    if user_info:
        session["user_info"] = user_info

        # Auto-add user to game lobby by creating/getting player in database
        try:
            username = user_info.get("preferred_username") or user_info.get("sub")
            email = user_info.get("email")
            name = user_info.get("name") or user_info.get("given_name", username)

            if username:
                player = game_manager.db_service.get_or_create_player(
                    username=username,
                    email=email,
                    name=name,
                )
                if player:
                    session["player_id"] = player.id
                    app.logger.info(f"Player created/retrieved: {username} (ID: {player.id})")
        except Exception as e:
            app.logger.warning(f"Failed to create/get player in callback: {e}")

    # Clear OAuth state
    session.pop("oauth_state", None)

    # Redirect to original destination or home
    next_url = request.args.get("next") or url_for("index")
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
    from src.core.auth import get_user_groups_from_scim2, get_user_roles, validate_token

    access_token = session.get("access_token")
    user_info = session.get("user_info", {})

    # Validate token and get claims
    token_claims = validate_token(access_token) if access_token else {}

    # Extract roles
    extracted_roles = get_user_roles(token_claims, access_token=access_token)

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
              description: Type of game (301, 401, 501, cricket)
              enum: ['301', '401', '501', 'cricket']
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
              enum: ['301', '401', '501', 'cricket']
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
    """
    data = request.json
    game_type = data.get("game_type", "301")
    player_names = data.get("players", ["Player 1", "Player 2"])
    double_out = data.get("double_out", False)

    game_manager.new_game(game_type, player_names, double_out)
    # Game state is automatically emitted by game_manager.new_game()
    return jsonify({"status": "success", "message": "New game started"})


@app.route("/api/players", methods=["GET"])
@login_required
def get_players():
    """Get all players - all authenticated users
    ---
    tags:
      - Players
    summary: Get all players
    description: Returns a list of all players in the current game
    responses:
      200:
        description: List of players
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
                description: Player ID
                example: 0
              name:
                type: string
                description: Player name
                example: Alice
    """
    return jsonify(game_manager.get_players())


@app.route("/api/players", methods=["POST"])
@login_required
@permission_required("player:add")
def add_player():
    """Add a new player - requires player:add permission
    ---
    tags:
      - Players
    summary: Add a new player
    description: Adds a new player to the current game
    parameters:
      - in: body
        name: body
        description: Player information
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              description: Player name
              example: Charlie
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
    """
    data = request.json
    player_name = data.get("name", f"Player {len(game_manager.players) + 1}")
    game_manager.add_player(player_name)
    # Game state is automatically emitted by game_manager.add_player()
    return jsonify({"status": "success", "message": "Player added"})


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


@app.route("/api/Throw", methods=["POST"])
# @login_required
# @permission_required("score:submit")
def submit_score():
    """Submit a score via API - requires score:submit permission
    ---
    tags:
      - Score
    summary: Submit a dart score
    description: Submits a dart throw score for the current player
    parameters:
      - in: body
        name: body
        description: Score information
        required: true
        schema:
          type: object
          required:
            - score
            - multiplier
          properties:
            score:
              type: integer
              description: Base score value (0-20 for regular segments, 25 for bull)
              example: 20
              minimum: 0
              maximum: 25
            multiplier:
              type: string
              description: Score multiplier type
              enum: ['SINGLE', 'DOUBLE', 'TRIPLE', 'BULL', 'DBLBULL']
              example: TRIPLE
            user:
              type: string
              description: Optional player name (for future use)
              example: Alice
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
    """
    data = request.json
    score = data.get("score", 0)
    multiplier = data.get("multiplier", "SINGLE")

    # Process the score
    game_manager.process_score({"score": score, "multiplier": multiplier})
    # Game state is automatically emitted by game_manager.process_score()

    return jsonify({"status": "success", "message": "Score submitted"})


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
    from flask import Response

    data = request.json
    text = data.get("text")
    lang = data.get("lang", "en")

    if not text:
        return jsonify({"status": "error", "message": "Text is required"}), 400

    audio_data = game_manager.tts.generate_audio_data(text, lang)

    if audio_data:
        return Response(audio_data, mimetype="audio/mpeg")
    return jsonify({"status": "error", "message": "Failed to generate audio"}), 500


# SocketIO Events
@app.route("/api/game/history", methods=["GET"])
def get_game_history():
    """Get recent game history
    ---
    tags:
      - Game
    summary: Get recent game history
    description: Returns a list of recent games with basic information
    parameters:
      - in: query
        name: limit
        type: integer
        description: Maximum number of games to return
        default: 10
        example: 10
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
    try:
        games = game_manager.db_service.get_recent_games(limit=limit)
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
    from functools import wraps

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
        request.player_info = player_info
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
    player_id = session.get("user_id", 1)  # TODO: Get from actual session
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
    player_id = session.get("user_id", 1)  # TODO: Get from actual session

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
    player_id = session.get("user_id", 1)  # TODO: Get from actual session
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
    player_id = session.get("user_id", 1)  # TODO: Get from actual session
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
    player_id = session.get("user_id", 1)  # TODO: Get from actual session

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
    player_id = session.get("user_id", 1)  # TODO: Get from actual session
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
    player_id = session.get("user_id", 1)  # TODO: Get from actual session
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
    player_id = session.get("user_id", 1)  # TODO: Get from actual session

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
    player_id = session.get("user_id", 1)  # TODO: Get from actual session

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
    description: Returns the complete current state including players,
    scores, and game type (mobile-friendly endpoint)
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


@app.route("/api/game/start", methods=["POST"])
@login_required
@permission_required("game:create")
def start_game():
    """Start a new game (mobile alias)
    ---
    tags:
      - Mobile
    summary: Start a new game
    description: Initializes a new darts game with specified type and
    players (mobile-friendly endpoint)
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
              enum: ['301', '401', '501', 'cricket']
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
    """
    data = request.json
    game_type = data.get("game_type", "301")
    player_names = data.get("players", ["Player 1", "Player 2"])
    double_out = data.get("double_out", False)

    game_manager.new_game(game_type, player_names, double_out)
    game_state = game_manager.get_game_state()

    return jsonify(
        {
            "success": True,
            "message": "Game started successfully",
            "game": game_state,
        },
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


@app.route("/api/game/results", methods=["GET"])
@login_required
def get_game_results():
    """Get game results (mobile alias)
    ---
    tags:
      - Mobile
    summary: Get game results
    description: Returns a list of recent games with results (mobile-friendly endpoint)
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


@socketio.on("connect", namespace="/")
def handle_connect():
    """Handle client connection"""
    print("Client connected")
    # Use socketio.emit to ensure the message reaches the test client
    socketio.emit("game_state", game_manager.get_game_state(), namespace="/", to=request.sid)


@socketio.on("disconnect", namespace="/")
def handle_disconnect():
    """Handle client disconnection"""
    print("Client disconnected")


@socketio.on("new_game", namespace="/")
def handle_new_game(data):
    """Handle new game request"""
    game_type = data.get("game_type", "301")
    player_names = data.get("players", ["Player 1", "Player 2"])
    double_out = data.get("double_out", False)
    game_manager.new_game(game_type, player_names, double_out)


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


@socketio.on("manual_score", namespace="/")
def handle_manual_score(data):
    """Handle manual score entry"""
    game_manager.process_score(data)


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
    import ssl
    import time

    from eventlet import wsgi

    # Store original handler
    original_handle = wsgi.HttpProtocol.handle

    # Rate limiting state
    ssl_error_state = {"count": 0, "last_logged": 0}

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
                        f"   {ssl_error_state['count']} HTTP request(s) "
                        "to HTTPS server (rejected)",
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
