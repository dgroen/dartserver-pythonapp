# Authentication Flow Diagram

This document provides visual representations of the authentication and authorization flows in the Darts Game System.

---

## OAuth2 Authorization Code Flow

```
┌─────────┐                                                          ┌──────────┐
│         │                                                          │          │
│  User   │                                                          │ WSO2 IS  │
│ Browser │                                                          │          │
└────┬────┘                                                          └────┬─────┘
     │                                                                    │
     │  1. Access Protected Page (e.g., http://localhost:5000/)          │
     │────────────────────────────────────────────────────────────►      │
     │                                                              │     │
     │  2. Redirect to /login (no session found)                   │     │
     │◄────────────────────────────────────────────────────────────│     │
     │                                                              │     │
     │  3. Click "Login with WSO2"                                 │     │
     │────────────────────────────────────────────────────────►    │     │
     │                                                              │     │
     │  4. Redirect to WSO2 Authorization Endpoint                 │     │
     │    with client_id, redirect_uri, state                      │     │
     │──────────────────────────────────────────────────────────────────►│
     │                                                                    │
     │  5. WSO2 Login Page                                               │
     │◄──────────────────────────────────────────────────────────────────│
     │                                                                    │
     │  6. User enters credentials (username/password)                   │
     │───────────────────────────────────────────────────────────────────►
     │                                                                    │
     │  7. WSO2 validates credentials and checks roles                   │
     │                                                                    │
     │  8. Redirect to callback with authorization code                  │
     │◄──────────────────────────────────────────────────────────────────│
     │                                                              │     │
     │  9. GET /callback?code=xxx&state=yyy                        │     │
     │────────────────────────────────────────────────────────►    │     │
     │                                                              │     │
     │                                                              │  10. Exchange code for tokens
     │                                                              │──────►
     │                                                              │     │
     │                                                              │  11. Return access_token, refresh_token, id_token
     │                                                              │◄─────│
     │                                                              │     │
     │                                                              │  12. Validate token (introspection or JWKS)
     │                                                              │──────►
     │                                                              │     │
     │                                                              │  13. Return token info with roles
     │                                                              │◄─────│
     │                                                              │     │
     │  14. Create session with user info and roles                │     │
     │      Store: access_token, refresh_token, user_claims        │     │
     │                                                              │     │
     │  15. Redirect to original page (/)                          │     │
     │◄────────────────────────────────────────────────────────────│     │
     │                                                              │     │
     │  16. Access granted - render page with user info            │     │
     │◄────────────────────────────────────────────────────────────│     │
     │                                                                    │
```

---

## Role-Based Access Control Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     User Makes Request                          │
│                  (e.g., GET /control)                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ @login_required│
                    │   Decorator    │
                    └────────┬───────┘
                             │
                    ┌────────▼────────┐
                    │ Session exists? │
                    └────────┬────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
               NO                        YES
                │                         │
                ▼                         ▼
        ┌───────────────┐        ┌───────────────┐
        │ Redirect to   │        │ Extract user  │
        │    /login     │        │  from session │
        └───────────────┘        └───────┬───────┘
                                         │
                                         ▼
                                ┌────────────────┐
                                │ @role_required │
                                │   Decorator    │
                                └────────┬───────┘
                                         │
                                ┌────────▼────────┐
                                │ User has role?  │
                                │ (gamemaster or  │
                                │     admin)      │
                                └────────┬────────┘
                                         │
                            ┌────────────┴────────────┐
                            │                         │
                           NO                        YES
                            │                         │
                            ▼                         ▼
                    ┌───────────────┐        ┌───────────────┐
                    │  Return 403   │        │ Check         │
                    │  Forbidden    │        │ permissions   │
                    └───────────────┘        └───────┬───────┘
                                                     │
                                            ┌────────▼────────┐
                                            │@permission_     │
                                            │  required       │
                                            │  Decorator      │
                                            └────────┬────────┘
                                                     │
                                            ┌────────▼────────┐
                                            │ User has        │
                                            │ permission?     │
                                            │ (e.g.,          │
                                            │ game:create)    │
                                            └────────┬────────┘
                                                     │
                                        ┌────────────┴────────────┐
                                        │                         │
                                       NO                        YES
                                        │                         │
                                        ▼                         ▼
                                ┌───────────────┐        ┌───────────────┐
                                │  Return 403   │        │ Execute route │
                                │  Forbidden    │        │   function    │
                                └───────────────┘        └───────────────┘
