"""
Darts Game Web Application
Receives scores through RabbitMQ and manages 301 and Cricket games
"""

import os
import threading

from dotenv import load_dotenv
from flasgger import Swagger
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit

from game_manager import GameManager
from rabbitmq_consumer import RabbitMQConsumer

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
_dsas = os.getenv("DARTBOARD_SENDS_ACTUAL_SCORE", "false")
app.config["DARTBOARD_SENDS_ACTUAL_SCORE"] = _dsas.lower() == "true"
CORS(app)

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
    "host": os.getenv("SWAGGER_HOST", "localhost:5000"),
    "basePath": "/",
    "schemes": ["http", "https"],
    "tags": [
        {"name": "Game", "description": "Game management endpoints"},
        {"name": "Players", "description": "Player management endpoints"},
        {"name": "Score", "description": "Score submission endpoints"},
        {"name": "UI", "description": "User interface endpoints"},
    ],
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

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
    return render_template("index.html")


@app.route("/control")
def control():
    """Game control panel
    ---
    tags:
      - UI
    summary: Game control panel
    description: Renders the control panel interface for managing the game
    responses:
      200:
        description: HTML page rendered successfully
    """
    return render_template("control.html")


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
def get_game_state():
    """Get current game state
    ---
    tags:
      - Game
    summary: Get current game state
    description: Returns the complete current state of the game including players,
    scores, and game type
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
def new_game():
    """Start a new game
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
def get_players():
    """Get all players
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
def add_player():
    """Add a new player
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
def remove_player(player_id):
    """Remove a player
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
def submit_score():
    """Submit a score via API
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
