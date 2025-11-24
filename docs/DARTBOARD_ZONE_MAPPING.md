# Dartboard Zone Mapping Architecture

## Overview

This document describes the new dartboard zone mapping system that allows generic GPIO pin-based dartboards to work with the DartServer application. The system supports:

1. **Generic pin-based architecture** - Dartboards send raw GPIO pin combinations
2. **Multi-board support** - Different dartboard types can be registered with their own pin mappings
3. **Backwards compatibility** - Legacy boards using score/multiplier format still work
4. **Centralized mapping** - All zone mapping logic lives on the server, not on the hardware

## Problem Statement

Previously, dartboards had hardcoded zone mappings in their firmware (Arduino code). This created several issues:

- **Firmware updates required** for each new dartboard type
- **Hardcoded multiplier arrays** that were error-prone (e.g., triple 4 and 13 were missing)
- **Array bounds bugs** - loops accessing out-of-bounds indices
- **No support for multiple board types** without firmware changes
- **Difficult to debug** - zone mapping errors embedded in hardware

## Solution

The new architecture separates concerns:

### Arduino/Hardware Layer

- Send raw **GPIO pin combinations** to the server
- Send **dartboard type identifier** for lookup
- No zone mapping logic on hardware

### Server Layer

- Maintain **dartboard type registry** in database
- Store **GPIO pin to zone mappings** per dartboard type
- **Calculate scores** from base value and multiplier
- Support both **new generic format** and **legacy format** endpoints

## Database Schema

### DartboardType Table

```sql
CREATE TABLE dartboard_type (
  id INTEGER PRIMARY KEY,
  name VARCHAR(100) UNIQUE NOT NULL,  -- e.g., 'carromco', 'winmau'
  brand VARCHAR(100) NOT NULL,        -- e.g., 'Carromco', 'Winmau'
  model VARCHAR(100),                 -- e.g., 'Striker', 'Blade 6'
  description TEXT,
  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

### DartboardZoneMapping Table

```sql
CREATE TABLE dartboard_zone_mapping (
  id INTEGER PRIMARY KEY,
  dartboard_type_id INTEGER NOT NULL REFERENCES dartboard_type(id),
  master_pin INTEGER NOT NULL,        -- Row GPIO pin
  slave_pin INTEGER NOT NULL,         -- Column GPIO pin
  zone_number INTEGER NOT NULL,       -- 1-20 or 25 (bull)
  multiplier_type VARCHAR(20),        -- SINGLE, DOUBLE, TRIPLE, BULL, DBLBULL
  base_value INTEGER NOT NULL,        -- 1-20 or 25
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  UNIQUE(dartboard_type_id, master_pin, slave_pin)
);
```

## API Endpoints

### New Generic Format Endpoint

#### POST /api/Throw/zone

Send raw GPIO pin combination for zone lookup

**Request:**

```json
{
  "masterPin": 4,
  "slavePin": 13,
  "boardType": "carromco",
  "user": "dgroen"
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Score submitted",
  "zone_info": {
    "zone_number": 20,
    "multiplier_type": "TRIPLE",
    "base_value": 20,
    "score": 60
  }
}
```

### Legacy Endpoint (Backwards Compatibility)

#### POST /api/Throw

Old format for existing boards - still supported

**Request:**

```json
{
  "score": 20,
  "multiplier": "TRIPLE",
  "user": "Alice"
}
```

**Response:**

```json
{
  "status": "success",
  "message": "Score submitted"
}
```

### Dartboard Management Endpoints

#### GET /api/dartboard/types

Get all registered dartboard types

**Response:**

```json
{
  "status": "success",
  "types": [
    {
      "id": 1,
      "name": "carromco",
      "brand": "Carromco",
      "model": "Striker",
      "description": "Carromco Striker board"
    },
    {
      "id": 2,
      "name": "winmau",
      "brand": "Winmau",
      "model": "Blade 6",
      "description": "Winmau Blade 6"
    }
  ]
}
```

#### GET /api/dartboard/types/<board_type>/mappings

Get all zone mappings for a specific dartboard type

**Response:**

```json
{
  "status": "success",
  "board_type": "carromco",
  "mappings": [
    {
      "master_pin": 4,
      "slave_pin": 13,
      "zone_number": 20,
      "multiplier_type": "TRIPLE",
      "base_value": 20
    },
    {
      "master_pin": 4,
      "slave_pin": 12,
      "zone_number": 20,
      "multiplier_type": "DOUBLE",
      "base_value": 20
    }
  ]
}
```

## Arduino/ESP32 Code Changes

### Before (Hardcoded)

```cpp
// Hardcoded multiplier arrays with errors (triple 4, 13 missing)
const int x3Len = 20;
int x3[] = { 1713, 1712, ... };  // Only 20 elements, but accessing with x2Len=21

