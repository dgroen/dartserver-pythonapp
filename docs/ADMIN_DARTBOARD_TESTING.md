# Admin Dartboard Testing & Calibration Guide

## Overview

The Admin Dartboard Testing & Calibration page (`/admin/dartboard-testing`) is a comprehensive tool for managing dartboard GPIO pin-to-zone mappings. It provides an intuitive interface for:

- **Viewing GPIO pin matrix** - See all master/slave pin combinations in a visual grid
- **Mapping physical presses** - Associate dartboard presses to GPIO pins and game zones
- **Real-time message logging** - View raw dartboard messages as they arrive
- **Manual mapping** - Create or update individual pin-to-zone mappings
- **Bulk import** - Import multiple mappings from CSV files at once

## Access Requirements

- **Role Required**: Admin
- **Authentication**: Required (WSO2 Identity Server)
- **URL**: `https://your-server:5000/admin/dartboard-testing`

## Features

### 1. Dartboard Selection

**Location**: Top-left Configuration section

- **Dropdown Menu**: Select which dartboard type to configure
- **Auto-populated**: Lists all registered dartboard types from the database
- **Board Info**: Shows brand, model, and total number of existing mappings

```
Example:
- Carromco - Striker (64 mappings)
- Winmau - Blade 6 (0 mappings)
```

### 2. GPIO Pin Matrix

**Location**: Right side of screen

**Features**:
- **Grid Layout**: Master pins (rows) × Slave pins (columns)
- **Color Coding**:
  - **White cells**: Unmapped pin combinations
  - **Blue cells**: Already mapped combinations (show zone number, multiplier, base value)
  - **Highlighted on hover**: Shows which cell will be selected
- **Interactive**: Click any cell to populate the manual mapping form

**Matrix Example** (Carromco 8×8):
```
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

### 3. Manual Mapping Form

**Location**: Left side, below Configuration

**Fields**:
- **Master Pin (Row)**: GPIO pin number for row (0-40 typically)
- **Slave Pin (Column)**: GPIO pin number for column (0-40 typically)
- **Zone Number**: 1-20 for dartboard segments, 25 for bull's eye
- **Multiplier Type**: SINGLE, DOUBLE, TRIPLE, BULL, or DBLBULL
- **Base Value**: 1-20 for segments, 25 for bull (must match zone for BULL/DBLBULL)

**Usage**:
1. Select a dartboard type
2. Click a cell in the matrix OR manually enter pin values
3. Select zone number, multiplier type, and base value
4. Click **Save Mapping**

**Validation Rules**:
- BULL and DBLBULL only valid for zone 25
- Base value must be 1-20 for segments, 25 for bull
- Zone and base value typically match (both represent the score)

### 4. Real-Time Message Log

**Location**: Bottom full-width section

**Display Format**:
```
[14:32:45] GPIO: master=4, slave=13
Zone: 20, Mult: TRIPLE, Value: 20, Score: 60

[14:32:46] GPIO: master=4, slave=12
Zone: 20, Mult: DOUBLE, Value: 20, Score: 40
```

**Features**:
- **Auto-scroll**: New messages appear at top
- **Color-coded**: Green text on black background (terminal style)
- **Raw data**: Shows GPIO pins, zone info, and calculated score
- **History**: Keeps last 50 entries
- **Clear button**: Manually clear the log

### 5. Bulk CSV Import

**Location**: Left side, bottom section

**Supported Format**:
```csv
master_pin,slave_pin,zone_number,multiplier_type,base_value
4,13,20,TRIPLE,20
4,12,20,DOUBLE,20
4,11,20,SINGLE,20
2,13,1,TRIPLE,1
16,13,25,BULL,25
16,12,25,DBLBULL,25
```

**Features**:
- **Drag & Drop**: Drop CSV file on the upload area
- **Click to Upload**: Click to select file from system
- **Template Download**: Download pre-formatted template
- **Validation**: Each row validated before import
- **Report**: Shows created count and updated count
- **Error Handling**: Stops on first error and reports problem row

**CSV Template Format**:
| Field | Type | Valid Range | Description |
|-------|------|-------------|-------------|
| master_pin | integer | 0-40 | GPIO row pin |
| slave_pin | integer | 0-40 | GPIO column pin |
| zone_number | integer | 1-20, 25 | Dartboard zone |
| multiplier_type | string | SINGLE, DOUBLE, TRIPLE, BULL, DBLBULL | Score multiplier |
| base_value | integer | 1-20, 25 | Base score value |

**Example CSV (Carromco 8×8 full matrix)**:
```csv
master_pin,slave_pin,zone_number,multiplier_type,base_value
15,13,12,SINGLE,12
15,12,50,SINGLE,50
15,14,36,SINGLE,36
15,27,15,SINGLE,15
15,26,5,SINGLE,5
15,25,10,SINGLE,10
15,33,24,SINGLE,24
15,32,0,SINGLE,0
2,13,9,SINGLE,9
2,12,25,SINGLE,25
... (more rows)
```

## API Endpoints

### GET /api/admin/dartboard/matrix/{board_type}

Returns matrix visualization data for admin interface.

**Parameters**:
- `board_type` (path): Dartboard type name (e.g., 'carromco')

**Response**:
```json
{
  "status": "success",
  "dartboard_type": {
    "id": 1,
    "name": "carromco",
    "brand": "Carromco",
    "model": "Striker",
    "description": "Carromco Striker board"
  },
  "master_pins": [15, 2, 4, 16, 17, 5, 18, 19],
  "slave_pins": [13, 12, 14, 27, 26, 25, 33, 32],
  "matrix": [
    {
      "master_pin": 15,
      "cells": [
        {
          "master_pin": 15,
          "slave_pin": 13,
          "mapping": {
            "zone_number": 12,
            "multiplier_type": "SINGLE",
            "base_value": 12,
            "id": 1
          }
        },
        ...
      ]
    },
    ...
  ]
}
```

### POST /api/admin/dartboard/mapping

Update or create a single zone mapping.

**Request Body**:
```json
{
  "boardType": "carromco",
  "masterPin": 4,
  "slavePin": 13,
  "zoneNumber": 20,
  "multiplierType": "TRIPLE",
  "baseValue": 20
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Mapping for pins (4, 13) updated successfully"
}
```

### POST /api/admin/dartboard/import

Bulk import multiple mappings from CSV data.

**Request Body**:
```json
{
  "boardType": "carromco",
  "mappings": [
    {
      "masterPin": 4,
      "slavePin": 13,
      "zoneNumber": 20,
      "multiplierType": "TRIPLE",
      "baseValue": 20
    },
    {
      "masterPin": 4,
      "slavePin": 12,
      "zoneNumber": 20,
      "multiplierType": "DOUBLE",
      "baseValue": 20
    }
  ]
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Imported 2 new mappings and updated 0 existing mappings",
  "created": 2,
  "updated": 0
}
```

## Workflow Examples

### Example 1: Testing a New Dartboard

1. **Register Dartboard Type**:
   ```python
   from src.core.dartboard_service import DartboardService
   from src.core.database_service import get_session

   session = get_session()
   board = DartboardService.register_dartboard_type(
       session,
       name="winmau",
       brand="Winmau",
       model="Blade 6"
   )
   ```

2. **Access Testing Page**:
   - Navigate to `https://your-server/admin/dartboard-testing`
   - Select "Winmau - Blade 6" from dropdown

