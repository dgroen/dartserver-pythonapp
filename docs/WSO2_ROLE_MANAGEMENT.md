# WSO2 Identity Server - Role Management Guide

This guide explains how to manage roles and groups for the Darts Game application using WSO2 Identity Server's SCIM2 API.

---

## 📋 Overview

The Darts Game application uses WSO2 Identity Server for authentication and role-based access control (RBAC). Users must be assigned to specific groups in WSO2 IS to access different features of the application.

### Available Roles

| Role           | Description                              | Access Level                                           |
| -------------- | ---------------------------------------- | ------------------------------------------------------ |
| **gamemaster** | Game management and control panel access | Can create games, manage players, access control panel |
| **admin**      | Full system access                       | All permissions including system administration        |
| **player**     | Basic game participation                 | Can view games and submit scores                       |

---

## 🛠️ Management Scripts

### 1. Setup Roles Script (`setup_wso2_roles.py`)

This script configures roles for users by adding them to appropriate groups in WSO2 IS.

**Usage:**

```bash
python3 setup_wso2_roles.py
```

**What it does:**

- Searches for the specified user in WSO2 IS
- Creates groups if they don't exist
- Adds the user to the specified groups
- Verifies the final group membership

**Configuration:**
Edit the script to change the username or roles:

```python
username = "Dennis"
roles = ["gamemaster"]  # Add more: ["gamemaster", "admin", "player"]
```

### 2. Verify Roles Script (`verify_wso2_roles.py`)

This script verifies the current role configuration for a user.

**Usage:**

```bash
python3 verify_wso2_roles.py
```

**What it shows:**

- User information (username, ID, email)
- Current group membership
- All available groups in the system
- Role requirements for Darts application
- Recommendations for next steps

---

## 🚀 Quick Start Guide

### Step 1: Configure Roles for a User

Run the setup script to assign the `gamemaster` role to user Dennis:

```bash
cd /data/dartserver-pythonapp
python3 setup_wso2_roles.py
```

Expected output:

```
✅ Role configuration completed successfully!

📝 Next steps:
   1. Logout from the Darts application: https://letsplaydarts.eu/logout
   2. Login again: https://letsplaydarts.eu/login
   3. Check debug endpoint: https://letsplaydarts.eu/debug/auth
   4. Access control panel: https://letsplaydarts.eu/control
```

### Step 2: Verify Configuration

Run the verification script to confirm the roles are set correctly:

```bash
python3 verify_wso2_roles.py
```

Expected output:

```
✅ User has sufficient permissions for control panel access

🎭 Group Membership (1 groups)
1. gamemaster
   └─ Group ID: 90a344ca-e87e-437d-8c5d-eaf30a1ca99e
```

### Step 3: Test in Application

1. **Logout** from the application:

   ```
   https://letsplaydarts.eu/logout
   ```

2. **Login** again to get a fresh token with the new roles:

   ```
   https://letsplaydarts.eu/login
   ```

3. **Check debug endpoint** to verify roles are being extracted:

   ```
   https://letsplaydarts.eu/debug/auth
   ```

   Look for:

   ```json
   {
     "extracted_roles": ["gamemaster"],
     "scim2_groups": ["gamemaster"],
     "request_user_roles": ["gamemaster"]
   }
   ```

4. **Access control panel**:

   ```
   https://letsplaydarts.eu/control
   ```

   This should now work! 🎉

---

## 🔧 Advanced Configuration

### Adding Multiple Roles

To assign multiple roles to a user, edit `setup_wso2_roles.py`:

```python
username = "Dennis"
roles = ["gamemaster", "admin", "player"]
```

Then run the script:

```bash
python3 setup_wso2_roles.py
```

### Configuring Different Users

To configure roles for a different user, edit `setup_wso2_roles.py`:

```python
username = "JohnDoe"
roles = ["player"]
```

### Creating Custom Groups

The script automatically creates groups if they don't exist. To create a custom group:

