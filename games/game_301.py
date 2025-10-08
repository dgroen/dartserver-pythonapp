"""
301 Game Implementation (also supports 401, 501)
"""


class Game301:
    """301/401/501 game logic"""

    def __init__(self, players, start_score=301, double_out=False):
        """
        Initialize 301 game

        Args:
            players: List of player dictionaries
            start_score: Starting score (301, 401, or 501)
            double_out: Whether to require double-out to finish
        """
        self.start_score = start_score
        self.double_out = double_out
        self.players = []

        for player in players:
            self.players.append(
                {
                    "id": player["id"],
                    "name": player["name"],
                    "score": start_score,
                    "is_turn": False,
                },
            )

        if self.players:
            self.players[0]["is_turn"] = True

    def add_player(self, player):
        """Add a new player"""
        self.players.append(
            {
                "id": player["id"],
                "name": player["name"],
                "score": self.start_score,
                "is_turn": False,
            },
        )

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

    def process_throw(self, player_id, base_score, multiplier, multiplier_type):
        """
        Process a dart throw

        Args:
            player_id: ID of the player
            base_score: Base score value
            multiplier: Multiplier value (1, 2, or 3)
            multiplier_type: Type of multiplier (SINGLE, DOUBLE, TRIPLE, etc.)

        Returns:
            Dictionary with result information
        """
        if player_id < 0 or player_id >= len(self.players):
            return {"error": "Invalid player ID"}

        player = self.players[player_id]
        actual_score = base_score * multiplier

        # Store original score for bust detection
        original_score = player["score"]

        # Subtract score
        player["score"] -= actual_score

        result = {
            "player_id": player_id,
            "score": actual_score,
            "new_total": player["score"],
            "bust": False,
            "winner": False,
        }

        # Check for bust (score goes below 0)
        if player["score"] < 0:
            player["score"] = original_score
            result["bust"] = True
            result["new_total"] = original_score
            return result

        # Check for bust (score goes to 1 - impossible to finish)
        if player["score"] == 1:
            player["score"] = original_score
            result["bust"] = True
            result["new_total"] = original_score
            return result

        # Check for exact win (score reaches exactly 0)
        if player["score"] == 0:
            # If double-out is enabled, must finish with a double
            if self.double_out:
                is_double = multiplier_type in ["DOUBLE", "DBLBULL"]
                if is_double:
                    result["winner"] = True
                else:
                    # Not a double - bust!
                    player["score"] = original_score
                    result["bust"] = True
                    result["new_total"] = original_score
            else:
                result["winner"] = True
            return result

        return result

    def set_current_player(self, player_id):
        """Set the current player"""
        for i, player in enumerate(self.players):
            player["is_turn"] = i == player_id

    def get_player_score(self, player_id):
        """Get a player's current score"""
        if 0 <= player_id < len(self.players):
            return self.players[player_id]["score"]
        return 0

    def get_state(self):
        """Get current game state"""
        return {
            "type": f"{self.start_score}",
            "start_score": self.start_score,
            "double_out": self.double_out,
            "players": self.players,
        }

    def reset(self):
        """Reset the game"""
        for player in self.players:
            player["score"] = self.start_score
