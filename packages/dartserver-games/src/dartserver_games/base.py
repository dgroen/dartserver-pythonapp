"""Base game class for all game types."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseGame(ABC):
    """Abstract base class for all game types."""

    game_type: str

    @abstractmethod
    def __init__(self, players: List[Dict[str, Any]]) -> None:
        """Initialize a game.

        Args:
            players: List of player dictionaries with 'id' and 'name' keys
        """
        pass

    @abstractmethod
    def add_player(self, player: Dict[str, Any]) -> None:
        """Add a new player to the game."""
        pass

    @abstractmethod
    def remove_player(self, player_id: int) -> None:
        """Remove a player from the game."""
        pass

    @abstractmethod
    def process_score(self, base_score: int, multiplier_type: str) -> Dict[str, Any]:
        """Process a score for the current player.

        Args:
            base_score: Base score value (1-25)
            multiplier_type: Type of multiplier (SINGLE, DOUBLE, TRIPLE, BULL, DBLBULL)

        Returns:
            Dictionary with result information
        """
        pass

    @abstractmethod
    def set_current_player(self, player_id: int) -> None:
        """Set the current player."""
        pass

    @abstractmethod
    def get_player_score(self, player_id: int) -> int:
        """Get a player's current score."""
        pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """Get current game state."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Reset the game."""
        pass
