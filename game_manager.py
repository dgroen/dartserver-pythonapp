"""
Game Manager for handling game logic
"""

import os

from games.game_301 import Game301
from games.game_cricket import GameCricket
from tts_service import TTSService


class GameManager:
    """Manages game state and logic"""

    def __init__(self, socketio):
        """
        Initialize game manager

        Args:
            socketio: SocketIO instance for emitting events
        """
        self.socketio = socketio
        self.players = []
        self.current_player = 0
        self.game_type = "301"
        self.game = None
        self.is_started = False
        self.is_paused = True
        self.current_throw = 1
        self.throws_per_turn = 3
        self.start_score = 0
        self.is_winner = False

        # Sound arrays
        self.miss_sounds = [
            "doh",
            "ohNo",
            "triedNotMissing",
            "soClose",
            "AwwTooBad",
            "miss",
            "ha-ha",
        ]
        self.turn_sounds = ["ThrowDarts", "fireAway", "showMe", "yerTurn", "yerUp", "letErFly"]

        # Initialize TTS service
        tts_enabled = os.getenv("TTS_ENABLED", "true").lower() == "true"
        tts_engine = os.getenv("TTS_ENGINE", "pyttsx3")
        tts_speed = int(os.getenv("TTS_SPEED", "150"))
        tts_volume = float(os.getenv("TTS_VOLUME", "0.9"))
        tts_voice = os.getenv("TTS_VOICE", "default")

        self.tts = TTSService(
            engine=tts_engine,
            voice_type=tts_voice,
            speed=tts_speed,
            volume=tts_volume,
        )

        if not tts_enabled:
            self.tts.disable()

    def new_game(self, game_type="301", player_names=None, double_out=False):
        """
        Start a new game

        Args:
            game_type: Type of game ('301', '401', '501', 'cricket')
            player_names: List of player names
            double_out: Whether to require double-out to finish (only for 301/401/501)
        """
        self.game_type = game_type.lower()

        # Initialize players
        if player_names:
            self.players = [{"name": name, "id": i} for i, name in enumerate(player_names)]
        elif not self.players:
            self.players = [
                {"name": "Player 1", "id": 0},
                {"name": "Player 2", "id": 1},
            ]

        # Create appropriate game instance
        if self.game_type == "cricket":
            self.game = GameCricket(self.players)
        else:
            # Default to 301, but support 401, 501
            start_score = 301
            if self.game_type == "401":
                start_score = 401
            elif self.game_type == "501":
                start_score = 501
            self.game = Game301(self.players, start_score, double_out)

        # Reset game state
        self.current_player = 0
        self.is_started = True
        self.is_paused = False
        self.current_throw = 1
        self.is_winner = False

        # Emit game state
        self._emit_game_state()
        self._emit_sound("intro", "Welcome to the game")
        message = f"{self.players[self.current_player]['name']}, Throw Darts"
        self._emit_message(message)
        self._emit_sound("yerTurn", message)

        print(
            f"New {self.game_type} game started with {len(self.players)} \
            players (double-out: {double_out})",
        )

    def add_player(self, name=None):
        """Add a new player"""
        if not name:
            name = f"Player {len(self.players) + 1}"

        # Cricket supports max 4 players
        if self.game_type == "cricket" and len(self.players) >= 4:
            print("Cricket game supports maximum 4 players")
            return

        player_id = len(self.players)
        self.players.append({"name": name, "id": player_id})

        if self.game:
            self.game.add_player({"name": name, "id": player_id})

        self._emit_game_state()
        self._emit_sound("addPlayer", f"Player {name} added")
        print(f"Player added: {name}")

    def remove_player(self, player_id):
        """Remove a player"""
        # Allow single player games - no minimum restriction
        if len(self.players) <= 1:
            print("Cannot remove player: at least 1 player required")
            return

        if 0 <= player_id < len(self.players):
            removed_player = self.players.pop(player_id)

            # Update player IDs
            for i, player in enumerate(self.players):
                player["id"] = i

            # Adjust current player if necessary
            if self.current_player >= len(self.players):
                self.current_player = 0

            if self.game:
                self.game.remove_player(player_id)

            self._emit_game_state()
            self._emit_sound("removePlayer", f"Player {removed_player['name']} removed")
            print(f"Player removed: {removed_player['name']}")

    def process_score(self, score_data):
        if not self.is_started or self.is_paused:
            print("Game not active, ignoring score")
            return

        if not isinstance(score_data, dict):
            print("Invalid score_data: must be a dictionary, ignoring score")
            return

        base_score, multiplier = self._parse_score_data(score_data)

        if not self._is_valid_score(base_score):
            return

        result = None
        if self.game:
            result = self.game.process_score(base_score, multiplier)

        # Handle game events
        if result:
            # Convert multiplier string to numeric for effects
            multiplier_map = {
                "SINGLE": 1,
                "DOUBLE": 2,
                "TRIPLE": 3,
                "BULL": 1,
                "DBLBULL": 2,
            }
            multiplier_value = multiplier_map.get(multiplier, 1)
            actual_score = base_score * multiplier_value

            # Emit throw effects
            self._emit_throw_effects(multiplier, base_score, actual_score)

            # Check for bust
            if result.get("bust"):
                self._handle_bust(result)
            # Check for winner
            elif result.get("winner"):
                self._handle_winner(result.get("player_id", self.current_player))
            # Check if turn is complete (after incrementing)
            else:
                # Increment throw counter
                self.current_throw += 1
                if self.current_throw > self.throws_per_turn:
                    self._end_turn()

        self._emit_game_state()
        print(f"Score processed: {base_score} {multiplier}")

    def _parse_score_data(self, score_data):
        base_score_raw = score_data.get("score")
        if base_score_raw is None:
            base_score = 0
        else:
            try:
                base_score = int(base_score_raw)
            except (TypeError, ValueError) as e:
                print(f"Invalid score value '{base_score_raw}': {e}, defaulting to 0")
                base_score = 0

        multiplier_raw = score_data.get("multiplier", "SINGLE")
        multiplier = self._get_valid_multiplier(multiplier_raw)

        return base_score, multiplier

    def _get_valid_multiplier(self, multiplier_raw):
        multiplier = multiplier_raw.upper()
        valid_multipliers = {"SINGLE", "DOUBLE", "TRIPLE", "BULL", "DBLBULL"}
        if multiplier not in valid_multipliers:
            print(f"Invalid multiplier '{multiplier}', defaulting to SINGLE")
            multiplier = "SINGLE"
        return multiplier

    def _is_valid_score(self, base_score):
        if base_score < 0:
            print(f"Invalid score value '{base_score}', ignoring score")
            return False
        return True

    def next_player(self):
        """Move to the next player"""
        if not self.is_started:
            return

        self.current_player = (self.current_player + 1) % len(self.players)
        self.current_throw = 1
        self.is_paused = False

        # Update current player in game object
        if self.game:
            self.game.set_current_player(self.current_player)

        self._emit_game_state()
        message = f"{self.players[self.current_player]['name']}, Throw Darts"
        self._emit_sound(f"Player{self.current_player + 1}", message)
        self._emit_message(message)

    def skip_to_player(self, player_id):
        """Skip to a specific player"""
        if not self.is_started or player_id < 0 or player_id >= len(self.players):
            return

        self.current_player = player_id
        self.current_throw = 1
        self.is_paused = False

        # Update current player in game object
        if self.game:
            self.game.set_current_player(self.current_player)

        self._emit_game_state()
        message = f"{self.players[self.current_player]['name']}, Throw Darts"
        self._emit_sound(f"Player{self.current_player + 1}", message)
        self._emit_message(message)

    def get_game_state(self):
        """Get current game state"""
        state = {
            "players": self.players,
            "current_player": self.current_player,
            "game_type": self.game_type,
            "is_started": self.is_started,
            "is_paused": self.is_paused,
            "is_winner": self.is_winner,
            "current_throw": self.current_throw,
        }

        if self.game:
            state["game_data"] = self.game.get_state()

        return state

    def get_players(self):
        """Get all players"""
        return self.players

    def _handle_bust(self, _result):
        """Handle a bust"""
        self.is_paused = True
        self.current_throw = self.throws_per_turn + 1

        message = "BUST! Remove Darts, Press Button to Continue"
        self._emit_message(message)
        self._emit_sound("Bust", "Bust!")
        self._emit_video("bust.mp4", 0)
        self._emit_game_state()

    def _handle_winner(self, player_id):
        """Handle a winner"""
        self.is_winner = True
        self.is_paused = True

        winner_name = self.players[player_id]["name"]
        message = f"{winner_name} WINS!"
        self._emit_message(f"🎉 {message} 🎉")
        self._emit_sound("WeHaveAWinner", f"We have a winner! {winner_name} wins!")
        self._emit_video("winner.mp4", 0)
        self._emit_game_state()

        print(f"Winner: {winner_name}")

    def _end_turn(self):
        """End the current turn"""
        self.is_paused = True
        message = "Remove Darts, Press Button to Continue"
        self._emit_message(message)
        self._emit_sound("RemoveDarts", "Remove darts")

    def _emit_throw_effects(self, multiplier, base_score, actual_score):
        """Emit sound and video effects for a throw"""
        self._emit_sound("Plink")

        if multiplier == "TRIPLE":
            self._emit_sound("Triple", f"Triple {base_score}! {actual_score} points")
            self._emit_video("triple.mp4", self._get_angle(base_score))
            message = f"TRIPLE! 3 x {base_score} = {actual_score}"
        elif multiplier == "DOUBLE":
            self._emit_sound("Dbl", f"Double {base_score}! {actual_score} points")
            self._emit_video("double.mp4", self._get_angle(base_score))
            message = f"DOUBLE! 2 x {base_score} = {actual_score}"
        elif multiplier == "BULL":
            self._emit_sound("Bullseye", f"Bullseye! {actual_score} points")
            self._emit_video("bullseye.mp4", 0)
            message = f"BULLSEYE! {actual_score}"
        elif multiplier == "DBLBULL":
            self._emit_sound("DblBullseye", f"Double Bullseye! {actual_score} points")
            self._emit_video("bullseye.mp4", 0)
            message = f"DOUBLE BULL! 2 x {base_score} = {actual_score}"
        else:
            self._emit_video("single.mp4", self._get_angle(base_score))
            message = str(actual_score)
            if actual_score > 0:
                self._emit_sound("score", f"{actual_score} points")

        self._emit_big_message(message)

    def _get_angle(self, score):
        """Get angle for video rotation based on score"""
        zones = [20, 1, 18, 4, 13, 6, 10, 15, 2, 17, 3, 19, 7, 16, 8, 11, 14, 9, 12, 5]
        try:
            return zones.index(score) * 18
        except ValueError:
            return 0

    def _emit_game_state(self):
        """Emit game state to all clients"""
        self.socketio.emit("game_state", self.get_game_state(), namespace="/")

    def _emit_sound(self, sound, text=None):
        """
        Emit sound event and optionally speak text via TTS

        Args:
            sound: Sound identifier
            text: Optional text to speak via TTS
        """
        self.socketio.emit("play_sound", {"sound": sound}, namespace="/")

        # Use TTS if text is provided
        if text and self.tts.is_enabled():
            self.tts.speak(text)

    def _emit_video(self, video, angle):
        """Emit video event"""
        self.socketio.emit("play_video", {"video": video, "angle": angle}, namespace="/")

    def _emit_message(self, message):
        """Emit message event"""
        self.socketio.emit("message", {"text": message}, namespace="/")

    def _emit_big_message(self, message):
        """Emit big message event"""
        self.socketio.emit("big_message", {"text": message}, namespace="/")
