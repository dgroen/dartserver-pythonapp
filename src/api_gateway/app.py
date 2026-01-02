"""
API Gateway Service for Darts Game System
Provides secure REST API endpoints that publish to RabbitMQ
Integrates with WSO2 Identity Server for OAuth2/JWT authentication
"""

import json
import logging
import os
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import TYPE_CHECKING, Any

import jwt
import pika
import requests
import yaml
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from jwt import PyJWKClient

if TYPE_CHECKING:
    import pika.adapters.blocking_connection

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
# Enable CORS with credentials support - required for session cookies to work
CORS(app, supports_credentials=True, origins=["http://localhost:8080", "https://localhost:8080"])

# WSO2 Identity Server Configuration
WSO2_IS_URL = os.getenv("WSO2_IS_URL", "https://localhost:9443")
# Optional internal URL to use for backend-to-backend calls from inside Docker
# If provided, use it for JWKS and introspection endpoints so the container
# can reach the WSO2 service on the Docker network (e.g. https://darts-wso2is:9443)
WSO2_IS_INTERNAL_URL = os.getenv("WSO2_IS_INTERNAL_URL", WSO2_IS_URL)
WSO2_IS_JWKS_URL = f"{WSO2_IS_INTERNAL_URL}/oauth2/jwks"
WSO2_IS_INTROSPECT_URL = f"{WSO2_IS_INTERNAL_URL}/oauth2/introspect"
# Prefer the explicit internal client id, but fall back to the common
# `WSO2_CLIENT_ID` if the internal-specific variable isn't provided.
WSO2_IS_CLIENT_ID = os.getenv("WSO2_IS_CLIENT_ID", os.getenv("WSO2_CLIENT_ID", ""))
WSO2_IS_CLIENT_SECRET = os.getenv("WSO2_IS_CLIENT_SECRET", "")

# Introspection credentials (separate from client credentials)
WSO2_IS_INTROSPECT_USER = os.getenv("WSO2_IS_INTROSPECT_USER", "admin")
WSO2_IS_INTROSPECT_PASSWORD = os.getenv("WSO2_IS_INTROSPECT_PASSWORD", "admin")
WSO2_IS_VERIFY_SSL = os.getenv("WSO2_IS_VERIFY_SSL", "False").lower() == "true"

# RabbitMQ Configuration
RABBITMQ_CONFIG = {
    "host": os.getenv("RABBITMQ_HOST", "localhost"),
    "port": int(os.getenv("RABBITMQ_PORT", 5672)),
    "user": os.getenv("RABBITMQ_USER", "guest"),
    "password": os.getenv("RABBITMQ_PASSWORD", "guest"),
    "vhost": os.getenv("RABBITMQ_VHOST", "/"),
    "exchange": os.getenv("RABBITMQ_EXCHANGE", "darts_exchange"),
}

# JWT validation mode: 'jwks' or 'introspection'
JWT_VALIDATION_MODE = os.getenv("JWT_VALIDATION_MODE", "jwks")

# Initialize JWKS client for JWT validation
jwks_client = None
if JWT_VALIDATION_MODE == "jwks":
    try:
        jwks_client = PyJWKClient(WSO2_IS_JWKS_URL)
    except Exception as e:
        logger.warning(f"Failed to initialize JWKS client: {e}")


