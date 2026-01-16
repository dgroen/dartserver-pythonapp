# Dartboard Client Integration Guide

This guide explains how to integrate dartboard hardware with the Darts API Gateway using OAuth2 client credentials authentication.

## Overview

The API Gateway provides a secure endpoint for dartboard hardware to submit throws. This replaces the legacy insecure `/api/Throw/zone` endpoint with a properly authenticated `/api/v1/dartboard/throw` endpoint.

## Key Features

- **Secure Authentication**: OAuth2 client credentials flow
- **Automatic Token Management**: Handle token expiration and renewal
- **Simple Integration**: HTTP REST API
- **Pin-based Scoring**: Send GPIO pin combinations, server maps to scores
- **Multiple Board Types**: Support for different dartboard models

## Prerequisites

- Dartboard hardware with network connectivity
- Client credentials (client_id and client_secret) from WSO2
- HTTPS support (for production) or HTTP (for development)

## Quick Start

### 1. Obtain Credentials

Contact your system administrator to obtain:
- `CLIENT_ID`: Unique identifier for your dartboard (e.g., `dartboard_001_client`)
- `CLIENT_SECRET`: Secret key for authentication
- `API_GATEWAY_URL`: URL of the API Gateway (e.g., `https://api.dartsapp.example.com/darts/v1`)
- `TOKEN_URL`: OAuth2 token endpoint (e.g., `https://wso2-apim:9443/oauth2/token`)

### 2. Configure Your Dartboard

Store credentials securely on your dartboard device. Example configuration:

```ini
# dartboard.conf
[oauth2]
client_id = dartboard_001_client
client_secret = 1234567890abcdef1234567890abcdef
token_url = https://wso2-apim:9443/oauth2/token
scope = dartboard:write

[api]
gateway_url = https://api.dartsapp.example.com/darts/v1
board_type = carromco
```

### 3. Implement Token Management

Your dartboard firmware must:
1. Obtain an access token before submitting throws
2. Cache the token until it expires
3. Refresh the token when expired
4. Retry failed requests

## Implementation Examples

### Python Example

```python
import requests
import time
from datetime import datetime, timedelta

class DartboardClient:
    def __init__(self, client_id, client_secret, token_url, gateway_url, board_type):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.gateway_url = gateway_url
        self.board_type = board_type
        self.access_token = None
        self.token_expires_at = None

    def get_access_token(self):
        """Obtain a new access token using client credentials"""
        response = requests.post(
            self.token_url,
            auth=(self.client_id, self.client_secret),
            data={
                "grant_type": "client_credentials",
                "scope": "dartboard:write"
            },
            verify=True  # Set to False for development with self-signed certs
        )
        
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data["access_token"]
            expires_in = token_data["expires_in"]
            # Refresh token 60 seconds before expiration
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
            return True
        else:
            print(f"Failed to obtain token: {response.status_code} {response.text}")
            return False

    def ensure_valid_token(self):
        """Ensure we have a valid access token"""
        if not self.access_token or datetime.now() >= self.token_expires_at:
            return self.get_access_token()
        return True

    def submit_throw(self, master_pin, slave_pin, max_retries=3):
        """Submit a dartboard throw"""
        for attempt in range(max_retries):
            if not self.ensure_valid_token():
                print("Failed to obtain valid token")
                time.sleep(1)
                continue

            response = requests.post(
                f"{self.gateway_url}/api/v1/dartboard/throw",
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "masterPin": master_pin,
                    "slavePin": slave_pin,
                    "boardType": self.board_type
                },
                verify=True  # Set to False for development
            )

            if response.status_code == 201:
                result = response.json()
                print(f"Throw submitted successfully: {result}")
                return True
            elif response.status_code == 401:
                # Token expired, retry with new token
                print("Token expired, refreshing...")
                self.access_token = None
                continue
            else:
                print(f"Failed to submit throw: {response.status_code} {response.text}")
                return False

        print("Max retries exceeded")
        return False

# Usage
if __name__ == "__main__":
    client = DartboardClient(
        client_id="dartboard_001_client",
        client_secret="your_secret_here",
        token_url="https://wso2-apim:9443/oauth2/token",
        gateway_url="https://api.dartsapp.example.com/darts/v1",
        board_type="carromco"
    )

    # Simulate a triple 20 throw
    client.submit_throw(master_pin=4, slave_pin=13)
```

