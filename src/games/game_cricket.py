"""
Cricket Game Implementation
"""

from typing import ClassVar


class GameCricket:
    """Cricket game logic"""

    # Cricket targets: 15, 16, 17, 18, 19, 20, and Bull (25)
    CRICKET_TARGETS: ClassVar[list[int]] = [15, 16, 17, 18, 19, 20, 25]

    def __init__(self, players):
        """
        Initialize Cricket game

        Args:
            players: List of player dictionaries
        """
        self.players = []

        for player in players:
            player_data = {
                "id": player["id"],
                "name": player["name"],
                "score": 0,
                "is_turn": False,
                "targets": {},
            }

            # Initialize targets
            for target in self.CRICKET_TARGETS:
                player_data["targets"][target] = {
                    "hits": 0,
                    "status": 0,  # 0: closed, 1: open, 2: closed for all
                }

            self.players.append(player_data)

        if self.players:
            self.players[0]["is_turn"] = True

    def add_player(self, player):
        """Add a new player"""
        if len(self.players) >= 4:
            return  # Cricket supports max 4 players

        player_data = {
            "id": player["id"],
            "name": player["name"],
            "score": 0,
            "is_turn": False,
            "targets": {},
        }

        # Initialize targets
        for target in self.CRICKET_TARGETS:
            player_data["targets"][target] = {
                "hits": 0,
                "status": 0,
            }

        self.players.append(player_data)

    def remove_player(self, player_id):
        """Remove a player"""
        if 0 <= player_id < len(self.players):
            self.players.pop(player_id)
            # Update player IDs
            for i, player in enumerate(self.players):
                player["id"] = i

    def process_score(self, base_score, multiplier_type):
        """
        Process a score (wrapper for process_throw)

        Args:
            base_score: Base score value
            multiplier_type: Type of multiplier (SINGLE, DOUBLE, TRIPLE, BULL, DBLBULL)

        Returns:
            Dictionary with result information
        """
        # Find current player
        current_player_id = 0
        for i, player in enumerate(self.players):
            if player.get("is_turn", False):
                current_player_id = i
                break

        # Convert multiplier type to numeric value
        multiplier_map = {
            "SINGLE": 1,
            "DOUBLE": 2,
            "TRIPLE": 3,
            "BULL": 1,
            "DBLBULL": 2,
        }
        multiplier = multiplier_map.get(multiplier_type, 1)

        return self.process_throw(current_player_id, base_score, multiplier, multiplier_type)

    def process_throw(self, player_id, base_score, multiplier, _multiplier_type):
        """
        Process a dart throw

        Args:
            player_id: ID of the player
            base_score: Base score value
            multiplier: Multiplier value (1, 2, or 3)
            _multiplier_type: Type of multiplier (SINGLE, DOUBLE, TRIPLE, etc.) - unused

        Returns:
            Dictionary with result information
        """
        if player_id < 0 or player_id >= len(self.players):
            return {"error": "Invalid player ID"}

        player = self.players[player_id]

        result = {
            "player_id": player_id,
            "target": base_score,
            "hits": multiplier,
            "bust": False,
            "winner": False,
            "opened": False,
            "closed": False,
            "points_scored": 0,
        }

        # Check if the target is a cricket target
        if base_score not in self.CRICKET_TARGETS:
            return result

        target = player["targets"][base_score]

        # Check if target is already closed for everyone
        if target["status"] == 2:
            return result

        # Process each hit
        for _ in range(multiplier):
            # If player has opened the target (3+ hits)
            if target["status"] == 1:
                player["score"] += base_score
                result["points_scored"] += base_score

            # Add hit if not yet at 3
            if target["hits"] < 3:
                target["hits"] += 1

                # Check if target is now opened (3 hits)
                if target["hits"] == 3:
                    target["status"] = 1
                    result["opened"] = True

                    # Check if all other players have also opened this target
                    if self._check_all_opened(base_score):
                        # Close the target for everyone
                        self._close_target_for_all(base_score)
                        result["closed"] = True

        # Check for winner
        if self._check_winner(player_id):
            result["winner"] = True

        return result

    def _check_all_opened(self, target):
        """Check if all players have opened a target"""
        return all(player["targets"][target]["hits"] >= 3 for player in self.players)

    def _close_target_for_all(self, target):
        """Close a target for all players"""
        for player in self.players:
            player["targets"][target]["status"] = 2

    def set_current_player(self, player_id):
        """Set the current player"""
        for i, player in enumerate(self.players):
            player["is_turn"] = i == player_id

    def _check_winner(self, player_id):
        """
        Check if a player has won
        A player wins when:
        1. All their targets are opened (3+ hits each)
        2. They have the highest score OR all targets are closed
        """
        player = self.players[player_id]

        # Check if all targets are opened for this player
        for target in self.CRICKET_TARGETS:
            if player["targets"][target]["hits"] < 3:
                return False

        # All targets are opened, check if they have the highest score
        # or if all targets are closed
        all_closed = True
        for target in self.CRICKET_TARGETS:
            if player["targets"][target]["status"] != 2:
                all_closed = False
                break

        if all_closed:
            # If all targets are closed, player with highest score wins
            max_score = max(p["score"] for p in self.players)
            return player["score"] == max_score
        # If not all closed, check if this player has highest score
        # and all their targets are opened
        max_score = max(p["score"] for p in self.players)
        return player["score"] >= max_score

    def get_player_score(self, player_id):
        """Get a player's current score"""
        if 0 <= player_id < len(self.players):
            return self.players[player_id]["score"]
        return 0

    def get_state(self):
        """Get current game state"""
        return {
            "type": "cricket",
            "targets": self.CRICKET_TARGETS,
            "players": self.players,
        }

    def reset(self):
        """Reset the game"""
        for player in self.players:
            player["score"] = 0
            for target in self.CRICKET_TARGETS:
                player["targets"][target] = {
                    "hits": 0,
                    "status": 0,
                }
