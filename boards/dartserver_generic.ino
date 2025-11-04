/**
 * Generic Dartboard Arduino Sketch
 *
 * This is a generic implementation for any dartboard using a GPIO pin matrix.
 * All board-specific configurations are defined in a separate header file.
 *
 * To use this sketch:
 * 1. Create a configuration header (e.g., carromco_config.h, crivit_config.h)
 * 2. Include it below in the #include directive
 * 3. Upload to your ESP32
 *
 * Configuration header must define:
 * - const int masterLines
 * - const int slaveLines
 * - int matrixMaster[]
 * - int matrixSlave[]
 * - const char* BOARD_TYPE
 * - const char* BOARD_NAME
 */

// ============================================================================
// INCLUDE YOUR BOARD CONFIGURATION HERE
// ============================================================================
// Uncomment the configuration you want to use:
// #include "carromco_config.h"
// #include "crivit_config.h"

// For now, using default carromco config
#include "carromco_config.h"

// ============================================================================
// LIBRARIES
// ============================================================================
#include <ArduinoJson.h>
#include <WiFi.h>
#include <ArduinoHttpClient.h>

// ============================================================================
// NETWORK CONFIGURATION
// ============================================================================
const char* ssid = "<SSID>";
const char* password = "<SSID_KEY>";
const char* serverAddress = "85.214.85.65";
const int serverPort = 5001;

WiFiClient wifiClient;
HttpClient http(wifiClient, serverAddress, serverPort);

// ============================================================================
// BUTTON HANDLING
// ============================================================================
int bigRedState = 0;
int lastButtonState = HIGH;
unsigned long lastPressTime = 0;
unsigned long debounceDelay = 1000;

// ============================================================================
// TIMING
// ============================================================================
unsigned long previousMillis = 0;
const long interval = 1000;

// ============================================================================
// SETUP
// ============================================================================
void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.print("Starting ");
  Serial.println(BOARD_NAME);
  Serial.print("Board Type: ");
  Serial.println(BOARD_TYPE);
  Serial.print("Matrix: ");
  Serial.print(masterLines);
  Serial.print("x");
  Serial.println(slaveLines);

  // WiFi Configuration
  WiFi.config(INADDR_NONE, INADDR_NONE, INADDR_NONE, INADDR_NONE);
  WiFi.setHostname("esp32-dartboard");
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  Serial.print("Connecting to Wi-Fi");
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  Serial.println();
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("Connected to Wi-Fi");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("WARNING: Failed to connect to Wi-Fi - will retry in loop");
  }

  // Initialize matrix pins
  Serial.println("Initializing GPIO matrix pins...");
  for (int j = 0; j < slaveLines; j++) {
    pinMode(matrixSlave[j], INPUT_PULLUP);
  }
  for (int i = 0; i < masterLines; i++) {
    pinMode(matrixMaster[i], OUTPUT);
    digitalWrite(matrixMaster[i], HIGH);  // Keep HIGH by default
  }

  Serial.println("Setup complete. Ready for throws.");
  delay(1000);
}

// ============================================================================
// MAIN LOOP
// ============================================================================
void loop() {
  // Check WiFi connection periodically
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= interval) {
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("Wi-Fi disconnected. Attempting to reconnect...");
      WiFi.reconnect();
    }
    previousMillis = currentMillis;
  }

  // Check for dart throws
  throwCheck();
}

// ============================================================================
// DARTBOARD DETECTION
// ============================================================================
/**
 * Scans the GPIO matrix for dart throws
 * When a throw is detected, sends the raw master/slave pin combination to the server
 * The server then uses the board type to determine the score and multiplier
 */
void throwCheck() {
  for (int i = 0; i < masterLines; i++) {
    // Set this row to LOW to scan
    digitalWrite(matrixMaster[i], LOW);
    delayMicroseconds(100);  // Small delay for signal stabilization

    for (int j = 0; j < slaveLines; j++) {
      // Check if column pin is pulled LOW (dart detected)
      if (digitalRead(matrixSlave[j]) == LOW) {
        // Dart detected!
        int masterPin = matrixMaster[i];
        int slavePin = matrixSlave[j];

        // Debug output
        Serial.print("DART DETECTED - Master: ");
        Serial.print(masterPin);
        Serial.print(", Slave: ");
        Serial.println(slavePin);

        // Send to server
        sendData(masterPin, slavePin);

        // Debounce - wait for dart to settle
        delay(500);
        break;  // Exit slave loop, continue with next master row
      }
    }

    // Reset this row to HIGH
    digitalWrite(matrixMaster[i], HIGH);
  }
}

// ============================================================================
// NETWORK COMMUNICATION
// ============================================================================
/**
 * Sends dart throw data to the dartserver API
 *
 * The API endpoint is now generic and handles board type routing:
 * - For new boards: POST /api/Throw/zone with raw pins and boardType
 * - Server determines score based on database mappings
 * - For legacy boards: falls back to /api/Throw with score+multiplier
 */
void sendData(int masterPin, int slavePin) {
  // Reconnect WiFi if necessary
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Wi-Fi not connected. Retrying...");
    WiFi.reconnect();
    delay(500);
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("Failed to connect to Wi-Fi. Discarding throw.");
      return;
    }
  }

  if (WiFi.status() == WL_CONNECTED) {
    // Create JSON payload with raw pin data
    StaticJsonDocument<256> doc;
    doc["masterPin"] = masterPin;
    doc["slavePin"] = slavePin;
    doc["boardType"] = String(BOARD_TYPE);
    doc["boardName"] = String(BOARD_NAME);
    doc["timestamp"] = millis();

    String jsonString;
    serializeJson(doc, jsonString);

    Serial.print("Sending: ");
    Serial.println(jsonString);

    // Send to generic endpoint
    http.beginRequest();
    http.post("/api/Throw/zone", "application/json", jsonString);

    int httpResponseCode = http.responseStatusCode();
    String response = http.responseBody();

    Serial.print("Response Code: ");
    Serial.println(httpResponseCode);
    if (response.length() > 0) {
      Serial.print("Response: ");
      Serial.println(response);
    }

    http.endRequest();
  } else if (WiFi.status() == WL_CONNECT_FAILED ||
             WiFi.status() == WL_CONNECTION_LOST ||
             WiFi.status() == WL_DISCONNECTED) {
    Serial.println("Wi-Fi connection lost.");
  }
}

// ============================================================================
// OPTIONAL: BIG RED BUTTON HANDLER
// ============================================================================
/**
 * Uncomment this if your dartboard has a physical button for special actions
 * (e.g., "Start Game", "Undo Last Throw", etc.)
 */
/*
void bigRedCheck() {
  // bigRedState = digitalRead(bigRedBtn);
  if (lastButtonState == LOW && bigRedState == LOW) {
    // Button held down - do nothing
    Serial.println("Button held");
  } else if (lastButtonState == HIGH && bigRedState == LOW) {
    // Button pressed
    lastButtonState = LOW;
    Serial.println("Big Red button pressed");
    sendData(0, 0);  // Special code for button press
  } else {
    if (lastButtonState != HIGH) {
      lastButtonState = HIGH;
    }
  }
}
*/
