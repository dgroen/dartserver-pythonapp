# Authentication Setup Guide

## Overview

This guide explains how to set up role-based authentication for the Darts Game System using WSO2 Identity Server. The system implements three distinct roles with different permission levels.

## Role Definitions

### 1. Player Role

**Access Level:** Basic

**Permissions:**

- View game board (`/`)
- View game state
- Submit scores
- View own profile

**Use Case:** Regular players who participate in games

### 2. Game Master Role

**Access Level:** Intermediate

**Permissions:**

- All Player permissions
- Access control panel (`/control`)
- Create new games (`game:create`)
- Add players (`player:add`)
- Remove players (`player:remove`)
- Manage game settings

**Use Case:** Game organizers, tournament managers

### 3. Admin Role

**Access Level:** Full

**Permissions:**

- All Game Master permissions
- Full system access
- User management
- System configuration

**Use Case:** System administrators

## Architecture

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │
       │ 1. Access protected page
       │
       ▼
┌─────────────────┐
│  Darts App      │
│  (Flask)        │
│  - Check session│
│  - Redirect to  │
│    login        │
└──────┬──────────┘
       │
       │ 2. OAuth2 Authorization Code Flow
       │
       ▼
┌─────────────────┐
│  WSO2 Identity  │
│  Server         │
│  - Authenticate │
│  - Get roles    │
│  - Issue token  │
└──────┬──────────┘
       │
       │ 3. Callback with code
       │
       ▼
┌─────────────────┐
│  Darts App      │
│  - Exchange code│
│  - Get token    │
│  - Store session│
│  - Check roles  │
└─────────────────┘
```

## Setup Instructions

### Step 1: Start WSO2 Identity Server

```bash
docker-compose -f docker-compose-wso2.yml up -d wso2is
```

Wait for WSO2 IS to be fully started (~2 minutes):

```bash
docker logs -f darts-wso2is
```

### Step 2: Access WSO2 Management Console

1. Open browser: <https://localhost:9443/carbon>
2. Login with default credentials:
   - Username: `admin`
   - Password: `admin`
3. Accept the self-signed certificate warning

### Step 3: Create Roles

1. Navigate to: **Main > Identity > Users and Roles > Add**
2. Click **Add New Role**
3. Create three roles:

#### Create "player" Role

- Role Name: `player`
- Permissions: (leave default or customize as needed)
- Click **Finish**

#### Create "gamemaster" Role

- Role Name: `gamemaster`
- Permissions: (leave default or customize as needed)
- Click **Finish**

#### Create "admin" Role

- Role Name: `admin`
- Permissions: Select all or administrative permissions
- Click **Finish**

### Step 4: Create Test Users

1. Navigate to: **Main > Identity > Users and Roles > Add**
2. Click **Add New User**
3. Create test users:

#### Test Player

- Username: `testplayer`
- Password: `Player@123`
- Roles: Select `player`
- Click **Finish**

#### Test Game Master

- Username: `testgamemaster`
- Password: `GameMaster@123`
- Roles: Select `gamemaster`
- Click **Finish**

#### Test Admin

- Username: `testadmin`
- Password: `Admin@123`
- Roles: Select `admin`
- Click **Finish**

### Step 5: Register OAuth2 Application

1. Navigate to: **Main > Identity > Service Providers > Add**
2. Service Provider Name: `DartsGameWebApp`
3. Click **Register**
4. Expand **Inbound Authentication Configuration**
5. Expand **OAuth/OpenID Connect Configuration**
6. Click **Configure**
7. Set the following:
   - **Callback Url:** `http://localhost:5000/callback`
   - **Allowed Grant Types:** Check `Code` and `Refresh Token`
   - **PKCE:** Select `Plain` (optional but recommended)
8. Click **Add**
9. **IMPORTANT:** Copy the generated **Client ID** and **Client Secret**

### Step 6: Configure Claims

1. In the same Service Provider configuration
2. Expand **Claim Configuration**
3. Select **Use Local Claim Dialect**
4. Click **Add Claim URI** and add:
   - `http://wso2.org/claims/username`
   - `http://wso2.org/claims/emailaddress`
   - `http://wso2.org/claims/role`
5. Set **Subject Claim URI:** `http://wso2.org/claims/username`
6. Check **Include User Domain** (optional)
7. Click **Update**

### Step 7: Configure Application Environment

Create or update `.env` file:

```bash
# WSO2 Identity Server Configuration
WSO2_IS_URL=https://localhost:9443
WSO2_CLIENT_ID=<paste_client_id_from_step_5>
WSO2_CLIENT_SECRET=<paste_client_secret_from_step_5>
WSO2_REDIRECT_URI=http://localhost:5000/callback
JWT_VALIDATION_MODE=introspection
WSO2_IS_INTROSPECT_USER=admin
WSO2_IS_INTROSPECT_PASSWORD=admin
SESSION_COOKIE_SECURE=False

# Flask Configuration
SECRET_KEY=<generate_random_secret_key>
FLASK_DEBUG=True
```

Generate a secure secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 8: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 9: Start the Application

```bash
python app.py
```

Or using Docker Compose:

```bash
docker-compose -f docker-compose-wso2.yml up -d
```

### Step 10: Test Authentication

1. Open browser: <http://localhost:5000>
2. You should be redirected to WSO2 IS login page
3. Login with one of the test users:
   - `testplayer` / `Player@123`
   - `testgamemaster` / `GameMaster@123`
   - `testadmin` / `Admin@123`
