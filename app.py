"""
Darts Game Web Application
Receives scores through RabbitMQ and manages 301 and Cricket games
Includes WSO2 IS authentication and role-based access control
"""

import os
import secrets
import threading

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from flask_cors import CORS
from flask_socketio import SocketIO, emit

from auth import (
    exchange_code_for_token,
    get_authorization_url,
    get_user_info,
    login_required,
    logout_user,
    permission_required,
    role_required,
)
from game_manager import GameManager
from rabbitmq_consumer import RabbitMQConsumer

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["SESSION_COOKIE_SECURE"] = os.getenv("SESSION_COOKIE_SECURE", "False").lower() == "true"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["PERMANENT_SESSION_LIFETIME"] = 3600  # 1 hour
CORS(app)

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# Initialize Game Manager
game_manager = GameManager(socketio)

# Initialize RabbitMQ Consumer
rabbitmq_consumer = None


def on_score_received(score_data):
    """Callback when a score is received from RabbitMQ"""
    print(f"Score received: {score_data}")
    game_manager.process_score(score_data)


@app.route("/")
@login_required
def index():
    """Main game board page"""
    user_roles = getattr(request, "user_roles", [])
    user_claims = getattr(request, "user_claims", {})
    return render_template("index.html", user_roles=user_roles, user_claims=user_claims)


@app.route("/control")
@login_required
@role_required("admin", "gamemaster")
def control():
    """Game control panel - requires admin or gamemaster role"""
    user_roles = getattr(request, "user_roles", [])
    user_claims = getattr(request, "user_claims", {})
    return render_template("control.html", user_roles=user_roles, user_claims=user_claims)


@app.route("/login")
def login():
    """Login page"""
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state

    # Get authorization URL
    auth_url = get_authorization_url(state)

    error = request.args.get("error")
    return render_template("login.html", auth_url=auth_url, error=error)


@app.route("/callback")
def callback():
    """OAuth2 callback endpoint"""
    # Verify state to prevent CSRF
    state = request.args.get("state")
    if state != session.get("oauth_state"):
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


@app.route("/test-refresh")
def test_refresh():
    """Test page for automatic refresh functionality"""
    return render_template("test_refresh.html")


@app.route("/api/game/state", methods=["GET"])
@login_required
def get_game_state():
    """Get current game state - all authenticated users"""
    return jsonify(game_manager.get_game_state())


@app.route("/api/game/new", methods=["POST"])
@login_required
@permission_required("game:create")
def new_game():
    """Start a new game - requires game:create permission"""
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
    """Get all players - all authenticated users"""
    return jsonify(game_manager.get_players())


@app.route("/api/players", methods=["POST"])
@login_required
@permission_required("player:add")
def add_player():
    """Add a new player - requires player:add permission"""
    data = request.json
    player_name = data.get("name", f"Player {len(game_manager.players) + 1}")
    game_manager.add_player(player_name)
    # Game state is automatically emitted by game_manager.add_player()
    return jsonify({"status": "success", "message": "Player added"})


@app.route("/api/players/<int:player_id>", methods=["DELETE"])
@login_required
@permission_required("player:remove")
def remove_player(player_id):
    """Remove a player - requires player:remove permission"""
    game_manager.remove_player(player_id)
    # Game state is automatically emitted by game_manager.remove_player()
    return jsonify({"status": "success", "message": "Player removed"})


@app.route("/api/score", methods=["POST"])
@login_required
@permission_required("score:submit")
def submit_score():
    """Submit a score via API - requires score:submit permission"""
    data = request.json
    score = data.get("score", 0)
    multiplier = data.get("multiplier", "SINGLE")

    # Process the score
    game_manager.process_score({"score": score, "multiplier": multiplier})
    # Game state is automatically emitted by game_manager.process_score()

    return jsonify({"status": "success", "message": "Score submitted"})


# SocketIO Events
@socketio.on("connect")
def handle_connect():
    """Handle client connection"""
    print("Client connected")
    emit("game_state", game_manager.get_game_state())


@socketio.on("disconnect")
def handle_disconnect():
    """Handle client disconnection"""
    print("Client disconnected")


@socketio.on("new_game")
def handle_new_game(data):
    """Handle new game request"""
    game_type = data.get("game_type", "301")
    player_names = data.get("players", ["Player 1", "Player 2"])
    double_out = data.get("double_out", False)
    game_manager.new_game(game_type, player_names, double_out)


@socketio.on("add_player")
def handle_add_player(data):
    """Handle add player request"""
    player_name = data.get("name", f"Player {len(game_manager.players) + 1}")
    game_manager.add_player(player_name)


@socketio.on("remove_player")
def handle_remove_player(data):
    """Handle remove player request"""
    player_id = data.get("player_id")
    if player_id is not None:
        game_manager.remove_player(player_id)


@socketio.on("next_player")
def handle_next_player():
    """Handle next player request"""
    game_manager.next_player()


@socketio.on("skip_to_player")
def handle_skip_to_player(data):
    """Handle skip to specific player"""
    player_id = data.get("player_id")
    if player_id is not None:
        game_manager.skip_to_player(player_id)


@socketio.on("manual_score")
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


if __name__ == "__main__":
    # Start RabbitMQ consumer
    start_rabbitmq_consumer()

    # Start Flask app
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"

    print(f"Starting Darts Game Server on {host}:{port}")
    socketio.run(app, host=host, port=port, debug=debug)
