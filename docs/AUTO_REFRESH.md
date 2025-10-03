# Automatic UI Refresh Documentation

## Overview

The Darts Game application features **automatic UI refresh** functionality that updates all connected clients in real-time whenever game state changes occur. This is implemented using **WebSocket** technology via **Socket.IO**.

## How It Works

### Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   API Request   │────────▶│  Game Manager    │────────▶│   SocketIO      │
│  (HTTP/RabbitMQ)│         │  (Process Score) │         │   (Broadcast)   │
└─────────────────┘         └──────────────────┘         └─────────────────┘
                                                                    │
                                                                    ▼
                                                          ┌─────────────────┐
                                                          │  All Connected  │
                                                          │    Clients      │
                                                          │  (Auto Update)  │
                                                          └─────────────────┘
```

### Key Components

1. **Socket.IO Server** (`app.py`)
   - Manages WebSocket connections
   - Broadcasts game state updates to all connected clients

2. **Game Manager** (`game_manager.py`)
   - Processes game logic
   - Emits `game_state` events via Socket.IO whenever state changes

3. **Client JavaScript** (`main.js`, `control.js`)
   - Connects to Socket.IO server
   - Listens for `game_state` events
   - Updates UI automatically when events are received

## Triggers for Automatic Refresh

The UI automatically refreshes when any of the following actions occur:

### 1. Score Submission

**Via RabbitMQ:**
```python
# Scores received from RabbitMQ automatically trigger refresh
# Message format: {"score": 20, "multiplier": "TRIPLE"}
```

**Via REST API:**
```bash
curl -X POST http://localhost:5000/api/score \
  -H "Content-Type: application/json" \
  -d '{"score": 20, "multiplier": "TRIPLE"}'
```

**Via WebSocket:**
```javascript
socket.emit('manual_score', {
    score: 20,
    multiplier: 'TRIPLE'
});
```

### 2. New Game

**Via REST API:**
```bash
curl -X POST http://localhost:5000/api/game/new \
  -H "Content-Type: application/json" \
  -d '{
    "game_type": "301",
    "players": ["Alice", "Bob"],
    "double_out": false
  }'
```

**Via WebSocket:**
```javascript
socket.emit('new_game', {
    game_type: '301',
    players: ['Alice', 'Bob'],
    double_out: false
});
```

### 3. Player Management

**Add Player (REST API):**
```bash
curl -X POST http://localhost:5000/api/players \
  -H "Content-Type: application/json" \
  -d '{"name": "Charlie"}'
```

**Remove Player (REST API):**
```bash
curl -X DELETE http://localhost:5000/api/players/2
```

**Via WebSocket:**
```javascript
// Add player
socket.emit('add_player', { name: 'Charlie' });

// Remove player
socket.emit('remove_player', { player_id: 2 });
```

### 4. Game Control

**Next Player:**
```javascript
socket.emit('next_player');
```

**Skip to Player:**
```javascript
socket.emit('skip_to_player', { player_id: 1 });
```

## WebSocket Events

### Client → Server Events

| Event | Data | Description |
|-------|------|-------------|
| `new_game` | `{game_type, players, double_out}` | Start a new game |
| `add_player` | `{name}` | Add a player |
| `remove_player` | `{player_id}` | Remove a player |
| `next_player` | - | Move to next player |
| `skip_to_player` | `{player_id}` | Skip to specific player |
| `manual_score` | `{score, multiplier}` | Submit a score |

### Server → Client Events

| Event | Data | Description |
|-------|------|-------------|
| `game_state` | `{players, current_player, game_type, ...}` | **Main event for auto-refresh** |
| `message` | `{text}` | Display a message |
| `big_message` | `{text}` | Display a big message (auto-clears) |
| `play_sound` | `{sound}` | Play a sound effect |
| `play_video` | `{video, angle}` | Play a video effect |

## Testing Automatic Refresh

### Method 1: Use the Test Page

1. Start the application:
   ```bash
   python app.py
   ```

2. Open the test page in your browser:
   ```
   http://localhost:5000/test-refresh
   ```

3. Click the test buttons and watch the game state update automatically!

### Method 2: Use the Test Script

1. Start the application in one terminal:
   ```bash
   python app.py
   ```

2. Open the game UI in a browser:
   ```
   http://localhost:5000
   ```

3. Run the test script in another terminal:
   ```bash
   python examples/test_auto_refresh.py
   ```

4. Watch the UI update automatically as the script makes API calls!

### Method 3: Manual Testing

1. Open the game UI: `http://localhost:5000`
2. Open the control panel: `http://localhost:5000/control`
3. Make changes in the control panel
4. Watch the game UI update automatically!

