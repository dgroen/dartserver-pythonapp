"""Multi-Game Manager for handling multiple concurrent games."""

from typing import Dict, Optional

from dartserver_app.game_manager import GameManager


class MultiGameManager:
    """Manages multiple concurrent game sessions"""

    def __init__(self, socketio):
        """
        Initialize multi-game manager

        Args:
            socketio: SocketIO instance for emitting events
        """
        self.socketio = socketio
        self.games: Dict[str, GameManager] = {}
        self.active_game_id: Optional[str] = None

    def create_game(self, game_id: str) -> GameManager:
        """
        Create a new game session

        Args:
            game_id: Unique identifier for the game

        Returns:
            GameManager instance for the new game
        """
        if game_id in self.games:
            raise ValueError(f"Game with id '{game_id}' already exists")

        game_manager = GameManager(self.socketio)

        # If running inside a Flask request/app context, prefer the app's
        # game_manager.db_service so tests and request-scoped DB overrides
        # are respected. This avoids new GameManager instances using a
        # different DatabaseService than the test fixture-provided one.
        try:
            from flask import current_app

            app_gm = getattr(current_app, "game_manager", None)
            if app_gm is not None and getattr(app_gm, "db_service", None) is not None:
                game_manager.db_service = app_gm.db_service
        except Exception:
            # Not running in Flask app context — nothing to do
            pass
        self.games[game_id] = game_manager

        # Set as active game if it's the first game
        if self.active_game_id is None:
            self.active_game_id = game_id

        return game_manager

    def get_game(self, game_id: Optional[str] = None) -> Optional[GameManager]:
        """
        Get a game by ID, or the active game if no ID provided

        Args:
            game_id: Game ID to retrieve, or None for active game

        Returns:
            GameManager instance or None if not found
        """
        if game_id is None:
            game_id = self.active_game_id

        return self.games.get(game_id) if game_id else None

    def set_active_game(self, game_id: str) -> bool:
        """
        Set the active game

        Args:
            game_id: Game ID to set as active

        Returns:
            True if successful, False if game not found
        """
        if game_id not in self.games:
            return False

        self.active_game_id = game_id
        return True

    def delete_game(self, game_id: str) -> bool:
        """
        Delete a game session

        Args:
            game_id: Game ID to delete

        Returns:
            True if successful, False if game not found
        """
        if game_id not in self.games:
            return False

        del self.games[game_id]

        # If we deleted the active game, set a new active game
        if self.active_game_id == game_id:
            if self.games:
                self.active_game_id = next(iter(self.games.keys()))
            else:
                self.active_game_id = None

        return True

    def list_games(self) -> list:
        """
        List all game sessions with their basic info

        Returns:
            List of game info dictionaries
        """
        games_list = []
        for game_id, game_manager in self.games.items():
            state = game_manager.get_game_state()
            players = state.get("players", [])

            # Extract player information with scores
            player_info = []
            for idx, player in enumerate(players):
                player_data = {"name": player.get("name", f"Player {idx + 1}")}

                # Get score from game_data if available
                if state.get("game_data") and state["game_data"].get("players"):
                    game_players = state["game_data"]["players"]
                    if idx < len(game_players):
                        player_data["score"] = game_players[idx].get("score", 0)

                player_info.append(player_data)

            game_info = {
                "game_id": game_id,
                "game_type": state.get("game_type"),
                "is_started": state.get("is_started"),
                "is_active": game_id == self.active_game_id,
                "player_count": len(players),
                # Return players as a simple list of names for compatibility with tests
                "players": [p.get("name") for p in player_info],
            }

            # Debug logging (reduce noise in INFO logs)
            import logging

            logging.getLogger(__name__).debug(
                f"Game {game_id}: players={len(players)}, "
                f"is_active={game_id == self.active_game_id}, "
                f"player_names={[p['name'] for p in players]}"
            )

            games_list.append(game_info)
        return games_list

    def get_active_game_id(self) -> Optional[str]:
        """
        Get the ID of the currently active game

        Returns:
            Active game ID or None
        """
        return self.active_game_id

    def has_game(self, game_id: str) -> bool:
        """
        Check if a game exists

        Args:
            game_id: Game ID to check

        Returns:
            True if game exists, False otherwise
        """
        return game_id in self.games
