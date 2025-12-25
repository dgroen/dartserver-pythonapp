"""
General API endpoints (players, WSO2, training, history, user info, debug)
"""

import logging
import os
import uuid
from datetime import datetime, timezone

from flask import Blueprint
from flask import current_app as _flask_current_app
from flask import jsonify, request, session
from sqlalchemy import func

from src.core.auth import (
    get_wso2_user_info,
    login_required,
    permission_required,
    search_wso2_users,
)
from src.core.database_models import GameType, TrainingScore, TrainingSession

api_bp = Blueprint("api", __name__)
logger = logging.getLogger(__name__)

# Module-level placeholder so tests can patch `src.app.app_api.current_app`.
current_app = None


def _app():
    return current_app if current_app is not None else _flask_current_app


# ============================================================================
# Player Management Endpoints
# ============================================================================


@api_bp.route("/api/players", methods=["GET"])
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
            players = _app().game_manager.db_service.get_all_players_with_usernames()
            return jsonify({"status": "success", "players": players})
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500
    else:
        # Return current game players
        return jsonify(_app().game_manager.get_players())


@api_bp.route("/api/players", methods=["POST"])
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
        player = _app().game_manager.db_service.get_or_create_player(
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
        _app().game_manager.add_player_with_id(player_name, player.id)

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


@api_bp.route("/api/players/<int:player_id>", methods=["DELETE"])
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
    _app().game_manager.remove_player(player_id)
    # Game state is automatically emitted by _app().game_manager.remove_player()
    return jsonify({"status": "success", "message": "Player removed"})


# ============================================================================
# WSO2 User Search
# ============================================================================


@api_bp.route("/api/wso2/users/search", methods=["GET"])
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


# ============================================================================
# User Information Endpoints
# ============================================================================


@api_bp.route("/api/user/current", methods=["GET"])
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


@api_bp.route("/api/player/history", methods=["GET"])
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

        games = _app().game_manager.db_service.get_player_game_history(
            player_id=player_id,
            game_type=game_type,
            limit=limit,
        )

        return jsonify({"success": True, "games": games})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/api/player/statistics", methods=["GET"])
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

        stats = _app().game_manager.db_service.get_player_statistics(player_id=player_id)

        if stats:
            return jsonify({"success": True, "statistics": stats})
        return jsonify({"success": False, "error": "Player not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# Training Endpoints
# ============================================================================


@api_bp.route("/api/training/start", methods=["POST"])
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
        db_session = _app().game_manager.db_service.db_manager.get_session()

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
        _app().game_manager.new_game(
            game_type=game_type,
            player_ids=[{"db_id": player_id, "name": session.get("username", "Player")}],
            double_out=double_out,
        )

        # Set training mode flags in game manager
        _app().game_manager.is_training_mode = True
        _app().game_manager.training_session_id = training_session.id

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
        _app().logger.exception("Failed to start training session")
        return (
            jsonify({"success": False, "error": "Failed to start training session"}),
            500,
        )


@api_bp.route("/api/training/end", methods=["POST"])
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

        db_session = _app().game_manager.db_service.db_manager.get_session()
        training_session = (
            db_session.query(TrainingSession)
            .filter(TrainingSession.id == training_session_id)
            .first()
        )

        if training_session:
            training_session.completed = True
            training_session.finished_at = datetime.now(tz=timezone.utc)
            training_session.final_score = (
                _app().game_manager.game.get_player_score(0) if _app().game_manager.game else 0
            )
            db_session.commit()

        db_session.close()

        # Clear training mode flags
        _app().game_manager.is_training_mode = False
        _app().game_manager.training_session_id = None

        # Reset game manager
        _app().game_manager.reset_game()

        # Clear training session from session
        session.pop("training_session_id", None)

        return jsonify({"success": True, "message": "Training session ended"})
    except Exception:
        _app().logger.exception("Failed to end training session")
        return (
            jsonify({"success": False, "error": "Failed to end training session"}),
            500,
        )


@api_bp.route("/api/training/history", methods=["GET"])
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

        db_session = _app().game_manager.db_service.db_manager.get_session()
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
        _app().logger.exception("Failed to get training history")
        return (
            jsonify({"success": False, "error": "Failed to retrieve training history"}),
            500,
        )


@api_bp.route("/api/training/statistics", methods=["GET"])
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

        db_session = _app().game_manager.db_service.db_manager.get_session()

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
        _app().logger.exception("Failed to get training statistics")
        return (
            jsonify({"success": False, "error": "Failed to retrieve training statistics"}),
            500,
        )


# ============================================================================
# Game History and Replay Endpoints
# ============================================================================


@api_bp.route("/api/game/history", methods=["GET"])
@login_required
def get_game_history():
    """Get recent game history
    ---
    tags:
      - History
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
        f"get_game_history: username={user_claims.get('username')}, "
        f"preferred_username={user_claims.get('preferred_username')}, sub={user_claims.get('sub')}",
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
        games = _app().game_manager.db_service.get_recent_games(
            limit=limit,
            username=username_filter,
        )
        logger.info(f"get_game_history: Found {len(games)} games")
        return jsonify({"status": "success", "games": games})
    except Exception as e:
        logger.exception("Error getting game history")
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route("/api/game/replay/<game_session_id>", methods=["GET"])
@login_required
def get_game_replay(game_session_id):
    """Get replay data for a specific game
    ---
    tags:
      - History
    summary: Get game replay data
    description: Returns complete game data including all throws for replay/review
    parameters:
      - in: path
        name: game_session_id
        type: string
        required: true
        description: Game session ID
    responses:
      200:
        description: Game replay data
        schema:
          type: object
          properties:
            status:
              type: string
              example: success
            game_data:
              type: object
              description: Complete game data with throws
      404:
        description: Game not found
    """
    try:
        game_data = _app().game_manager.db_service.get_game_replay_data(game_session_id)

        if not game_data:
            return jsonify({"status": "error", "message": "Game not found"}), 404

        return jsonify({"status": "success", "game_data": game_data})
    except Exception as e:
        logger.exception(f"Error getting game replay for {game_session_id}")
        return jsonify({"status": "error", "message": str(e)}), 500


@api_bp.route("/api/game/current/session_id", methods=["GET"])
@login_required
def get_current_game_session_id():
    """Get the current game's session ID
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
            success:
              type: boolean
            session_id:
              type: string
              description: Current game session ID
      404:
        description: No active game
    """
    try:
        session_id = _app().game_manager.current_game_session_id

        if not session_id:
            return jsonify({"success": False, "error": "No active game"}), 404

        return jsonify({"success": True, "session_id": session_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route("/api/game/results", methods=["GET"])
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
        games = _app().game_manager.db_service.get_recent_games(limit=limit)

        # Filter by game type if specified
        if game_type:
            games = [g for g in games if g.get("game_type") == game_type]

        return jsonify({"success": True, "results": games})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============================================================================
# Debug Endpoints
# ============================================================================


@api_bp.route("/api/debug/session", methods=["GET"])
def debug_session():
    """Debug endpoint - returns session and player info
    ---
    tags:
      - Debug
    summary: Session debug
    description: Returns current Flask session keys and simple auth flags for debugging.
    responses:
      200:
        description: Session information
    """
    return jsonify(
        {
            "player_id": session.get("player_id"),
            "username": session.get("username"),
            "session_keys": list(session.keys()),
            "auth_disabled": os.getenv("AUTH_DISABLED") == "true",
        },
    )