4. After successful login, you'll be redirected back to the application
5. You should see your username and role badge in the top-right corner

## Testing Role-Based Access

### Test Player Access

1. Login as `testplayer`
2. ✅ Should access: Game board (`/`)
3. ❌ Should NOT access: Control panel (`/control`)
4. Try accessing `/control` - should get 403 Forbidden

### Test Game Master Access

1. Login as `testgamemaster`
2. ✅ Should access: Game board (`/`)
3. ✅ Should access: Control panel (`/control`)
4. ✅ Can create games and manage players

### Test Admin Access

1. Login as `testadmin`
2. ✅ Should access: All pages
3. ✅ Full control over all features

## API Endpoints and Permissions

| Endpoint            | Method | Required Permission          | Roles              |
| ------------------- | ------ | ---------------------------- | ------------------ |
| `/`                 | GET    | Authenticated                | All                |
| `/control`          | GET    | `admin` or `gamemaster` role | Admin, Game Master |
| `/api/game/state`   | GET    | Authenticated                | All                |
| `/api/game/new`     | POST   | `game:create`                | Admin, Game Master |
| `/api/players`      | GET    | Authenticated                | All                |
| `/api/players`      | POST   | `player:add`                 | Admin, Game Master |
| `/api/players/<id>` | DELETE | `player:remove`              | Admin, Game Master |
| `/api/score`        | POST   | `score:submit`               | All                |
| `/profile`          | GET    | Authenticated                | All                |
| `/logout`           | GET    | Authenticated                | All                |

## Troubleshooting

### Issue: Redirect Loop

**Cause:** Session not being stored properly
**Solution:**

- Check SECRET_KEY is set
- Verify cookies are enabled in browser
- Check SESSION_COOKIE_SECURE setting

### Issue: 401 Unauthorized

**Cause:** Token validation failing
**Solution:**

- Verify WSO2_IS_URL is correct
- Check introspection credentials
- Ensure WSO2 IS is running

### Issue: 403 Forbidden

**Cause:** User doesn't have required role/permission
**Solution:**

- Verify user has correct role assigned in WSO2 IS
- Check role name matches exactly (case-sensitive)
- Review role permissions in `auth.py`

### Issue: Claims Not Available

**Cause:** Claims not configured in Service Provider
**Solution:**

- Follow Step 6 to configure claims
- Ensure role claim is included
- Update Service Provider configuration

### Issue: Cannot Access Control Panel

**Cause:** User doesn't have gamemaster or admin role
**Solution:**

- Login to WSO2 IS Management Console
- Navigate to Users and Roles
- Edit user and assign appropriate role

## Security Best Practices

### Production Deployment

1. **Use HTTPS Everywhere**

   ```bash
   SESSION_COOKIE_SECURE=True
   WSO2_IS_URL=https://your-domain.com
   WSO2_REDIRECT_URI=https://your-app-domain.com/callback
   ```

2. **Use Strong Secret Keys**

   ```bash
   # Generate with:
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

3. **Enable Certificate Verification**
   - In `auth.py`, change `verify=False` to `verify=True`
   - Use proper SSL certificates (not self-signed)

4. **Create Dedicated Service Account**
   - Don't use admin credentials for introspection
   - Create a dedicated service account with minimal permissions

5. **Enable Additional Security Features**
   - Multi-factor authentication (MFA)
   - Account lockout policies
   - Password policies
   - Session timeout

6. **Implement Rate Limiting**
   - Add rate limiting to login endpoints
   - Prevent brute force attacks

7. **Enable Audit Logging**
   - Log all authentication attempts
   - Monitor for suspicious activity

8. **Regular Security Updates**
   - Keep WSO2 IS updated
   - Update Python dependencies regularly
   - Monitor security advisories

## Advanced Configuration

### Custom Role Permissions

Edit `auth.py` to customize role permissions:

```python
ROLES = {
    "admin": {
        "name": "Admin",
        "description": "Full system access",
        "permissions": ["*"],
    },
    "gamemaster": {
        "name": "Game Master",
        "description": "Can manage games and players",
        "permissions": [
            "game:create",
            "game:manage",
            "game:delete",
            "player:add",
            "player:remove",
            "score:submit",
            "score:view",
        ],
    },
    "player": {
        "name": "Player",
        "description": "Can view games and submit scores",
        "permissions": ["game:view", "score:submit", "score:view"],
    },
}
```

### Add New Role

1. Add role definition in `auth.py`
2. Create role in WSO2 IS
3. Assign permissions
4. Update decorators in `app.py` as needed

### Custom Claims

To add custom claims:

1. In WSO2 IS, go to **Main > Identity > Claims > Add**
2. Add new claim dialect or claim
3. Map claim to user attributes
4. Include claim in Service Provider configuration
5. Access claim in application via `user_claims`

## Support

For issues or questions:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review WSO2 IS logs: `docker logs darts-wso2is`
3. Review application logs
4. Consult WSO2 IS documentation: <https://is.docs.wso2.com/>

## References

- [WSO2 Identity Server Documentation](https://is.docs.wso2.com/)
- [OAuth 2.0 Authorization Code Flow](https://oauth.net/2/grant-types/authorization-code/)
- [OpenID Connect](https://openid.net/connect/)
- [Flask Session Management](https://flask.palletsprojects.com/en/latest/api/#sessions)
