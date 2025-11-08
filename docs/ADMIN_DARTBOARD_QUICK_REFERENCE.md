# Dartboard Admin Quick Reference

## Quick Access

| Task                      | How-To                                                                                     |
| ------------------------- | ------------------------------------------------------------------------------------------ |
| **Access Testing Page**   | `https://your-server/admin/dartboard-testing` (Admin login required)                       |
| **Download CSV Template** | Click "📥 Download CSV Template" button in admin page                                      |
| **View Matrix**           | Select dartboard type from dropdown - grid loads automatically                             |
| **Update Single Mapping** | Click cell in grid OR enter pins manually → Fill zone/mult/value → Click "💾 Save Mapping" |
| **Bulk Import**           | Upload CSV file or drag-drop on upload area                                                |
| **Clear Message Log**     | Click "Clear Log" button (bottom of page)                                                  |

## Zone & Multiplier Quick Reference

### Dartboard Zones

```
Zone 1-20:   Regular dartboard segments
Zone 25:     Bull's eye (center)
```

### Multipliers & Scoring

```
SINGLE:   Base value × 1    (e.g., 20 × 1 = 20)
DOUBLE:   Base value × 2    (e.g., 20 × 2 = 40)
TRIPLE:   Base value × 3    (e.g., 20 × 3 = 60)
BULL:     Always 25 points (fixed value)
DBLBULL:  Always 50 points (fixed value)
```

### Valid Combinations

| Zone | Multiplier | Base Value | Valid | Example                |
| ---- | ---------- | ---------- | ----- | ---------------------- |
| 1-20 | SINGLE     | 1-20       | ✅    | 20 SINGLE (20 points)  |
| 1-20 | DOUBLE     | 1-20       | ✅    | 20 DOUBLE (40 points)  |
| 1-20 | TRIPLE     | 1-20       | ✅    | 20 TRIPLE (60 points)  |
| 1-20 | BULL       | 25         | ❌    | Invalid                |
| 1-20 | DBLBULL    | 25         | ❌    | Invalid                |
| 25   | SINGLE     | 25         | ✅    | BULL ring              |
| 25   | DOUBLE     | 25         | ✅    | BULL ring (double)     |
| 25   | TRIPLE     | 25         | ❌    | Invalid                |
| 25   | BULL       | 25         | ✅    | Inner bull (25 points) |
| 25   | DBLBULL    | 25         | ✅    | Outer bull (50 points) |

## Common Tasks

### Task 1: Map a New Dartboard from Scratch

```
1. Register dartboard type (Python):
   board = DartboardService.register_dartboard_type(
       session, "myboard", "Brand", "Model"
   )

2. Go to admin page and select it from dropdown

3. Click cells one-by-one and assign zones:
   - Click cell → Master/Slave pins auto-fill
   - Enter Zone (1-20 or 25)
   - Select Multiplier
   - Enter Base Value
   - Click "Save Mapping"

4. Repeat for all ~60-80 pin combinations
   OR use CSV bulk import (faster!)
```

### Task 2: Import 64 Mappings via CSV

```
1. Click "📥 Download CSV Template"

2. Open in Excel/Google Sheets

3. Fill in all 64 rows:
   Row 1 (headers): master_pin,slave_pin,zone_number,multiplier_type,base_value
   Row 2-65: 4,13,20,TRIPLE,20
            4,12,20,DOUBLE,20
            ... etc ...

4. Save as CSV

5. Go to admin page

6. Select dartboard type

7. Drag CSV file onto upload area

8. Confirm results
```

### Task 3: Fix One Wrong Mapping

```
1. Go to admin page

2. Select dartboard type

3. Look for incorrectly mapped cell (blue but wrong value)

4. Click the cell

5. Correct the zone/multiplier/value

6. Click "Save Mapping"

7. Cell updates immediately
```

### Task 4: View Live Dartboard Messages

```
1. Open admin page in browser

2. Have someone press physical dartboard keys

3. Watch message log update in real-time:
   [14:32:45] GPIO: master=4, slave=13
   Zone: 20, Mult: TRIPLE, Value: 20, Score: 60

4. If zone is unmapped:
   [14:32:46] GPIO: master=5, slave=14
   (no mapping found)
```

## Validation Rules

❌ **Invalid**: Zone 1-20 with BULL/DBLBULL multiplier

```
Zone: 20, Multiplier: BULL → ERROR
```

❌ **Invalid**: Zone 25 with TRIPLE multiplier

```
Zone: 25, Multiplier: TRIPLE → ERROR
```

❌ **Invalid**: Base value doesn't match zone

```
Zone: 20, Base Value: 15 → Should both be same (OK to be same though)
```

✅ **Valid**: Any combination below

```
Zone 1-20 + SINGLE/DOUBLE/TRIPLE + Base 1-20
Zone 25 + BULL/DBLBULL + Base 25
Zone 25 + SINGLE/DOUBLE + Base 25
```

