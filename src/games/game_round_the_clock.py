"""
Round the Clock Game Implementation
"""


class GameRoundTheClock:
    """Round the Clock game logic"""

    def __init__(self, players, reset_on_miss=False):
        """
        Initialize Round the Clock game

        Args:
            players: List of player dictionaries
            reset_on_miss: Boolean to enable hard mode - reset to 20 after 3 consecutive misses
        """
        self.players = []
        self.reset_on_miss = reset_on_miss

        for player in players:
            player_data = {
                "id": player["id"],
                "name": player["name"],
                "current_target": 20,  # Start from 20
                "is_turn": False,
                "bull_hits": 0,  # Count single bull hits for win condition
                "turn_misses": 0,  # Track consecutive misses in current turn
            }
            self.players.append(player_data)

        if self.players:
            self.players[0]["is_turn"] = True

    def add_player(self, player):
        """Add a new player"""
        player_data = {
            "id": player["id"],
            "name": player["name"],
            "current_target": 20,
            "is_turn": False,
            "bull_hits": 0,
            "turn_misses": 0,
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

        # Infer multiplier from multiplier_type
        multiplier_map = {
            "SINGLE": 1,
            "DOUBLE": 2,
            "TRIPLE": 3,
            "BULL": 1,
            "DBLBULL": 2,
        }
        multiplier = multiplier_map.get(multiplier_type, 1)
        return self.process_throw(current_player_id, base_score, multiplier, multiplier_type)

    def process_throw(self, player_id, base_score, multiplier_type):
        """
        Process a dart throw

        Args:
            player_id: ID of the player
            base_score: Base score value (or 25 for bull)
            multiplier_type: Type of multiplier (SINGLE, DOUBLE, TRIPLE, BULL, DBLBULL)

        Returns:
            Dictionary with result information
        """
        if player_id < 0 or player_id >= len(self.players):
            return {"error": "Invalid player ID"}

        player = self.players[player_id]
        current_target = player["current_target"]

        result = {
            "player_id": player_id,
            "hit": False,
            "current_target": current_target,
            "new_target": current_target,
            "skipped": 0,
            "winner": False,
        }

        # Check for bull (25) - special win condition
        if base_score == 25:
            # Already finished the sequence (1-20)
            if current_target == 0:
                if multiplier_type == "DBLBULL":
                    # Double bull wins immediately
                    result["winner"] = True
                    result["hit"] = True
                    return result
                if multiplier_type == "BULL":
                    # Single bull - need 5 total
                    player["bull_hits"] += 1
                    result["hit"] = True
                    result["bull_hits"] = player["bull_hits"]
                    if player["bull_hits"] >= 5:
                        result["winner"] = True
                    return result
            # Bull hit but not at the end - doesn't count
            return result

        # Check if player hit their current target
        if base_score == current_target:
            result["hit"] = True

            # Reset miss counter on hit
            player["turn_misses"] = 0

            # Move to next target based on multiplier
            if multiplier_type == "TRIPLE":
                # Triple - skip 2 numbers
                result["skipped"] = 2
                player["current_target"] = max(0, current_target - 3)
            elif multiplier_type == "DOUBLE":
                # Double - skip 1 number
                result["skipped"] = 1
                player["current_target"] = max(0, current_target - 2)
            else:
                # Single - just move to next
                player["current_target"] = max(0, current_target - 1)

            result["new_target"] = player["current_target"]

            # Reset bull hits when advancing (only count at the end)
            player["bull_hits"] = 0
        elif current_target > 0:  # Only track misses for targets 1-20
            # Missed the target - increment miss counter if not at bull stage
            player["turn_misses"] += 1

        return result

    def set_current_player(self, player_id):
        """Set the current player"""
        for i, player in enumerate(self.players):
            player["is_turn"] = i == player_id

    def end_turn(self, player_id):
        """
        End turn for a player and check if reset is needed in hard mode

        Args:
            player_id: ID of the player whose turn is ending

        Returns:
            Dictionary with reset information if applicable
        """
        if player_id < 0 or player_id >= len(self.players):
            return {"error": "Invalid player ID"}

        player = self.players[player_id]
        result = {"reset": False, "player_id": player_id}

        # Check if hard mode is enabled and player missed all 3 darts
        if self.reset_on_miss and player["turn_misses"] >= 3 and player["current_target"] > 0:
            # Only reset if not at bull stage (target > 0)
            player["current_target"] = 20
            result["reset"] = True
            result["message"] = "Missed target! Reset to 20"

        # Reset miss counter for next turn
        player["turn_misses"] = 0

        return result

    def get_player_score(self, player_id):
        """
        Get a player's current progress (for compatibility)
        Returns the current target number (20 = just started, 0 = need bull)
        """
        if 0 <= player_id < len(self.players):
            return self.players[player_id]["current_target"]
        return 20

    def get_state(self):
        """Get current game state"""
        return {
            "type": "round_the_clock",
            "players": self.players,
        }

    def reset(self):
        """Reset the game"""
        for player in self.players:
            player["current_target"] = 20
            player["bull_hits"] = 0
            player["turn_misses"] = 0
