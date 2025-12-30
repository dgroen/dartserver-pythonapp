"""
Darts Game Web Application
Receives scores through RabbitMQ and manages 301 and Cricket games
Includes WSO2 IS authentication and role-based access control
"""

import logging
import os
import ssl
import sys
import threading
import time
import traceback
from pathlib import Path

import yaml
from dartserver_core import get_session
from dartserver_core.config import Config
from dartserver_core.database_models import Player
from dartserver_core.database_service import set_database_service
from dartserver_services.dartboard_service import DartboardService
from dartserver_services.rabbitmq import RabbitMQConsumer
from dotenv import load_dotenv
from eventlet import wsgi
from flasgger import Swagger
from flask import Flask, request, session
from flask_cors import CORS
from flask_socketio import SocketIO
from werkzeug.middleware.proxy_fix import ProxyFix

from src.app.multi_game_manager import MultiGameManager

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

swagger_template = None
try:
    # Prefer the centralized OpenAPI spec in docs if available so Swagger UI
    # reflects the full API surface instead of relying solely on docstrings.
    spec_path = _root_dir / "docs" / "api-spec.yaml"
    if spec_path.exists():
        with Path.open(spec_path) as fh:
            swagger_template = yaml.safe_load(fh)
        # flasgger expects 'swagger' 2.0 style when using template. If the
        # loaded YAML is an OpenAPI 3 spec it will contain an 'openapi'
        # top-level key. Flasgger may merge in a `swagger: "2.0"` field,
        # producing a spec that contains both 'swagger' and 'openapi' —
        # which breaks the Swagger UI. Remove the top-level 'openapi'
        # key to avoid that conflict while keeping the rest of the
        # spec (paths/components) available to the UI.
        if isinstance(swagger_template, dict) and "openapi" in swagger_template:
            logger.info(
                "Loaded OpenAPI 3 spec; removing top-level 'openapi' to avoid Flasgger conflict.",
            )
            swagger_template.pop("openapi", None)
            # Convert OpenAPI3 'components' -> Swagger 2.0 compatible fields
            comps = swagger_template.get("components") or {}
            schemas = comps.get("schemas")
            if schemas:
                logger.info(
                    "Converting components.schemas -> definitions for Swagger UI compatibility.",
                )
                swagger_template["definitions"] = schemas
            sec = comps.get("securitySchemes")
            if sec:
                logger.info("Converting components.securitySchemes -> securityDefinitions.")
                swagger_template["securityDefinitions"] = sec
            # Remove components to avoid mixed OpenAPI3 keys
            if "components" in swagger_template:
                swagger_template.pop("components", None)
            # Ensure top-level swagger field exists
            swagger_template.setdefault("swagger", "2.0")

            # Convert requestBody/content to Swagger 2.0 compatible parameters and
            # replace any component $ref references with definitions refs.
            def _replace_refs(obj):
                if isinstance(obj, dict):
                    for k, v in list(obj.items()):
                        if isinstance(v, str) and v.startswith("#/components/schemas/"):
                            obj[k] = v.replace("#/components/schemas/", "#/definitions/")
                        else:
                            _replace_refs(v)
                elif isinstance(obj, list):
                    for item in obj:
                        _replace_refs(item)

            paths = swagger_template.get("paths") or {}
            for _path, methods in list(paths.items()):
                if not isinstance(methods, dict):
                    continue
                for _method, op in list(methods.items()):
                    if not isinstance(op, dict):
                        continue
                    # requestBody -> parameters (body)
                    rb = op.pop("requestBody", None)
                    if rb:
                        required = rb.get("required", False)
                        content = rb.get("content", {}) or {}
                        schema = None
                        for _media, media_val in content.items():
                            if isinstance(media_val, dict) and "schema" in media_val:
                                schema = media_val["schema"]
                                break
                        if schema is not None:
                            params = op.get("parameters", [])
                            params.append(
                                {
                                    "in": "body",
                                    "name": "body",
                                    "required": required,
                                    "schema": schema,
                                },
                            )
                            op["parameters"] = params
                    # responses: move content -> schema
                    responses = op.get("responses", {})
                    for code, resp in list(responses.items()):
                        if isinstance(resp, dict):
                            content = resp.pop("content", None)
                            if content and isinstance(content, dict):
                                for _media, media_val in content.items():
                                    if isinstance(media_val, dict) and "schema" in media_val:
                                        resp["schema"] = media_val["schema"]
                                        break
                                responses[code] = resp
                    # Replace refs within operation
                    _replace_refs(op)
            # Replace refs in whole template as a final pass
            _replace_refs(swagger_template)
