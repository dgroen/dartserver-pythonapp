"""Multi-Game Manager for handling multiple concurrent games."""

from typing import Dict, Optional, Tuple

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
        # Which (game, player) currently owns each physical board.
        # A board is a single physical device, so it can only be locked by one
        # player at a time system-wide -- but one game may hold several boards
        # concurrently, one per participating player. In-memory only, matching
        # `self.games`.
        self.board_locks: Dict[int, Tuple[str, int]] = {}

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
        # Let the game reach back to release its board locks when it finishes
        game_manager.game_id = game_id
        game_manager.multi_game_manager = self

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
        self.unlock_board_for_player(game_id)

        # If we deleted the active game, set a new active game
        if self.active_game_id == game_id:
            if self.games:
                self.active_game_id = next(iter(self.games.keys()))
            else:
                self.active_game_id = None

        return True

    def list_games(self) -> list:
        """
        List all active game sessions with their basic info
        Excludes finished games (games where is_finished is True)

        Returns:
            List of active game info dictionaries
        """
        games_list = []
        for game_id, game_manager in self.games.items():
            state = game_manager.get_game_state()

            # Skip finished games
            if state.get("is_finished"):
                continue

            players = state.get("players", [])

            # Prefer authoritative player list from game_data replay when present
            game_data_players = None
            if state.get("game_data") and isinstance(state["game_data"].get("players"), list):
                game_data_players = state["game_data"]["players"]

            # Build player information using game_data players if available,
            # otherwise fall back to the live `state['players']` list.
            player_info = []
            if game_data_players is not None:
                for idx, gp in enumerate(game_data_players):
                    name = gp.get("name") or gp.get("player_name") or f"Player {idx + 1}"
                    player_data = {"name": name}
                    # Score may be present on the replay player object
                    player_data["score"] = gp.get("score", 0)
                    player_info.append(player_data)
                players_for_count = game_data_players
            else:
                for idx, player in enumerate(players):
                    player_data = {"name": player.get("name", f"Player {idx + 1}")}
                    # Get score from game_data if available
                    if state.get("game_data") and state["game_data"].get("players"):
                        game_players = state["game_data"]["players"]
                        if idx < len(game_players):
                            player_data["score"] = game_players[idx].get("score", 0)
                    player_info.append(player_data)
                players_for_count = players

            game_info = {
                "game_id": game_id,
                "game_type": state.get("game_type"),
                "is_started": state.get("is_started"),
                "is_active": game_id == self.active_game_id,
                "player_count": len(players_for_count),
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

    def lock_board(self, board_id: int, game_id: str, player_id: int) -> None:
        """
        Lock a physical board to a (game, player) pair.

        Re-locking a board to the same (game, player) is a no-op, so confirming
        the same board twice is harmless.

        Args:
            board_id: Board.id of the physical board
            game_id: Game session the board is used in
            player_id: Database Player.id using the board

        Raises:
            ValueError: If the board is already locked by a different (game, player)
        """
        existing = self.board_locks.get(board_id)
        if existing is not None and existing != (game_id, player_id):
            raise ValueError(
                f"Board {board_id} is already in use by player {existing[1]} "
                f"in game '{existing[0]}'",
            )

        self.board_locks[board_id] = (game_id, player_id)

    def unlock_board_for_player(self, game_id: str, player_id: Optional[int] = None) -> int:
        """
        Release board locks held in a game.

        Args:
            game_id: Game whose locks should be released
            player_id: Only release this player's board; None releases every
                board locked by the game (used when the whole game ends)

        Returns:
            Number of locks released
        """
        to_release = [
            board_id
            for board_id, (locked_game, locked_player) in self.board_locks.items()
            if locked_game == game_id and (player_id is None or locked_player == player_id)
        ]
        for board_id in to_release:
            del self.board_locks[board_id]
        return len(to_release)

    def get_lock_for_board(self, board_id: int) -> Optional[Tuple[str, int]]:
        """
        Get the (game_id, player_id) currently holding a board.

        Returns:
            The lock tuple, or None if the board is not locked
        """
        return self.board_locks.get(board_id)

    def get_board_for_player(self, game_id: str, player_id: int) -> Optional[int]:
        """Get the Board.id a player has locked in a game, or None."""
        for board_id, lock in self.board_locks.items():
            if lock == (game_id, player_id):
                return board_id
        return None

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