String multiCheck(int M, int S) {
  // Complex logic trying to determine multiplier
  // Has array bounds bug and missing entries
}

void sendData(int point, String msg) {
  // Sends pre-calculated score
  doc["score"] = String(point);
  doc["multiplier"] = String(msg);
}
```

### After (Generic)

```cpp
// Simple, generic implementation
void sendData(int masterPin, String slavePin) {
  // Send raw pin data - server will handle mapping
  doc["masterPin"] = masterPin;
  doc["slavePin"] = slavePin;
  doc["boardType"] = String("carromco");
}

void throwCheck() {
  for (int i = 0; i < masterLines; i++) {
    digitalWrite(matrixMaster[i], LOW);
    for (int j = 0; j < slaveLines; j++) {
      if (digitalRead(matrixSlave[j]) == LOW) {
        // Simply send the pins that triggered
        sendData(matrixMaster[i], String(matrixSlave[j]));
        delay(500);
        break;
      }
    }
    digitalWrite(matrixMaster[i], HIGH);
  }
}
```

## Adding New Dartboard Types

### Step 1: Register Dartboard Type

```python
from src.core.dartboard_service import DartboardService
from src.core.database_service import get_session

session = get_session()

board_type = DartboardService.register_dartboard_type(
    session,
    name="winmau",
    brand="Winmau",
    model="Blade 6",
    description="Winmau Blade 6 dartboard"
)
```

### Step 2: Create Pin Mapping Matrix

Physically map each GPIO pin combination to the corresponding zone:

```
GPIO Matrix (Carromco example):
     13   12   14   27   26   25   33   32   (slave pins)
15    12   50   36   15    5   10   24    0   (master pin 15)
2     9   25   27   60   20   60   18    0   (master pin 2)
4    28   22   16   32   14   38    6   34   (master pin 4)
16   14   11    8   16    7   19    3   17   (master pin 16)
17    3   54   12   39   18   30   45    6   (master pin 17)
5    42   33   24   48   21   57    9   51   (master pin 5)
18    1   18    4   13    6   10   15    2   (master pin 18)
19    2   36    8   26   12   20   30    4   (master pin 19)
```

### Step 3: Add Mappings to Database

```python
# Triple 20 at master_pin=4, slave_pin=13
DartboardService.add_zone_mapping(
    session,
    dartboard_type_id=board_type.id,
    master_pin=4,
    slave_pin=13,
    zone_number=20,
    multiplier_type="TRIPLE",
    base_value=20
)

# Double 20 at master_pin=4, slave_pin=12
DartboardService.add_zone_mapping(
    session,
    dartboard_type_id=board_type.id,
    master_pin=4,
    slave_pin=12,
    zone_number=20,
    multiplier_type="DOUBLE",
    base_value=20
)

# ... add remaining mappings
```

### Step 4: Update Arduino Code

```cpp
const char* ssid = "<SSID>";
const char* password = "<PASSWORD>";

int matrixMaster[] = {...};  // Your board's master pins
int matrixSlave[] = {...};   // Your board's slave pins

