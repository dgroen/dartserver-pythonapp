# Remote Login Flow - Visual Guide

## 🔴 BEFORE FIX - Broken Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER JOURNEY                             │
└─────────────────────────────────────────────────────────────────┘

Step 1: User opens browser on mobile device
┌──────────────┐
│   📱 Mobile  │
│   Browser    │
└──────┬───────┘
       │
       │ Opens: https://letsplaydarts.eu
       ↓
┌──────────────┐
│    Nginx     │ Port 443
│ Reverse Proxy│
└──────┬───────┘
       │
       │ Routes to darts-app
       ↓
┌──────────────┐
│  Darts App   │ Port 5000
│  (Flask)     │
└──────┬───────┘
       │
       │ User clicks "Login"
       ↓

Step 2: App generates authorization URL
┌──────────────────────────────────────────────────────────────┐
│ auth.py:                                                      │
│   WSO2_IS_URL = "https://localhost:9443"  ❌ PROBLEM!       │
│   redirect_url = f"{WSO2_IS_URL}/oauth2/authorize"          │
│   # Returns: https://localhost:9443/oauth2/authorize         │
└──────────────────────────────────────────────────────────────┘
       │
       │ Browser redirects to localhost
       ↓
┌──────────────┐
│   📱 Mobile  │
│   Browser    │  Tries to connect to: https://localhost:9443
└──────┬───────┘
       │
       │ ❌ ERROR: localhost is not accessible from mobile!
       ↓
   Connection Failed
   User cannot login
```

---

## 🟢 AFTER FIX - Working Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER JOURNEY (FIXED)                          │
└─────────────────────────────────────────────────────────────────┘

Step 1: User opens browser on mobile device
┌──────────────┐
│   📱 Mobile  │
│   Browser    │
└──────┬───────┘
       │
       │ Opens: https://letsplaydarts.eu
       ↓
┌──────────────┐
│    Nginx     │ Port 443
│ Reverse Proxy│
└──────┬───────┘
       │
       │ Routes to darts-app
       ↓
┌──────────────┐
│  Darts App   │ Port 5000
│  (Flask)     │
└──────┬───────┘
       │
       │ User clicks "Login"
       ↓

Step 2: App generates authorization URL (FIXED)
┌──────────────────────────────────────────────────────────────┐
│ auth.py:                                                      │
│   WSO2_IS_URL = "https://letsplaydarts.eu/auth"  ✅ FIXED!  │
│   redirect_url = f"{WSO2_IS_URL}/oauth2/authorize"          │
│   # Returns: https://letsplaydarts.eu/auth/oauth2/authorize  │
└──────────────────────────────────────────────────────────────┘
       │
       │ Browser redirects to public URL
       ↓
┌──────────────┐
│   📱 Mobile  │
│   Browser    │  Connects to: https://letsplaydarts.eu/auth/oauth2/authorize
└──────┬───────┘
       │
       │ ✅ SUCCESS: Public URL is accessible!
       ↓
┌──────────────┐
│    Nginx     │ Port 443
│ Reverse Proxy│
└──────┬───────┘
       │
       │ Routes /auth/ to wso2is:9443
       ↓
┌──────────────┐
│   WSO2 IS    │ Port 9443
│  (Docker)    │
└──────┬───────┘
       │
       │ Shows login page
       ↓
┌──────────────┐
│   📱 Mobile  │
│   Browser    │  User enters credentials
└──────┬───────┘
       │
       │ Submits login form
       ↓
┌──────────────┐
│   WSO2 IS    │ Validates credentials
└──────┬───────┘
       │
       │ Redirects back with authorization code
       ↓
┌──────────────┐
│   📱 Mobile  │
│   Browser    │  Redirects to: https://letsplaydarts.eu/callback?code=...
└──────┬───────┘
       │
       ↓
┌──────────────┐
│    Nginx     │
└──────┬───────┘
       │
       ↓
┌──────────────┐
│  Darts App   │ Receives authorization code
└──────┬───────┘
       │
       │ Exchanges code for token (Backend API call)
       ↓

Step 3: Backend token exchange (OPTIMIZED)
┌──────────────────────────────────────────────────────────────┐
│ auth.py:                                                      │
│   WSO2_IS_INTERNAL_URL = "https://wso2is:9443"  ✅ FAST!    │
│   token_url = f"{WSO2_IS_INTERNAL_URL}/oauth2/token"        │
│   # Uses internal Docker network - no nginx overhead         │
└──────────────────────────────────────────────────────────────┘
       │
       │ Direct Docker network call (fast!)
       ↓
┌──────────────┐
│   WSO2 IS    │ Returns access token
└──────┬───────┘
       │
       │ Token returned to app
       ↓
┌──────────────┐
│  Darts App   │ Stores token in session
└──────┬───────┘
       │
       │ Redirects to home page
       ↓
┌──────────────┐
│   📱 Mobile  │
│   Browser    │  ✅ Successfully logged in!
└──────────────┘
```