### C++ Example (for Arduino/ESP32)

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

class DartboardClient {
private:
    String clientId;
    String clientSecret;
    String tokenUrl;
    String gatewayUrl;
    String boardType;
    String accessToken;
    unsigned long tokenExpiresAt;

public:
    DartboardClient(String cId, String cSecret, String tUrl, String gUrl, String bType) 
        : clientId(cId), clientSecret(cSecret), tokenUrl(tUrl), 
          gatewayUrl(gUrl), boardType(bType), tokenExpiresAt(0) {}

    bool getAccessToken() {
        HTTPClient http;
        http.begin(tokenUrl);
        
        // Set authorization header (Basic Auth)
        String auth = clientId + ":" + clientSecret;
        String authHeader = "Basic " + base64::encode(auth);
        http.addHeader("Authorization", authHeader);
        http.addHeader("Content-Type", "application/x-www-form-urlencoded");
        
        String payload = "grant_type=client_credentials&scope=dartboard:write";
        int httpCode = http.POST(payload);
        
        if (httpCode == 200) {
            String response = http.getString();
            DynamicJsonDocument doc(1024);
            deserializeJson(doc, response);
            
            accessToken = doc["access_token"].as<String>();
            int expiresIn = doc["expires_in"];
            tokenExpiresAt = millis() + (expiresIn - 60) * 1000; // Refresh 60s early
            
            http.end();
            return true;
        }
        
        http.end();
        return false;
    }

    bool ensureValidToken() {
        if (accessToken.length() == 0 || millis() >= tokenExpiresAt) {
            return getAccessToken();
        }
        return true;
    }

    bool submitThrow(int masterPin, int slavePin) {
        if (!ensureValidToken()) {
            Serial.println("Failed to obtain valid token");
            return false;
        }

        HTTPClient http;
        String url = gatewayUrl + "/api/v1/dartboard/throw";
        http.begin(url);
        
        http.addHeader("Authorization", "Bearer " + accessToken);
        http.addHeader("Content-Type", "application/json");
        
        DynamicJsonDocument doc(256);
        doc["masterPin"] = masterPin;
        doc["slavePin"] = slavePin;
        doc["boardType"] = boardType;
        
        String payload;
        serializeJson(doc, payload);
        
        int httpCode = http.POST(payload);
        
        if (httpCode == 201) {
            Serial.println("Throw submitted successfully");
            http.end();
            return true;
        } else if (httpCode == 401) {
            // Token expired, retry
            Serial.println("Token expired, retrying...");
            accessToken = "";
            http.end();
            return submitThrow(masterPin, slavePin);
        } else {
            Serial.printf("Failed to submit throw: %d\n", httpCode);
            http.end();
            return false;
        }
    }
};

// Usage
DartboardClient* dartboard;

void setup() {
    Serial.begin(115200);
    
    // Connect to WiFi
    WiFi.begin("YOUR_SSID", "YOUR_PASSWORD");
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println("\nWiFi connected");
    
    // Initialize dartboard client
    dartboard = new DartboardClient(
        "dartboard_001_client",
        "your_secret_here",
        "https://wso2-apim:9443/oauth2/token",
        "https://api.dartsapp.example.com/darts/v1",
        "carromco"
    );
}

