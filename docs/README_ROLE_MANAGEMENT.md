# 🎯 WSO2 Role Management - Complete Solution

## 📋 Overview

This directory contains a complete solution for managing user roles and groups in WSO2 Identity Server for the Darts Game application. All configuration is done via the SCIM2 API.

---

## ✅ Current Status

**User:** Dennis  
**Role:** gamemaster ✅  
**Status:** Configured and verified via SCIM2 API

---

## 🛠️ Management Tools

### Python Scripts

| Script                   | Purpose              | Usage                                                            |
| ------------------------ | -------------------- | ---------------------------------------------------------------- |
| **setup_wso2_roles.py**  | Automated role setup | `python3 setup_wso2_roles.py`                                    |
| **verify_wso2_roles.py** | Verify configuration | `python3 verify_wso2_roles.py`                                   |
| **manage_user_roles.py** | Interactive CLI      | `python3 manage_user_roles.py [add\|remove\|list] <user> [role]` |

### Documentation Files

| File                              | Description                                    |
| --------------------------------- | ---------------------------------------------- |
| **WSO2_ROLE_MANAGEMENT.md**       | Complete management guide with troubleshooting |
| **ROLE_CONFIGURATION_SUMMARY.md** | Detailed summary of current configuration      |
| **QUICK_REFERENCE.md**            | Quick command reference card                   |
| **README_ROLE_MANAGEMENT.md**     | This file (index)                              |

---

## 🚀 Quick Start

### For User Dennis (First Time)

**⚠️ IMPORTANT: You must logout and login after role configuration!**

```bash
# 1. Verify role is configured
python3 verify_wso2_roles.py

# 2. Logout from application
# Visit: https://letsplaydarts.eu/logout

# 3. Login again
# Visit: https://letsplaydarts.eu/login

# 4. Test control panel access
# Visit: https://letsplaydarts.eu/control
```

### For Adding Roles to Other Users

```bash
# Add gamemaster role to a user
python3 manage_user_roles.py add JohnDoe gamemaster

# Verify it was added
python3 manage_user_roles.py list JohnDoe

# User must logout and login to activate the role
```

---

## 📚 Available Roles

| Role           | Description         | Permissions                                                |
| -------------- | ------------------- | ---------------------------------------------------------- |
| **gamemaster** | Game management     | Control panel, create games, manage players, submit scores |
| **admin**      | Full system access  | All permissions                                            |
| **player**     | Basic participation | View games, submit scores                                  |

---

## 🔧 Common Tasks

### List User's Current Roles

```bash
python3 manage_user_roles.py list Dennis
```

### Add a Role

```bash
python3 manage_user_roles.py add Dennis gamemaster
```

### Remove a Role

```bash
python3 manage_user_roles.py remove Dennis player
```

### Verify Configuration

```bash
python3 verify_wso2_roles.py
```

### Check Application Logs

```bash
docker-compose -f docker-compose-wso2.yml logs -f darts-app | grep -E "roles|SCIM2"
```

---

## 🐛 Troubleshooting

### Issue: 403 Forbidden on /control

**Solution:**

1. Verify role is assigned: `python3 verify_wso2_roles.py`
2. **Logout:** <https://letsplaydarts.eu/logout>
3. **Login:** <https://letsplaydarts.eu/login>
4. Try again: <https://letsplaydarts.eu/control>

### Issue: Roles Not Showing

**Solution:**

1. Check debug endpoint: <https://letsplaydarts.eu/debug/auth>
2. Look for `extracted_roles` and `scim2_groups` in the output
3. Check logs: `docker-compose -f docker-compose-wso2.yml logs -f darts-app | grep SCIM2`

### Issue: User Not Found

**Solution:**

1. Verify username spelling (case-sensitive)
2. Check WSO2 IS Console: <https://letsplaydarts.eu/auth/console>
3. Create user if needed via WSO2 console

---

## 🔍 How It Works

The application uses a **multi-tier role extraction** approach:

```
1. Token Claims → 2. UserInfo API → 3. SCIM2 API (Fallback) → 4. Normalize
```

### OAuth2 Scopes

- `openid` - Basic OpenID Connect
- `profile` - User profile
- `email` - Email address
- `groups` - Group membership
- `internal_login` - SCIM2 API access ✨

### Role Normalization

- Removes domain prefixes: `Internal/gamemaster` → `gamemaster`
- Converts to lowercase: `GameMaster` → `gamemaster`

---

## 📊 Configuration Details

### WSO2 IS Endpoints Used

