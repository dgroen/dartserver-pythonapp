"""
Game management endpoints (state, new, start, end, list, activate, delete, resume, types)
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone

from flask import Blueprint, current_app, jsonify, request, session

from src.core.auth import login_required, permission_required
from src.core.database_models import GameType, Player

games_bp = Blueprint("games", __name__)
logger = logging.getLogger(__name__)


@games_bp.route("/api/game/state", methods=["GET"])
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
    game_manager = current_app.game_manager
    return jsonify(current_app.game_manager.get_game_state())


@games_bp.route("/api/game/new", methods=["POST"])
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

    # Get references from current_app
    multi_game_manager = current_app.multi_game_manager
    games_store = current_app.games_store

    data = request.json
    game_type = data.get("game_type", "301")
    player_data = data.get("players", [])
    double_out = data.get("double_out", False)
    reset_on_miss = data.get("reset_on_miss", False)

    # Generate game_id if not provided
    game_id = f"game-{uuid.uuid4().hex[:8]}"

    # Convert player names to player objects with database IDs
    # Use the request-bound app's game_manager to ensure tests' patched
    # DatabaseService is respected (avoid stale module-level globals).
    db_session = current_app.game_manager.db_service.db_manager.get_session()
    try:
        player_ids = []
        # Debug: log players currently in DB for troubleshooting tests
        try:
            all_players = db_session.query(Player).all()
            current_app.logger.debug(
                "Players in DB at request: %s",
                [f"{p.name}<{p.username}>" for p in all_players],
            )
        except Exception:
            current_app.logger.debug("Could not enumerate players in DB for debug")

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
                current_app.logger.warning(
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
        current_app.game_manager = new_game_manager
        current_app.game_manager = game_manager

        # Store game metadata in games_store
        games_store[game_id] = {
            "game_id": game_id,
            "game_type": game_type,
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
            "players": player_ids,
            "double_out": double_out,
            "reset_on_miss": reset_on_miss,
        }
        current_app.active_game_id = game_id

        # Game state is automatically emitted by current_app.game_manager.new_game()
        return jsonify({"status": "success", "message": "New game started", "game_id": game_id})
    except Exception:
        current_app.logger.exception("Error starting new game")
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


@games_bp.route("/api/games", methods=["GET"])
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
        games = current_app.multi_game_manager.list_games()
        # Hide legacy default session from UI
        games = [g for g in games if g.get("game_id") != "default"]
        active_id = current_app.multi_game_manager.get_active_game_id()
        if active_id == "default":
            active_id = None
        return jsonify({"status": "success", "games": games, "active_game_id": active_id})
    except Exception:
        current_app.logger.exception("Error getting games list")
        return jsonify({"status": "error", "message": "Failed to list games"}), 500


@games_bp.route("/api/games/create", methods=["POST"])
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
              description: Unique identifier for the game (optional, \
                will be auto-generated if not provided)
              example: game-1
            game_type:
              type: string
              description: Type of game to start
              enum: ['301', '401', '501', 'cricket', 'round_the_clock', \
                'round_the_clock_double']
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
    if current_app.multi_game_manager.has_game(game_id):
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
                        current_app.logger.warning(
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
            current_app.game_manager = new_game_manager

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
        current_app.logger.exception("Error creating game session")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "An error occurred while creating the game. Please try again.",
                },
            ),
            500,
        )


@games_bp.route("/api/games/<game_id>/activate", methods=["POST"])
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
    # Get references from current_app
    multi_game_manager = current_app.multi_game_manager
    
    if not multi_game_manager.has_game(game_id):
        return jsonify({"status": "error", "message": f"Game '{game_id}' not found"}), 404

    multi_game_manager.set_active_game(game_id)
    
    game_manager = multi_game_manager.get_game(game_id)
    current_app.game_manager = game_manager

    return jsonify(
        {
            "status": "success",
            "message": "Game activated",
            "game_id": game_id,
        },
    )


@games_bp.route("/api/games/<game_id>", methods=["DELETE"])
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


    # Get references from current_app
    multi_game_manager = current_app.multi_game_manager
    games_store = current_app.games_store
    active_game = multi_game_manager.get_game()
    if active_game:
        game_manager = active_game
        current_app.game_manager = game_manager

    return jsonify(
        {
            "status": "success",
            "message": "Game session deleted",
        },
    )


@games_bp.route("/api/games/<game_id>/state", methods=["GET"])
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
    game = current_app.multi_game_manager.get_game(game_id)
    if not game:
        return jsonify({"status": "error", "message": f"Game '{game_id}' not found"}), 404

    return jsonify(game.get_game_state())


@games_bp.route("/api/game/current", methods=["GET"])
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
    game_state = current_app.game_manager.get_game_state()
    return jsonify({"success": True, "game": game_state})


@games_bp.route("/api/game/types", methods=["GET"])
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
        session = current_app.game_manager.db_service.db_manager.get_session()
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


@games_bp.route("/api/game/start", methods=["POST"])
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

    # Get references from current_app
    multi_game_manager = current_app.multi_game_manager
    games_store = current_app.games_store

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
    db_session = current_app.game_manager.db_service.db_manager.get_session()
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
                current_app.logger.warning(
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
        current_app.game_manager = new_game_manager
        current_app.game_manager = game_manager

        # Store game metadata in games_store
        games_store[game_id] = {
            "game_id": game_id,
            "game_type": game_type,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "players": player_ids,
            "double_out": double_out,
            "reset_on_miss": reset_on_miss,
        }
        current_app.active_game_id = game_id

        # Set throwout advice if requested on the newly active session
        if show_throwout_advice:
            current_app.game_manager.set_show_throwout_advice(True)

        game_state = current_app.game_manager.get_game_state()

        return jsonify(
            {
                "success": True,
                "message": "Game started successfully",
                "game": game_state,
                "game_id": game_id,
            },
        )
    except Exception:
        current_app.logger.exception("Error starting game")
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


@games_bp.route("/api/mobile/game/start-single-player", methods=["POST"])
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

        current_app.game_manager.new_game(
            game_type=game_type,
            player_ids=player_ids,
            double_out=double_out,
            reset_on_miss=reset_on_miss,
        )

        game_state = current_app.game_manager.get_game_state()

        return jsonify(
            {
                "success": True,
                "message": f"Single-player {game_type} game started",
                "game": game_state,
            },
        )
    except Exception as e:
        current_app.logger.exception("Failed to start single-player game")
        return (
            jsonify({"success": False, "error": str(e)}),
            500,
        )


@games_bp.route("/api/game/end", methods=["POST"])
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
    current_app.game_manager.reset_game()

    return jsonify(
        {
            "success": True,
            "message": "Game ended successfully",
        },
    )


@games_bp.route("/api/game/<game_session_id>", methods=["DELETE"])
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
    game_manager = current_app.game_manager
    try:
        # Get the game to check if it can be deleted
        game_data = current_app.game_manager.db_service.get_game_replay_data(game_session_id)

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
        success = current_app.game_manager.db_service.delete_game(game_session_id)

        if success:
            return jsonify({"status": "success", "message": "Game deleted successfully"})

        return jsonify({"status": "error", "message": "Failed to delete game"}), 500

    except Exception as e:
        logger.exception(f"Error deleting game {game_session_id}")
        return jsonify({"status": "error", "message": str(e)}), 500


@games_bp.route("/api/game/resume/<game_session_id>", methods=["POST"])
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

    # Get references from current_app
    multi_game_manager = current_app.multi_game_manager
    games_store = current_app.games_store

    try:
        # Get the game data
        game_data = current_app.game_manager.db_service.get_game_replay_data(game_session_id)

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

        # Use the existing persisted game_session_id as the multi-game session id
        # so we load the exact saved game instead of creating a new DB session.
        game_id = game_session_id

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
            "double_out": game_data.get("double_out_enabled", game_data.get("double_out", False)),
            "reset_on_miss": game_data.get("reset_on_miss", False),
            "resumed_from": game_session_id,
        }
        # Set active and update global pointers so UI shows resumed session
        multi_game_manager.set_active_game(game_id)
        current_app.game_manager = new_game_manager
        current_app.active_game_id = game_id

        # Emit game state to all clients
        current_app.socketio.emit("game_state", new_game_manager.get_game_state(), namespace="/")

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


@games_bp.route("/api/active-games", methods=["GET"])
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
    game_manager = current_app.game_manager
    try:
        games = current_app.game_manager.db_service.get_active_games()
        return jsonify({"success": True, "games": games})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


