"""Game Session Manager for handling multiple concurrent games."""

import secrets
from typing import Dict, Optional


class GameSessionManager:
    """Manages multiple concurrent game sessions"""

    def __init__(self, socketio):
        """
        Initialize game session manager

        Args:
            socketio: SocketIO instance for emitting events
        """
        self.socketio = socketio
        self.sessions: Dict[str, "GameManager"] = {}  # session_id -> GameManager

    def create_session(self, creator_id: Optional[str] = None) -> str:
        """
        Create a new game session

        Args:
            creator_id: Optional creator/game master ID

        Returns:
            session_id: Unique session identifier
        """
        from src.app.game_manager import GameManager

        # Generate unique session ID
        session_id = secrets.token_urlsafe(16)
        while session_id in self.sessions:
            session_id = secrets.token_urlsafe(16)

        # Create new GameManager for this session
        game_manager = GameManager(self.socketio)
        game_manager.session_id = session_id
        game_manager.creator_id = creator_id

        self.sessions[session_id] = game_manager

        print(f"Created new game session: {session_id} (creator: {creator_id})")
        return session_id

    def get_session(self, session_id: str) -> Optional["GameManager"]:
        """
        Get a game session by ID

        Args:
            session_id: Session identifier

        Returns:
            GameManager instance or None if not found
        """
        return self.sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a game session

        Args:
            session_id: Session identifier

        Returns:
            True if session was deleted, False if not found
        """
        if session_id in self.sessions:
            # Clean up the session
            game_manager = self.sessions[session_id]
            game_manager.reset_game()
            del self.sessions[session_id]
            print(f"Deleted game session: {session_id}")
            return True
        return False

    def list_sessions(self) -> list:
        """
        List all active game sessions

        Returns:
            List of session info dicts
        """
        sessions_info = []
        for session_id, game_manager in self.sessions.items():
            sessions_info.append(
                {
                    "session_id": session_id,
                    "creator_id": getattr(game_manager, "creator_id", None),
                    "game_type": game_manager.game_type,
                    "is_started": game_manager.is_started,
                    "is_paused": game_manager.is_paused,
                    "players": [
                        {
                            "name": p["name"],
                            "id": p["id"],
                        }
                        for p in game_manager.players
                    ],
                    "player_count": len(game_manager.players),
                },
            )
        return sessions_info

    def get_or_create_default_session(self) -> str:
        """
        Get the default session or create one if it doesn't exist
        This is for backward compatibility

        Returns:
            session_id: Default session identifier
        """
        # Use a well-known session ID for the default session
        default_session_id = "default"

        if default_session_id not in self.sessions:
            from src.app.game_manager import GameManager

            game_manager = GameManager(self.socketio)
            game_manager.session_id = default_session_id
            game_manager.creator_id = None

            self.sessions[default_session_id] = game_manager
            print("Created default game session for backward compatibility")

        return default_session_id