---

## 🔄 Complete Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    COMPLETE OAUTH2 FLOW                                  │
└─────────────────────────────────────────────────────────────────────────┘

1. AUTHORIZATION REQUEST (Browser → WSO2 IS)
   ┌─────────────┐                                    ┌─────────────┐
   │   Browser   │──── Public URL ──────────────────→│   Nginx     │
   │  (Mobile)   │  https://letsplaydarts.eu/auth    │             │
   └─────────────┘                                    └──────┬──────┘
                                                             │
                                                             ↓
                                                      ┌─────────────┐
                                                      │  WSO2 IS    │
                                                      │  Container  │
                                                      └─────────────┘

2. USER AUTHENTICATION (Browser ↔ WSO2 IS)
   ┌─────────────┐                                    ┌─────────────┐
   │   Browser   │←──── Login Form ────────────────→│  WSO2 IS    │
   │  (Mobile)   │      Credentials                  │             │
   └─────────────┘                                    └─────────────┘

3. AUTHORIZATION CODE (WSO2 IS → Browser → App)
   ┌─────────────┐                                    ┌─────────────┐
   │  WSO2 IS    │──── Redirect with code ──────────→│   Browser   │
   └─────────────┘  /callback?code=ABC123            └──────┬──────┘
                                                             │
                                                             ↓
                                                      ┌─────────────┐
                                                      │  Darts App  │
                                                      └─────────────┘

4. TOKEN EXCHANGE (App → WSO2 IS, Backend)
   ┌─────────────┐                                    ┌─────────────┐
   │  Darts App  │──── Internal Network ────────────→│  WSO2 IS    │
   │             │  https://wso2is:9443/oauth2/token │  Container  │
   │             │←──── Access Token ────────────────│             │
   └─────────────┘                                    └─────────────┘
        │
        │ Store token in session
        ↓
   ┌─────────────┐
   │   Browser   │  ✅ Logged in!
   └─────────────┘
```

---

## 🏗️ Network Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         NETWORK TOPOLOGY                                 │
└─────────────────────────────────────────────────────────────────────────┘

                        INTERNET
                           │
                           │ HTTPS (443)
                           ↓
                    ┌──────────────┐
                    │   Firewall   │
                    └──────┬───────┘
                           │
                           ↓
                    ┌──────────────┐
                    │    Nginx     │  Port 443 (HTTPS)
                    │ Reverse Proxy│  Port 80 (HTTP → HTTPS redirect)
                    └──────┬───────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
            ↓              ↓              ↓
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │  Darts App   │ │ API Gateway  │ │   WSO2 IS    │
    │  Port 5000   │ │  Port 8080   │ │  Port 9443   │
    └──────┬───────┘ └──────────────┘ └──────┬───────┘
           │                                   │
           │  Internal Docker Network          │
           │  (Fast, Secure)                   │
           └───────────────────────────────────┘
                  Backend API Calls
              (Token, Userinfo, Introspect)

┌─────────────────────────────────────────────────────────────────────────┐
│ URL ROUTING                                                              │
├─────────────────────────────────────────────────────────────────────────┤
│ https://letsplaydarts.eu/          → darts-app:5000                    │
│ https://letsplaydarts.eu/api/v1/   → api-gateway:8080                  │
│ https://letsplaydarts.eu/auth/     → wso2is:9443                       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Security Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      SECURITY BOUNDARIES                                 │
└─────────────────────────────────────────────────────────────────────────┘

PUBLIC INTERNET (Untrusted)
│
│ ┌─────────────────────────────────────────────────────────────┐
│ │ TLS/SSL Encryption                                           │
│ └─────────────────────────────────────────────────────────────┘
│
↓
┌─────────────────────────────────────────────────────────────────┐
│                        FIREWALL                                  │
│  - Allows: 80, 443                                              │
│  - Blocks: All other ports                                      │
└─────────────────────────────────────────────────────────────────┘
│
↓
┌─────────────────────────────────────────────────────────────────┐
│                    NGINX REVERSE PROXY                           │
│  - SSL Termination                                              │
│  - Rate Limiting                                                │
│  - Security Headers                                             │
│  - Request Filtering                                            │
└─────────────────────────────────────────────────────────────────┘
│
↓
┌─────────────────────────────────────────────────────────────────┐
│              INTERNAL DOCKER NETWORK (Trusted)                   │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │  Darts App   │←──→│   WSO2 IS    │←──→│ API Gateway  │     │
│  │              │    │              │    │              │     │
│  │ No public    │    │ No public    │    │ No public    │     │
│  │ exposure     │    │ exposure     │    │ exposure     │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│                                                                  │
│  Benefits:                                                       │
│  ✅ Fast communication (no internet routing)                    │
│  ✅ Secure (not exposed to public)                              │
│  ✅ No SSL overhead for internal calls                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 URL Comparison Table

| Scenario             | Old URL (Broken)                           | New URL (Fixed)                                  | Accessible From  |
| -------------------- | ------------------------------------------ | ------------------------------------------------ | ---------------- |
| **Login Redirect**   | `https://localhost:9443/oauth2/authorize`  | `https://letsplaydarts.eu/auth/oauth2/authorize` | ✅ Anywhere      |
| **Logout Redirect**  | `https://localhost:9443/oidc/logout`       | `https://letsplaydarts.eu/auth/oidc/logout`      | ✅ Anywhere      |
| **Token Exchange**   | `https://localhost:9443/oauth2/token`      | `https://wso2is:9443/oauth2/token`               | 🔒 Internal only |
| **User Info**        | `https://localhost:9443/oauth2/userinfo`   | `https://wso2is:9443/oauth2/userinfo`            | 🔒 Internal only |
| **Token Introspect** | `https://localhost:9443/oauth2/introspect` | `https://wso2is:9443/oauth2/introspect`          | 🔒 Internal only |

