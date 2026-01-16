"""SocketIO event handler registration module."""

import logging

from dartserver_core.database_models import Player
from flask import request, session

logger = logging.getLogger(__name__)


def register_events(socketio, app):
    """
    Register all SocketIO event handlers.

    Args:
        socketio: Flask-SocketIO instance
        app: Flask application instance
    """
    game_manager = app.game_manager

    @socketio.on("connect", namespace="/")
    def handle_connect():
        """Handle client connection"""
        print("Client connected")
        socketio.emit(
            "game_state",
            game_manager.get_game_state(),
            namespace="/",
            to=request.sid,
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

        db_session = game_manager.db_service.db_manager.get_session()
        try:
            player_ids = []

            for player_name in player_data:
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
                    app.logger.warning(
                        f"Player '{player_name}' not found in database. "
                        "Only registered WSO2 users can play.",
                    )
                    socketio.emit(
                        "error",
                        {
                            "message": (
                                f"Player '{player_name}' not found. "
                                "Only registered WSO2 users allowed."
                            ),
                        },
                        namespace="/",
                    )
                    return

            if not player_ids:
                player_ids = [session.get("player_id")]

            game_manager.new_game(
                game_type,
                player_ids=player_ids,
                double_out=double_out,
                reset_on_miss=reset_on_miss,
            )
        except Exception:
            app.logger.exception("Error starting new game via WebSocket")
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

    @socketio.on("end_turn_early", namespace="/")
    def handle_end_turn_early():
        """Handle end turn early request - records remaining throws as misses"""
        game_manager.end_turn_early()

    @socketio.on("manual_score", namespace="/")
    def handle_manual_score(data):
        """Handle manual score entry"""
        game_manager.process_score(data)

    @socketio.on("set_throwout_advice", namespace="/")
    def handle_set_throwout_advice(data):
        """Handle toggle of throwout advice"""
        enabled = data.get("enabled", False)
        game_manager.set_show_throwout_advice(enabled)

    @socketio.on("dartboard_test_message", namespace="/")
    def handle_dartboard_test_message(data):
        """Handle raw dartboard test messages for admin calibration"""
        socketio.emit("dartboard_test_received", data, namespace="/")

    logger.info("SocketIO event handlers registered (11 events)")


__all__ = ["register_events"]
