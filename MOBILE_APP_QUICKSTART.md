# Mobile App Quick Start Guide

Get started with the dartboard mobile app in 5 minutes!

## For Users

### 1. Access the Mobile App

Open your mobile browser and navigate to:
```
https://yourdomain.com/mobile
```

Or for local testing:
```
http://localhost:5000/mobile
```

### 2. Install as PWA (Optional)

**On Android (Chrome):**
1. Tap the menu (⋮) in the top-right
2. Select "Add to Home screen"
3. Tap "Add"

**On iOS (Safari):**
1. Tap the Share button
2. Scroll down and tap "Add to Home Screen"
3. Tap "Add"

### 3. Set Up Your Dartboard

#### Step 1: Create an API Key
1. Go to **Account** page
2. Tap "Generate New API Key"
3. Give it a name (e.g., "My Dartboard")
4. **Save the key** - you'll need it for your dartboard

#### Step 2: Register Your Dartboard
1. Go to **Dartboard Setup** page
2. Tap "Register New Dartboard"
3. Enter a unique ID (e.g., `DART-ABC123`)
4. Enter the dartboard key (from Step 1)
5. Tap "Register"

#### Step 3: Configure Mobile Hotspot
1. Go to **Hotspot Control** page
2. Select your dartboard from the list
3. Note the SSID and Password shown
4. **Manually create a mobile hotspot** on your phone:
   - **Android**: Settings → Network & Internet → Hotspot & tethering → Wi-Fi hotspot
   - **iOS**: Settings → Personal Hotspot
5. Set the hotspot name to the SSID shown (e.g., `DART-ABC123`)
6. Set the password to the one shown
7. Enable the hotspot

#### Step 4: Connect Your Dartboard
1. Power on your dartboard
2. It will search for the hotspot with its ID
3. Once connected, you'll see "Connected" status in the app
4. You're ready to play!

### 4. Start a Game

#### As Game Master:
1. Go to **Game Master** page
2. Select game type (301, 401, 501, or Cricket)
3. Add players
4. Tap "Start Game"

#### As Player:
1. Go to **Gameplay** page
2. Watch the live scoreboard
3. Throw your darts!
4. Scores update in real-time

### 5. View Results

1. Go to **Results** page
2. See all your past games
3. Filter by game type or date
4. Tap a game to see details

## For Dartboard Developers

### Dartboard Connection Flow

```
1. Dartboard powers on
2. Searches for WiFi with SSID matching its ID
3. Connects to mobile hotspot
4. Sends connection request to API
5. Receives acknowledgment
6. Ready to send scores
```

### API Integration

#### 1. Connect to Hotspot

Configure your dartboard to:
- Search for SSID: `DART-{YOUR-ID}`
- Use WPA2 password from app
- Connect to WiFi

#### 2. Send Connection Request

```http
POST /api/dartboard/connect
Headers:
  X-API-Key: your-api-key-here
  Content-Type: application/json
Body:
  {
    "dartboard_id": "DART-ABC123"
  }
```

Response:
```json
{
  "success": true,
  "message": "Connection acknowledged"
}
```

#### 3. Submit Scores

```http
POST /api/dartboard/score
Headers:
  X-API-Key: your-api-key-here
  Content-Type: application/json
Body:
  {
    "player_id": 1,
    "score": 60,
    "multiplier": 1,
    "segment": 20,
    "throw_number": 1
  }
```

Response:
```json
{
  "success": true,
  "message": "Score submitted"
}
```

### Example Python Code

```python
import requests

API_URL = "https://yourdomain.com"
API_KEY = "your-api-key-here"
DARTBOARD_ID = "DART-ABC123"

# Connect
response = requests.post(
    f"{API_URL}/api/dartboard/connect",
    headers={"X-API-Key": API_KEY},
    json={"dartboard_id": DARTBOARD_ID}
)
print(response.json())

# Submit score
response = requests.post(
    f"{API_URL}/api/dartboard/score",
    headers={"X-API-Key": API_KEY},
    json={
        "player_id": 1,
        "score": 60,
        "multiplier": 1,
        "segment": 20,
        "throw_number": 1
    }
)
print(response.json())
```

### Example Arduino/ESP32 Code

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

const char* ssid = "DART-ABC123";
const char* password = "your-hotspot-password";
const char* apiUrl = "http://192.168.43.1:5000";  // Mobile hotspot IP
const char* apiKey = "your-api-key-here";

void setup() {
  Serial.begin(115200);
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected!");
  
  // Send connection request
  sendConnect();
}

void sendConnect() {
  HTTPClient http;
  http.begin(String(apiUrl) + "/api/dartboard/connect");
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", apiKey);
  
  StaticJsonDocument<200> doc;
  doc["dartboard_id"] = ssid;
  
  String requestBody;
  serializeJson(doc, requestBody);
  
  int httpCode = http.POST(requestBody);
  if (httpCode > 0) {
    String response = http.getString();
    Serial.println(response);
  }
  http.end();
}

void sendScore(int playerId, int score, int multiplier, int segment) {
  HTTPClient http;
  http.begin(String(apiUrl) + "/api/dartboard/score");
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", apiKey);
  
  StaticJsonDocument<200> doc;
  doc["player_id"] = playerId;
  doc["score"] = score;
  doc["multiplier"] = multiplier;
  doc["segment"] = segment;
  doc["throw_number"] = 1;
  
  String requestBody;
  serializeJson(doc, requestBody);
  
  int httpCode = http.POST(requestBody);
  if (httpCode > 0) {
    String response = http.getString();
    Serial.println(response);
  }
  http.end();
}

void loop() {
  // Example: Send score when dart hits
  // sendScore(1, 60, 1, 20);
  delay(1000);
}
```

## Troubleshooting

### Can't Access Mobile App
- Check if server is running
- Verify URL is correct
- Try clearing browser cache

### PWA Won't Install
- Ensure you're using HTTPS (required for PWA)
- Check if manifest.json loads
- Try a different browser

### Dartboard Won't Connect
- Verify hotspot is enabled
- Check SSID matches dartboard ID exactly
- Verify password is correct
- Check dartboard is in range

### Scores Not Updating
- Check dartboard connection status
- Verify API key is valid
- Check WebSocket connection
- Review browser console for errors

### Hotspot Issues on iOS
- iOS doesn't allow custom SSID names for Personal Hotspot
- Use Android device for hotspot
- Or use a dedicated WiFi router

## Tips & Tricks

### Offline Mode
- The app works offline after first load
- Scores are queued and synced when online
- Perfect for areas with poor connectivity

### Multiple Dartboards
- Register multiple dartboards
- Each gets unique ID and API key
- Switch between them in Hotspot Control

### Battery Saving
- Disable hotspot when not playing
- Close unused browser tabs
- Use airplane mode + WiFi only

### Security
- Keep API keys secret
- Don't share dartboard credentials
- Revoke old API keys regularly
- Use strong hotspot passwords

## Next Steps

- Read the [Full User Guide](docs/MOBILE_APP_GUIDE.md)
- Check [Architecture Documentation](docs/MOBILE_APP_ARCHITECTURE.md)
- Review [Deployment Guide](MOBILE_APP_DEPLOYMENT.md)
- Run tests: `python test_mobile_app.py`

## Support

Need help? Check:
- Documentation in `/docs/` folder
- Test your setup: `python test_mobile_app.py`
- Review logs for errors
- Check GitHub issues

Happy darting! 🎯