class RabbitMQPublisher:
    """RabbitMQ message publisher"""

    def __init__(self, config: dict[str, Any]):
        """Initialize RabbitMQ publisher with configuration."""
        self.config = config
        self.connection = None
        self.channel = None
        self._connect()

    def _connect(self):
        """Establish connection to RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(
                self.config["user"],
                self.config["password"],
            )
            parameters = pika.ConnectionParameters(
                host=self.config["host"],
                port=self.config["port"],
                virtual_host=self.config["vhost"],
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300,
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()  # type: ignore

            # Declare exchange
            self.channel.exchange_declare(  # type: ignore
                exchange=self.config["exchange"],
                exchange_type="topic",
                durable=True,
            )
            logger.info("Connected to RabbitMQ")
        except Exception:
            logger.exception("Failed to connect to RabbitMQ")
            raise

    def publish(self, routing_key: str, message: dict[str, Any]) -> bool:
        """Publish message to RabbitMQ"""
        try:
            # Ensure connection is alive
            if self.connection is None or self.connection.is_closed:
                self._connect()

            # Publish message
            self.channel.basic_publish(  # type: ignore
                exchange=self.config["exchange"],
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type="application/json",
                    timestamp=int(datetime.now(timezone.utc).timestamp()),
                ),
            )
            logger.info(f"Published message to {routing_key}: {message}")
            return True
        except Exception:
            logger.exception("Failed to publish message")
            # Try to reconnect
            try:
                self._connect()
            except Exception:
                logger.exception("Failed to reconnect")
            return False

    def close(self):
        """Close RabbitMQ connection"""
        try:
            if self.channel and not self.channel.is_closed:
                self.channel.close()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            logger.info("Closed RabbitMQ connection")
        except Exception:
            logger.exception("Error closing RabbitMQ connection")


# Initialize RabbitMQ publisher
rabbitmq_publisher = RabbitMQPublisher(RABBITMQ_CONFIG)


def validate_jwt_token(token: str) -> dict[str, Any] | None:
    """
    Validate JWT token using JWKS or introspection
    Returns decoded token claims if valid, None otherwise
    """
    result = None
    if JWT_VALIDATION_MODE == "jwks" and jwks_client:
        try:
            # Get signing key from JWKS
            signing_key = jwks_client.get_signing_key_from_jwt(token)

            # Decode and validate token
            decoded = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                options={"verify_exp": True},
            )
            logger.info(f"Token validated for user: {decoded.get('sub', 'unknown')}")
            result = decoded
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
        except Exception:
            logger.exception("Error validating token")
    elif JWT_VALIDATION_MODE == "introspection":
        try:
            # Use token introspection endpoint with admin credentials
            logger.info(
                f"Introspecting token at {WSO2_IS_INTROSPECT_URL} "
                f"with user {WSO2_IS_INTROSPECT_USER}",
            )
            response = requests.post(
                WSO2_IS_INTROSPECT_URL,
                auth=(WSO2_IS_INTROSPECT_USER, WSO2_IS_INTROSPECT_PASSWORD),
                data={"token": token},
                verify=WSO2_IS_VERIFY_SSL,
                timeout=10,
            )
            logger.info(
                f"Introspection response: status={response.status_code}, body={response.text}",
            )
            if response.status_code == 200:
                introspection_result = response.json()
                if introspection_result.get("active"):
                    logger.info(
                        f"Token validated via introspection for client: "
                        f"{introspection_result.get('client_id', 'unknown')}",
                    )
                    result = introspection_result
                else:
                    logger.warning(f"Token is not active: {introspection_result}")
            else:
                logger.warning(
                    f"Token introspection failed: status={response.status_code}, "
                    f"body={response.text}",
                )
        except Exception:
            logger.exception("Error during token introspection")
    else:
        logger.error("No valid JWT validation mode configured")
    return result


def require_auth(required_scopes: list | None = None):
    """
    Decorator to require authentication and authorization
    Validates JWT token and checks required scopes
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get token from Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                return (
                    jsonify(
                        {
                            "error": "Missing Authorization header",
                            "message": "Please provide a valid Bearer token",
                        },
                    ),
                    401,
                )

            # Extract token
            parts = auth_header.split()
            if len(parts) != 2 or parts[0].lower() != "bearer":
                return (
                    jsonify(
                        {
                            "error": "Invalid Authorization header",
                            "message": "Format should be: Bearer <token>",
                        },
                    ),
                    401,
                )

            token = parts[1]

            # Validate token
            claims = validate_jwt_token(token)
            if not claims:
                return (
                    jsonify(
                        {
                            "error": "Invalid or expired token",
                            "message": "Please obtain a new access token",
                        },
                    ),
                    401,
                )

            # Check required scopes
            if required_scopes:
                token_scopes = claims.get("scope", "").split()
                if not any(scope in token_scopes for scope in required_scopes):
                    return (
                        jsonify(
                            {
                                "error": "Insufficient permissions",
                                "message": f"Required scopes: {', '.join(required_scopes)}",
                            },
                        ),
                        403,
                    )

            # Add claims to request context
            request.user_claims = claims  # type: ignore

            return f(*args, **kwargs)

        return decorated_function

    return decorator