3. **Start Testing**:
   - Have someone press zones on physical dartboard
   - Watch GPIO signals appear in Message Log
   - Click cells in matrix or manually enter pin values
   - Save mappings for each press

### Example 2: Bulk Import Known Configuration

1. **Prepare CSV File**:
   - Download template from admin page
   - Fill in all pin combinations for your dartboard
   - Save as `carromco_mappings.csv`

2. **Import in Admin Page**:
   - Select dartboard type
   - Drag & drop CSV file onto upload area
   - Confirm import results

3. **Verify**:
   - Matrix should show all cells in blue
   - Message log shows import results

### Example 3: Fixing Incorrect Mapping

1. **View Current Matrix**:
   - Open admin testing page
   - Select dartboard type
   - Identify incorrectly mapped cell (blue but wrong values)

2. **Correct Mapping**:
   - Click the cell to select it
   - Update zone, multiplier, and base value
   - Click **Save Mapping** to update

3. **Verify**:
   - Cell updates immediately
   - Previous incorrect values replaced

## Troubleshooting

### "Dartboard type not found"
- **Cause**: Dartboard type not registered in database
- **Fix**: Register dartboard type first using `DartboardService.register_dartboard_type()`

### "Zone mapping not found" in message log
- **Cause**: GPIO pins haven't been mapped yet
- **Fix**: Click the cell to select pins, fill form, and save mapping

### Matrix shows all white cells
- **Cause**: No mappings exist for this dartboard type
- **Fix**: Start creating mappings using manual form or CSV import

### CSV import fails
- **Cause**: Invalid CSV format or values
- **Fix**:
  - Download template to see correct format
  - Verify all numeric values are integers
  - Check zone numbers are 1-20 or 25
  - Verify multiplier types are uppercase

### Cannot access admin page
- **Cause**: Not logged in or don't have admin role
- **Fix**:
  - Log in with admin credentials
  - Verify role is set to "admin" in identity provider

## Performance Considerations

- **Matrix Size**: Grid renders up to 40×40 (1,600 cells) smoothly
- **Message Log**: Keeps last 50 entries, older entries removed
- **Update Speed**: Mappings save instantly with database persistence
- **CSV Import**: Tested with up to 1,000 mappings per import

## Security Notes

- **Admin Only**: Page requires admin role - enforced server-side
- **No Direct Access**: All API endpoints check role/permission
- **Input Validation**: All numeric inputs validated on server
- **CSRF Protected**: Flask CSRF protection enabled for forms

## WebSocket Real-Time Updates

When dartboards send test messages during testing:

1. **Message arrives** at `/api/Throw/zone` endpoint
2. **Socket event** `dartboard_test_message` emitted
3. **Admin page listens** for `dartboard_test_received` event
4. **Message logged** in real-time in Message Log section
5. **Matrix highlights** corresponding cell (if mapped)

## Future Enhancements

Potential improvements:
- **Live dartboard streaming**: Real-time pin detection from connected board
- **Calibration wizard**: Step-by-step guide for new board setup
- **Import templates**: Pre-built templates for popular dartboard types
- **Export mappings**: Save current board configuration as CSV
- **Board profiles**: Save/load multiple configurations per board
- **Visual board image**: Overlay matrix on actual dartboard photo
- **Statistics**: Show which zones are most/least used
- **Testing reports**: Generate PDF calibration reports

## See Also

- [Dartboard Zone Mapping Architecture](DARTBOARD_ZONE_MAPPING.md)
- [Dartboard Migration Guide](DARTBOARD_MIGRATION_GUIDE.md)
- [DartboardService API Reference](DARTBOARD_ZONE_MAPPING.md#dartboardservice-methods)
