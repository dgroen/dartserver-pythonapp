"""Game Manager for handling game logic."""

import base64
import os

from src.core.database_service import DatabaseService
from src.core.tts_service import TTSService
from src.games.game_301 import Game301
from src.games.game_cricket import GameCricket


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
        self.double_out = False

        # Turn tracking for undo on bust
        self.turn_throws = []  # List of throws in current turn
        self.turn_start_state = None  # Game state at start of turn
        self.turn_number = {}  # Track turn number per player

        # Throwout advice settings
        self.show_throwout_advice = False  # Toggle for showing throwout advice

        # Initialize database service
        self.db_service = DatabaseService()
        try:
            self.db_service.initialize_database()
        except Exception as e:
            print(f"Warning: Could not initialize database: {e}")

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
        self.double_out = double_out

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
            self.start_score = 0
        else:
            # Default to 301, but support 401, 501
            start_score = 301
            if self.game_type == "401":
                start_score = 401
            elif self.game_type == "501":
                start_score = 501
            self.start_score = start_score
            self.game = Game301(self.players, start_score, double_out)

        # Reset game state
        self.current_player = 0
        self.is_started = True
        self.is_paused = False
        self.current_throw = 1
        self.is_winner = False

        # Reset turn tracking
        self.turn_throws = []
        self.turn_start_state = None
        self.turn_number = dict.fromkeys(range(len(self.players)), 1)
        self._save_turn_start_state()

        # Start new game in database
        try:
            player_name_list = [p["name"] for p in self.players]
            self.db_service.start_new_game(
                game_type_name=self.game_type,
                player_names=player_name_list,
                start_score=self.start_score if self.game_type != "cricket" else None,
                double_out=double_out,
            )
            print(f"Game started in database: session_id={self.db_service.current_game_session_id}")
        except Exception as e:
            print(f"Warning: Could not start game in database: {e}")

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

        # Convert multiplier string to numeric value
        multiplier_map = {
            "SINGLE": 1,
            "DOUBLE": 2,
            "TRIPLE": 3,
            "BULL": 1,
            "DBLBULL": 2,
        }
        multiplier_value = multiplier_map.get(multiplier, 1)

        # Handle dartboard configuration
        from app import app  # Import here to avoid circular dependency

        if app.config["DARTBOARD_SENDS_ACTUAL_SCORE"]:
            # Dartboard sent the actual score (e.g., 60 for triple 20)
            # Convert to base score for game logic
            actual_score = base_score
            base_score = int(base_score / multiplier_value)
        else:
            # Dartboard sent base score (e.g., 20 for triple 20)
            # Calculate actual score for display
            actual_score = base_score * multiplier_value

        # Get score before throw
        score_before = self._get_player_current_score(self.current_player)

        # Track this throw before processing
        throw_data = {
            "base_score": base_score,
            "multiplier": multiplier,
            "multiplier_value": multiplier_value,
            "actual_score": actual_score,
            "throw_number": self.current_throw,
            "score_before": score_before,
        }
        self.turn_throws.append(throw_data)

        result = None
        if self.game:
            result = self.game.process_score(base_score, multiplier)

        # Get score after throw
        score_after = self._get_player_current_score(self.current_player)

        # Handle game events
        if result:
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
                # Record throw in database (not a bust)
                self._record_throw_in_db(
                    base_score,
                    multiplier,
                    multiplier_value,
                    actual_score,
                    score_before,
                    score_after,
                    is_bust=False,
                    is_finish=False,
                )

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

        # Reset turn tracking for new player
        self.turn_throws = []
        self._save_turn_start_state()

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

        # Reset turn tracking for new player
        self.turn_throws = []
        self._save_turn_start_state()

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
            "show_throwout_advice": self.show_throwout_advice,
        }

        if self.game:
            state["game_data"] = self.game.get_state()

        # Add throwout advice if enabled
        if self.show_throwout_advice and self.game and self.game_type != "cricket":
            current_score = self._get_player_current_score(self.current_player)
            advice = self.get_throwout_advice(current_score)
            if advice:
                state["throwout_advice"] = advice

        return state

    def get_players(self):
        """Get all players"""
        return self.players

    def set_show_throwout_advice(self, enabled):
        """
        Set whether to show throwout advice

        Args:
            enabled: Boolean to enable/disable throwout advice
        """
        self.show_throwout_advice = enabled
        self._emit_game_state()
        import logging

        logging.getLogger(__name__).info(f"Throwout advice: {'enabled' if enabled else 'disabled'}")

    def get_throwout_advice(self, score):
        """
        Get throwout advice for a given score

        Args:
            score: Current score for which to provide advice

        Returns:
            List of suggested finishes or None if not available
        """
        if not self.show_throwout_advice or self.game_type == "cricket":
            return None

        if score <= 0 or score > 170:
            return None

        # Generate throwout advice based on common finishing moves
        advice = []
        # Comprehensive throwout advice for common finishes
        finishes = {
            170: ["T20", "T20", "Bull"],
            167: ["T20", "T19", "Bull"],
            164: ["T20", "T18", "Bull"],
            161: ["T20", "T17", "Bull"],
            160: ["T20", "T20", "D20"],
            158: ["T20", "T20", "D19"],
            157: ["T20", "T19", "D20"],
            156: ["T20", "T20", "D18"],
            155: ["T20", "T19", "D19"],
            154: ["T20", "T18", "D20"],
            153: ["T20", "T19", "D18"],
            152: ["T20", "T20", "D16"],
            151: ["T20", "T17", "D20"],
            150: ["T20", "T18", "D18"],
            149: ["T20", "T19", "D16"],
            148: ["T20", "T16", "D20"],
            147: ["T20", "T17", "D18"],
            146: ["T20", "T18", "D16"],
            145: ["T20", "T15", "D20"],
            144: ["T20", "T20", "D12"],
            143: ["T20", "T17", "D16"],
            142: ["T20", "T14", "D20"],
            141: ["T20", "T19", "D12"],
            140: ["T20", "T20", "D10"],
            139: ["T20", "T13", "D20"],
            138: ["T20", "T18", "D12"],
            137: ["T20", "T15", "D16"],
            136: ["T20", "T20", "D8"],
            135: ["T20", "T17", "D12"],
            134: ["T20", "T14", "D16"],
            133: ["T20", "T19", "D8"],
            132: ["T20", "T16", "D12"],
            131: ["T20", "T13", "D16"],
            130: ["T20", "T18", "D8"],
            129: ["T19", "T16", "D12"],
            128: ["T18", "T14", "D16"],
            127: ["T20", "T17", "D8"],
            126: ["T19", "T19", "D6"],
            125: ["T20", "T15", "D10"],
            124: ["T20", "T16", "D8"],
            123: ["T19", "T16", "D9"],
            122: ["T18", "T20", "D4"],
            121: ["T20", "T11", "D14"],
            120: ["T20", "20", "D20"],
            119: ["T19", "T10", "D16"],
            118: ["T20", "18", "D20"],
            117: ["T20", "17", "D20"],
            116: ["T20", "16", "D20"],
            115: ["T20", "15", "D20"],
            114: ["T20", "14", "D20"],
            113: ["T20", "13", "D20"],
            112: ["T20", "12", "D20"],
            111: ["T20", "11", "D20"],
            110: ["T20", "10", "D20"],
            109: ["T20", "9", "D20"],
            108: ["T20", "8", "D20"],
            107: ["T19", "10", "D20"],
            106: ["T20", "6", "D20"],
            105: ["T19", "8", "D20"],
            104: ["T18", "18", "D16"],
            103: ["T20", "3", "D20"],
            102: ["T20", "10", "D16"],
            101: ["T17", "18", "D16"],
            100: ["T20", "D20"],
            99: ["T19", "10", "D16"],
            98: ["T20", "D19"],
            97: ["T19", "D20"],
            96: ["T20", "D18"],
            95: ["T19", "D19"],
            94: ["T18", "D20"],
            93: ["T19", "D18"],
            92: ["T20", "D16"],
            91: ["T17", "D20"],
            90: ["T18", "D18"],
            89: ["T19", "D16"],
            88: ["T16", "D20"],
            87: ["T17", "D18"],
            86: ["T18", "D16"],
            85: ["T15", "D20"],
            84: ["T20", "D12"],
            83: ["T17", "D16"],
            82: ["Bull", "D16"],
            81: ["T19", "D12"],
            80: ["T20", "D10"],
            79: ["T19", "D11"],
            78: ["T18", "D12"],
            77: ["T19", "D10"],
            76: ["T20", "D8"],
            75: ["T17", "D12"],
            74: ["T14", "D16"],
            73: ["T19", "D8"],
            72: ["T16", "D12"],
            71: ["T13", "D16"],
            70: ["T18", "D8"],
            69: ["T19", "D6"],
            68: ["T20", "D4"],
            67: ["T17", "D8"],
            66: ["T10", "D18"],
            65: ["25", "D20"],
            64: ["16", "D24"],
            63: ["13", "D25"],
            62: ["10", "D26"],
            61: ["25", "D18"],
            60: ["20", "D20"],
            59: ["19", "D20"],
            58: ["18", "D20"],
            57: ["17", "D20"],
            56: ["16", "D20"],
            55: ["15", "D20"],
            54: ["14", "D20"],
            53: ["13", "D20"],
            52: ["12", "D20"],
            51: ["11", "D20"],
            50: ["10", "D20"],
            49: ["9", "D20"],
            48: ["16", "D16"],
            47: ["15", "D16"],
            46: ["14", "D16"],
            45: ["13", "D16"],
            44: ["12", "D16"],
            43: ["11", "D16"],
            42: ["10", "D16"],
            41: ["9", "D16"],
            40: ["D20"],
            38: ["D19"],
            36: ["D18"],
            34: ["D17"],
            32: ["D16"],
            30: ["D15"],
            28: ["D14"],
            26: ["D13"],
            24: ["D12"],
            22: ["D11"],
            20: ["D10"],
            18: ["D9"],
            16: ["D8"],
            14: ["D7"],
            12: ["D6"],
            10: ["D5"],
            8: ["D4"],
            6: ["D3"],
            4: ["D2"],
            2: ["D1"],
        }

        if (self.double_out and score in finishes) or (not self.double_out and score in finishes):
            advice = [" + ".join(finishes[score])]
        else:
            advice = []
            # Fallback for scores not in finishes
            if self.double_out:
                if score <= 40 and score % 2 == 0:
                    advice.append(f"Double {score // 2}")
                if score == 50:
                    advice.append("Bull")
            else:
                for i in range(1, 21):
                    if score == i:
                        advice.append(f"Single {i}")
                    elif score == i * 2:
                        advice.append(f"Double {i}")
                    elif score == i * 3:
                        advice.append(f"Triple {i}")
                if score == 25:
                    advice.append("Bull")
                elif score == 50:
                    advice.append("Double Bull")

        return advice if advice else None
        return advice if advice else None

    def _handle_bust(self, _result):
        """Handle a bust - undo all throws in the turn"""
        # Record the bust throw in database before undoing
        if self.turn_throws:
            last_throw = self.turn_throws[-1]
            self._record_throw_in_db(
                last_throw["base_score"],
                last_throw["multiplier"],
                last_throw["multiplier_value"],
                last_throw["actual_score"],
                last_throw["score_before"],
                last_throw["score_before"],  # Score stays the same on bust
                is_bust=True,
                is_finish=False,
            )

        # Undo throws in database (except the bust throw which we just recorded)
        throw_count = len(self.turn_throws) - 1
        if throw_count > 0:
            try:
                self.db_service.undo_throws_for_bust(self.current_player, throw_count)
            except Exception as e:
                print(f"Warning: Could not undo throws in database: {e}")

        # Restore game state to beginning of turn
        self._restore_turn_start_state()

        self.is_paused = True
        self.current_throw = self.throws_per_turn + 1

        message = "BUST! Remove Darts, Press Button to Continue"
        self._emit_message(message)
        self._emit_sound("Bust", "Bust!")
        self._emit_video("bust.mp4", 0)
        self._emit_game_state()

        print(f"Bust! Undid {len(self.turn_throws)} throw(s) in this turn")

    def _handle_winner(self, player_id):
        """Handle a winner"""
        # Record the winning throw in database
        if self.turn_throws:
            last_throw = self.turn_throws[-1]
            self._record_throw_in_db(
                last_throw["base_score"],
                last_throw["multiplier"],
                last_throw["multiplier_value"],
                last_throw["actual_score"],
                last_throw["score_before"],
                0,  # Final score is 0 for 301/401/501 games
                is_bust=False,
                is_finish=True,
            )

        # Mark winner in database
        try:
            self.db_service.mark_winner(player_id)
        except Exception as e:
            print(f"Warning: Could not mark winner in database: {e}")

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
        # Update player score in database after turn completes
        try:
            current_score = self._get_player_current_score(self.current_player)
            self.db_service.update_player_score(self.current_player, current_score)
        except Exception as e:
            print(f"Warning: Could not update player score in database: {e}")

        # Increment turn number for next turn
        if self.current_player in self.turn_number:
            self.turn_number[self.current_player] += 1

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
            # Generate audio data for client-side playback
            audio_data = self.tts.speak(text, generate_audio=True)
            if audio_data:
                # Encode audio data as base64 for transmission
                audio_base64 = base64.b64encode(audio_data).decode("utf-8")
                self.socketio.emit(
                    "play_tts",
                    {
                        "audio": audio_base64,
                        "text": text,
                    },
                    namespace="/",
                )

    def _emit_video(self, video, angle):
        """Emit video event"""
        self.socketio.emit("play_video", {"video": video, "angle": angle}, namespace="/")

    def _emit_message(self, message):
        """Emit message event"""
        self.socketio.emit("message", {"text": message}, namespace="/")

    def _emit_big_message(self, message):
        """Emit big message event"""
        self.socketio.emit("big_message", {"text": message}, namespace="/")

    def _save_turn_start_state(self):
        """Save the game state at the start of a turn for potential undo"""
        if self.game:
            import copy

            # Deep copy the game state to preserve it
            self.turn_start_state = copy.deepcopy(self.game.get_state())
            print(f"Saved turn start state for player {self.current_player}")

    def _restore_turn_start_state(self):
        """Restore the game state to the beginning of the turn (undo all throws)"""
        if not self.turn_start_state or not self.game:
            print("No turn start state to restore")
            return

        import copy

        # Restore the saved state
        saved_state = copy.deepcopy(self.turn_start_state)

        # Restore player data based on game type
        if self.game_type == "cricket":
            # Restore cricket game state
            for i, player_data in enumerate(saved_state["players"]):
                if i < len(self.game.players):
                    self.game.players[i]["score"] = player_data["score"]
                    self.game.players[i]["targets"] = copy.deepcopy(player_data["targets"])
        else:
            # Restore 301/401/501 game state
            for i, player_data in enumerate(saved_state["players"]):
                if i < len(self.game.players):
                    self.game.players[i]["score"] = player_data["score"]

        print(f"Restored turn start state, undid {len(self.turn_throws)} throw(s)")

    def _get_player_current_score(self, player_id):
        """
        Get the current score for a player

        Args:
            player_id: Player ID (0-based index)

        Returns:
            Current score
        """
        if self.game and 0 <= player_id < len(self.game.players):
            return self.game.players[player_id].get("score", 0)
        return 0

    def _record_throw_in_db(
        self,
        base_score,
        multiplier,
        multiplier_value,
        actual_score,
        score_before,
        score_after,
        is_bust=False,
        is_finish=False,
    ):
        """
        Record a throw in the database

        Args:
            base_score: Base score value
            multiplier: Multiplier type string
            multiplier_value: Numeric multiplier value
            actual_score: Calculated actual score
            score_before: Score before this throw
            score_after: Score after this throw
            is_bust: Whether this throw resulted in a bust
            is_finish: Whether this throw won the game
        """
        try:
            # Get dartboard configuration
            from app import app  # Import here to avoid circular dependency

            dartboard_sends_actual_score = app.config.get("DARTBOARD_SENDS_ACTUAL_SCORE", False)

            # Get current turn number
            turn_num = self.turn_number.get(self.current_player, 1)

            self.db_service.record_throw(
                player_id=self.current_player,
                base_score=base_score,
                multiplier=multiplier,
                multiplier_value=multiplier_value,
                actual_score=actual_score,
                score_before=score_before,
                score_after=score_after,
                turn_number=turn_num,
                throw_in_turn=self.current_throw,
                dartboard_sends_actual_score=dartboard_sends_actual_score,
                is_bust=is_bust,
                is_finish=is_finish,
            )
        except Exception as e:
            print(f"Warning: Could not record throw in database: {e}")
