"""
Darts Game Web Application
Receives scores through RabbitMQ and manages 301 and Cricket games
"""

import os
import threading

from dotenv import load_dotenv
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
def index():
    """Main game board page"""
    return render_template("index.html")


@app.route("/control")
def control():
    """Game control panel"""
    return render_template("control.html")


@app.route("/test-refresh")
def test_refresh():
    """Test page for automatic refresh functionality"""
    return render_template("test_refresh.html")


@app.route("/api/game/state", methods=["GET"])
def get_game_state():
    """Get current game state"""
    return jsonify(game_manager.get_game_state())


@app.route("/api/game/new", methods=["POST"])
def new_game():
    """Start a new game"""
    data = request.json
    game_type = data.get("game_type", "301")
    player_names = data.get("players", ["Player 1", "Player 2"])
    double_out = data.get("double_out", False)

    game_manager.new_game(game_type, player_names, double_out)
    # Game state is automatically emitted by game_manager.new_game()
    return jsonify({"status": "success", "message": "New game started"})


@app.route("/api/players", methods=["GET"])
def get_players():
    """Get all players"""
    return jsonify(game_manager.get_players())


@app.route("/api/players", methods=["POST"])
def add_player():
    """Add a new player"""
    data = request.json
    player_name = data.get("name", f"Player {len(game_manager.players) + 1}")
    game_manager.add_player(player_name)
    # Game state is automatically emitted by game_manager.add_player()
    return jsonify({"status": "success", "message": "Player added"})


@app.route("/api/players/<int:player_id>", methods=["DELETE"])
def remove_player(player_id):
    """Remove a player"""
    game_manager.remove_player(player_id)
    # Game state is automatically emitted by game_manager.remove_player()
    return jsonify({"status": "success", "message": "Player removed"})


@app.route("/api/score", methods=["POST"])
def submit_score():
    """Submit a score via API"""
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