```

---

## Permission Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                         ADMIN ROLE                              │
│                      Permission: "*"                            │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              ✓ All Permissions                            │ │
│  │              ✓ Full System Access                         │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │ Includes all permissions from:
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      GAMEMASTER ROLE                            │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  ✓ game:view      - View game board                      │ │
│  │  ✓ game:state     - View game state                      │ │
│  │  ✓ score:submit   - Submit scores                        │ │
│  │  ✓ game:create    - Create new games                     │ │
│  │  ✓ game:control   - Access control panel                 │ │
│  │  ✓ player:add     - Add players to game                  │ │
│  │  ✓ player:remove  - Remove players from game             │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │ Includes all permissions from:
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        PLAYER ROLE                              │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  ✓ game:view      - View game board                      │ │
│  │  ✓ game:state     - View game state                      │ │
│  │  ✓ score:submit   - Submit scores                        │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Route Protection Matrix

| Route                     | Decorator                                                    | Required Role     | Required Permission | Access                             |
| ------------------------- | ------------------------------------------------------------ | ----------------- | ------------------- | ---------------------------------- |
| `/`                       | `@login_required`                                            | Any               | `game:view`         | 🟢 Player, 🟡 GameMaster, 🔴 Admin |
| `/control`                | `@login_required`<br>`@role_required("admin", "gamemaster")` | admin, gamemaster | `game:control`      | 🟡 GameMaster, 🔴 Admin            |
| `/login`                  | None                                                         | None              | None                | 🌐 Public                          |
| `/callback`               | None                                                         | None              | None                | 🌐 Public                          |
| `/logout`                 | `@login_required`                                            | Any               | None                | 🟢 Player, 🟡 GameMaster, 🔴 Admin |
| `/profile`                | `@login_required`                                            | Any               | None                | 🟢 Player, 🟡 GameMaster, 🔴 Admin |
| `GET /api/game`           | `@login_required`<br>`@permission_required("game:view")`     | Any               | `game:view`         | 🟢 Player, 🟡 GameMaster, 🔴 Admin |
| `POST /api/game`          | `@login_required`<br>`@permission_required("game:create")`   | gamemaster, admin | `game:create`       | 🟡 GameMaster, 🔴 Admin            |
| `POST /api/player`        | `@login_required`<br>`@permission_required("player:add")`    | gamemaster, admin | `player:add`        | 🟡 GameMaster, 🔴 Admin            |
| `DELETE /api/player/<id>` | `@login_required`<br>`@permission_required("player:remove")` | gamemaster, admin | `player:remove`     | 🟡 GameMaster, 🔴 Admin            |
| `POST /api/score`         | `@login_required`<br>`@permission_required("score:submit")`  | Any               | `score:submit`      | 🟢 Player, 🟡 GameMaster, 🔴 Admin |

Legend:

- 🌐 Public - No authentication required
- 🟢 Player - Basic role
- 🟡 GameMaster - Intermediate role
- 🔴 Admin - Full access role

---

## Token Validation Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Incoming Request with Token                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ Extract token  │
                    │ from session   │
                    └────────┬───────┘
                             │
                    ┌────────▼────────┐
                    │ Token exists?   │
                    └────────┬────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
               NO                        YES
                │                         │
                ▼                         ▼
        ┌───────────────┐        ┌───────────────┐
        │ Return 401    │        │ Check         │
        │ Unauthorized  │        │ JWT_VALIDATION│
        └───────────────┘        │ _MODE         │
                                 └───────┬───────┘
                                         │
                            ┌────────────┴────────────┐
                            │                         │
                       introspection                 jwks
                            │                         │
                            ▼                         ▼
                    ┌───────────────┐        ┌───────────────┐
                    │ Call WSO2     │        │ Download JWKS │
                    │ introspection │        │ from WSO2     │
                    │ endpoint      │        └───────┬───────┘
                    └───────┬───────┘                │
                            │                        │
                            │                        ▼
                            │                ┌───────────────┐
                            │                │ Verify JWT    │
                            │                │ signature     │
                            │                └───────┬───────┘
                            │                        │
                            └────────────┬───────────┘
                                         │
                                         ▼
                                ┌────────────────┐
                                │ Token valid?   │
                                └────────┬───────┘
                                         │
                            ┌────────────┴────────────┐
                            │                         │
                           NO                        YES
                            │                         │
                            ▼                         ▼
                    ┌───────────────┐        ┌───────────────┐
                    │ Return 401    │        │ Extract claims│
                    │ Unauthorized  │        │ (username,    │
                    └───────────────┘        │  roles, etc.) │
                                             └───────┬───────┘
                                                     │
                                                     ▼
                                             ┌───────────────┐
                                             │ Normalize     │
                                             │ roles         │
                                             │ (remove       │
                                             │  Internal/)   │
                                             └───────┬───────┘
                                                     │
                                                     ▼
                                             ┌───────────────┐
                                             │ Store in      │
                                             │ request       │
                                             │ context       │
                                             └───────┬───────┘
                                                     │
                                                     ▼
                                             ┌───────────────┐
                                             │ Proceed to    │
                                             │ route handler │
                                             └───────────────┘
```

---

