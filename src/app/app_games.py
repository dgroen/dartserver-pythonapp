"""
Game management endpoints (state, new, start, end, list, activate, delete, resume, types)
"""

import logging
import uuid
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, session
from flask import current_app as _flask_current_app

# Module-level placeholder so tests can patch `src.app.app_games.current_app`.
current_app = None


def _app():
    return current_app if current_app is not None else _flask_current_app


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
    return jsonify(_app().game_manager.get_game_state())


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
    multi_game_manager = _app().multi_game_manager
    games_store = _app().games_store
    game_manager = _app().game_manager

    data = request.json or {}
    game_type = data.get("game_type", "301")
    player_data = data.get("players", [])
    double_out = data.get("double_out", False)
    reset_on_miss = data.get("reset_on_miss", False)

    # Generate game_id if not provided
    game_id = f"game-{uuid.uuid4().hex[:8]}"

    # Convert player names to player objects with database IDs
    db_session = game_manager.db_service.db_manager.get_session()
    try:
        player_ids = []
        # Debug: log players currently in DB for troubleshooting tests
        try:
            all_players = db_session.query(Player).all()
            _app().logger.debug(
                "Players in DB at request: %s",
                [f"{p.name}<{p.username}>" for p in all_players],
            )
        except Exception:
            _app().logger.debug("Could not enumerate players in DB for debug")

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
                _app().logger.warning(
                    f"Player '{player_name}' not found in database. Only registered WSO2 users can play.",
                )
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": (
                                f"Player '{player_name}' not found. Only registered WSO2 users allowed."
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
        # Update the request app's game_manager to the newly created game
        _app().game_manager = new_game_manager

        # Store game metadata in games_store
        games_store[game_id] = {
            "game_id": game_id,
            "game_type": game_type,
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
            "players": player_ids,
            "double_out": double_out,
            "reset_on_miss": reset_on_miss,
        }
        _app().active_game_id = game_id

        # Game state is automatically emitted by _app().game_manager.new_game()
        return jsonify({"status": "success", "message": "New game started", "game_id": game_id})
    except Exception:
        _app().logger.exception("Error starting new game")
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
        games = _app().multi_game_manager.list_games()
        # Hide legacy default session from UI
        games = [g for g in games if g.get("game_id") != "default"]
        active_id = _app().multi_game_manager.get_active_game_id()
        if active_id == "default":
            active_id = None
        return jsonify({"status": "success", "games": games, "active_game_id": active_id})
    except Exception:
        _app().logger.exception("Error getting games list")
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
    if _app().multi_game_manager.has_game(game_id):
        return jsonify({"status": "error", "message": f"Game '{game_id}' already exists"}), 400

    # Create the game session
    try:
        new_game_manager = _app().multi_game_manager.create_game(game_id)

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
                        _app().logger.warning(
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
            _app().multi_game_manager.set_active_game(game_id)
            # Update global game_manager reference
            _app().game_manager = new_game_manager

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
        _app().logger.exception("Error creating game session")
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
    multi_game_manager = _app().multi_game_manager

    if not multi_game_manager.has_game(game_id):
        return jsonify({"status": "error", "message": f"Game '{game_id}' not found"}), 404

    multi_game_manager.set_active_game(game_id)

    game_manager = multi_game_manager.get_game(game_id)
    _app().game_manager = game_manager

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

    if not _app().multi_game_manager.has_game(game_id):
        return jsonify({"status": "error", "message": f"Game '{game_id}' not found"}), 404

    _app().multi_game_manager.delete_game(game_id)

    # Get references from current_app
    multi_game_manager = _app().multi_game_manager
    games_store = _app().games_store
    active_game = multi_game_manager.get_game()
    if active_game:
        game_manager = active_game
        _app().game_manager = game_manager

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
    game = _app().multi_game_manager.get_game(game_id)
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
    game_state = _app().game_manager.get_game_state()
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
        session = _app().game_manager.db_service.db_manager.get_session()
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

    # Minimal, test-friendly implementation reusing new_game logic
    data = request.json or {}
    # Delegate to the same flow as new_game but return mobile-friendly response
    # Reuse multi_game_manager and games_store
    multi_game_manager = _app().multi_game_manager
    games_store = _app().games_store

    # Use the same player conversion logic as new_game
    game_type = data.get("game_type", "301")
    player_data = data.get("players", [])
    double_out = data.get("double_out", False)
    reset_on_miss = data.get("reset_on_miss", False)
    show_throwout_advice = data.get("show_throwout_advice", False)
    game_id = data.get("game_id") or f"game-{uuid.uuid4().hex[:8]}"

    game_manager = _app().game_manager
    db_session = game_manager.db_service.db_manager.get_session()
    try:
        player_ids = []
        for player_name in player_data:
            player = (
                db_session.query(Player)
                .filter((Player.name == player_name) | (Player.username == player_name))
                .first()
            )
            if player:
                player_ids.append({"db_id": player.id, "name": player.name})
            else:
                _app().logger.warning("Player '%s' not found in DB", player_name)
                return (
                    jsonify({"success": False, "message": f"Player '{player_name}' not found."}),
                    400,
                )

        if not player_ids:
            player_ids = [session.get("player_id")]

        new_game_manager = multi_game_manager.create_game(game_id)
        new_game_manager.new_game(
            game_type,
            player_ids=player_ids,
            double_out=double_out,
            reset_on_miss=reset_on_miss,
        )
        multi_game_manager.set_active_game(game_id)
        _app().game_manager = new_game_manager

        games_store[game_id] = {
            "game_id": game_id,
            "game_type": game_type,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "players": player_ids,
            "double_out": double_out,
            "reset_on_miss": reset_on_miss,
        }
        _app().active_game_id = game_id

        if show_throwout_advice:
            _app().game_manager.set_show_throwout_advice(True)

        game_state = _app().game_manager.get_game_state()
        return jsonify(
            {
                "success": True,
                "message": "Game started successfully",
                "game": game_state,
                "game_id": game_id,
            },
        )
    except Exception:
        _app().logger.exception("Error starting game")
        return (
            jsonify({"success": False, "message": "An error occurred while starting the game."}),
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
                        "error": f"Training mode '{game_type}' requires gamemaster or admin role",
                    },
                ),
                403,
            )

        # Get player name from session
        user_info = session.get("user_info", {})
        player_name = user_info.get("name") or user_info.get("username") or "Player"

        # Start single-player game with current user
        player_ids = [{"db_id": player_id, "name": player_name}]

        # Create a new game session and start
        multi_game_manager = _app().multi_game_manager
        game_id = f"game-{uuid.uuid4().hex[:8]}"
        new_game_manager = multi_game_manager.create_game(game_id)
        new_game_manager.new_game(
            game_type=game_type,
            player_ids=player_ids,
            double_out=double_out,
            reset_on_miss=reset_on_miss,
        )
        multi_game_manager.set_active_game(game_id)
        _app().game_manager = new_game_manager

        game_state = _app().game_manager.get_game_state()

        return jsonify(
            {
                "success": True,
                "message": f"Single-player {game_type} game started",
                "game": game_state,
            },
        )
    except Exception as e:
        _app().logger.exception("Failed to start single-player game")
        return (jsonify({"success": False, "error": str(e)}), 500)


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

    try:
        _app().game_manager.reset_game()
        return jsonify({"success": True, "message": "Game ended successfully"})
    except Exception:
        _app().logger.exception("Failed to end game")
        return jsonify({"success": False, "message": "Failed to end game"}), 500


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
    try:
        # Check if game exists first
        game_data = _app().game_manager.db_service.get_game_replay_data(game_session_id)
        if not game_data:
            return jsonify({"status": "error", "message": "Game not found"}), 404

        # Check if game is completed
        if game_data.get("finished_at"):
            return jsonify({"status": "error", "message": "Cannot delete a completed game"}), 403

        # Check if game is too recent (created within the last day)
        created_at = game_data.get("started_at") or game_data.get("created_at")
        if created_at:
            try:
                from datetime import datetime, timezone

                created_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                if created_time.tzinfo is None:
                    created_time = created_time.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                if (now - created_time).total_seconds() < 24 * 60 * 60:  # Less than 1 day
                    return (
                        jsonify(
                            {
                                "status": "error",
                                "message": "Cannot delete game created within the last 24 hours",
                            },
                        ),
                        403,
                    )
            except (ValueError, TypeError):
                # If we can't parse the date, allow deletion
                pass

        # Delegate deletion to the game_manager's db_service if available
        success = _app().game_manager.db_service.delete_game(game_session_id)
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

    # Use _app() so tests can patch module-level current_app
    try:
        multi_game_manager = _app().multi_game_manager
        games_store = _app().games_store

        game_data = _app().game_manager.db_service.get_game_replay_data(game_session_id)
        if not game_data:
            return jsonify({"status": "error", "message": "Game not found"}), 404

        if game_data.get("finished_at"):
            return jsonify({"status": "error", "message": "Cannot resume a completed game"}), 403

        game_id = game_session_id
        new_game_manager = multi_game_manager.create_game(game_id)
        success = new_game_manager.resume_game_from_replay_data(game_data)
        if not success:
            return jsonify({"status": "error", "message": "Failed to resume game"}), 500

        games_store[game_id] = {
            "game_id": game_id,
            "game_type": game_data.get("game_type", "301"),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "players": game_data.get("players", []),
            "double_out": game_data.get("double_out_enabled", game_data.get("double_out", False)),
            "reset_on_miss": game_data.get("reset_on_miss", False),
            "resumed_from": game_session_id,
        }

        multi_game_manager.set_active_game(game_id)
        _app().game_manager = new_game_manager
        _app().active_game_id = game_id

        # Update builtins for test compatibility
        import builtins

        builtins.game_manager = new_game_manager

        _app().socketio.emit("game_state", new_game_manager.get_game_state(), namespace="/")

        return jsonify(
            {
                "status": "success",
                "message": f"Game resumed with {len(game_data.get('throws', []))} throws replayed",
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
    try:
        games = _app().game_manager.db_service.get_active_games()
        return jsonify({"success": True, "games": games})
    except Exception as e:
        _app().logger.exception("Error fetching active games")
        return jsonify({"success": False, "error": str(e)}), 500
