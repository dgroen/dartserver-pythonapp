"""Multi-Game Manager for handling multiple concurrent games."""

from typing import Dict, Optional

from game_manager import GameManager


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
            games_list.append(
                {
                    "game_id": game_id,
                    "game_type": state.get("game_type"),
                    "is_started": state.get("is_started"),
                    "is_active": game_id == self.active_game_id,
                    "player_count": len(state.get("players", [])),
                    "players": [p["name"] for p in state.get("players", [])],
                }
            )
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
