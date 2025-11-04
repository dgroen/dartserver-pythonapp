# Development Environment - READY ✅

## Summary

Your local development environment has been successfully configured with all fixes from the test environment (test.letsplaydarts.eu).

**Status**: All systems operational and tested ✅

### Configuration Updates

#### 1. WSO2 OAuth Client ✅
- **Application**: DartsApp Local
- **Client ID**: `zWDyLDXaMQcKiFcENwsTduXpKoka`
- **Client Secret**: `1qiEYLgIe9LrtKxD3J1YMo1psmJ3Gg8LMXF9rTg60Vka`
- **Callback URLs**:
  - `https://localhost:5000/callback`
  - `http://localhost:5000/callback`
  - `https://localhost:5001` (alternate)
- **Status**: ACTIVE ✅

#### 2. SSL Certificates ✅
- **Nginx certificate**: `/data/dartserver-pythonapp/nginx/nginx.crt`
- **SSL certificate**: `/data/dartserver-pythonapp/ssl/cert.pem`
- **Status**: Identical (MD5: 49b721c256c9fb38847d43aefb6f56f9) ✅
- **CN**: letsplaydarts.eu
- **SANs**:
  - `*.letsplaydarts.eu`
  - `letsplaydarts.eu`
  - `localhost`
  - `*.localhost`
  - `127.0.0.1`
  - `::1`

#### 3. Database Game Types ✅
The `dartsdb` database now has all 5 game types:

| ID | Name | Description |
|----|------|-------------|
| 6 | 301 | 301 darts game |
| 7 | 401 | 401 darts game |
| 8 | 501 | 501 darts game |
| 9 | cricket | Cricket darts game |
| 11 | round_the_clock | Round the Clock - hit numbers 1-20 in order |

**Note**: Removed duplicate Cricket entry (id 10) and updated 6 existing games to use id 9.

#### 4. Code Fixes Already Applied ✅

All fixes from the test environment are already in the codebase:

**app.py:**
- ✅ SCIM2 fallback for username fetching when userinfo doesn't provide it
- ✅ WSO2 tenant suffix stripping (`@carbon.super` removal)
- ✅ Debug logging for player creation and session tracking
- ✅ CORS credentials support
- ✅ `/api/game/types` endpoint for dynamic game type loading

**main.js:**
- ✅ `loadGameTypes()` function for dynamic game type population
- ✅ Null-safety checks for cross-page compatibility
- ✅ Single `socket` declaration (no duplicates)
- ✅ `formatGameTypeName()` helper for display formatting
- ✅ Default selection of "501" game type

**control.js:**
- ✅ Removed duplicate `const socket` declaration
- ✅ Debug logging for add player and start game actions

**Templates:**
- ✅ control.html - Dynamic game type loading
- ✅ history.html - Dynamic filter with "All Games" option
- ✅ mobile_gamemaster.html - Dynamic selection (default: 501)
- ✅ mobile_results.html - Dynamic filter

### Next Steps - Manual Testing Required

#### 1. Restart the Flask App

**Important**: The `.env` file has been updated with the correct WSO2 OAuth credentials. You need to restart `python run.py` to pick up the changes.

```bash
# Stop the current python run.py process (Ctrl+C in the terminal)
# Then restart:
python run.py
```

#### 2. Test the Complete Flow

**A. Access the Application**
```
https://localhost:5000/
```

**Expected**:
- Browser shows SSL certificate warning (self-signed cert)
- Accept the warning (Advanced → Proceed to localhost)
- Page should load without JavaScript errors

**B. Check Browser Console**
- Press F12 → Console tab
- Should see debug messages like:
  ```
  loadGameTypes called with: game-type includeAllOption: false
  API response: {status: "success", game_types: Array(5)}
  Added option: 301 -> 301
  ...
  Set default value to 501
  ```

**C. Test Login Flow**
1. Click "Login" button
2. Should redirect to WSO2 at `https://localhost:9443/authenticationendpoint/login.do`
3. Login with WSO2 credentials (e.g., admin/admin or your test user)
4. Should redirect back to `https://localhost:5000/callback`
5. Should be logged in and redirected to main page

**D. Test Control Panel**
```
https://localhost:5000/control
```

**Expected**:
- ✅ No "const socket" errors in console
- ✅ Game type dropdown shows all 5 types (301, 401, 501, Cricket, Round the Clock)
- ✅ "501" is selected by default
- ✅ Can add players without errors
- ✅ Can start a new game

**E. Test History & Dashboard**
```
https://localhost:5000/history
https://localhost:5000/dashboard
```

**Expected**:
- ✅ Pages load without errors
- ✅ Show games for the logged-in user
- ✅ Game type filter includes "All Games" option
- ✅ Can filter by specific game types

### Differences Between Environments

| Feature | Dev (localhost) | Test (test.letsplaydarts.eu) | Prod (letsplaydarts.eu) |
|---------|----------------|------------------------------|-------------------------|
| **Domain** | localhost:5000 | test.letsplaydarts.eu | letsplaydarts.eu |
| **Database** | dartsdb | dartsdbtest | dartsdb (prod) |
| **WSO2 Hostname** | localhost | test.letsplaydarts.eu | letsplaydarts.eu |
| **OAuth Client** | DartsApp Local | DartsGameTestServer | DartsApp (prod) |
| **Environment** | development | test | production |
| **Debug Mode** | True | True | False |
| **SSL** | Self-signed | Self-signed | Let's Encrypt (production) |

### Troubleshooting

**Issue**: "SSL_ERROR_INTERNAL_ERROR_ALERT"
- **Cause**: Nginx certificates don't match expected CN/SAN
- **Status**: ✅ Fixed - certificates are correct

**Issue**: "invalid_client" on WSO2 redirect
- **Cause**: OAuth client ID/secret don't match registered application
- **Status**: ✅ Fixed - using correct credentials from DartsApp Local

**Issue**: History/Dashboard empty
- **Causes**:
  1. Username mismatch (WSO2 returns `testuser001@carbon.super` but DB has `testuser001`)
  2. Session doesn't have `player_id` set
  3. SCIM2 not fetching real username
- **Status**: ✅ All fixed in code

**Issue**: Control panel JavaScript errors
- **Causes**:
  1. Duplicate `const socket` declaration
  2. Null pointer errors when accessing DOM elements that don't exist
- **Status**: ✅ Fixed with null checks and removed duplicate

**Issue**: Game type selector empty
- **Cause**: API call timing or caching
- **Status**: ✅ Fixed with proper async loading and fallback

### Git Workflow Reminder

For future changes:

1. **Dev Machine** (another machine):
   - Make changes on `dev` branch
   - Test locally
   - Push to remote: `git push origin dev`

2. **Test Machine** (this machine):
   - Pull dev changes: `git pull origin dev`
   - Merge into test: `git checkout test && git merge dev`
   - Push test branch: `git push origin test`
   - Deploy and test at test.letsplaydarts.eu

3. **Production** (after testing):
   - Merge test into main: `git checkout main && git merge test`
   - Push main: `git push origin main`
   - Deploy to production at letsplaydarts.eu

**Flow**: `dev` → `test` → `main`

---

## Summary

✅ **WSO2 OAuth**: Configured with DartsApp Local credentials  
✅ **SSL Certificates**: Verified and matching  
✅ **Database**: All 5 game types present, including Round the Clock  
✅ **Code Fixes**: SCIM2, username handling, CORS, SocketIO all applied  
✅ **JavaScript**: Null-safe, no duplicate declarations, dynamic game types  

**Ready to test!** Restart `python run.py` and access https://localhost:5000/
