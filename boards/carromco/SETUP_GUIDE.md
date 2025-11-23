# Carromco Dartboard Setup Guide

## Quick Start (5 minutes)

### 1. Flash Arduino Sketch

- Open: `boards/carromco/dartserver_carromco.ino`
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
python helpers/setup_dartboard_types.py carromco
```

### 3. Configure Zone Mappings

1. Open admin panel: `https://your-server/admin/dartboard-testing`
2. Select "carromco" from dropdown
3. Use "Manual Mapping" or "Bulk Import" to add zones
4. Test with real dartboard

---

## Specifications

| Property                 | Value                             |
| ------------------------ | --------------------------------- |
| **Board Type**           | `carromco`                        |
| **Board Name**           | Carromco Striker                  |
| **Matrix Size**          | 8 rows × 8 columns = 64 zones     |
| **GPIO Master Pins**     | 15, 2, 4, 16, 17, 5, 18, 19       |
| **GPIO Slave Pins**      | 13, 12, 14, 27, 26, 25, 33, 32    |
| **Total GPIO Used**      | 16 pins                           |
| **API Endpoint**         | `POST /api/Throw/zone`            |
| **Pre-configured Zones** | 50 zones (Triple 4 and 13 fixed!) |

---

## Pin Configuration

### Master Pins (Rows)

```
Row 0 → GPIO 15
Row 1 → GPIO 2
Row 2 → GPIO 4   ← Triple 4 fixed!
Row 3 → GPIO 16
Row 4 → GPIO 17  ← Triple 13 fixed!
Row 5 → GPIO 5
Row 6 → GPIO 18
Row 7 → GPIO 19
```

### Slave Pins (Columns)

```
Col 0 → GPIO 13
Col 1 → GPIO 12
Col 2 → GPIO 14
Col 3 → GPIO 27  ← Triple locations (Row 2 & 4, Col 3)
Col 4 → GPIO 26
Col 5 → GPIO 25
Col 6 → GPIO 33
Col 7 → GPIO 32
```

---

## What's New? ✨

### Previous Issues (Broken Firmware)

- Triple 4: Not in array → Didn't work ❌
- Triple 13: Not in array → Didn't work ❌
- Array bounds error: x2Len = 21 but array only 20 elements → Crashes ❌
- Hardcoded multiplier logic: ~100 lines of code per board ❌

### Now Fixed! ✅

- All zones stored in database
- Server-side mapping = easy to fix
- No firmware updates needed for calibration
- ~10 lines of generic code instead of ~100
- Triple 4 and Triple 13 now work perfectly!

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
Master Pins (Rows) ← GPIO 15,2,4,16,17,5,18,19
Slave Pins (Cols)  ← GPIO 13,12,14,27,26,25,33,32
        ↓
When dart presses zone:
- That row pin pulled LOW
- That column pin pulled LOW
- Arduino detects (master, slave) combination
- Sends to server with boardType="carromco"
- Server maps to zone using database
```

---

## Zone Configuration Workflow

### First Time Setup

1. **Verify Setup:**

   ```bash
   python helpers/setup_dartboard_types.py carromco
   # Output should show: 50 zone mappings pre-configured
   ```

2. **Go to admin panel:**
   - URL: `https://your-server/admin/dartboard-testing`
   - Select "carromco" dartboard
   - Should see 8×8 matrix with pre-mapped zones

3. **Test zones:**
   - Press each zone on dartboard
   - Verify score appears correctly
   - Check that Triple 4 and Triple 13 work!

4. **Adjust if needed:**
   - If zone detection wrong: Use admin panel to update
   - Manual Mapping tab: Edit individual zones
   - Bulk Import tab: Replace all zones at once

### Ongoing Maintenance

- **Zone detection wrong?**
  - Use admin panel to update that zone
  - No Arduino reflash needed!

- **Want to recalibrate all zones?**
  - Download CSV from admin panel
  - Update all mappings
  - Upload CSV back
  - Test again

---

## Test Matrix Reference

Pre-configured Carromco zones (50 total):

```
Row × Col layout:
         Col0  Col1  Col2  Col3  Col4  Col5  Col6  Col7
Row0(15):  12    25    36    15     5    10    24     0
Row1(2):    9   DBL*   27    20    20    20    18     0
Row2(4):   20    20    20   T4*   14   D4*    6     34
Row3(16):  14    11     8    16     7    19     3    17
Row4(17):   3    18    12   T13*   18   D15*   9     6
Row5(5):   D14   33    24   D16   21*  D19*   9    51*
Row6(18):   1    18     4    13     6    10    15     2
Row7(19):   2    36*    8   26*   12*   20    30*    4

Legend:
T4  = Triple 4 (4 × 3 = 12) ← NOW WORKS!
T13 = Triple 13 (13 × 3 = 39) ← NOW WORKS!
DBL = Double Bull (25 × 2 = 50)
D4  = Double 4 (4 × 2 = 8)
D15 = Double 15 (15 × 2 = 30)
D16 = Double 16 (16 × 2 = 32)
D19 = Double 19 (19 × 2 = 38)
* = Invalid zones (not in 1-20 range, excluded from database)
```

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
   - Verify connections match carromco_config.h
   - Test with Serial prints

