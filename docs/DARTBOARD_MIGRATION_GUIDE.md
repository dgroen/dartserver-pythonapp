# Dartboard System Migration Guide

## Overview

This guide helps you migrate from the legacy hardcoded dartboard system to the new generic pin-based architecture.

## For Users (No Action Required)

If you're using an existing Carromco dartboard, **no immediate changes are needed**:

- ✓ Legacy endpoint `/api/Throw` still works
- ✓ No firmware update required
- ✓ Game functionality unchanged
- ✓ Gradual migration path available

## For Developers: Adding a New Dartboard Type

### Step 1: Identify Dartboard Matrix

First, determine the GPIO pin matrix for your dartboard:

```
GPIO Matrix Layout:
     Column1  Column2  Column3  ...  ColumnN (slave pins)
Row1   pin     pin      pin              pin
Row2   pin     pin      pin              pin
...
RowN   pin     pin      pin              pin    (master pins)
```

Example - Carromco with 8x8 matrix:

```
matrixMaster[] = {15, 2, 4, 16, 17, 5, 18, 19}  (row pins)
matrixSlave[] = {13, 12, 14, 27, 26, 25, 33, 32}  (column pins)
```

### Step 2: Create Dartboard Matrix Map

Map each GPIO combination to a dartboard zone:

```
For each (master_pin, slave_pin) combination:
  → Determine the zone number (1-20 or 25 for bull)
  → Determine the multiplier (SINGLE, DOUBLE, TRIPLE, BULL, DBLBULL)
  → Record base_value (same as zone number for non-bulls)
```

For Carromco, this creates 64 mappings (8x8 matrix).

### Step 3: Register Dartboard Type

```python
from src.core.dartboard_service import DartboardService
from src.core.database_service import get_session

session = get_session()

board_type = DartboardService.register_dartboard_type(
    session,
    name="my_board",           # Unique identifier (lowercase)
    brand="My Brand",          # Manufacturer name
    model="Model X",           # Optional model number
    description="..."          # Optional description
)
```

### Step 4: Add Zone Mappings

```python
# Add mappings for each GPIO combination
mappings_data = [
    # (master_pin, slave_pin, zone_number, multiplier_type, base_value)
    (15, 13, 12, "SINGLE", 12),
    (15, 12, 25, "BULL", 25),
    (4, 13, 20, "TRIPLE", 20),
    (4, 12, 20, "DOUBLE", 20),
    (17, 5, 13, "TRIPLE", 13),
    # ... add all 64 combinations
]

for master_pin, slave_pin, zone, mult_type, base_val in mappings_data:
    DartboardService.add_zone_mapping(
        session,
        board_type.id,
        master_pin,
        slave_pin,
        zone,
        mult_type,
        base_val
    )
```

### Step 5: Update Arduino Code

Create a new file: `boards/my_board/dartserver_my_board.ino`

```cpp
// Update these with your pins
int matrixMaster[] = {15, 2, 4, ...};  // Your master pins
int matrixSlave[] = {13, 12, 14, ...}; // Your slave pins

void sendData(int masterPin, String slavePin) {
  if (WiFi.status() == WL_CONNECTED) {
    StaticJsonDocument<200> doc;
    doc["masterPin"] = masterPin;
    doc["slavePin"] = slavePin;
    doc["boardType"] = String("my_board");  // Your board type name
    doc["user"] = String("username");

    String jsonString;
    serializeJson(doc, jsonString);

    http.beginRequest();
    http.post("/api/Throw/zone", "application/json", jsonString);
    http.endRequest();
  }
}
```

### Step 6: Test Setup

```bash
# Verify board type registered
curl http://localhost:5000/api/dartboard/types

# Check mappings
curl http://localhost:5000/api/dartboard/types/my_board/mappings

# Test a throw
curl -X POST http://localhost:5000/api/Throw/zone \
  -H "Content-Type: application/json" \
  -d '{
    "masterPin": 4,
    "slavePin": 13,
    "boardType": "my_board"
  }'
```

## For Existing Carromco Users: Migration Path

