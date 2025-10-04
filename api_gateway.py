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
from typing import Any

import jwt
import pika
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from jwt import PyJWKClient

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
CORS(app)

# WSO2 Identity Server Configuration
WSO2_IS_URL = os.getenv("WSO2_IS_URL", "https://localhost:9443")
WSO2_IS_JWKS_URL = f"{WSO2_IS_URL}/oauth2/jwks"
WSO2_IS_INTROSPECT_URL = f"{WSO2_IS_URL}/oauth2/introspect"
WSO2_IS_CLIENT_ID = os.getenv("WSO2_IS_CLIENT_ID", "")
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
            self.channel = self.connection.channel()

            # Declare exchange
            self.channel.exchange_declare(
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
            self.channel.basic_publish(
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
            request.user_claims = claims

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


# API v1 endpoints
@app.route("/api/v1/scores", methods=["POST"])
@require_auth(required_scopes=["score:write"])
def submit_score():
    """
    Submit a score to the game system
    Publishes score to RabbitMQ for processing
    """
    try:
        data = request.json
        error_response = None

        if not data:
            error_response = jsonify(
                {
                    "error": "Invalid request",
                    "message": "Request body must be JSON",
                },
            )

        # Validate required fields
        if not error_response:
            required_fields = ["score", "multiplier"]
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                error_response = jsonify(
                    {
                        "error": "Missing required fields",
                        "message": f"Required fields: {', '.join(missing_fields)}",
                    },
                )

        # Validate score value
        if not error_response:
            score = data.get("score")
            if not isinstance(score, int) or score < 0 or score > 60:
                error_response = jsonify(
                    {
                        "error": "Invalid score",
                        "message": "Score must be an integer between 0 and 60",
                    },
                )

        # Validate multiplier
        if not error_response:
            valid_multipliers = ["SINGLE", "DOUBLE", "TRIPLE"]
            multiplier = data.get("multiplier", "SINGLE").upper()
            if multiplier not in valid_multipliers:
                error_response = jsonify(
                    {
                        "error": "Invalid multiplier",
                        "message": f"Multiplier must be one of: {', '.join(valid_multipliers)}",
                    },
                )

        if error_response:
            return error_response, 400

        # Add metadata
        message = {
            "score": score,
            "multiplier": multiplier,
            "player_id": data.get("player_id"),
            "game_id": data.get("game_id"),
            "user": request.user_claims.get("sub", "unknown"),
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
            "created_by": request.user_claims.get("sub", "unknown"),
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
            "added_by": request.user_claims.get("sub", "unknown"),
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