## Session Lifecycle

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Login                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ OAuth2 flow    │
                    │ completes      │
                    └────────┬───────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ Create session │
                    │ Store:         │
                    │ - access_token │
                    │ - refresh_token│
                    │ - user_claims  │
                    │ - roles        │
                    └────────┬───────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ Set session    │
                    │ cookie         │
                    │ (HttpOnly,     │
                    │  SameSite)     │
                    └────────┬───────┘
                             │
                             ▼
        ┌────────────────────────────────────────┐
        │         User Makes Requests            │
        │    (Session cookie sent with each)     │
        └────────────────┬───────────────────────┘
                         │
                         ▼
                ┌────────────────┐
                │ Validate       │
                │ session        │
                └────────┬───────┘
                         │
            ┌────────────┴────────────┐
            │                         │
        Valid                     Expired
            │                         │
            ▼                         ▼
    ┌───────────────┐        ┌───────────────┐
    │ Continue      │        │ Try refresh   │
    │ processing    │        │ token         │
    └───────────────┘        └───────┬───────┘
                                     │
                        ┌────────────┴────────────┐
                        │                         │
                    Success                    Failure
                        │                         │
                        ▼                         ▼
                ┌───────────────┐        ┌───────────────┐
                │ Update session│        │ Clear session │
                │ with new token│        │ Redirect to   │
                └───────────────┘        │ /login        │
                                         └───────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ User clicks    │
                    │ Logout         │
                    └────────┬───────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ Clear session  │
                    │ Delete cookie  │
                    └────────┬───────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ Redirect to    │
                    │ /login         │
                    └────────────────┘
```

---

## Component Interaction

```
┌──────────────────────────────────────────────────────────────────────┐
│                           User Browser                               │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             │ HTTP/HTTPS
                             │
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                         Darts Application                            │
│                           (Flask App)                                │
│                                                                      │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐       │
│  │   app.py       │  │   auth.py      │  │  Templates     │       │
│  │                │  │                │  │                │       │
│  │ - Routes       │◄─┤ - OAuth2 flow │  │ - login.html   │       │
│  │ - Decorators   │  │ - Token valid. │  │ - index.html   │       │
│  │ - Session mgmt │  │ - Role extract │  │ - control.html │       │
│  └────────┬───────┘  └────────┬───────┘  └────────────────┘       │
│           │                   │                                     │
│           │                   │                                     │
└───────────┼───────────────────┼─────────────────────────────────────┘
            │                   │
            │                   │ OAuth2/Token API
            │                   │
            │                   ▼
            │          ┌────────────────────────────────┐
            │          │      WSO2 Identity Server      │
            │          │                                │
            │          │  - Authentication              │
            │          │  - Authorization               │
            │          │  - Token issuance              │
            │          │  - Token validation            │
            │          │  - User/Role management        │
            │          └────────────────────────────────┘
            │
            │ WebSocket/AMQP
            │
            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                          RabbitMQ Broker                             │
│                                                                      │
│  - Message routing                                                   │
│  - Score distribution                                                │
│  - Real-time updates                                                 │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Security Layers

```
┌─────────────────────────────────────────────────────────────────┐
│                      Layer 1: Network                           │
│                                                                 │
│  - HTTPS (production)                                           │
│  - Firewall rules                                               │
│  - Network isolation                                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Layer 2: Authentication                       │
│                                                                 │
│  - OAuth2 Authorization Code Flow                              │
│  - WSO2 Identity Server                                        │
│  - Secure token exchange                                       │
│  - CSRF protection (state parameter)                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Layer 3: Token Validation                    │
│                                                                 │
│  - JWT signature verification (JWKS)                           │
│  - Token introspection                                         │
│  - Expiration checking                                         │
│  - Issuer validation                                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Layer 4: Authorization                       │
│                                                                 │
│  - Role-based access control                                   │
│  - Permission checking                                         │
│  - Route protection decorators                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Layer 5: Session Security                   │
│                                                                 │
│  - HttpOnly cookies                                            │
│  - SameSite protection                                         │
│  - Secure flag (production)                                    │
│  - Session expiration                                          │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Layer 6: Application Logic                    │
│                                                                 │
│  - Input validation                                            │
│  - Error handling                                              │
│  - Audit logging                                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Error Handling Flow

```
                    ┌────────────────┐
                    │ Request arrives│
                    └────────┬───────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ Try to         │
                    │ authenticate   │
                    └────────┬───────┘
                             │
                    ┌────────▼────────┐
                    │ Error occurred? │
                    └────────┬────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
               NO                        YES
                │                         │
                ▼                         ▼
        ┌───────────────┐        ┌───────────────┐
        │ Continue      │        │ What type?    │
        │ processing    │        └───────┬───────┘
        └───────────────┘                │
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
            ┌───────────────┐    ┌───────────────┐   ┌───────────────┐
            │ No session    │    │ Invalid token │   │ Insufficient  │
            │               │    │               │   │ permissions   │
            └───────┬───────┘    └───────┬───────┘   └───────┬───────┘
                    │                    │                    │
                    ▼                    ▼                    ▼
            ┌───────────────┐    ┌───────────────┐   ┌───────────────┐
            │ Redirect to   │    │ Clear session │   │ Return 403    │
            │ /login        │    │ Redirect to   │   │ Forbidden     │
            │               │    │ /login        │   │               │
            └───────────────┘    └───────────────┘   └───────────────┘
```

---

This diagram provides a comprehensive visual guide to understanding how authentication and authorization work in the Darts Game System.