# Health check endpoint (no auth required)
@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "healthy",
            "service": "darts-api-gateway",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# OpenAPI specification endpoint (no auth required)
@app.route("/api/v1/openapi.yaml", methods=["GET"])
def get_openapi_spec():
    """Serve OpenAPI specification"""
    try:
        spec_path = Path(__file__).parent / "openapi.yaml"
        # Read YAML and replace any internal WSO2 host placeholders so the
        # documentation served reflects the configured WSO2_IS_URL
        with spec_path.open() as fh:
            yaml_text = fh.read()

        # Common internal hostname patterns to replace
        yaml_text = yaml_text.replace("https://wso2-is:9443", WSO2_IS_URL)
        yaml_text = yaml_text.replace("https://wso2-is", WSO2_IS_URL)
        yaml_text = yaml_text.replace("wso2-is:9443", WSO2_IS_URL.replace("https://", ""))

        return Response(yaml_text, mimetype="application/x-yaml")
    except Exception:
        logger.exception("Error serving OpenAPI spec")
        return jsonify({"error": "OpenAPI spec not found"}), 404


@app.route("/api/v1/openapi.json", methods=["GET"])
def get_openapi_spec_json():
    """Serve OpenAPI specification as JSON"""
    try:
        spec_path = Path(__file__).parent / "openapi.yaml"
        with spec_path.open() as f:
            spec_dict = yaml.safe_load(f)

        # Replace any internal wso2-is occurrences in all string fields
        def _deep_replace(o):
            if isinstance(o, dict):
                for k, v in list(o.items()):
                    o[k] = _deep_replace(v)
                return o
            if isinstance(o, list):
                return [_deep_replace(i) for i in o]
            if isinstance(o, str):
                s = o.replace("https://wso2-is:9443", WSO2_IS_URL)
                s = s.replace("https://wso2-is", WSO2_IS_URL)
                s = s.replace("wso2-is:9443", WSO2_IS_URL.replace("https://", ""))
                s = s.replace("wso2-is", WSO2_IS_URL.replace("https://", ""))
                # Also replace the token URL with local proxy for Swagger UI
                s = s.replace(
                    f"{WSO2_IS_URL}/oauth2/token",
                    "http://localhost:8080/oauth2/token",
                )
                return s.replace(
                    "https://localhost:9443/oauth2/token",
                    "http://localhost:8080/oauth2/token",
                )
            return o

        spec_dict = _deep_replace(spec_dict)
        return jsonify(spec_dict)
    except Exception:
        logger.exception("Error serving OpenAPI spec as JSON")
        return jsonify({"error": "OpenAPI spec not found"}), 404


