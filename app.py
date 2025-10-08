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
from flask_socketio import SocketIO

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
        {"name": "TTS", "description": "Text-to-Speech configuration endpoints"},
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


if __name__ == "__main__":
    # Start RabbitMQ consumer
    start_rabbitmq_consumer()

    # Start Flask app
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"

    print(f"Starting Darts Game Server on {host}:{port}")
    socketio.run(app, host=host, port=port, debug=debug)