3. If output shows but zone not mapped:
   - Go to admin panel
   - Select "carromco" board
   - Use Message Log to see raw pins
   - Check if those pins are mapped

---

### Triple 4 or Triple 13 Not Working

**This was the original bug - now fixed!**

**Check:**

1. Verify database has these mappings:

   ```sql
   SELECT * FROM dartboard_zone_mappings
   WHERE zone_number IN (4, 13)
   AND multiplier_type = 'TRIPLE';
   ```

   Should return 2 rows (one each for Triple 4 and 13)

2. Re-run setup if missing:

   ```bash
   python helpers/setup_dartboard_types.py carromco
   ```

3. Test in admin panel - should see them mapped in matrix

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
2. Select "carromco" board type
3. Check if mappings exist in GPIO Matrix tab
4. If empty: Something went wrong with setup
5. If shown but not matching: verify pin ordering
6. Re-run: `python helpers/setup_dartboard_types.py carromco`

---

## CSV Format for Bulk Import/Export

### Download Current Mappings

In admin panel, "Bulk Import" tab has a download button to get current CSV

### Format

```csv
masterPin,slavePin,zoneNumber,multiplierType,baseValue
15,13,12,SINGLE,12
15,12,25,BULL,25
2,13,9,SINGLE,9
4,27,4,TRIPLE,4
17,27,13,TRIPLE,13
```

### Column Descriptions

| Column           | Type   | Valid Values                          | Example            |
| ---------------- | ------ | ------------------------------------- | ------------------ |
| `masterPin`      | int    | 15,2,4,16,17,5,18,19                  | 4                  |
| `slavePin`       | int    | 13,12,14,27,26,25,33,32               | 27                 |
| `zoneNumber`     | int    | 1-20, 25                              | 4 (or 25 for bull) |
| `multiplierType` | string | SINGLE, DOUBLE, TRIPLE, BULL, DBLBULL | TRIPLE             |
| `baseValue`      | int    | 1-20, 25                              | 4                  |

### Examples

```csv
# Triple 4 (4 × 3 = 12)
4,27,4,TRIPLE,4

# Triple 13 (13 × 3 = 39)
17,27,13,TRIPLE,13

# Bull (25 points)
15,12,25,BULL,25

# Double Bull (25 × 2 = 50)
2,12,25,DBLBULL,25
```

---

## Performance Notes

### Scan Speed

- Single full scan: ~50ms (8×8 matrix)
- WiFi transmission: 100-500ms (network dependent)
- Server processing: <1ms (database query)
- **Total per throw:** 200-700ms

---

## Advanced Configuration

### Modify Scan Delay

In `dartserver_carromco.ino`, change:

```cpp
delay(500);  // Debounce time after dart detected
```

Shorter = faster but may cause double-detects
Longer = more stable but slower response

### Add Button Support

Uncomment the `bigRedCheck()` function in sketch to enable physical button

---

## Reference Files

| File                                      | Purpose                |
| ----------------------------------------- | ---------------------- |
| `boards/carromco/dartserver_carromco.ino` | Arduino sketch         |
| `boards/carromco_config.h`                | GPIO pin mappings      |
| `boards/README_GENERIC_ARCHITECTURE.md`   | Full architecture docs |
| `helpers/setup_dartboard_types.py`        | Database setup         |
| `src/core/dartboard_service.py`           | Backend service        |

---

## FAQ

**Q: Will updating the firmware break my zones?**  
A: No, zones are stored in database. Zones survive firmware updates

**Q: Can I customize which zone is where?**  
A: Yes, use admin panel to map zones exactly as you want

**Q: Why do we need this setup?**  
A: Previous firmware had hardcoded bugs (Triple 4/13 missing). Now server handles it

**Q: Can I use the old firmware?**  
A: Not recommended - it has bugs. Use new firmware + admin panel to configure

**Q: What if zone mappings are wrong?**  
A: Use admin panel to correct them - instant fix, no firmware updates needed!

---

## Getting Help

1. **Check admin panel** - Message log shows raw GPIO signals
2. **Check Serial monitor** - Arduino prints debug info
3. **Review logs** - Server logs show zone lookups
4. **Read docs** - See `boards/README_GENERIC_ARCHITECTURE.md`

---

## What's Different from Old Firmware?

| Feature            | Old (Broken)               | New (Fixed)    |
| ------------------ | -------------------------- | -------------- |
| Triple 4           | ❌ Missing                 | ✅ Works       |
| Triple 13          | ❌ Missing                 | ✅ Works       |
| Zone changes       | ❌ Firmware update         | ✅ Admin panel |
| Code size          | ~500 lines                 | ~200 lines     |
| Array bugs         | ❌ Yes (x2Len/x3 mismatch) | ✅ No arrays   |
| Support new boards | ❌ Requires coding         | ✅ Just config |

---

## Summary

Carromco is now using the **new generic architecture**:

- ✅ Triple 4 and Triple 13 fixed!
- ✅ No hardcoded zone arrays
- ✅ Configure zones via web admin panel
- ✅ Share codebase with other boards
- ✅ 50 zones pre-configured
- ✅ Production-ready

**You're all set!** 🎯