## Implementation Details

### Game Manager Emits Events

Every time the game state changes, the `GameManager` calls `_emit_game_state()`:

```python
def _emit_game_state(self):
    """Emit game state to all clients"""
    self.socketio.emit("game_state", self.get_game_state())
```

This is called in:
- `new_game()` - When starting a new game
- `add_player()` - When adding a player
- `remove_player()` - When removing a player
- `process_score()` - When processing a score
- `next_player()` - When moving to next player
- `skip_to_player()` - When skipping to a player

### Client Listens for Events

The client JavaScript listens for the `game_state` event:

```javascript
socket.on('game_state', (state) => {
    console.log('Game state:', state);
    updateGameDisplay(state);
});
```

### RabbitMQ Integration

When scores are received from RabbitMQ, they are processed the same way:

```python
def on_score_received(score_data):
    """Callback when a score is received from RabbitMQ"""
    print(f"Score received: {score_data}")
    game_manager.process_score(score_data)
    # game_manager.process_score() automatically emits game_state
```

## Troubleshooting

### UI Not Updating?

1. **Check WebSocket Connection:**
   - Open browser console (F12)
   - Look for "Connected to server" message
   - If you see connection errors, check that Socket.IO is properly initialized

2. **Check Server Logs:**
   - Look for "Client connected" messages
   - Verify that game state changes are being logged

3. **Verify Socket.IO Library:**
   - Make sure the Socket.IO client library is loaded:
     ```html
     <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
     ```

4. **Check CORS Settings:**
   - The app uses `cors_allowed_origins="*"` which should allow all origins
   - If you have custom CORS settings, verify they're correct

5. **Test with the Test Page:**
   - Visit `http://localhost:5000/test-refresh`
   - This page shows detailed logs of all WebSocket events

### RabbitMQ Scores Not Working?

1. **Verify RabbitMQ is Running:**
   ```bash
   # Check if RabbitMQ is running
   sudo systemctl status rabbitmq-server
   ```

2. **Check RabbitMQ Configuration:**
   - Verify `.env` file has correct RabbitMQ settings
   - Check that the exchange and topic are correct

3. **Check Consumer Logs:**
   - Look for "Connected to RabbitMQ" message
   - Verify messages are being received

4. **Test Message Format:**
   - Ensure messages have the correct format:
     ```json
     {
       "score": 20,
       "multiplier": "TRIPLE"
     }
     ```

## Performance Considerations

- **Broadcast to All Clients:** Every game state change is broadcast to all connected clients
- **Efficient Updates:** Only the changed state is sent, not the entire application state
- **Connection Management:** Socket.IO handles reconnection automatically
- **Scalability:** For high-traffic scenarios, consider using Redis adapter for Socket.IO

## Future Enhancements

Possible improvements to the auto-refresh functionality:

1. **Selective Updates:** Only send updates to clients viewing the current game
2. **Diff-based Updates:** Send only the changed fields instead of entire state
3. **Rate Limiting:** Throttle updates during rapid score submissions
4. **Offline Support:** Queue updates when client is disconnected
5. **Multi-room Support:** Separate game rooms for multiple concurrent games

## Related Files

- `/app.py` - Main application with Socket.IO setup
- `/game_manager.py` - Game logic with event emission
- `/static/js/main.js` - Main game UI client
- `/static/js/control.js` - Control panel client
- `/templates/test_refresh.html` - Test page for auto-refresh
- `/examples/test_auto_refresh.py` - Automated test script
- `/rabbitmq_consumer.py` - RabbitMQ consumer

## Summary

The automatic UI refresh is a core feature that makes the Darts Game application feel responsive and real-time. It works seamlessly across:

- ✅ REST API calls
- ✅ WebSocket events
- ✅ RabbitMQ messages
- ✅ Control panel actions
- ✅ Multiple connected clients

All clients stay synchronized automatically without requiring manual page refreshes!