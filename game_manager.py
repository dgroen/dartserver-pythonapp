"""
Game Manager for handling game logic
"""
import random
from games.game_301 import Game301
from games.game_cricket import GameCricket


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
        self.game_type = '301'
        self.game = None
        self.is_started = False
        self.is_paused = True
        self.current_throw = 1
        self.throws_per_turn = 3
        self.start_score = 0
        self.is_winner = False
        
        # Sound arrays
        self.miss_sounds = ['doh', 'ohNo', 'triedNotMissing', 'soClose', 'AwwTooBad', 'miss', 'ha-ha']
        self.turn_sounds = ['ThrowDarts', 'fireAway', 'showMe', 'yerTurn', 'yerUp', 'letErFly']
        
    def new_game(self, game_type='301', player_names=None):
        """
        Start a new game
        
        Args:
            game_type: Type of game ('301', '401', '501', 'cricket')
            player_names: List of player names
        """
        self.game_type = game_type.lower()
        
        # Initialize players
        if player_names:
            self.players = [{'name': name, 'id': i} for i, name in enumerate(player_names)]
        elif not self.players:
            self.players = [
                {'name': 'Player 1', 'id': 0},
                {'name': 'Player 2', 'id': 1}
            ]
        
        # Create appropriate game instance
        if self.game_type == 'cricket':
            self.game = GameCricket(self.players)
        else:
            # Default to 301, but support 401, 501
            start_score = 301
            if self.game_type == '401':
                start_score = 401
            elif self.game_type == '501':
                start_score = 501
            self.game = Game301(self.players, start_score)
        
        # Reset game state
        self.current_player = 0
        self.is_started = True
        self.is_paused = False
        self.current_throw = 1
        self.is_winner = False
        
        # Emit game state
        self._emit_game_state()
        self._emit_sound('intro')
        self._emit_message(f"{self.players[self.current_player]['name']}, Throw Darts")
        
        print(f"New {self.game_type} game started with {len(self.players)} players")
        
    def add_player(self, name=None):
        """Add a new player"""
        if not name:
            name = f"Player {len(self.players) + 1}"
        
        # Cricket supports max 4 players
        if self.game_type == 'cricket' and len(self.players) >= 4:
            print("Cricket game supports maximum 4 players")
            return
        
        player_id = len(self.players)
        self.players.append({'name': name, 'id': player_id})
        
        if self.game:
            self.game.add_player({'name': name, 'id': player_id})
        
        self._emit_game_state()
        self._emit_sound('addPlayer')
        print(f"Player added: {name}")
        
    def remove_player(self, player_id):
        """Remove a player"""
        if len(self.players) <= 2:
            print("Cannot remove player: minimum 2 players required")
            return
        
        if 0 <= player_id < len(self.players):
            removed_player = self.players.pop(player_id)
            
            # Update player IDs
            for i, player in enumerate(self.players):
                player['id'] = i
            
            # Adjust current player if necessary
            if self.current_player >= len(self.players):
                self.current_player = 0
            
            if self.game:
                self.game.remove_player(player_id)
            
            self._emit_game_state()
            self._emit_sound('removePlayer')
            print(f"Player removed: {removed_player['name']}")
    
    def process_score(self, score_data):
        """
        Process a dart score
        
        Args:
            score_data: Dictionary with score information
                {
                    'score': int (base score value),
                    'multiplier': str ('SINGLE', 'DOUBLE', 'TRIPLE', 'BULL', 'DBLBULL'),
                    'user': str (optional player name)
                }
        """
        if not self.is_started or self.is_paused:
            print("Game not active, ignoring score")
            return
        
        # Parse score data
        base_score = score_data.get('score', 0)
        multiplier = score_data.get('multiplier', 'SINGLE').upper()
        
        # Calculate actual score
        if multiplier == 'TRIPLE':
            actual_score = base_score * 3
            mult_value = 3
        elif multiplier in ['DOUBLE', 'DBLBULL']:
            actual_score = base_score * 2
            mult_value = 2
        else:
            actual_score = base_score
            mult_value = 1
        
        # Store start score for bust detection
        if self.current_throw == 1:
            self.start_score = self.game.get_player_score(self.current_player)
        
        # Process the throw
        result = self.game.process_throw(
            self.current_player,
            base_score,
            mult_value,
            multiplier
        )
        
        # Emit sound and video effects
        self._emit_throw_effects(multiplier, base_score, actual_score)
        
        # Check for bust
        if result.get('bust'):
            self._handle_bust(result)
            return
        
        # Check for winner
        if result.get('winner'):
            self._handle_winner(self.current_player)
            return
        
        # Increment throw counter
        self.current_throw += 1
        
        # Check if turn is over
        if self.current_throw > self.throws_per_turn:
            self._end_turn()
        
        # Emit updated game state
        self._emit_game_state()
    
    def next_player(self):
        """Move to the next player"""
        if not self.is_started:
            return
        
        self.current_player = (self.current_player + 1) % len(self.players)
        self.current_throw = 1
        self.is_paused = False
        
        self._emit_game_state()
        self._emit_sound(f"Player{self.current_player + 1}")
        self._emit_message(f"{self.players[self.current_player]['name']}, Throw Darts")
        
    def skip_to_player(self, player_id):
        """Skip to a specific player"""
        if not self.is_started or player_id < 0 or player_id >= len(self.players):
            return
        
        self.current_player = player_id
        self.current_throw = 1
        self.is_paused = False
        
        self._emit_game_state()
        self._emit_sound(f"Player{self.current_player + 1}")
        self._emit_message(f"{self.players[self.current_player]['name']}, Throw Darts")
    
    def get_game_state(self):
        """Get current game state"""
        state = {
            'players': self.players,
            'current_player': self.current_player,
            'game_type': self.game_type,
            'is_started': self.is_started,
            'is_paused': self.is_paused,
            'is_winner': self.is_winner,
            'current_throw': self.current_throw
        }
        
        if self.game:
            state['game_data'] = self.game.get_state()
        
        return state
    
    def get_players(self):
        """Get all players"""
        return self.players
    
    def _handle_bust(self, result):
        """Handle a bust"""
        self.is_paused = True
        self.current_throw = self.throws_per_turn + 1
        
        self._emit_message('BUST! Remove Darts, Press Button to Continue')
        self._emit_sound('Bust')
        self._emit_video('bust.mp4', 0)
        self._emit_game_state()
        
    def _handle_winner(self, player_id):
        """Handle a winner"""
        self.is_winner = True
        self.is_paused = True
        
        winner_name = self.players[player_id]['name']
        self._emit_message(f"🎉 {winner_name} WINS! 🎉")
        self._emit_sound('WeHaveAWinner')
        self._emit_video('winner.mp4', 0)
        self._emit_game_state()
        
        print(f"Winner: {winner_name}")
    
    def _end_turn(self):
        """End the current turn"""
        self.is_paused = True
        self._emit_message('Remove Darts, Press Button to Continue')
        self._emit_sound('RemoveDarts')
    
    def _emit_throw_effects(self, multiplier, base_score, actual_score):
        """Emit sound and video effects for a throw"""
        self._emit_sound('Plink')
        
        if multiplier == 'TRIPLE':
            self._emit_sound('Triple')
            self._emit_video('triple.mp4', self._get_angle(base_score))
            message = f"TRIPLE! 3 x {base_score} = {actual_score}"
        elif multiplier == 'DOUBLE':
            self._emit_sound('Dbl')
            self._emit_video('double.mp4', self._get_angle(base_score))
            message = f"DOUBLE! 2 x {base_score} = {actual_score}"
        elif multiplier == 'BULL':
            self._emit_sound('Bullseye')
            self._emit_video('bullseye.mp4', 0)
            message = f"BULLSEYE! {actual_score}"
        elif multiplier == 'DBLBULL':
            self._emit_sound('DblBullseye')
            self._emit_video('bullseye.mp4', 0)
            message = f"DOUBLE BULL! 2 x {base_score} = {actual_score}"
        else:
            self._emit_video('single.mp4', self._get_angle(base_score))
            message = str(actual_score)
        
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
        self.socketio.emit('game_state', self.get_game_state())
    
    def _emit_sound(self, sound):
        """Emit sound event"""
        self.socketio.emit('play_sound', {'sound': sound})
    
    def _emit_video(self, video, angle):
        """Emit video event"""
        self.socketio.emit('play_video', {'video': video, 'angle': angle})
    
    def _emit_message(self, message):
        """Emit message event"""
        self.socketio.emit('message', {'text': message})
    
    def _emit_big_message(self, message):
        """Emit big message event"""
        self.socketio.emit('big_message', {'text': message})