1. Edit `setup_wso2_roles.py`
2. Add the custom group name to the roles list:

   ```python
   roles = ["gamemaster", "custom_role"]
   ```

3. Run the script

---

## 🐛 Troubleshooting

### Issue: User not found

**Error:**

```
❌ User 'Dennis' not found
```

**Solution:**

1. Check that the user exists in WSO2 IS Console: `https://letsplaydarts.eu/auth/console`
2. Verify the username is correct (case-sensitive)
3. Create the user if needed via WSO2 IS Console

### Issue: Authentication failed

**Error:**

```
❌ Error searching for user: 401
```

**Solution:**

1. Check WSO2 admin credentials in the script:

   ```python
   WSO2_ADMIN_USER = "admin"
   WSO2_ADMIN_PASSWORD = "admin"
   ```

2. Verify WSO2 IS is running: `docker-compose -f docker-compose-wso2.yml ps`

### Issue: Roles not appearing in application

**Problem:** User has roles in WSO2 but they don't appear in the application.

**Solution:**

1. **Logout and login again** - This is crucial! The application caches tokens.
2. Check the debug endpoint: `https://letsplaydarts.eu/debug/auth`
3. Look for roles in the output:
   - `extracted_roles`: Should show your roles
   - `scim2_groups`: Should show groups from SCIM2 API
4. Check application logs:

   ```bash
   docker-compose -f docker-compose-wso2.yml logs -f darts-app | grep -E "roles|SCIM2"
   ```

### Issue: 403 Forbidden on control panel

**Problem:** User gets 403 error when accessing `/control`

**Solution:**

1. Verify user has `gamemaster` or `admin` role:

   ```bash
   python3 verify_wso2_roles.py
   ```

2. Ensure the role name matches exactly (lowercase, no spaces)
3. Logout and login again to refresh the token
4. Check application logs for role extraction errors

---

## 📊 Role Extraction Flow

The application uses a multi-tier approach to extract roles:

```
1. Check Token Claims
   ├─ groups
   ├─ roles
   ├─ role
   ├─ group
   └─ realm_roles

2. If not found → Check UserInfo Endpoint
   └─ /oauth2/userinfo

3. If still not found → Check SCIM2 API (Fallback)
   └─ /scim2/Me

4. Normalize Roles
   ├─ Remove domain prefixes (Internal/, Application/)
   └─ Convert to lowercase
```

---

## 🔐 Security Notes

1. **Admin Credentials**: The scripts use admin credentials to access SCIM2 API. Keep these secure.
2. **SSL Verification**: SSL verification is disabled for self-signed certificates. In production, use proper SSL certificates.
3. **Token Refresh**: Always logout and login after role changes to get a fresh token.
4. **Scope Requirements**: The application requests `internal_login` scope for SCIM2 API access.

---

## 📚 Related Documentation

- [Authentication Flow](./docs/AUTHENTICATION_FLOW.md) - Detailed authentication flow diagrams
- [WSO2 IS Documentation](https://is.docs.wso2.com/) - Official WSO2 Identity Server docs
- [SCIM2 API Reference](https://is.docs.wso2.com/en/latest/apis/scim2-rest-apis/) - SCIM2 API documentation

---

## ✅ Current Configuration Status

**User:** Dennis  
**Email:** <dennis@it-groen.com>  
**User ID:** d39f3c2c-dc26-4067-a21d-de932d79b53c  
**Groups:** gamemaster  
**Status:** ✅ Configured and verified

**Next Steps:**

1. Logout: <https://letsplaydarts.eu/logout>
2. Login: <https://letsplaydarts.eu/login>
3. Debug: <https://letsplaydarts.eu/debug/auth>
4. Control: <https://letsplaydarts.eu/control>

---

## 🎯 Summary

The `gamemaster` role has been successfully configured for user Dennis via the WSO2 IS SCIM2 API. The user can now:

✅ Access the control panel at `/control`  
✅ Create and manage games  
✅ Add and remove players  
✅ View game state and scores

**Important:** You must logout and login again for the changes to take effect!