except Exception:
    swagger_template = None

if not swagger_template:
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
            {"name": "Game Management", "description": "Game management endpoints"},
            {"name": "Multi-Game", "description": "Multi-game session management"},
            {"name": "Players", "description": "Player management endpoints"},
            {"name": "Score", "description": "Score submission endpoints"},
            {"name": "Dartboard", "description": "Dartboard configuration and mappings"},
            {"name": "Admin", "description": "Administrative endpoints"},
            {"name": "TTS", "description": "Text-to-Speech configuration endpoints"},
            {"name": "Mobile", "description": "Mobile app API endpoints"},
            {"name": "Training", "description": "Training session endpoints"},
            {"name": "UI", "description": "User interface endpoints"},
            {"name": "History", "description": "History and replay endpoints"},
            {"name": "Debug", "description": "Debugging endpoints (no auth)"},
            {"name": "WSO2", "description": "WSO2 user and auth helpers"},
        ],
    }

swagger = Swagger(app, config=swagger_config, template=swagger_template)


# Remove any Python None values from the template to avoid rendering 'None' in
# the generated Swagger UI HTML/JS which causes client-side errors.
def _prune_none(obj):
    if isinstance(obj, dict):
        for k in list(obj.keys()):
            v = obj.get(k)
            if v is None:
                obj.pop(k, None)
            else:
                _prune_none(v)
    elif isinstance(obj, list):
        # Remove None entries from lists and recurse into remaining items
        i = 0
        while i < len(obj):
            if obj[i] is None:
                obj.pop(i)
            else:
                _prune_none(obj[i])
                i += 1


try:  # noqa: SIM105
    _prune_none(swagger_template)
except Exception:  # noqa: S110
    # If pruning fails, continue without raising; avoid breaking app startup
    pass

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

# Attach multi-game manager, games_store, and socketio to app for blueprint access
app.multi_game_manager = multi_game_manager
app.games_store = games_store
app.active_game_id = None  # Track active game ID
app.socketio = socketio  # Attach socketio for blueprint access

# Initialize global database service for dartboard endpoints
set_database_service(game_manager.db_service)

# Import and register blueprints
from src.app.app_admin import admin_bp
from src.app.app_api import api_bp
from src.app.app_auth import auth_bp
from src.app.app_games import games_bp
from src.app.app_services import services_bp
from src.app.app_ui import ui_bp

app.register_blueprint(ui_bp)
app.register_blueprint(auth_bp)
app.register_blueprint(games_bp)
app.register_blueprint(api_bp)
app.register_blueprint(services_bp)
app.register_blueprint(admin_bp)

# Initialize RabbitMQ Consumer
rabbitmq_consumer = None


def on_score_received(score_data):
    """Callback when a score is received from RabbitMQ"""
    print(f"Score received: {score_data}")
    app.game_manager.process_score(score_data)


def on_dartboard_throw_received(throw_data):
    """Callback when a dartboard throw is received from RabbitMQ"""
    print(f"[DARTBOARD_HANDLER] Dartboard throw received: {throw_data}", flush=True)
    sys.stdout.flush()

    try:
        # Extract pin data
        master_pin = throw_data.get("masterPin")
        slave_pin = throw_data.get("slavePin")
        board_type = throw_data.get("boardType", "carromco")

        if master_pin is None or slave_pin is None:
            print(f"Invalid throw data: missing pins - {throw_data}")
            return

        # Get zone mapping from database
        session = get_session()
        try:
            zone_info = DartboardService.get_zone_from_pins(
                session,
                board_type,
                master_pin,
                slave_pin,
            )

            if not zone_info:
                print(
                    f"Zone mapping not found for pins ({master_pin}, {slave_pin}) "
                    f"on board type '{board_type}'",
                )
                return

            # Convert to score format and process
            score_data = {
                "score": zone_info["base_value"],
                "multiplier": zone_info["multiplier_type"],
            }

            print(
                f"Mapped pins ({master_pin},{slave_pin}) to "
                f"{zone_info['multiplier_type']} {zone_info['base_value']} "
                f"(zone {zone_info['zone_number']})",
            )

            # Process through game manager
            app.game_manager.process_score(score_data)

        finally:
            session.close()

    except Exception as e:
        print(f"Error processing dartboard throw: {e}")
        traceback.print_exc()