# Swagger UI (no auth required - documentation is public)
@app.route("/docs", methods=["GET"])
@app.route("/api-docs", methods=["GET"])
def swagger_ui():
    """Serve Swagger UI for API documentation"""
    html = r"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Darts API Gateway - API Documentation</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.10.0/swagger-ui.css">
        <style>
            body {
                margin: 0;
                padding: 0;
            }
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@5.10.0/swagger-ui-bundle.js"></script>
        <script src="https://unpkg.com/swagger-ui-dist@5.10.0/swagger-ui-standalone-preset.js"></script>
        <script>
            // Injected WSO2 IS URL from server-side env (placeholder)
            const WSO2_IS_URL = "__WSO2_IS_URL__";

            function deepReplace(obj, matchRe, replacement) {
                if (obj && typeof obj === 'object') {
                    for (const k of Object.keys(obj)) {
                        const v = obj[k];
                        if (typeof v === 'string') {
                            obj[k] = v.replace(matchRe, replacement);
                        } else if (typeof v === 'object') {
                            deepReplace(v, matchRe, replacement);
                        }
                    }
                }
            }

            window.onload = function() {
                // Fetch the JSON spec, replace internal wso2-is occurrences,
                // and initialize Swagger UI with the modified spec.
                fetch('/api/v1/openapi.json')
                    .then(response => response.json())
                    .then(spec => {
                        try {
                            // Replace common internal host patterns
                            const re = /https?:\/\/wso2-is(:\d+)?/g;
                            deepReplace(spec, re, WSO2_IS_URL);

                            // Also replace plain host entries (swagger 2.0)
                            if (spec.host && typeof spec.host === 'string') {
                                const hostReplacement = WSO2_IS_URL.replace(/^https?:\/\//, '');
                                spec.host = spec.host.replace(/wso2-is/g, hostReplacement);
                            }

                            const ui = SwaggerUIBundle({
                                spec: spec,
                                dom_id: '#swagger-ui',
                                deepLinking: true,
                                // Ensure the OAuth redirect URI matches the browser origin
                                oauth2RedirectUrl: window.location.origin + '/oauth2-redirect',
                                presets: [
                                    SwaggerUIBundle.presets.apis,
                                    SwaggerUIStandalonePreset
                                ],
                                plugins: [
                                    SwaggerUIBundle.plugins.DownloadUrl
                                ],
                                layout: "StandaloneLayout"
                            });
                            window.ui = ui;

                            // Pre-fill OAuth client id in the Authorize dialog
                            // (client secret is NOT exposed here)
                            try {
                                const CLIENT_ID = "__WSO2_CLIENT_ID__";
                                if (CLIENT_ID && CLIENT_ID !== "") {
                                    // initOAuth takes configuration for the auth
                                    // flow used by the UI
                                    ui.initOAuth({
                                        clientId: CLIENT_ID,
                                        appName: 'Darts API Gateway',
                                        scopeSeparator: ' ',
                                        additionalQueryStringParams: {}
                                    });
                                }
                            } catch (e) {
                                console.warn('Failed to initOAuth prefill', e);
                            }
                        } catch (err) {
                            console.error('Failed to load or rewrite OpenAPI spec', err);
                            // Fallback to loading YAML URL
                            const ui = SwaggerUIBundle({
                                url: "/api/v1/openapi.yaml",
                                dom_id: '#swagger-ui',
                                deepLinking: true,
                                // Ensure the OAuth redirect URI matches the browser origin
                                oauth2RedirectUrl: window.location.origin + '/oauth2-redirect',
                                presets: [
                                    SwaggerUIBundle.presets.apis,
                                    SwaggerUIStandalonePreset
                                ],
                                plugins: [
                                    SwaggerUIBundle.plugins.DownloadUrl
                                ],
                                layout: "StandaloneLayout"
                            });
                            window.ui = ui;
                        }
                    })
                    .catch(err => {
                        console.error('Error fetching OpenAPI JSON:', err);
                        // Fallback to YAML URL
                        const ui = SwaggerUIBundle({
                            url: "/api/v1/openapi.yaml",
                            dom_id: '#swagger-ui',
                            deepLinking: true,
                            presets: [
                                SwaggerUIBundle.presets.apis,
                                SwaggerUIStandalonePreset
                            ],
                            plugins: [
                                SwaggerUIBundle.plugins.DownloadUrl
                            ],
                            layout: "StandaloneLayout"
                        });
                        window.ui = ui;
                    });
            };
        </script>
    </body>
    </html>
    """
    # Replace placeholders with configured values safely (avoid f-string parsing issues)
    html = html.replace("__WSO2_IS_URL__", WSO2_IS_URL)
    html = html.replace("__WSO2_CLIENT_ID__", WSO2_IS_CLIENT_ID or "")
    return Response(html, mimetype="text/html")


# API v1 endpoints
@app.route("/api/v1/scores", methods=["POST"])
@require_auth(required_scopes=["score:write"])
def submit_score():  # noqa: PLR0911
    """
    Submit a score to the game system
    Publishes score to RabbitMQ for processing
    """
    try:
        data = request.json
        if not data:
            return (
                jsonify(
                    {
                        "error": "Invalid request",
                        "message": "Request body must be JSON",
                    },
                ),
                400,
            )

        # Validate required fields
        required_fields = ["score", "multiplier"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return (
                jsonify(
                    {
                        "error": "Missing required fields",
                        "message": f"Required fields: {', '.join(missing_fields)}",
                    },
                ),
                400,
            )

        # Validate score value
        score = data.get("score")
        if not isinstance(score, int) or score < 0 or score > 60:
            return (
                jsonify(
                    {
                        "error": "Invalid score",
                        "message": "Score must be an integer between 0 and 60",
                    },
                ),
                400,
            )

        # Validate multiplier
        valid_multipliers = ["SINGLE", "DOUBLE", "TRIPLE"]
        multiplier = data.get("multiplier", "SINGLE").upper()
        if multiplier not in valid_multipliers:
            return (
                jsonify(
                    {
                        "error": "Invalid multiplier",
                        "message": f"Multiplier must be one of: {', '.join(valid_multipliers)}",
                    },
                ),
                400,
            )

        # Add metadata
        message = {
            "score": score,
            "multiplier": multiplier,
            "player_id": data.get("player_id"),
            "game_id": data.get("game_id"),
            "user": request.user_claims.get("sub", "unknown"),  # type: ignore
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Publish to RabbitMQ
        routing_key = "darts.scores.api"
        success = rabbitmq_publisher.publish(routing_key, message)

        if success:
            return (
                jsonify(
                    {
                        "status": "success",
                        "message": "Score submitted successfully",
                        "data": message,
                    },
                ),
                201,
            )
        return (
            jsonify(
                {
                    "error": "Failed to submit score",
                    "message": "Unable to publish message to queue",
                },
            ),
            500,
        )

    except Exception as e:
        logger.exception("Error submitting score")
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": str(e),
                },
            ),
            500,
        )


@app.route("/api/v1/games", methods=["POST"])
@require_auth(required_scopes=["game:write"])
def create_game():
    """
    Create a new game
    Publishes game creation event to RabbitMQ
    """
    try:
        data = request.json
        if not data:
            return (
                jsonify(
                    {
                        "error": "Invalid request",
                        "message": "Request body must be JSON",
                    },
                ),
                400,
            )

        # Validate game type
        valid_game_types = ["301", "401", "501", "cricket"]
        game_type = data.get("game_type", "301")
        if game_type not in valid_game_types:
            return (
                jsonify(
                    {
                        "error": "Invalid game type",
                        "message": f"Game type must be one of: {', '.join(valid_game_types)}",
                    },
                ),
                400,
            )

        # Validate players
        players = data.get("players", [])
        if not players or len(players) < 1:
            return (
                jsonify(
                    {
                        "error": "Invalid players",
                        "message": "At least one player is required",
                    },
                ),
                400,
            )

        # Create game message
        message = {
            "action": "new_game",
            "game_type": game_type,
            "players": players,
            "double_out": data.get("double_out", False),
            "created_by": request.user_claims.get("sub", "unknown"),  # type: ignore
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Publish to RabbitMQ
        routing_key = "darts.games.create"
        success = rabbitmq_publisher.publish(routing_key, message)

        if success:
            return (
                jsonify(
                    {
                        "status": "success",
                        "message": "Game created successfully",
                        "data": message,
                    },
                ),
                201,
            )
        return (
            jsonify(
                {
                    "error": "Failed to create game",
                    "message": "Unable to publish message to queue",
                },
            ),
            500,
        )

    except Exception as e:
        logger.exception("Error creating game")
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": str(e),
                },
            ),
            500,
        )


@app.route("/api/v1/players", methods=["POST"])
@require_auth(required_scopes=["player:write"])
def add_player():
    """
    Add a player to the current game
    Publishes player addition event to RabbitMQ
    """
    try:
        data = request.json
        if not data:
            return (
                jsonify(
                    {
                        "error": "Invalid request",
                        "message": "Request body must be JSON",
                    },
                ),
                400,
            )

        # Validate player name
        player_name = data.get("name")
        if not player_name or not isinstance(player_name, str):
            return (
                jsonify(
                    {
                        "error": "Invalid player name",
                        "message": "Player name is required and must be a string",
                    },
                ),
                400,
            )

        # Create player message
        message = {
            "action": "add_player",
            "name": player_name,
            "added_by": request.user_claims.get("sub", "unknown"),  # type: ignore
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Publish to RabbitMQ
        routing_key = "darts.players.add"
        success = rabbitmq_publisher.publish(routing_key, message)

        if success:
            return (
                jsonify(
                    {
                        "status": "success",
                        "message": "Player added successfully",
                        "data": message,
                    },
                ),
                201,
            )
        return (
            jsonify(
                {
                    "error": "Failed to add player",
                    "message": "Unable to publish message to queue",
                },
            ),
            500,
        )

    except Exception as e:
        logger.exception("Error adding player")
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": str(e),
                },
            ),
            500,
        )


@app.route("/api/v1/dartboard/throw", methods=["POST"])
@require_auth(required_scopes=["dartboard:write"])
def dartboard_throw():  # noqa: PLR0911
    """
    Submit a dartboard throw (secure replacement for /api/Throw/zone)
    This endpoint requires client credentials authentication
    """
    try:
        data = request.json
        if not data:
            return (
                jsonify(
                    {
                        "error": "Invalid request",
                        "message": "Request body must be JSON",
                    },
                ),
                400,
            )

        # Validate required fields for dartboard
        required_fields = ["masterPin", "slavePin", "boardType"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return (
                jsonify(
                    {
                        "error": "Missing required fields",
                        "message": f"Required fields: {', '.join(missing_fields)}",
                    },
                ),
                400,
            )

        # Validate pin values
        master_pin = data.get("masterPin")
        slave_pin = data.get("slavePin")
        if not isinstance(master_pin, int) or not isinstance(slave_pin, int):
            return (
                jsonify(
                    {
                        "error": "Invalid pin values",
                        "message": "masterPin and slavePin must be integers",
                    },
                ),
                400,
            )

        # Validate board type
        board_type = data.get("boardType", "").strip()
        if not board_type:
            return (
                jsonify(
                    {
                        "error": "Invalid board type",
                        "message": "boardType must be a non-empty string",
                    },
                ),
                400,
            )

        # Add metadata
        message = {
            "masterPin": master_pin,
            "slavePin": slave_pin,
            "boardType": board_type,
            "client_id": request.user_claims.get("client_id", "unknown"),  # type: ignore
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        # Publish to RabbitMQ
        routing_key = "darts.dartboard.throw"
        success = rabbitmq_publisher.publish(routing_key, message)

        if success:
            return (
                jsonify(
                    {
                        "status": "success",
                        "message": "Throw submitted successfully",
                        "data": message,
                    },
                ),
                201,
            )
        return (
            jsonify(
                {
                    "error": "Failed to submit throw",
                    "message": "Unable to publish message to queue",
                },
            ),
            500,
        )

    except Exception as e:
        logger.exception("Error submitting dartboard throw")
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": str(e),
                },
            ),
            500,
        )


@app.route("/api/v1/game/actions/end-turn", methods=["POST"])
@require_auth(required_scopes=["game:control"])
def end_turn():
    """
    End the current player's turn early
    Publishes turn end event to RabbitMQ
    """
    try:
        data = request.json or {}
        game_id = data.get("game_id")

        message = {
            "action": "end_turn",
            "game_id": game_id,
            "user": request.user_claims.get("sub", "unknown"),  # type: ignore
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        routing_key = "darts.game.action"
        success = rabbitmq_publisher.publish(routing_key, message)

        if success:
            return (
                jsonify(
                    {
                        "status": "success",
                        "message": "Turn ended successfully",
                        "data": message,
                    },
                ),
                200,
            )
        return (
            jsonify(
                {
                    "error": "Failed to end turn",
                    "message": "Unable to publish message to queue",
                },
            ),
            500,
        )

    except Exception as e:
        logger.exception("Error ending turn")
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": str(e),
                },
            ),
            500,
        )


@app.route("/api/v1/game/actions/continue", methods=["POST"])
@require_auth(required_scopes=["game:control"])
def continue_game():
    """
    Continue the game after a pause or prompt
    Publishes continue event to RabbitMQ
    """
    try:
        data = request.json or {}
        game_id = data.get("game_id")

        message = {
            "action": "continue",
            "game_id": game_id,
            "user": request.user_claims.get("sub", "unknown"),  # type: ignore
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        routing_key = "darts.game.action"
        success = rabbitmq_publisher.publish(routing_key, message)

        if success:
            return (
                jsonify(
                    {
                        "status": "success",
                        "message": "Game continued successfully",
                        "data": message,
                    },
                ),
                200,
            )
        return (
            jsonify(
                {
                    "error": "Failed to continue game",
                    "message": "Unable to publish message to queue",
                },
            ),
            500,
        )

    except Exception as e:
        logger.exception("Error continuing game")
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": str(e),
                },
            ),
            500,
        )


@app.route("/api/v1/game/actions/pause", methods=["POST"])
@require_auth(required_scopes=["game:control"])
def pause_game():
    """
    Pause the current game
    Publishes pause event to RabbitMQ
    """
    try:
        data = request.json or {}
        game_id = data.get("game_id")

        message = {
            "action": "pause",
            "game_id": game_id,
            "user": request.user_claims.get("sub", "unknown"),  # type: ignore
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        routing_key = "darts.game.action"
        success = rabbitmq_publisher.publish(routing_key, message)

        if success:
            return (
                jsonify(
                    {
                        "status": "success",
                        "message": "Game paused successfully",
                        "data": message,
                    },
                ),
                200,
            )
        return (
            jsonify(
                {
                    "error": "Failed to pause game",
                    "message": "Unable to publish message to queue",
                },
            ),
            500,
        )

    except Exception as e:
        logger.exception("Error pausing game")
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": str(e),
                },
            ),
            500,
        )


# OAuth2 token proxy for Swagger UI
@app.route("/oauth2/token", methods=["POST", "OPTIONS"])
def oauth2_token_proxy():
    """
    Proxy OAuth2 token requests from Swagger UI.
    This allows the browser to get tokens without exposing client_secret.
    """
    # Handle CORS preflight
    if request.method == "OPTIONS":
        response = Response()
        response.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin", "*")
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response, 200

    try:
        # Log the request for debugging
        logger.info(f"OAuth2 token proxy called with form data: {request.form}")
        logger.info(f"OAuth2 token proxy called with JSON data: {request.get_json(silent=True)}")

        # Try to get parameters from both form data and JSON
        auth_code = request.form.get("code") or (request.get_json(silent=True) or {}).get("code")
        redirect_uri = request.form.get("redirect_uri") or (
            request.get_json(silent=True) or {}
        ).get("redirect_uri")
        grant_type = request.form.get("grant_type") or (request.get_json(silent=True) or {}).get(
            "grant_type",
            "authorization_code",
        )
        client_id = (
            request.form.get("client_id")
            or (request.get_json(silent=True) or {}).get("client_id")
            or WSO2_IS_CLIENT_ID
        )
        scope = request.form.get("scope") or (request.get_json(silent=True) or {}).get("scope")

        logger.info(
            f"Extracted: code={auth_code}, redirect_uri={redirect_uri}, "
            f"grant_type={grant_type}, scope={scope}",
        )

        # Build the token request data
        token_data = {
            "grant_type": grant_type,
            "client_id": client_id,
        }

        # Add grant-type specific parameters
        if grant_type == "authorization_code":
            if not auth_code:
                logger.error("Missing authorization code for authorization_code grant")
                return (
                    jsonify(
                        {
                            "error": "invalid_request",
                            "error_description": "Missing authorization code",
                        },
                    ),
                    400,
                )
            token_data["code"] = auth_code
            token_data["redirect_uri"] = redirect_uri
        elif grant_type == "client_credentials":
            # Client credentials flow - just needs scope
            if scope:
                token_data["scope"] = scope
        else:
            logger.error(f"Unsupported grant type: {grant_type}")
            return (
                jsonify(
                    {
                        "error": "unsupported_grant_type",
                        "error_description": f"Grant type {grant_type} is not supported",
                    },
                ),
                400,
            )

        # Exchange for token using backend credentials
        logger.info(
            f"Requesting token at {WSO2_IS_INTERNAL_URL}/oauth2/token with grant_type={grant_type}",
        )
        token_response = requests.post(
            f"{WSO2_IS_INTERNAL_URL}/oauth2/token",
            data=token_data,
            auth=(WSO2_IS_CLIENT_ID, WSO2_IS_CLIENT_SECRET),
            verify=WSO2_IS_VERIFY_SSL,
            timeout=10,
        )

        if token_response.status_code == 200:
            logger.info("Token exchange successful")
            response = jsonify(token_response.json())
            response.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin", "*")
            response.headers["Access-Control-Allow-Credentials"] = "true"
            return response, 200
        logger.error(
            f"Token exchange failed: {token_response.status_code} - {token_response.text}",
        )
        response = jsonify(token_response.json())
        response.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin", "*")
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response, token_response.status_code

    except Exception as e:
        logger.exception("Error in OAuth2 token proxy")
        return jsonify({"error": "server_error", "error_description": str(e)}), 500


# OAuth2 redirect handler for Swagger UI
@app.route("/oauth2-redirect")
def oauth2_redirect():
    """Serve the OAuth2 redirect handler for Swagger UI"""
    # This is the standard Swagger UI OAuth2 redirect handler
    # It captures the authorization code and passes it to Swagger UI
    html = """
    <!DOCTYPE html>
    <html lang="en-US">
    <head>
        <title>Swagger UI: OAuth2 Redirect</title>
    </head>
    <body>
        <script>
            'use strict';
            function run () {
                var oauth2 = window.opener.swaggerUIRedirectOauth2;
                var sentState = oauth2.state;
                var redirectUrl = oauth2.redirectUrl;
                var isValid, qp, arr;

                if (/code|token|error/.test(window.location.hash)) {
                    qp = window.location.hash.substring(1);
                } else {
                    qp = location.search.substring(1);
                }

                arr = qp.split("&");
                arr.forEach(function (v,i,_arr) { _arr[i] = '"' + v.replace('=', '":"') + '"';});
                qp = qp ? JSON.parse('{' + arr.join() + '}',
                        function (key, value) {
                            return key === "" ? value : decodeURIComponent(value);
                        }
                ) : {};

                isValid = qp.state === sentState;

                if ((
                  oauth2.auth.schema.get("flow") === "accessCode" ||
                  oauth2.auth.schema.get("flow") === "authorizationCode" ||
                  oauth2.auth.schema.get("flow") === "authorization_code"
                ) && !oauth2.auth.code) {
                    if (!isValid) {
                        oauth2.errCb({
                            authId: oauth2.auth.name,
                            source: "auth",
                            level: "warning",
                            message: "Authorization may be unsafe, passed state was "
                                + "changed in server. Passed state wasn't returned from auth server"
                        });
                    }

                    if (qp.code) {
                        delete oauth2.state;
                        oauth2.auth.code = qp.code;
                        oauth2.callback({auth: oauth2.auth, redirectUrl: redirectUrl});
                    } else {
                        let oauthErrorMsg;
                        if (qp.error) {
                            oauthErrorMsg = "[" + qp.error + "]: " +
                                (qp.error_description
                                    ? qp.error_description + ". "
                                    : "no accessCode received from the server. ") +
                                (qp.error_uri
                                    ? "More info: " + qp.error_uri
                                    : "");
                        }

                        oauth2.errCb({
                            authId: oauth2.auth.name,
                            source: "auth",
                            level: "error",
                            message: oauthErrorMsg
                                || "[Authorization failed]: no accessCode received from the server"
                        });
                    }
                } else {
                    oauth2.callback({
                        auth: oauth2.auth,
                        token: qp,
                        isValid: isValid,
                        redirectUrl: redirectUrl
                    });
                }
                window.close();
            }

            window.addEventListener('DOMContentLoaded', function () {
              run();
            });
        </script>
    </body>
    </html>
    """
    return Response(html, mimetype="text/html")


# Test route
@app.route("/test")
def test():
    return "Test route working"


# Error handlers
@app.errorhandler(404)
def not_found(_error):
    """Handle 404 errors"""
    return (
        jsonify(
            {
                "error": "Not found",
                "message": "The requested resource was not found",
            },
        ),
        404,
    )


@app.errorhandler(500)
def internal_error(_error):
    """Handle 500 errors"""
    return (
        jsonify(
            {
                "error": "Internal server error",
                "message": "An unexpected error occurred",
            },
        ),
        500,
    )


if __name__ == "__main__":
    # Start Flask app
    host = os.getenv("API_GATEWAY_HOST", "0.0.0.0")
    port = int(os.getenv("API_GATEWAY_PORT", 8080))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"

    logger.info(f"Starting API Gateway on {host}:{port}")
    logger.info(f"WSO2 IS URL: {WSO2_IS_URL}")
    logger.info(f"JWT Validation Mode: {JWT_VALIDATION_MODE}")
    logger.info(f"RabbitMQ Host: {RABBITMQ_CONFIG['host']}")

    try:
        app.run(host=host, port=port, debug=debug)
    finally:
        # Clean up
        rabbitmq_publisher.close()
