# Quick Start Guide

## Option 1: Docker (Recommended)

The easiest way to get started is using Docker Compose, which will set up both RabbitMQ and the application:

```bash
docker-compose up
```

This will:
- Start RabbitMQ on port 5672 (management UI on 15672)
- Start the Darts application on port 5000

Access the application:
- Game Board: http://localhost:5000
- Control Panel: http://localhost:5000/control
- RabbitMQ Management: http://localhost:15672 (guest/guest)

## Option 2: Manual Setup

### 1. Install RabbitMQ

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install rabbitmq-server
sudo systemctl start rabbitmq-server
```

**macOS:**
```bash
brew install rabbitmq
brew services start rabbitmq
```

**Windows:**
Download and install from https://www.rabbitmq.com/download.html

### 2. Set up Python environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env if needed
```

### 3. Start the application

```bash
python app.py
```

Or use the startup script:
```bash
./run.sh
```

## Testing the Application

### 1. Access the Web Interface

Open your browser:
- Main Board: http://localhost:5000
- Control Panel: http://localhost:5000/control

### 2. Start a Game

From the Control Panel:
1. Select game type (301, 401, 501, or Cricket)
2. Add players (or use default Player 1 and Player 2)
3. Click "Start New Game"

### 3. Send Test Scores

**Option A: Use the test script**
```bash
python test_rabbitmq.py
```

**Option B: Use the Control Panel**
- Go to "Manual Score Entry" section
- Enter score and multiplier
- Click "Submit Score"

**Option C: Send via RabbitMQ directly**
```bash
# Install rabbitmqadmin (if not already installed)
wget http://localhost:15672/cli/rabbitmqadmin
chmod +x rabbitmqadmin

# Send a test score
./rabbitmqadmin publish exchange=darts_exchange \
  routing_key=darts.scores.test \
  payload='{"score": 20, "multiplier": "TRIPLE", "user": "Player 1"}'
```

## Example Game Flow

### Playing 301

1. Start a new 301 game with 2 players
2. Each player starts with 301 points
3. Send scores via RabbitMQ or manual entry:
   ```json
   {"score": 20, "multiplier": "TRIPLE"}  // Subtracts 60
   {"score": 19, "multiplier": "DOUBLE"}  // Subtracts 38
   {"score": 17, "multiplier": "SINGLE"}  // Subtracts 17
   ```
4. After 3 throws, click "Next Player" to switch turns
5. First player to reach exactly 0 wins!

### Playing Cricket

1. Start a new Cricket game with 2-4 players
2. Players must hit 15, 16, 17, 18, 19, 20, and Bull (25)
3. Each number needs 3 hits to "open"
4. Once opened, additional hits score points
5. First to open all numbers with highest score wins

Example scores:
```json
{"score": 20, "multiplier": "TRIPLE"}  // 3 hits on 20 - opens it!
{"score": 19, "multiplier": "DOUBLE"}  // 2 hits on 19
{"score": 25, "multiplier": "BULL"}    // 1 hit on Bull
```

## Integration with Arduino/ESP32

If you have an electronic dartboard with Arduino/ESP32:

1. Configure your Arduino to publish to RabbitMQ
2. Use the message format:
   ```json
   {
     "score": <base_score>,
     "multiplier": "SINGLE|DOUBLE|TRIPLE|BULL|DBLBULL",
     "user": "<player_name>"
   }
   ```

Example Arduino code snippet:
```cpp
// Pseudo-code
void sendScore(int score, String multiplier) {
  String payload = "{\"score\":" + String(score) + 
                   ",\"multiplier\":\"" + multiplier + "\"}";
  mqttClient.publish("darts.scores.board1", payload);
}
```

## Troubleshooting

### RabbitMQ not connecting
- Check if RabbitMQ is running: `sudo systemctl status rabbitmq-server`
- Verify credentials in `.env` file
- Check firewall settings

### Application won't start
- Ensure Python 3.10+ is installed: `python --version`
- Check all dependencies are installed: `pip list`
- Look for error messages in console

### Scores not appearing
- Check RabbitMQ management UI (http://localhost:15672)
- Verify exchange `darts_exchange` exists
- Check application logs for errors
- Ensure message format is correct JSON

## Next Steps

- Customize player names
- Add audio files to `/static/audio/` for sound effects
- Add video files to `/static/video/` for animations
- Integrate with your electronic dartboard
- Deploy to a server for remote access

## Support

For issues or questions, check the main README.md or create an issue on GitHub.