void sendData(int masterPin, String slavePin) {
  if (WiFi.status() == WL_CONNECTED) {
    StaticJsonDocument<200> doc;
    doc["masterPin"] = masterPin;
    doc["slavePin"] = slavePin;
    doc["boardType"] = String("winmau");  // Your board type
    doc["user"] = String("player1");

    String jsonString;
    serializeJson(doc, jsonString);

    http.beginRequest();
    http.post("/api/Throw/zone", "application/json", jsonString);
    http.endRequest();
  }
}
```

## Multiplier Values

| Type    | Value | Example     |
| ------- | ----- | ----------- |
| SINGLE  | 1x    | 20 × 1 = 20 |
| DOUBLE  | 2x    | 20 × 2 = 40 |
| TRIPLE  | 3x    | 20 × 3 = 60 |
| BULL    | 25    | Always 25   |
| DBLBULL | 50    | Always 50   |

## Score Calculation

Final Score = Base Value × Multiplier Value

Examples:

- Triple 20: 20 × 3 = 60
- Triple 4: 4 × 3 = 12
- Triple 13: 13 × 3 = 39 (now properly supported!)
- Double Bull: 50

## DartboardService Methods

### register_dartboard_type()

Register a new dartboard type

```python
def register_dartboard_type(
    session: Session,
    name: str,
    brand: str,
    model: Optional[str] = None,
    description: Optional[str] = None
) -> DartboardType
```

### add_zone_mapping()

Add a GPIO pin to zone mapping

```python
def add_zone_mapping(
    session: Session,
    dartboard_type_id: int,
    master_pin: int,
    slave_pin: int,
    zone_number: int,
    multiplier_type: str,
    base_value: int
) -> DartboardZoneMapping
```

### get_zone_from_pins()

Look up zone information from pin combination

```python
def get_zone_from_pins(
    session: Session,
    dartboard_type_name: str,
    master_pin: int,
    slave_pin: int
) -> Optional[Dict]
```

Returns:

```python
{
    "zone_number": int,
    "multiplier_type": str,
    "base_value": int,
    "score": int
}
```

### calculate_score()

Calculate final score from base value and multiplier

```python
def calculate_score(base_value: int, multiplier_type: str) -> int
```

### validate_zone_mapping()

Validate zone mapping configuration

```python
def validate_zone_mapping(
    zone_number: int,
    multiplier_type: str,
    base_value: int
) -> bool
```

### convert_legacy_to_zone()

Convert legacy (score, multiplier) format to zone info

```python
def convert_legacy_to_zone(
    session: Session,
    dartboard_type_name: str,
    score: int,
    multiplier: str
) -> Dict
```

## Migration Guide

### For Old Dartboards

- **No changes required** - legacy `/api/Throw` endpoint still works
- Can continue sending score/multiplier format indefinitely
- No performance impact

### For New Dartboards

1. Flash updated Arduino code with generic pin-based format
2. Update `boardType` to match registered dartboard type
3. Ensure dartboard type is registered in database with all zone mappings
4. Use `/api/Throw/zone` endpoint
5. Benefit from centralized mapping management and easier debugging

## Testing

See `/data/dartserver-pythonapp/tests/unit/test_dartboard_service.py` for comprehensive unit tests covering:

- Zone mapping registration
- Zone lookup functionality
- Score calculation
- Validation logic
- Legacy format conversion
- Error handling

Run tests with:

```bash
pytest tests/unit/test_dartboard_service.py -v
pytest tests/unit/test_dartboard_api_endpoints.py -v
```

## Troubleshooting

### Zone mapping not found

- Verify dartboard type is registered: `GET /api/dartboard/types`
- Verify pins are mapped: `GET /api/dartboard/types/<board_type>/mappings`
- Check pins match exactly (Arduino sends actual GPIO pin numbers)

### Wrong score calculated

- Verify zone_number and base_value in database
- Verify multiplier_type is correct
- Use `/api/dartboard/types/<board_type>/mappings` to inspect mappings

### Arduino compilation errors

- Ensure ArduinoJson library is installed
- Ensure WiFi credentials are correct
- Verify GPIO pin numbers match your board

## Future Enhancements

- Admin UI for dartboard type registration
- Automatic pin mapping from physical dartboard tests
- Support for dynamic calibration
- Dartboard-specific statistics and accuracy tracking