---

## 🎯 Key Takeaways

### 1. **Browser Redirects = Public URL**

```python
# User's browser needs to access these
WSO2_IS_AUTHORIZE_URL = "https://letsplaydarts.eu/auth/oauth2/authorize"
WSO2_IS_LOGOUT_URL = "https://letsplaydarts.eu/auth/oidc/logout"
```

### 2. **Backend API Calls = Internal URL**

```python
# Server-to-server calls use internal network
WSO2_IS_TOKEN_URL = "https://wso2is:9443/oauth2/token"
WSO2_IS_USERINFO_URL = "https://wso2is:9443/oauth2/userinfo"
WSO2_IS_INTROSPECT_URL = "https://wso2is:9443/oauth2/introspect"
```

### 3. **Benefits of Dual-URL System**

- 🌍 **Remote Access**: Users can login from anywhere
- ⚡ **Performance**: Backend calls use fast internal network
- 🔒 **Security**: Internal APIs not exposed to public
- 🔄 **Flexibility**: Works with any deployment scenario

---

## 🧪 Testing Scenarios

### Test 1: Local Machine

```
User: localhost
URL: https://localhost:5000
Login: ✅ Works
Reason: Can access both localhost and public URLs
```

### Test 2: Remote Computer

```
User: Different computer on internet
URL: https://letsplaydarts.eu
Login: ✅ Works (FIXED!)
Reason: Uses public URL for redirects
```

### Test 3: Mobile Device

```
User: Smartphone on cellular network
URL: https://letsplaydarts.eu
Login: ✅ Works (FIXED!)
Reason: Uses public URL for redirects
```

### Test 4: Different Port

```
User: Any device
URL: https://letsplaydarts.eu:5000
Login: ✅ Works
Reason: Dynamic redirect URI adapts to port
```

---

## 📝 Configuration Examples

### Example 1: Production (Docker + Nginx)

```bash
# .env
WSO2_IS_URL=https://letsplaydarts.eu/auth
WSO2_IS_INTERNAL_URL=https://wso2is:9443
```

### Example 2: Development (Local)

```bash
# .env
WSO2_IS_URL=https://localhost:9443
# No WSO2_IS_INTERNAL_URL needed
```

### Example 3: Staging (Docker, No Nginx)

```bash
# .env
WSO2_IS_URL=https://staging.letsplaydarts.eu:9443
WSO2_IS_INTERNAL_URL=https://wso2is:9443
```

---

**Status:** ✅ **FIXED AND TESTED**  
**Impact:** 🟢 **HIGH** - Enables remote authentication  
**Complexity:** 🟡 **MEDIUM** - Dual-URL system  
**Risk:** 🟢 **LOW** - Backward compatible

---

_Remote login now works from any device, anywhere in the world! 🌍_
