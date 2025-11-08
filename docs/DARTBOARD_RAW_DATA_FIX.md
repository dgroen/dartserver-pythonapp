# Dartboard Raw Data Fix

## Problem

The dartboard-testing page (`/admin/dartboard-testing`) was not showing raw data when dartboards sent GPIO pin information to the `/api/Throw/zone` endpoint.

## Root Cause

The `/api/Throw/zone` endpoint was successfully processing dartboard throws but was **not emitting a WebSocket event** (`dartboard_test_received`) that the admin testing page listens for to display raw data in the message log.

## Solution

Added WebSocket event emission in the `/api/Throw/zone` endpoint handler in `src/app/app.py`.

### Code Changes

#### File: `src/app/app.py` (Line ~1121)

**Before:**

```python
# Process the score using the zone information
game_manager.process_score(
    {
        "score": zone_info["base_value"],
        "multiplier": zone_info["multiplier_type"],
    },
)

return jsonify(
    {
        "status": "success",
        "message": "Score submitted",
        "zone_info": zone_info,
    },
)
```

**After:**

```python
# Process the score using the zone information
game_manager.process_score(
    {
        "score": zone_info["base_value"],
        "multiplier": zone_info["multiplier_type"],
    },
)

# Emit WebSocket event for admin dartboard testing page
socketio.emit(
    "dartboard_test_received",
    {
        "masterPin": master_pin,
        "slavePin": slave_pin,
        "boardType": board_type,
        "zoneInfo": zone_info,
    },
    namespace="/",
)

return jsonify(
    {
        "status": "success",
        "message": "Score submitted",
        "zone_info": zone_info,
    },
)
```

#### File: `templates/admin_dartboard_testing.html` (WebSocket handler)

**Enhanced the WebSocket event handler** to:

1. Accept `zoneInfo` directly from the WebSocket event (no need for additional API call)
2. Fall back to fetching mapping if `zoneInfo` is not provided
3. Highlight the corresponding cell in the GPIO matrix when data is received
4. Better error handling

**Key improvements:**

```javascript
socket.on("dartboard_test_received", (data) => {
  console.log("Received dartboard test data:", data);

  const masterPin = data.masterPin;
  const slavePin = data.slavePin;
  const zoneInfo = data.zoneInfo;

  // Add to log with zone info if available
  if (zoneInfo) {
    addLogEntry(masterPin, slavePin, {
      zone_number: zoneInfo.zone_number,
      multiplier_type: zoneInfo.multiplier_type,
      base_value: zoneInfo.base_value,
      score: zoneInfo.score,
    });
  } else {
    // Fallback: fetch mapping info from the server
    // ... (see code for details)
  }

  // Highlight the cell in the matrix
  highlightMatrixCell(masterPin, slavePin);
});
```

## How It Works Now

1. **Dartboard sends data** → POST `/api/Throw/zone` with `{masterPin, slavePin, boardType}`
2. **Server processes** → Looks up zone mapping, processes score
3. **Server emits WebSocket event** → `dartboard_test_received` with full pin + zone data
4. **Admin page receives event** → Displays in message log with timestamp and zone info
5. **Visual feedback** → Highlights the corresponding cell in the GPIO matrix

## Testing

### Option 1: Test HTML Page

1. Open <http://localhost:5000/static/test_websocket.html> in your browser
2. Click the test buttons to simulate dartboard throws
3. Watch the WebSocket Events Log for incoming events
4. If events appear with full details, the fix is working! ✅

### Option 2: Python Test Script

```bash
cd /data/dartserver-pythonapp
python test_dartboard_raw_data.py
```

### Option 3: Manual Test with Browser DevTools

1. Open <http://localhost:5000/admin/dartboard-testing>
2. Open browser DevTools (F12) → Console tab
3. In another terminal, send a test throw:

   ```bash
   curl -X POST http://localhost:5000/api/Throw/zone \
     -H "Content-Type: application/json" \
     -d '{"masterPin": 4, "slavePin": 13, "boardType": "carromco"}'
   ```

4. Check the admin page's message log for the entry
5. Check browser console for the WebSocket event log

## What You Should See

On the dartboard-testing page, when a throw is sent, you should now see:

```
[14:32:15] GPIO: master=4, slave=13
Zone: 20, Mult: TRIPLE, Value: 20, Score: 60
```

The entry should appear in real-time with:

- ✅ Timestamp
- ✅ Raw GPIO pins (master and slave)
- ✅ Zone number
- ✅ Multiplier type
- ✅ Base value
- ✅ Calculated score

## Related Files

- `src/app/app.py` - Main Flask application with endpoint handlers
- `templates/admin_dartboard_testing.html` - Admin testing page with WebSocket listener
- `static/test_websocket.html` - Standalone test page (NEW)
- `test_dartboard_raw_data.py` - Python test script (NEW)

## Notes

- The fix maintains backward compatibility - old dartboard messages still work
- WebSocket events are broadcast to all connected admin clients
- The message log auto-scrolls and keeps the last 50 entries
- Cell highlighting animation runs for 600ms when data is received

## Verification Checklist

- [x] WebSocket event `dartboard_test_received` is emitted when `/api/Throw/zone` receives data
- [x] Event includes both raw GPIO pins and resolved zone information
- [x] Admin testing page displays raw data in message log
- [x] Matrix cell highlights when corresponding pin data is received
- [x] No additional API calls needed (zone info included in event)
- [x] Test page created for easy verification
- [x] Python test script created for automated testing

## Author

Fixed on: 2025-11-06
Issue: Raw data not showing on dartboard-testing page
