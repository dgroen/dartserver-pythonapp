"""
Bull Practice Game Implementation
"""


class GameBullPractice:
    """Bull Practice game logic - track consecutive bull hits"""

    def __init__(self, players):
        """
        Initialize Bull Practice game

        Args:
            players: List of player dictionaries (typically single player)
        """
        self.players = []

        for player in players:
            player_data = {
                "id": player["id"],
                "name": player["name"],
                "score": 0,  # Total accumulated score from bulls
                "is_turn": False,
                "current_turn_bull_hits": 0,  # Bulls hit in current turn
                "current_turn_score": 0,  # Score accumulated in current turn
                "throws_in_turn": 0,  # Number of throws in current turn
                "game_ended": False,  # Whether the current game has ended
            }
            self.players.append(player_data)

        if self.players:
            self.players[0]["is_turn"] = True

    def add_player(self, player):
        """Add a new player"""
        player_data = {
            "id": player["id"],
            "name": player["name"],
            "score": 0,
            "is_turn": False,
            "current_turn_bull_hits": 0,
            "current_turn_score": 0,
            "throws_in_turn": 0,
            "game_ended": False,
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
        return self.process_throw(current_player_id, base_score, multiplier_type)

    def process_throw(self, player_id, base_score, multiplier_type):
        """
        Process a dart throw

        Args:
            player_id: ID of the player
            base_score: Base score value (25 for bull)
            multiplier_type: Type of multiplier (SINGLE, DOUBLE, TRIPLE, BULL, DBLBULL)

        Returns:
            Dictionary with result information
        """
        if player_id < 0 or player_id >= len(self.players):
            return {"error": "Invalid player ID"}

        player = self.players[player_id]

        # If game ended, don't process more throws
        if player["game_ended"]:
            return {
                "player_id": player_id,
                "bull_hit": False,
                "score_added": 0,
                "current_turn_score": player["current_turn_score"],
                "total_score": player["score"],
                "game_ended": True,
                "auto_restart": True,
            }

        result = {
            "player_id": player_id,
            "bull_hit": False,
            "score_added": 0,
            "current_turn_score": player["current_turn_score"],
            "total_score": player["score"],
            "game_ended": False,
            "auto_restart": False,
        }

        # Increment throws in turn
        player["throws_in_turn"] += 1

        # Check if bull was hit
        is_bull = base_score == 25 and multiplier_type in ["BULL", "DBLBULL"]

        if is_bull:
            result["bull_hit"] = True
            player["current_turn_bull_hits"] += 1

            # Calculate score (single bull = 25, double bull = 50)
            score_value = 25 if multiplier_type == "BULL" else 50
            player["current_turn_score"] += score_value
            result["score_added"] = score_value
            result["current_turn_score"] = player["current_turn_score"]

        # Check if turn is complete (3 throws)
        if player["throws_in_turn"] >= 3:
            # End of turn - check if any bulls were hit
            if player["current_turn_bull_hits"] == 0:
                # No bulls hit this turn - game ends
                result["game_ended"] = True
                result["auto_restart"] = True
                player["game_ended"] = True
            else:
                # Bulls were hit - add to total score and start new turn
                player["score"] += player["current_turn_score"]
                result["total_score"] = player["score"]

                # Reset turn counters
                player["current_turn_bull_hits"] = 0
                player["current_turn_score"] = 0
                player["throws_in_turn"] = 0

        return result

    def restart_game(self, player_id=None):
        """
        Restart the game for a player (or all players if player_id is None)

        Args:
            player_id: ID of the player to restart (None for all players)
        """
        if player_id is not None:
            if 0 <= player_id < len(self.players):
                player = self.players[player_id]
                player["score"] = 0
                player["current_turn_bull_hits"] = 0
                player["current_turn_score"] = 0
                player["throws_in_turn"] = 0
                player["game_ended"] = False
        else:
            # Restart all players
            for player in self.players:
                player["score"] = 0
                player["current_turn_bull_hits"] = 0
                player["current_turn_score"] = 0
                player["throws_in_turn"] = 0
                player["game_ended"] = False

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
            "type": "bull_practice",
            "players": self.players,
        }

    def reset(self):
        """Reset the game"""
        for player in self.players:
            player["score"] = 0
            player["current_turn_bull_hits"] = 0
            player["current_turn_score"] = 0
            player["throws_in_turn"] = 0
            player["game_ended"] = False
