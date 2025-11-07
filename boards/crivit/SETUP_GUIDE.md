# Crivit Dartboard Setup Guide

## Quick Start (5 minutes)

### 1. Flash Arduino Sketch

- Open: `boards/crivit/dartserver_crivit.ino`
- Configure WiFi:

  ```cpp
  const char* ssid = "<YOUR_SSID>";
  const char* password = "<YOUR_PASSWORD>";
  ```

- Configure server:

  ```cpp
  const char* serverAddress = "YOUR_SERVER_IP";
  ```

- Upload to ESP32

### 2. Register Dartboard Type

```bash
python helpers/setup_dartboard_types.py crivit
```

### 3. Configure Zone Mappings

1. Open admin panel: `https://your-server/admin/dartboard-testing`
2. Select "crivit" from dropdown
3. Use "Manual Mapping" or "Bulk Import" to add zones
4. Test with real dartboard

---

## Specifications

| Property             | Value                                          |
| -------------------- | ---------------------------------------------- |
| **Board Type**       | `crivit`                                       |
| **Board Name**       | Crivit Dartboard                               |
| **Matrix Size**      | 7 rows × 12 columns = 84 zones                 |
| **GPIO Master Pins** | 2, 4, 16, 17, 5, 18, 19                        |
| **GPIO Slave Pins**  | 21, 22, 23, 13, 12, 14, 27, 26, 25, 33, 32, 15 |
| **Total GPIO Used**  | 19 pins                                        |
| **API Endpoint**     | `POST /api/Throw/zone`                         |

---

## Pin Configuration

### Master Pins (Rows)

```
Row 0 → GPIO 2
Row 1 → GPIO 4
Row 2 → GPIO 16
Row 3 → GPIO 17
Row 4 → GPIO 5
Row 5 → GPIO 18
Row 6 → GPIO 19
```

### Slave Pins (Columns)

```
Col 0  → GPIO 21    Col 6  → GPIO 27
Col 1  → GPIO 22    Col 7  → GPIO 26
Col 2  → GPIO 23    Col 8  → GPIO 25
Col 3  → GPIO 13    Col 9  → GPIO 33
Col 4  → GPIO 12    Col 10 → GPIO 32
Col 5  → GPIO 14    Col 11 → GPIO 15
```

---

## Hardware Connections

### Matrix Scanning

1. **Master Pins (Rows)** - Set to OUTPUT, switched between HIGH and LOW
   - Default: HIGH
   - During scan: One at a time set to LOW
   - Purpose: Identify which row is active

2. **Slave Pins (Columns)** - Set to INPUT_PULLUP
   - Default: HIGH (pulled up internally)
   - When dart pressed: Goes LOW (shorted to ground)
   - Purpose: Identify which column is active

### Dartboard Connection

```
Dartboard Physical Layout
        ↓
      [Pin Matrix]
        ↓
    Master Pins (Rows) ← Connected to Row Select (GPIO 2,4,16,17,5,18,19)
    Slave Pins (Cols) ← Connected to Column Sense (GPIO 21,22,23,13,12,14,27,26,25,33,32,15)
        ↓
    When dart presses zone:
    - That row pin pulled LOW
    - That column pin pulled LOW
    - Arduino detects combination
    - Sends (masterPin, slavePin) to server
```

---

## Zone Configuration Workflow

### First Time Setup

1. **Physical verification:**
   - Verify all GPIO pins connected correctly
   - Test each zone works on dartboard

2. **Register board type:**

   ```bash
   python helpers/setup_dartboard_types.py crivit
   ```

3. **Go to admin panel:**
   - URL: `https://your-server/admin/dartboard-testing`
   - Select "crivit" dartboard

4. **Map zones (Option A - Manual):**
   - Press zone on dartboard
   - See master/slave pins in "Raw Message Log"
   - Select that pin combination in matrix
   - Enter zone number (1-20 or 25 for bull)
   - Select multiplier (SINGLE, DOUBLE, TRIPLE, BULL, DBLBULL)
   - Save

5. **Map zones (Option B - CSV Import):**
   - Download template CSV
   - Fill in all zones:

     ```csv
     masterPin,slavePin,zoneNumber,multiplierType,baseValue
     2,21,14,SINGLE,14
     2,22,32,SINGLE,32
     ...
     ```

   - Upload CSV
   - Verify results

6. **Test:**
   - Press each zone on dartboard
   - Verify correct score appears in game

### Ongoing Maintenance

- **Zone detection wrong?**
  - Use admin panel to update that zone
  - No Arduino reflash needed!

- **Add new zone?**
  - Admin panel → Manual Mapping
  - Select pins → Enter details → Save
  - Immediate effect

---

## Troubleshooting

### Arduino Upload Fails

**Error:** "Board not found" or "Port not available"

**Solution:**

1. Check USB cable connection
2. Verify correct board selected (ESP32 Dev Module)
3. Check port in Tools → Port
4. Restart Arduino IDE
5. Try different USB port

---

### Zone Not Detected

**Symptom:** Press zone on dartboard, nothing happens

**Steps:**

1. Check Serial Monitor (115200 baud)
   - Should see: `DART DETECTED - Master: X, Slave: Y`
2. If no output:
   - GPIO pins might be crossed
   - Verify connections match crivit_config.h
   - Test with Serial prints