# ============================================================================
# Routes have been moved to blueprint modules:
# - app_ui.py: UI/page rendering endpoints
# - app_auth.py: Authentication/authorization endpoints
# - app_games.py: Game management endpoints
# - app_api.py: General API endpoints (players, WSO2, training, history)
# - app_services.py: Service endpoints (dartboard, TTS, mobile)
# ============================================================================


@socketio.on("connect", namespace="/")
def handle_connect():
    """Handle client connection
    ---
    tags:
      - UI
    summary: WebSocket connect
    description: Emits the current `game_state` to the connecting client on socket connect.
    responses:
      200:
        description: Connection accepted (socket event)
    """
    print("Client connected")
    # Use socketio.emit to ensure the message reaches the test client
    socketio.emit(
        "game_state",
        app.game_manager.get_game_state(),
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
    db_session = app.game_manager.db_service.db_manager.get_session()
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

        app.game_manager.new_game(
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
    player_name = data.get("name", f"Player {len(app.game_manager.players) + 1}")
    app.game_manager.add_player(player_name)


@socketio.on("remove_player", namespace="/")
def handle_remove_player(data):
    """Handle remove player request"""
    player_id = data.get("player_id")
    if player_id is not None:
        app.game_manager.remove_player(player_id)


@socketio.on("next_player", namespace="/")
def handle_next_player():
    """Handle next player request"""
    app.game_manager.next_player()


@socketio.on("skip_to_player", namespace="/")
def handle_skip_to_player(data):
    """Handle skip to specific player"""
    player_id = data.get("player_id")
    if player_id is not None:
        app.game_manager.skip_to_player(player_id)


@socketio.on("end_turn_early", namespace="/")
def handle_end_turn_early():
    """Handle end turn early request - records remaining throws as misses"""
    app.game_manager.end_turn_early()


@socketio.on("manual_score", namespace="/")
def handle_manual_score(data):
    """Handle manual score entry"""
    app.game_manager.process_score(data)


@socketio.on("set_throwout_advice", namespace="/")
def handle_set_throwout_advice(data):
    """Handle toggle of throwout advice"""
    enabled = data.get("enabled", False)
    app.game_manager.set_show_throwout_advice(enabled)


@socketio.on("dartboard_test_message", namespace="/")
def handle_dartboard_test_message(data):
    """Handle raw dartboard test messages for admin calibration"""
    # Broadcast to all admin clients for real-time testing feedback
    socketio.emit("dartboard_test_received", data, namespace="/")


@socketio.on("request_active_sessions", namespace="/")
def handle_request_active_sessions():
    """Handle request for active sessions (admin feature)"""
    # In a real implementation, you would query your session store
    # For now, return empty list as placeholder
    # You can integrate with Redis, database, or Flask session backend
    socketio.emit(
        "active_sessions_update",
        {
            "sessions": [],
            "message": "Session tracking integration pending",
        },
        namespace="/",
    )


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
        "topic": os.getenv("RABBITMQ_TOPIC", "darts.#"),
    }

    def message_router(message):
        """Route messages to appropriate handlers based on routing key"""
        print(f"[MESSAGE_ROUTER] Received message: {message}", flush=True)
        sys.stdout.flush()

        # The routing key is not passed in the message body by the consumer,
        # but we can infer it from the message structure
        if "masterPin" in message and "slavePin" in message:
            # This is a dartboard throw message
            print("[MESSAGE_ROUTER] Routing to dartboard handler", flush=True)
            sys.stdout.flush()
            on_dartboard_throw_received(message)
        else:
            # This is a score message
            print("[MESSAGE_ROUTER] Routing to score handler", flush=True)
            sys.stdout.flush()
            on_score_received(message)

    def consumer_wrapper():
        """Wrapper to catch and log consumer exceptions"""
        try:
            print("Consumer thread started, calling consumer.start()...")
            rabbitmq_consumer.start()
        except Exception as e:
            print(f"FATAL: RabbitMQ consumer thread crashed: {e}")
            traceback.print_exc()

    try:
        rabbitmq_consumer = RabbitMQConsumer(rabbitmq_config, message_router)
        consumer_thread = threading.Thread(target=consumer_wrapper, daemon=True)
        consumer_thread.start()
        print("RabbitMQ consumer started")
        print(f"Listening on topic: {rabbitmq_config['topic']}")
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
