# Darts Game Web Application

A Python web application for managing darts games (301 and Cricket) with RabbitMQ integration for receiving scores.

## Features

- **Multiple Game Modes**: 301, 401, 501, and Cricket
- **Multi-Player Support**: Support for 2-6 players (Cricket max 4)
- **RabbitMQ Integration**: Receives dart scores through RabbitMQ topic subscription
- **Real-time Updates**: WebSocket-based real-time game state updates
- **Web Interface**: Clean, responsive web interface for game display and control
- **Manual Score Entry**: Control panel for manual score entry and game management

## Installation

1. **Install Python dependencies**:
```bash
pip install -r requirements.txt
```

2. **Set up RabbitMQ** (if not already installed):
```bash
# On Ubuntu/Debian
sudo apt-get install rabbitmq-server

# On macOS
brew install rabbitmq

# Start RabbitMQ
sudo systemctl start rabbitmq-server  # Linux
brew services start rabbitmq          # macOS
```

3. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env with your RabbitMQ and Flask settings
```

## Configuration

Edit the `.env` file to configure:

- **RabbitMQ Settings**:
  - `RABBITMQ_HOST`: RabbitMQ server host (default: localhost)
  - `RABBITMQ_PORT`: RabbitMQ server port (default: 5672)
  - `RABBITMQ_USER`: RabbitMQ username (default: guest)
  - `RABBITMQ_PASSWORD`: RabbitMQ password (default: guest)
  - `RABBITMQ_EXCHANGE`: Exchange name (default: darts_exchange)
  - `RABBITMQ_TOPIC`: Topic pattern (default: darts.scores.#)

- **Flask Settings**:
  - `FLASK_HOST`: Flask server host (default: 0.0.0.0)
  - `FLASK_PORT`: Flask server port (default: 5000)
  - `FLASK_DEBUG`: Debug mode (default: True)

## Usage

1. **Start the application**:
```bash
python app.py
```

2. **Access the web interface**:
   - Main game board: http://localhost:5000/
   - Control panel: http://localhost:5000/control

3. **Send scores via RabbitMQ**:

The application listens for messages on the configured RabbitMQ exchange and topic.

**Message Format** (JSON):
```json
{
  "score": 20,
  "multiplier": "TRIPLE",
  "user": "Player 1"
}
```

**Multiplier Options**:
- `SINGLE`: Single score
- `DOUBLE`: Double score
- `TRIPLE`: Triple score
- `BULL`: Bullseye (25 points)
- `DBLBULL`: Double Bullseye (50 points)

## Game Rules

### 301/401/501
- Players start with 301/401/501 points
- Each dart score is subtracted from the player's total
- First player to reach exactly 0 wins
- Going below 0 results in a "bust" - score returns to start of turn

### Cricket
- Players must hit 15, 16, 17, 18, 19, 20, and Bull (25)
- Each number must be hit 3 times to "open" it
- Once opened, additional hits score points
- When all players have hit a number 3 times, it's "closed"
- First player to open all numbers with the highest score wins

## API Endpoints

### REST API

- `GET /api/game/state` - Get current game state
- `POST /api/game/new` - Start a new game
  ```json
  {
    "game_type": "301",
    "players": ["Player 1", "Player 2"]
  }
  ```
- `GET /api/players` - Get all players
- `POST /api/players` - Add a player
  ```json
  {
    "name": "Player 3"
  }
  ```
- `DELETE /api/players/<player_id>` - Remove a player

### WebSocket Events

**Client → Server**:
- `new_game` - Start a new game
- `add_player` - Add a player
- `remove_player` - Remove a player
- `next_player` - Move to next player
- `skip_to_player` - Skip to specific player
- `manual_score` - Submit a manual score

**Server → Client**:
- `game_state` - Game state update
- `play_sound` - Play a sound effect
- `play_video` - Play a video effect
- `message` - Display a message
- `big_message` - Display a big message

## Testing RabbitMQ Integration

Use the included test script to send test scores:

```bash
python test_rabbitmq.py
```

Or manually publish messages using RabbitMQ tools:

```bash
# Install rabbitmq management tools
sudo rabbitmq-plugins enable rabbitmq_management

# Publish a test message
rabbitmqadmin publish exchange=darts_exchange routing_key=darts.scores.test \
  payload='{"score": 20, "multiplier": "TRIPLE", "user": "Test Player"}'
```

## Project Structure

```
dartserver-pythonapp/
├── app.py                  # Main Flask application
├── game_manager.py         # Game logic manager
├── rabbitmq_consumer.py    # RabbitMQ consumer
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
├── games/
│   ├── __init__.py
│   ├── game_301.py        # 301/401/501 game logic
│   └── game_cricket.py    # Cricket game logic
├── templates/
│   ├── index.html         # Main game board
│   └── control.html       # Control panel
└── static/
    ├── css/
    │   ├── style.css      # Main styles
    │   └── control.css    # Control panel styles
    └── js/
        ├── main.js        # Main game board JavaScript
        └── control.js     # Control panel JavaScript
```

## Integration with Existing System

This Python application can work alongside your existing Node.js darts application. You can:

1. Use the Python app as a standalone system with RabbitMQ
2. Bridge the Node.js app to send scores to RabbitMQ
3. Use the Python app's REST API to integrate with other systems

## Troubleshooting

**RabbitMQ Connection Issues**:
- Ensure RabbitMQ is running: `sudo systemctl status rabbitmq-server`
- Check firewall settings
- Verify credentials in `.env` file

**WebSocket Connection Issues**:
- Check browser console for errors
- Ensure Flask server is running
- Try disabling browser extensions

**Game Logic Issues**:
- Check server console for error messages
- Verify score message format
- Use the control panel to manually test game logic

## License

See LICENSE file in the root directory.

## Credits

Built for the DigiDarts project - a rich media darts experience.