void loop() {
    // Simulate dart throw detection
    if (dartDetected()) {
        int masterPin = readMasterPin();
        int slavePin = readSlavePin();
        dartboard->submitThrow(masterPin, slavePin);
    }
    delay(100);
}
```

## Pin Mapping

The server maps GPIO pin combinations to dart scores based on board type. Example for Carromco board:

| Master Pin | Slave Pin | Zone | Multiplier | Score |
|------------|-----------|------|------------|-------|
| 4 | 13 | 20 | TRIPLE | 60 |
| 5 | 10 | 15 | DOUBLE | 30 |
| 7 | 13 | 25 | DBLBULL | 50 |
| ... | ... | ... | ... | ... |

Your dartboard firmware should:
1. Detect which pins are activated when a dart hits
2. Send the raw pin numbers to the API
3. Let the server calculate the actual score

## Error Handling

### Common Errors

| Status Code | Error | Solution |
|-------------|-------|----------|
| 401 | Unauthorized | Token expired or invalid - obtain new token |
| 400 | Bad Request | Invalid pin data - check masterPin, slavePin, boardType |
| 403 | Forbidden | Insufficient scopes - contact admin for correct scopes |
| 500 | Server Error | Temporary server issue - retry with exponential backoff |

### Retry Strategy

Implement exponential backoff for failed requests:

```python
def submit_with_backoff(client, master_pin, slave_pin, max_retries=5):
    for attempt in range(max_retries):
        if client.submit_throw(master_pin, slave_pin):
            return True
        
        # Exponential backoff: 1s, 2s, 4s, 8s, 16s
        wait_time = min(2 ** attempt, 30)  # Cap at 30 seconds
        print(f"Retry {attempt + 1}/{max_retries} in {wait_time}s...")
        time.sleep(wait_time)
    
    return False
```

## Testing Your Integration

### 1. Test Token Acquisition

```bash
curl -X POST https://wso2-apim:9443/oauth2/token \
  -u "dartboard_001_client:YOUR_SECRET" \
  -d "grant_type=client_credentials&scope=dartboard:write"
```

Expected response:
```json
{
  "access_token": "eyJhbGc...",
  "scope": "dartboard:write",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### 2. Test Throw Submission

```bash
curl -X POST https://api.dartsapp.example.com/darts/v1/api/v1/dartboard/throw \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "masterPin": 4,
    "slavePin": 13,
    "boardType": "carromco"
  }'
```

Expected response:
```json
{
  "status": "success",
  "message": "Throw submitted successfully",
  "data": {
    "masterPin": 4,
    "slavePin": 13,
    "boardType": "carromco",
    "client_id": "dartboard_001_client",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### 3. Test with Simulator

Use the provided test script:

```bash
# Install dependencies
pip install requests

# Run simulator
python dartboard_simulator.py \
  --client-id dartboard_001_client \
  --client-secret YOUR_SECRET \
  --token-url https://wso2-apim:9443/oauth2/token \
  --gateway-url https://api.dartsapp.example.com/darts/v1 \
  --board-type carromco
```

## Security Best Practices

1. **Store credentials securely**
   - Never hardcode credentials in firmware
   - Use secure storage (encrypted flash, TPM)
   - Rotate secrets regularly

2. **Use HTTPS in production**
   - Always validate SSL certificates
   - Use certificate pinning if possible
   - Only disable SSL verification in development

3. **Handle tokens carefully**
   - Don't log access tokens
   - Clear tokens from memory when done
   - Use short-lived tokens

4. **Implement rate limiting**
   - Don't spam the API
   - Respect HTTP 429 (Too Many Requests) responses
   - Implement local debouncing

## Troubleshooting

### Connection Issues

```
Error: Connection refused
```
- Check network connectivity
- Verify API Gateway URL is correct
- Check firewall rules

### Authentication Issues

```
Error: 401 Unauthorized
```
- Verify client ID and secret are correct
- Check token hasn't expired
- Ensure correct scope is requested

### Invalid Data

```
Error: 400 Bad Request - Invalid pin values
```
- Ensure masterPin and slavePin are integers
- Check boardType is a valid string
- Verify JSON format is correct

## Support

For issues or questions:
- Check the API documentation: `https://api.dartsapp.example.com/darts/v1/docs`
- Review logs on the dartboard device
- Contact system administrator for credential issues
- Report bugs to the development team

## Reference Implementation

A complete reference implementation is available in the `examples/dartboard-client/` directory:
- `dartboard_client.py` - Python reference implementation
- `dartboard_client.ino` - Arduino/ESP32 example
- `dartboard_simulator.py` - Testing and simulation tool

## API Reference

For complete API documentation, see:
- OpenAPI Specification: `src/api_gateway/openapi.yaml`
- Interactive docs: `https://api.dartsapp.example.com/darts/v1/docs`