### Option 1: Stay on Legacy (Current)

- No changes needed
- Continue using `/api/Throw` endpoint
- Existing firmware works as-is

### Option 2: Migrate to New System (Recommended)

**Advantages:**

- Server-side zone management
- Easier debugging
- Support for multiple board types
- Better error messages

**Steps:**

1. **Update Database** (if using migrations):

   ```bash
   alembic upgrade head
   ```

2. **Initialize Carromco Mappings**:

   ```bash
   python helpers/setup_dartboard_types.py carromco
   ```

3. **Flash New Firmware**:
   - Download updated `boards/carromco/dartserver_carromco.ino`
   - Flash to ESP32/Arduino
   - Restart device

4. **Verify**:

   ```bash
   # Test the new endpoint
   curl -X POST http://localhost:5000/api/Throw/zone \
     -H "Content-Type: application/json" \
     -d '{"masterPin": 4, "slavePin": 13, "boardType": "carromco"}'
   ```

## Quick Setup Script

For Carromco boards, use the provided helper:

```bash
# Full setup (Carromco + test board)
python helpers/setup_dartboard_types.py setup

# Just Carromco
python helpers/setup_dartboard_types.py carromco

# Just test board (for development)
python helpers/setup_dartboard_types.py test

# List all boards
python helpers/setup_dartboard_types.py list
```

## API Endpoint Migration

### Before (Legacy)

```bash
curl -X POST http://localhost:5000/api/Throw \
  -H "Content-Type: application/json" \
  -d '{"score": 20, "multiplier": "TRIPLE"}'
```

### After (New)

```bash
curl -X POST http://localhost:5000/api/Throw/zone \
  -H "Content-Type: application/json" \
  -d '{
    "masterPin": 4,
    "slavePin": 13,
    "boardType": "carromco"
  }'
```

**Note:** Both endpoints work! Use `/api/Throw/zone` for new boards, keep using `/api/Throw` for legacy boards.

## Troubleshooting Migration

### Issue: "Zone mapping not found"

**Solution:**

```bash
# 1. Verify board type exists
curl http://localhost:5000/api/dartboard/types

# 2. Check mappings for your board
curl http://localhost:5000/api/dartboard/types/carromco/mappings

# 3. Ensure pins match exactly (GPIO numbers, not array indices)
```

### Issue: "Database error"

**Solution:**

```bash
# 1. Ensure migrations are run
alembic upgrade head

# 2. Check database connection
python -c "from src.core.database_service import get_session; s = get_session(); print('OK')"

# 3. Run setup script
python helpers/setup_dartboard_types.py carromco
```

### Issue: Arduino fails to compile

**Solution:**

- Verify ArduinoJson library is installed
- Check WiFi credentials in code
- Verify GPIO pin numbers are correct
- Ensure Arduino IDE has ESP32 board support

### Issue: Scores still using old format

**Solution:**

1. Check `/api/Throw/zone` endpoint returns data
2. Verify game_manager receives correct score
3. Check zone_info in response contains expected values

## Rollback Plan

If you need to rollback to the legacy system:

1. **Revert Arduino code**: Use old firmware without board type
2. **Use legacy endpoint**: Continue using `/api/Throw`
3. **Database**: Old mappings tables are optional, can be dropped safely

```bash
# Rollback firmware
cd boards/carromco
git checkout main dartserver_carromco.ino
# Re-flash device
```

## Support

For issues during migration:

1. **Check logs**: Look for error messages in server logs
2. **Verify database**: Confirm board types and mappings exist
3. **Test endpoints**: Use curl to test API responses
4. **Debug Arduino**: Check serial output for connection issues

## References

- Full Documentation: `docs/DARTBOARD_ZONE_MAPPING.md`
- Implementation Summary: `docs/DARTBOARD_IMPLEMENTATION_SUMMARY.md`
- Setup Script: `helpers/setup_dartboard_types.py`
- Arduino Code: `boards/carromco/dartserver_carromco.ino`
- Test Files: `tests/unit/test_dartboard_service.py`
