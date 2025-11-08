# 🚀 Quick Reference - WSO2 Role Management

## One-Line Commands

```bash
# List roles for a user
python3 manage_user_roles.py list Dennis

# Add gamemaster role
python3 manage_user_roles.py add Dennis gamemaster

# Add admin role
python3 manage_user_roles.py add Dennis admin

# Add player role
python3 manage_user_roles.py add Dennis player

# Remove a role
python3 manage_user_roles.py remove Dennis player

# Verify configuration
python3 verify_wso2_roles.py

# Setup roles (batch)
python3 setup_wso2_roles.py
```

## Important URLs

| Purpose           | URL                                     |
| ----------------- | --------------------------------------- |
| **Logout**        | <https://letsplaydarts.eu/logout>       |
| **Login**         | <https://letsplaydarts.eu/login>        |
| **Debug Auth**    | <https://letsplaydarts.eu/debug/auth>   |
| **Control Panel** | <https://letsplaydarts.eu/control>      |
| **WSO2 Console**  | <https://letsplaydarts.eu/auth/console> |

## After Role Changes

**Always do this after changing roles:**

1. Logout: <https://letsplaydarts.eu/logout>
2. Login: <https://letsplaydarts.eu/login>
3. Test: <https://letsplaydarts.eu/control>

## Check Logs

```bash
# All logs
docker-compose -f docker-compose-wso2.yml logs -f darts-app

# Role-related logs only
docker-compose -f docker-compose-wso2.yml logs -f darts-app | grep -E "roles|SCIM2|DEBUG"

# WSO2 logs
docker-compose -f docker-compose-wso2.yml logs -f wso2is
```

## Available Roles

| Role         | Description     | Access                                      |
| ------------ | --------------- | ------------------------------------------- |
| `gamemaster` | Game management | Control panel, create games, manage players |
| `admin`      | Full access     | Everything                                  |
| `player`     | Basic access    | View games, submit scores                   |

## Current Configuration

**User:** Dennis  
**Role:** gamemaster ✅  
**Status:** Configured and verified

## Troubleshooting One-Liners

```bash
# Verify user exists
python3 verify_wso2_roles.py

# Check if role is assigned
python3 manage_user_roles.py list Dennis

# Test SCIM2 API directly
curl -k -u admin:admin "https://letsplaydarts.eu/auth/scim2/Users?filter=userName%20eq%20%22Dennis%22"

# Restart application
docker-compose -f docker-compose-wso2.yml restart darts-app

# Check application status
docker-compose -f docker-compose-wso2.yml ps
```

## Quick Test Sequence

```bash
# 1. Verify role is assigned
python3 verify_wso2_roles.py

# 2. Check logs for role extraction
docker-compose -f docker-compose-wso2.yml logs --tail=50 darts-app | grep -E "roles|SCIM2"

# 3. Test in browser
# - Logout: https://letsplaydarts.eu/logout
# - Login: https://letsplaydarts.eu/login
# - Debug: https://letsplaydarts.eu/debug/auth
# - Control: https://letsplaydarts.eu/control
```

## Common Issues

| Issue             | Solution                                 |
| ----------------- | ---------------------------------------- |
| 403 on /control   | Logout and login again                   |
| Roles not showing | Check debug endpoint                     |
| SCIM2 403 error   | Add API permissions in WSO2 console      |
| User not found    | Check username spelling (case-sensitive) |

## Files Created

- `setup_wso2_roles.py` - Automated setup
- `verify_wso2_roles.py` - Verification
- `manage_user_roles.py` - Interactive management
- `WSO2_ROLE_MANAGEMENT.md` - Full documentation
- `ROLE_CONFIGURATION_SUMMARY.md` - Completion summary
- `QUICK_REFERENCE.md` - This file

---

**Remember:** Always logout and login after role changes! 🔄
