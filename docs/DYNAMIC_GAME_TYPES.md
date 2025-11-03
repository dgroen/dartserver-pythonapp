# Dynamic Game Type Selection

## Overview
Game type selection dropdowns are now populated dynamically from the database instead of being hardcoded in HTML templates. This means when new game types are added to the `gametype` table, they will automatically appear in all game type selectors across the application without requiring HTML template changes.

## Implementation

### Backend API Endpoint
**Endpoint:** `GET /api/game/types`

Returns a list of all available game types from the database.

**Response:**
```json
{
  "status": "success",
  "game_types": [
    {
      "id": 1,
      "name": "301",
      "description": "301 darts game"
    },
    {
      "id": 2,
      "name": "401",
      "description": "401 darts game"
    },
    ...
  ]
}
```

**Location:** `src/app/app.py` (lines ~2011-2055)

### JavaScript Helper Functions
**File:** `static/js/main.js`

Two helper functions have been added:

1. **`loadGameTypes(selectElement, includeAllOption)`**
   - Fetches game types from the API
   - Populates the provided select element
   - If `includeAllOption` is `true`, adds an "All Games" option (for filters)
   - Includes error handling with fallback to hardcoded values

2. **`loadFallbackGameTypes(selectElement, includeAllOption)`**
   - Fallback function if API call fails
   - Uses hardcoded list: 301, 401, 501, cricket

### Updated Templates

All templates with game type selectors have been updated:

1. **`templates/control.html`** (Game Master Control Panel)
   - Select element: `#game-type`
   - Dynamic loading: Yes
   - Include "All" option: No
   - Default selection: None (first option)

2. **`templates/history.html`** (Game History Page)
   - Select element: `#gameTypeFilter`
   - Dynamic loading: Yes
   - Include "All" option: Yes
   - Default selection: "All Games"

3. **`templates/mobile_gamemaster.html`** (Mobile Game Master)
   - Select element: `#gameType`
   - Dynamic loading: Yes
   - Include "All" option: No
   - Default selection: "501"

4. **`templates/mobile_results.html`** (Mobile Results/History)
   - Select element: `#gameTypeFilter`
   - Dynamic loading: Yes
   - Include "All" option: Yes
   - Default selection: "All Games"

## Usage

### For Developers

To add a new game type to the system:

1. **Add to database:**
   ```sql
   INSERT INTO gametype (name, description) 
   VALUES ('701', '701 darts game');
   ```

2. **That's it!** The new game type will automatically appear in all selectors across:
   - Desktop control panel
   - Dashboard filters
   - Mobile game master
   - Mobile results filters
   - History page filters

### For Frontend Developers

To add a game type selector to a new page:

```html
<!-- In your HTML -->
<select id="myGameTypeSelect">
  <!-- Options loaded dynamically via JavaScript -->
</select>

<!-- Include main.js -->
<script src="{{ url_for('static', filename='js/main.js') }}"></script>

<!-- Initialize the select on page load -->
<script>
  document.addEventListener('DOMContentLoaded', function() {
    const gameTypeSelect = document.getElementById('myGameTypeSelect');
    if (gameTypeSelect && typeof loadGameTypes === 'function') {
      // For game selection (no "All" option)
      loadGameTypes(gameTypeSelect, false);
      
      // OR for filtering (with "All Games" option)
      loadGameTypes(gameTypeSelect, true).then(() => {
        gameTypeSelect.value = 'all';  // Set default to "All"
      });
    }
  });
</script>
```

## Error Handling

The implementation includes robust error handling:

1. **API Failures:** If the API call fails, the system falls back to a hardcoded list of game types (301, 401, 501, cricket)
2. **Network Errors:** Console errors are logged, but the application continues to function with fallback values
3. **Missing Elements:** Code checks for element existence before attempting to populate

## Testing

To verify the feature works:

1. **Test API endpoint:**
   ```bash
   curl http://localhost:5000/api/game/types
   ```

2. **Test in browser:**
   - Visit any page with game type selection
   - Open browser console (F12)
   - Look for: `"Loaded X game types into select element"`

3. **Test fallback:**
   - Temporarily break the API
   - Verify selectors still populate with default values

## Files Modified

- `src/app/app.py` - Added `/api/game/types` endpoint
- `static/js/main.js` - Added `loadGameTypes()` and `loadFallbackGameTypes()` helper functions
- `templates/control.html` - Updated to use dynamic loading
- `templates/history.html` - Updated to use dynamic loading
- `templates/mobile_gamemaster.html` - Updated to use dynamic loading
- `templates/mobile_results.html` - Updated to use dynamic loading

## Benefits

1. **Maintainability:** No need to update multiple HTML files when adding game types
2. **Consistency:** All selectors use the same data source (database)
3. **Flexibility:** Easy to add new game types without code changes
4. **Robustness:** Fallback mechanism ensures functionality even if API fails
5. **Future-proof:** Ready for admin panels that allow game type management via UI