- **SCIM2 Users API:** `/scim2/Users` - User management
- **SCIM2 Groups API:** `/scim2/Groups` - Group management
- **SCIM2 Me Endpoint:** `/scim2/Me` - Current user info (used by app)

### Authentication

- **Admin User:** admin
- **Admin Password:** admin
- **Method:** HTTP Basic Auth

### SSL Configuration

- **Verify SSL:** Disabled (self-signed certificates)
- **Production:** Should use proper SSL certificates

---

## 🎯 Testing Checklist

After configuring roles:

- [ ] Run verification script: `python3 verify_wso2_roles.py`
- [ ] Logout from application: <https://letsplaydarts.eu/logout>
- [ ] Login again: <https://letsplaydarts.eu/login>
- [ ] Check debug endpoint: <https://letsplaydarts.eu/debug/auth>
- [ ] Verify roles appear in `extracted_roles` field
- [ ] Test control panel access: <https://letsplaydarts.eu/control>
- [ ] Check application logs for errors

---

## 📖 Documentation Structure

```
/data/dartserver-pythonapp/
├── setup_wso2_roles.py              # Automated setup script
├── verify_wso2_roles.py             # Verification script
├── manage_user_roles.py             # Interactive CLI tool
├── WSO2_ROLE_MANAGEMENT.md          # Complete guide (START HERE)
├── ROLE_CONFIGURATION_SUMMARY.md    # Current configuration details
├── QUICK_REFERENCE.md               # Quick commands
└── README_ROLE_MANAGEMENT.md        # This file (index)
```

---

## 🌐 Important URLs

| Purpose              | URL                                     |
| -------------------- | --------------------------------------- |
| **Application Home** | <https://letsplaydarts.eu/>             |
| **Login**            | <https://letsplaydarts.eu/login>        |
| **Logout**           | <https://letsplaydarts.eu/logout>       |
| **Control Panel**    | <https://letsplaydarts.eu/control>      |
| **Debug Auth**       | <https://letsplaydarts.eu/debug/auth>   |
| **WSO2 Console**     | <https://letsplaydarts.eu/auth/console> |

---

## 🎉 Success Criteria

You'll know the configuration is working when:

1. ✅ `verify_wso2_roles.py` shows the user has the role
2. ✅ `/debug/auth` endpoint shows roles in `extracted_roles`
3. ✅ `/control` page loads without 403 error
4. ✅ Application logs show: `Extracted and normalized roles: ['gamemaster']`

---

## 💡 Tips

1. **Always logout and login** after role changes - tokens are cached!
2. **Use the debug endpoint** to verify role extraction
3. **Check application logs** for detailed debugging information
4. **Role names are case-insensitive** - they're normalized to lowercase
5. **Domain prefixes are removed** - `Internal/gamemaster` becomes `gamemaster`

---

## 🔐 Security Notes

- Admin credentials are used for SCIM2 API access
- SSL verification is disabled for self-signed certificates
- In production, use proper SSL certificates and secure credential storage
- The `internal_login` scope is required for SCIM2 API access

---

## 📞 Support

If you encounter issues:

1. **Read the documentation:** Start with `WSO2_ROLE_MANAGEMENT.md`
2. **Check the troubleshooting section** in the documentation
3. **Run verification script:** `python3 verify_wso2_roles.py`
4. **Check debug endpoint:** <https://letsplaydarts.eu/debug/auth>
5. **Review application logs:** Look for role extraction errors

---

## ✨ What's New

### Recent Changes

- ✅ Added SCIM2 API fallback for role extraction
- ✅ Added `internal_login` scope for SCIM2 access
- ✅ Created automated role management scripts
- ✅ Configured `gamemaster` role for user Dennis
- ✅ Added comprehensive documentation

### Previous Issues Fixed

- ✅ Nginx 404 errors for WSO2 endpoints
- ✅ Role extraction from WSO2 IS
- ✅ SCIM2 API integration

---

## 🎯 Next Steps

For user Dennis:

1. **Logout:** <https://letsplaydarts.eu/logout>
2. **Login:** <https://letsplaydarts.eu/login>
3. **Test:** <https://letsplaydarts.eu/control>

For administrators:

1. Review `WSO2_ROLE_MANAGEMENT.md` for complete documentation
2. Use `manage_user_roles.py` to manage other users
3. Monitor application logs for role extraction issues

---

**Configuration Date:** 2025-01-14  
**Status:** ✅ Complete and Verified  
**User:** Dennis  
**Role:** gamemaster

**Remember:** Logout and login to activate the role! 🔄