3. If output shows but zone not mapped:
   - Go to admin panel
   - Select "crivit" board
   - Use Message Log to see raw pins
   - Add mapping for those pins

---

### Wrong Zone Detected

**Symptom:** Press zone 20, get zone 18

**Solution:**

1. Use admin panel Message Log
2. Note the master/slave pins from real press
3. Find what they're currently mapped to
4. Update the mapping to correct zone
5. Test again

---

### WiFi Connection Failed

**Error:** "Wi-Fi not connected" in serial

**Solution:**

1. Edit sketch - verify SSID/password correct
2. Check network is accessible from device location
3. Verify IP address/port reachable
4. Check server logs for connection attempts
5. Try direct ping to server from another device

---

### Server Says "Zone mapping not found"

**Error:** HTTP response says pins unmapped

**Solution:**

1. Go to admin panel
2. Select "crivit" board type
3. Check if mappings exist in GPIO Matrix tab
4. If empty: needs zone configuration
5. If shown but not matching: verify pin ordering
6. Add/update mappings as needed

---

## CSV Format for Bulk Import

### Template

```csv
masterPin,slavePin,zoneNumber,multiplierType,baseValue
2,21,14,SINGLE,14
2,22,32,SINGLE,32
2,23,16,SINGLE,16
...
```

### Column Descriptions

| Column           | Type   | Valid Values                          | Example             |
| ---------------- | ------ | ------------------------------------- | ------------------- |
| `masterPin`      | int    | 2,4,16,17,5,18,19                     | 2                   |
| `slavePin`       | int    | 21,22,23,13,12,14,27,26,25,33,32,15   | 21                  |
| `zoneNumber`     | int    | 1-20, 25                              | 20 (or 25 for bull) |
| `multiplierType` | string | SINGLE, DOUBLE, TRIPLE, BULL, DBLBULL | TRIPLE              |
| `baseValue`      | int    | 1-20, 25                              | 20                  |

### Valid Combinations

```csv
# Single zones (1-20)
2,21,14,SINGLE,14

# Double zones
2,22,32,DOUBLE,16

# Triple zones
2,23,18,TRIPLE,18

# Bull (only one per dartboard, typically)
2,25,25,BULL,25

# Double bull
2,26,25,DBLBULL,25
```

### Invalid Examples (Won't Import)

```csv
# Zone > 25
2,21,30,SINGLE,30          ❌ Invalid zone

# Base value doesn't match multiplier
2,21,14,TRIPLE,14          ❌ Triple but base_value should be different

# Wrong multiplier for bull
2,25,25,SINGLE,25          ❌ Bull must be BULL or DBLBULL type

# Non-existent GPIO pin
99,21,14,SINGLE,14         ❌ 99 not a master pin on Crivit
```

---

## Performance Notes

### Scan Speed

- Single full scan: ~50ms (7×12 matrix)
- WiFi transmission: 100-500ms (network dependent)
- Server processing: <1ms (database query)
- **Total per throw:** 200-700ms

### Optimization Tips

- Position router near dartboard for WiFi speed
- Ensure server has good database performance
- Don't run excessive zone queries

---

## Advanced Configuration

### Modify Scan Delay

In `dartserver_crivit.ino`, change:

```cpp
delay(500);  // Debounce time after dart detected
```

Shorter = faster but may cause double-detects
Longer = more stable but slower response

### Add Button Support

Uncomment the `bigRedCheck()` function in sketch to enable physical button

### Custom Callbacks

Edit `sendData()` function to add logging, validation, etc.

---

## Reference Files

| File                                    | Purpose                   |
| --------------------------------------- | ------------------------- |
| `boards/crivit/dartserver_crivit.ino`   | Arduino sketch for Crivit |
| `boards/crivit_config.h`                | GPIO pin mappings         |
| `boards/README_GENERIC_ARCHITECTURE.md` | Full architecture docs    |
| `src/core/dartboard_service.py`         | Backend service           |
| `docs/DARTBOARD_ZONE_MAPPING.md`        | API documentation         |

---

## FAQ

**Q: Can I use Crivit config with different GPIO pins?**  
A: Yes, edit `crivit_config.h` and change the pin numbers, then re-upload

**Q: Will changing zones break the game?**  
A: No, game only gets scores. Changing zone mappings just sends different scores

**Q: How many zones can I have?**  
A: Up to 84 (7 rows × 12 columns) on Crivit. More master/slave pins = more zones

**Q: Do both boards need updating?**  
A: Each board needs its own config and sketch. They don't interfere

**Q: Can I switch between Crivit and Carromco easily?**  
A: Yes, just upload different sketch and select board in admin panel

---

## Getting Help

1. **Check admin panel** - Message log shows raw GPIO signals
2. **Check Serial monitor** - Arduino prints debug info
3. **Review logs** - Server logs show zone lookups
4. **Read docs** - See `boards/README_GENERIC_ARCHITECTURE.md`

---

## Summary

Crivit is now using the **new generic architecture**:

- ✅ No hardcoded zone arrays
- ✅ Configure zones via web admin panel
- ✅ Share codebase with other boards
- ✅ Easy to troubleshoot and maintain
- ✅ Production-ready

**You're all set!** 🎯