## Troubleshooting

| Problem                         | Cause                          | Solution                                                          |
| ------------------------------- | ------------------------------ | ----------------------------------------------------------------- |
| Dartboard not in dropdown       | Not registered in DB           | Register via Python: `DartboardService.register_dartboard_type()` |
| All cells white (unmapped)      | New dartboard with no mappings | Use CSV import or manually map each cell                          |
| CSV import fails                | Invalid format or values       | Download template, verify format, check numbers are integers      |
| "Zone mapping not found" in log | Pressing unmapped pin on board | Map that pin combination in admin panel                           |
| Can't access page               | Not admin or not logged in     | Log in with admin credentials                                     |
| Page won't load matrix          | Dartboard type invalid         | Select different dartboard from dropdown                          |

## Common GPIO Values

### Carromco Striker (8×8 Matrix)

**Master Pins (Rows)**: 15, 2, 4, 16, 17, 5, 18, 19
**Slave Pins (Columns)**: 13, 12, 14, 27, 26, 25, 33, 32

### Typical Arduino Configurations

```
Master (Rows):     0-19 (20 pins)    or  0-7 (8 pins)
Slave (Columns):   20-39 (20 pins)   or  0-7 (8 pins)
```

## Keyboard Shortcuts

Currently none - all features use mouse/touch. Future versions may add:

- ESC to clear form
- Enter to save mapping
- Arrow keys to navigate matrix

## CSV Template Format

```csv
master_pin,slave_pin,zone_number,multiplier_type,base_value
4,13,20,TRIPLE,20
4,12,20,DOUBLE,20
4,11,20,SINGLE,20
2,13,1,TRIPLE,1
2,12,1,DOUBLE,1
16,13,25,BULL,25
16,12,25,DBLBULL,25
```

## Alert Messages

### Success ✓ (Green)

- "✓ Mapping saved successfully"
- "✓ Imported 2 new and updated 0 existing mappings"

### Error ✗ (Red)

- "Invalid zone mapping: zone=..., mult=..., value=..."
- "Dartboard type 'xyz' not found"
- "Missing required fields"

### Info 📋 (Blue)

- "Please select a dartboard type"
- "No valid mappings found in CSV"

## Tips & Tricks

1. **Use matrix clicking for accuracy**
   - Clicking cells is faster than typing pin numbers
   - Visual grid makes it easy to spot patterns

2. **Download template before bulk import**
   - Ensures correct CSV format
   - Prevents formatting errors

3. **Clear log periodically**
   - Keeps page responsive
   - Last 50 entries auto-retained

4. **Test live after importing**
   - Press each zone on dartboard
   - Verify messages appear in log with correct zones

5. **Use zone number as score hint**
   - Zone typically = base value (20 = twenty)
   - Multiplier determines final points (TRIPLE = ×3)

## Security Notes

- **Admin only**: All features require admin role
- **HTTPS required**: Use HTTPS only (secure connection)
- **Session timeout**: Logout if inactive (depends on server config)
- **No data exported**: Mappings stay in database
- **Audit trail**: All changes logged (in future versions)

## API Endpoints (For Developers)

```bash
# Get matrix visualization
GET /api/admin/dartboard/matrix/carromco

# Save single mapping
POST /api/admin/dartboard/mapping
Body: {"boardType":"carromco","masterPin":4,"slavePin":13,"zoneNumber":20,"multiplierType":"TRIPLE","baseValue":20}

# Bulk import
POST /api/admin/dartboard/import
Body: {"boardType":"carromco","mappings":[...]}
```

## Performance Tips

- **Large matrices** (40×40) render smoothly
- **CSV import** handles up to 1,000 mappings
- **Message log** keeps system responsive (50 entry limit)
- **Each save** is instant (sub-100ms typically)

## Getting Help

1. Check [ADMIN_DARTBOARD_TESTING.md](ADMIN_DARTBOARD_TESTING.md) for detailed guide
2. Review [DARTBOARD_ZONE_MAPPING.md](DARTBOARD_ZONE_MAPPING.md) for architecture
3. Check error messages - they're specific to the problem
4. Verify dartboard type is registered in database
5. Try downloading and importing the CSV template first

## Quick Stats

| Metric                  | Value                                     |
| ----------------------- | ----------------------------------------- |
| **Zones**               | 21 (1-20 + bull)                          |
| **Multipliers**         | 5 (SINGLE, DOUBLE, TRIPLE, BULL, DBLBULL) |
| **Max combinations**    | ~100+ (varies by board)                   |
| **Supported GPIO pins** | 0-40 (varies by Arduino)                  |
| **CSV import limit**    | 1,000 mappings per import                 |
| **Message log entries** | 50 (oldest auto-removed)                  |
| **Page load time**      | <1 second                                 |
| **Save mapping time**   | <100ms                                    |

---

**Last Updated**: 2024
**Admin Feature Version**: 1.0
**Compatible With**: DartServer Python App v1.0+
