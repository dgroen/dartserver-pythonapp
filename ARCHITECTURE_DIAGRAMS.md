# Architecture Flow Diagrams & Verification Maps

## 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DARTS GAME SYSTEM v2.0                          │
│                   With WSO2 APIM Integration                            │
└─────────────────────────────────────────────────────────────────────────┘

CLIENTS LAYER:
┌──────────────┬──────────────┬──────────────────┐
│  Dartboards  │ Web Browser  │  Mobile Clients  │
│   (OAuth2)   │  (Session)   │   (Bearer Token) │
└──────┬───────┴──────┬───────┴────────┬─────────┘
       │              │                │
       │   All via HTTPS (TLS 1.3)    │
       ▼              ▼                ▼
    ┌────────────────────────────────────────┐
    │  NGINX REVERSE PROXY (Port 443)         │
    │  ├─ Terminates TLS                      │
    │  ├─ Routes /api/v1/* → APIM:8243       │
    │  ├─ Routes / → Flask:5000              │
    │  └─ Redirects HTTP → HTTPS             │
    └────────┬───────────────────────────────┘
             │ /api/v1 (OAuth2 token required)
             ▼
    ┌────────────────────────────────────────┐
    │  WSO2 APIM GATEWAY (Port 8243)          │
    │  ├─ Validates OAuth2 token              │
    │  ├─ Enforces scopes                     │
    │  ├─ Rate limiting:                      │
    │  │  ├─ Dartboard: 1000 req/min         │
    │  │  ├─ Game Control: 100 req/min       │
    │  │  └─ Health: Unlimited                │
    │  └─ Forwards to API Gateway             │
    └────────┬───────────────────────────────┘
             │ Request with validated token
             ▼
    ┌────────────────────────────────────────┐
    │  API GATEWAY (Port 8080)                │
    │  ├─ Parse request                       │
    │  ├─ Validate JWT token (JWKS/introspect)
    │  ├─ Publish to RabbitMQ                 │
    │  └─ Return HTTP response                │
    └────┬────────────┬──────────────┬───────┘
         │            │              │
         │ Message    │ Validate     │ Error
         │            │              │
         ▼            ▼              ▼
    ┌─────────┐ ┌──────────┐ ┌────────────┐
    │RabbitMQ │ │ WSO2 IS  │ │ HTTP Error │
    │         │ │          │ │  401/429   │
    │ darts_  │ │ /oauth2/ │ │  Response  │
    │exchange │ │  jwks    │ │            │
    │         │ │ /introspect
    │Topic:   │ │          │ └────────────┘
    │darts.   │ │ Port     │
    │scores.* │ │ 9443     │
    └────┬────┘ └──────────┘
         │
         │ Score event message
         │ (darts.scores.submit)
         ▼
    ┌────────────────────────────────────────┐
    │  FLASK APP (Port 5000)                  │
    │  Consumer Thread:                       │
    │  ├─ Receive message from RabbitMQ       │
    │  ├─ Parse game_id, player_id, score    │
    │  ├─ Execute game logic                  │
    │  │  ├─ 301 variant                      │
    │  │  ├─ Cricket variant                  │
    │  │  └─ Win conditions                   │
    │  └─ Persist to PostgreSQL               │
    │                                         │
    │  WebSocket Server:                      │
    │  ├─ Broadcast game state updates        │
    │  ├─ Real-time board updates             │
    │  └─ Player score notifications          │
    └────┬──────────────────────────────┬────┘
         │                              │
         │ Game state update            │ SQL Insert
         │                              │
         ▼                              ▼
    ┌──────────────┐          ┌────────────────────┐
    │ Browser Tab  │          │  PostgreSQL (DB)   │
    │              │          │                    │
    │ WebSocket    │          │ Tables:            │
    │ Connected    │          │ ├─ games           │
    │              │          │ ├─ players         │
    │ Display Game │          │ ├─ scores          │
    │ Board        │          │ ├─ sessions        │
    │              │          │ └─ game_states     │
    │ Real-time    │          │                    │
    │ Updates      │          │ Port: 5432         │
    │              │          │ DB: darts_game     │
    └──────────────┘          └────────────────────┘
```

---

## 2. Request Flow: Dartboard → PostgreSQL

```
TIME: t=0ms
┌─────────────┐
│   DARTBOARD │  POST https://dartboard.local:443/api/v1/dartboard/throw
│  (OAuth2)   │  Headers:
└──────┬──────┘    Authorization: Bearer eyJhbGc...
       │           Content-Type: application/json
       │  Body:
       │  {
       │    "game_id": "game-123",
       │    "player_id": "alice",
       │    "pins": [20, 1]
       │  }
       │
       ▼ ──────────────────────────────────────────────
TIME: t=5ms
┌─────────────────────────────────────────────────────────┐
│ NGINX:443                                               │
│ ├─ Verify SSL/TLS (self-signed)                         │
│ ├─ Add headers: X-Real-IP, X-Forwarded-For             │
│ ├─ Route: /api/v1/* → https://wso2apim:8243/api        │
│ └─ Forward request with token intact                    │
└──────┬──────────────────────────────────────────────────┘
       │ HTTPS Forward
       │ (proxied)
       ▼ ──────────────────────────────────────────────
TIME: t=10ms
┌──────────────────────────────────────────────────────────┐
│ WSO2 APIM:8243                                           │
│ ├─ Extract token from Authorization header              │
│ ├─ Lookup DartsGameAPI definition                       │
│ ├─ Find endpoint: /api/v1/dartboard/throw               │
│ ├─ Check scope: "dartboard:write" ✓                     │
│ ├─ Check rate limit: 1000/min                           │
│ │  ├─ Client: DARTBOARD_001                             │
│ │  ├─ Current rate: 42 req/min                          │
│ │  └─ Status: ALLOW ✓                                   │
│ ├─ Forward to API Gateway:8080                          │
│ └─ Keep token in Authorization header                   │
└──────┬───────────────────────────────────────────────────┘
       │ HTTP Request (internal Docker network)
       │ Token validated ✓
       ▼ ──────────────────────────────────────────────
TIME: t=20ms
┌─────────────────────────────────────────────────────────┐
│ API GATEWAY:8080                                        │
│ ├─ Receive request from APIM                           │
│ ├─ Extract token from header                           │
│ ├─ Validate token signature (JWKS)                     │
│ │  ├─ Fetch from https://wso2is:9443/oauth2/jwks      │
│ │  ├─ Verify RSA signature ✓                           │
│ │  ├─ Check exp claim: valid ✓                         │
│ │  └─ Extract subject: DARTBOARD_001 ✓                 │
│ ├─ Parse JSON body                                      │
│ │  ├─ game_id = "game-123" ✓                           │
│ │  ├─ player_id = "alice" ✓                            │
│ │  └─ pins = [20, 1] ✓                                 │
│ ├─ Publish to RabbitMQ                                  │
│ │  ├─ Connection: pika → rabbitmq:5672                │
│ │  ├─ Exchange: darts_exchange                         │
│ │  ├─ Routing Key: darts.scores.submit                 │
│ │  └─ Message: {"type": "score", ...} ✓               │
│ └─ Return HTTP 200 with status                          │
└──────┬──────────────┬──────────────────────────────────┘
       │              │
       │ HTTP 200     │ Message published
       │ Response     │ to RabbitMQ
       ▼              ▼ ──────────────────────────────────
TIME: t=25ms
    │            ┌──────────────────────────────────────┐
    │            │ RabbitMQ:5672                        │
    │            │ ├─ Receive message                   │
    │            │ ├─ Route: darts.scores.submit       │
    │            │ ├─ Queue: darts_score_queue         │
    │            │ └─ Persisted to disk ✓              │
    │            └──────────────────────────────────────┘
    │
    ▼ ──────────────────────────────────────────────
TIME: t=30ms (return to dartboard)
┌──────────────────────────────────────────────────┐
│ DARTBOARD                                        │
│                                                  │
│ Response: HTTP 200 OK                            │
│ {                                                │
│   "status": "success",                           │
│   "message": "Throw submitted to RabbitMQ",      │
│   "game_id": "game-123"                          │
│ }                                                │
│                                                  │
│ ✓ Request completed in ~30ms                     │
└──────────────────────────────────────────────────┘

---

TIME: t=100ms
┌──────────────────────────────────────────────────────────┐
│ FLASK APP - RabbitMQ Consumer Thread                     │
│ ├─ Poll RabbitMQ for messages                           │
│ ├─ Receive: darts.scores.submit                         │
│ ├─ Decode message body                                  │
│ ├─ Extract: game_id="game-123", player_id="alice",      │
│ │           pins=[20, 1]                                 │
│ ├─ Calculate score: 20 + 1 = 21 points                 │
│ ├─ Load game from PostgreSQL                            │
│ │  └─ SELECT * FROM games WHERE id='game-123'          │
│ ├─ Update game state (301 logic)                        │
│ │  └─ Current: 301 points → 301 - 21 = 280 points      │
│ ├─ Save score record                                    │
│ │  └─ INSERT INTO scores (game_id, player_id, ...)     │
│ ├─ Update game state                                    │
│ │  └─ UPDATE games SET current_player_score=280 ...    │
│ ├─ Emit WebSocket event: "score_updated"               │
│ │  └─ Broadcast to all connected clients               │
│ └─ ACK message to RabbitMQ ✓                            │
└──────┬───────────────────────────────────────────────────┘
       │
       │ ACK to RabbitMQ
       │ (message consumed)
       ▼ ──────────────────────────────────────────────
TIME: t=110ms
    ┌──────────────────────────────────────────────────────┐
    │ PostgreSQL                                           │
    │                                                      │
    │ ✓ INSERT: scores record                              │
    │   game_id='game-123'                                 │
    │   player_id='alice'                                  │
    │   score=21                                           │
    │   created_at='2025-01-05T12:00:00.100Z'              │
    │                                                      │
    │ ✓ UPDATE: games record                               │
    │   id='game-123'                                      │
    │   alice_score=280                                    │
    │   last_throw=[20,1]                                  │
    │   updated_at='2025-01-05T12:00:00.110Z'              │
    │                                                      │
    │ ✓ Data persisted (ACID compliance)                   │
    └──────────┬────────────────────────────────────────────┘
               │
               ▼ ──────────────────────────────────────────────
TIME: t=120ms
    ┌────────────────────────────────────────────────────┐
    │ BROWSER (connected via WebSocket)                  │
    │                                                    │
    │ Receive WebSocket message:                         │
    │ {                                                  │
    │   "type": "score_updated",                         │
    │   "game_id": "game-123",                           │
    │   "player": "alice",                               │
    │   "score": 21,                                     │
    │   "remaining": 280,                                │
    │   "last_throw": [20, 1]                            │
    │ }                                                  │
    │                                                    │
    │ ✓ Update game board display                        │
    │ ✓ Show alice's remaining: 280 points               │
    │ ✓ Show throw: 20 + 1                               │
    │ ✓ Play notification sound (optional)               │
    └────────────────────────────────────────────────────┘
```

---

## 3. Authentication & Authorization Flow

```
┌───────────────────────────────────────────────────────────┐
│  OAUTH2 CLIENT CREDENTIALS FLOW (For Dartboards)           │
└───────────────────────────────────────────────────────────┘

TIME: t=0
┌──────────────────┐
│    DARTBOARD     │  
│                  │  
│  Has credentials:│  
│  client_id: "..  │  
│  client_secret:"│  
└────────┬─────────┘
         │ POST /oauth2/token
         │ Authorization: Basic <b64(id:secret)>
         │ grant_type=client_credentials&scope=dartboard:write
         │
         ▼
       HTTPS ────────────────────────────────────────
         │
         ▼
┌──────────────────────────────────────────────────┐
│  WSO2 IS (Port 9443)                             │
│  POST /oauth2/token                              │
│                                                  │
│  ✓ Verify client_id exists                      │
│  ✓ Verify client_secret matches                 │
│  ✓ Check grant_type is allowed                  │
│  ✓ Verify scope is authorized                   │
│  ✓ Generate JWT token                           │
│    ├─ Header: {alg: "RS256", typ: "JWT"}        │
│    ├─ Payload:                                   │
│    │  {                                          │
│    │    sub: "DARTBOARD_001",                   │
│    │    scope: "dartboard:write",               │
│    │    iat: 1704450000,                        │
│    │    exp: 1704453600,                        │
│    │    iss: "https://wso2is:9443"              │
│    │  }                                          │
│    └─ Signature: RSA-SHA256(header.payload)     │
│                                                  │
│  ✓ Return response:                              │
│    {                                             │
│      "access_token": "eyJhbGc...SIGNATURE",     │
│      "token_type": "Bearer",                    │
│      "expires_in": 3600                         │
│    }                                             │
└────────┬──────────────────────────────────────────┘
         │ JWT Token
         │ (signed with WSO2 IS private key)
         ▼
TIME: t=100ms
┌──────────────────┐
│    DARTBOARD     │  Now has:
│                  │  Token: eyJhbGc...
│  access_token:   │  Valid for 1 hour
│  eyJhbGc...      │  
└────────┬─────────┘
         │ 
         │ Include in requests:
         │ Authorization: Bearer eyJhbGc...
         │
         ▼
       HTTPS ────────────────────────────────────────
         │
         ▼
┌──────────────────────────────────────────────────┐
│  NGINX:443                                       │
│  ├─ Accept request with Bearer token             │
│  └─ Forward to APIM with token intact            │
└────────┬──────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────┐
│  WSO2 APIM:8243                                  │
│  ├─ Extract token from Authorization header     │
│  ├─ Validate token:                              │
│  │  ├─ Check signature (RSA public key)          │
│  │  ├─ Verify issuer: https://wso2is:9443       │
│  │  ├─ Check not expired (exp > now)             │
│  │  ├─ Extract scope: "dartboard:write"          │
│  │  └─ Status: ✓ VALID                           │
│  ├─ Match scope to endpoint:                     │
│  │  ├─ Endpoint: /api/v1/dartboard/throw         │
│  │  ├─ Required scope: "dartboard:write"         │
│  │  └─ Match: ✓ OK                               │
│  ├─ Check rate limit:                            │
│  │  ├─ Policy: DartboardThrottle (1000/min)     │
│  │  ├─ Current rate: 42 req/min                  │
│  │  └─ Status: ✓ WITHIN LIMIT                    │
│  └─ Allow request → API Gateway:8080             │
└────────┬──────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────┐
│  API GATEWAY:8080                                │
│  ├─ Receive request (APIM validated)             │
│  ├─ Extract token again for verification         │
│  ├─ Fetch JWKS keys:                             │
│  │  └─ GET https://wso2is:9443/oauth2/jwks      │
│  ├─ Verify signature using public key            │
│  ├─ Validate token:                              │
│  │  ├─ sub: "DARTBOARD_001" ✓                   │
│  │  ├─ scope: "dartboard:write" ✓               │
│  │  ├─ exp: > now ✓                              │
│  │  └─ iss: https://wso2is:9443 ✓               │
│  ├─ Extract subject for logging/audit            │
│  ├─ Process request (all validations passed)     │
│  └─ Return HTTP 200 OK                           │
└──────────────────────────────────────────────────┘
```

---

## 4. Rate Limiting Flow

```
┌────────────────────────────────────────────────────┐
│  RATE LIMITING AT WSO2 APIM                        │
└────────────────────────────────────────────────────┘

Dartboard: DARTBOARD_001
Request Rate: 1 request per second
Policy Limit: 1000 requests per minute

Timeline (60 seconds):

Second 1-10:   Requests 1-10  (rate: 10/min)    ✓ ALLOW
Second 11-20:  Requests 11-20 (rate: 20/min)    ✓ ALLOW
Second 21-30:  Requests 21-30 (rate: 30/min)    ✓ ALLOW
...
Second 51-60:  Requests 1001-1010 (exceeds 1000/min limit)
               ├─ Request 1001-1000: ✓ ALLOW (within limit)
               ├─ Request 1001:      ✗ REJECT - 429 Too Many Requests
               ├─ Request 1002:      ✗ REJECT - 429 Too Many Requests
               └─ Request 1010:      ✗ REJECT - 429 Too Many Requests

At Second 61 (1 minute window complete):
  Counter resets to 0
  ├─ Request 1011: ✓ ALLOW (new window)
  ├─ Request 1012: ✓ ALLOW
  └─ ...

Response for Rate-Limited Request:
┌─────────────────────────────────────┐
│ HTTP/1.1 429 Too Many Requests       │
│ Content-Type: application/json       │
│                                      │
│ {                                    │
│   "error": "rate_limit_exceeded",    │
│   "message": "You have exceeded...", │
│   "retry_after": 60                  │
│ }                                    │
└─────────────────────────────────────┘
```

---

## 5. Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────┐
│          COMPONENT DEPENDENCIES & DATA FLOW                 │
└─────────────────────────────────────────────────────────────┘

┌──────────────────┐
│  POSTGRESQL 5432 │  ◄─────────────────┐
└──────────────────┘                     │
         ▲                          ┌─────┴──────────┐
         │                          │                │
         │ SQL Read/Write           │                │
         │ game_id, player_id       │                │
         │ score, game_state        │                │
         │                          │                │
┌────────┴──────────────┐    ┌──────┴──────┐
│  FLASK APP:5000       │    │  RabbitMQ   │
│  ├─ Game Logic        │    │  :5672      │
│  ├─ WebSocket Server  │    │             │
│  ├─ RabbitMQ Consumer │◄───┤  Topic:    │
│  └─ Session Manager   │    │  darts.    │
│                       │    │  scores.*  │
└────────┬──────────────┘    │             │
         ▲                    │ Message    │
         │                    │ (game_id,  │
         │ WebSocket          │ score)     │
         │ Update             └─────▲──────┘
         │                          │
┌────────┴───────────────┐          │
│  BROWSER (HTML/JS)     │          │ Publish
└────────────────────────┘          │
         ▲                          │
         │ GET / (game board)      │
         │                         │
┌────────┴──────────────────────┐  │
│  NGINX:443                     │  │
│  ├─ TLS Termination            │  │
│  ├─ Route / → Flask:5000       │  │
│  ├─ Route /api/v1 → APIM:8243 ├──┘
│  └─ Rate limiting (old)        │   (request)
└────────┬──────────────────────┘
         ▲
         │ HTTPS
         │
┌────────┴────────────────────┐
│  DARTBOARD HARDWARE          │
│  ├─ OAuth2 Credentials       │
│  ├─ Bearer Token             │
│  └─ Request: POST /api/v1/   │
│     dartboard/throw          │
└─────────────────────────────┘
         ▲
         │ HTTPS + Token
         │
    ┌────┴──────────────────────┐
    │  WSO2 APIM:8243            │
    │  ├─ Token Validation       │
    │  ├─ Rate Limiting          │
    │  │  ├─ DartboardThrottle   │
    │  │  └─ GameControlThrottle │
    │  ├─ Scope Enforcement      │
    │  └─ Request Forwarding     │
    └────┬──────────────────────┘
         │
         ▼ Validated request
    ┌────────────────────────────────┐
    │  API GATEWAY:8080              │
    │  ├─ Token Validation (JWKS)    │
    │  ├─ Request Parsing            │
    │  ├─ RabbitMQ Publisher         │
    │  └─ Response Generation        │
    └────┬───────────────────────────┘
         │
         │ Connects to WSO2 IS for JWKS
         │
    ┌────▼───────────────────────────┐
    │  WSO2 IS:9443                  │
    │  ├─ /oauth2/token (token gen)  │
    │  ├─ /oauth2/jwks (pub keys)   │
    │  ├─ /oauth2/introspect (valid) │
    │  └─ /oauth2/userinfo (claims)  │
    └────────────────────────────────┘
```

---

## 6. Verification Test Coverage Map

```
┌────────────────────────────────────────────────────────┐
│         AUTOMATED TEST COVERAGE                        │
│     (helpers/test_wso2_apim_integration.py)           │
└────────────────────────────────────────────────────────┘

Phase 1: OAUTH2 TOKEN ACQUISITION
├─ Endpoint: https://localhost:9443/oauth2/token
├─ Method: POST
├─ Auth: Basic(client_id:client_secret)
├─ Payload: grant_type=client_credentials
└─ Expected: ✓ access_token in response
   └─ Test Result: [Test: test_get_access_token()] ✓

Phase 2: API GATEWAY - HEALTH CHECK
├─ Endpoint: https://localhost:8243/health
├─ Method: GET
├─ Auth: None (public endpoint)
└─ Expected: ✓ {"status": "healthy"}
   └─ Test Result: [Test: test_health_endpoint()] ✓

Phase 3: API GATEWAY - DARTBOARD THROW
├─ Endpoint: https://localhost:8243/api/v1/dartboard/throw
├─ Method: POST
├─ Auth: Bearer Token
├─ Payload: {"game_id", "player_id", "pins"}
└─ Expected: ✓ {"status": "success"}
   └─ Test Result: [Test: test_dartboard_throw()] ✓

Phase 4: RATE LIMITING
├─ Endpoint: https://localhost:8243/api/v1/dartboard/throw
├─ Method: POST (x1005)
├─ Auth: Bearer Token
├─ Policy: 1000 requests/minute
└─ Expected:
   ├─ Requests 1-1000: ✓ HTTP 200
   └─ Requests 1001+:  ✓ HTTP 429
   └─ Test Result: [Test: test_rate_limiting()] ✓

Phase 5: UNAUTHORIZED ACCESS
├─ Endpoint: https://localhost:8243/api/v1/dartboard/throw
├─ Method: POST
├─ Auth: None or Invalid Token
└─ Expected: ✓ HTTP 401 Unauthorized
   └─ Test Result: [Test: test_unauthorized_access()] ✓

Phase 6: SCOPE VALIDATION
├─ Endpoint: https://localhost:8223/api/v1/game/actions/start
├─ Method: POST
├─ Auth: Token without required scope
├─ Required Scope: "game:control"
└─ Expected: ✓ HTTP 403 Forbidden
   └─ Test Result: [Test: test_scope_validation()] ✓

OVERALL TEST RESULT:
═══════════════════════════════════════════════════════
  ✓ Service connectivity verified
  ✓ OAuth2 flow validated
  ✓ Token validation working
  ✓ APIM rate limiting active
  ✓ Unauthorized access blocked
  ✓ All 6 phases passed
═══════════════════════════════════════════════════════
```

---

## 7. Error Response Flows

```
┌──────────────────────────────────────────────────────────┐
│         ERROR HANDLING & RESPONSE CODES                  │
└──────────────────────────────────────────────────────────┘

SCENARIO 1: Missing OAuth2 Token
┌──────────────┐
│  Client      │  GET /api/v1/dartboard/throw
│              │  (No Authorization header)
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  APIM:8243                               │
│  ├─ Check: Authorization header missing  │
│  └─ Action: Reject request               │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  Response: HTTP 401 Unauthorized         │
│  {                                       │
│    "error": "invalid_request",           │
│    "error_description":                  │
│      "Missing authorization header"      │
│  }                                       │
└──────────────────────────────────────────┘

---

SCENARIO 2: Invalid Token Signature
┌──────────────┐
│  Client      │  GET /api/v1/dartboard/throw
│              │  Authorization: Bearer forged_token
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  APIM:8243                               │
│  ├─ Extract token from header            │
│  ├─ Verify signature with JWKS           │
│  ├─ Signature check: ✗ FAILED            │
│  └─ Action: Reject request               │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  Response: HTTP 401 Unauthorized         │
│  {                                       │
│    "error": "invalid_token",             │
│    "error_description":                  │
│      "Invalid signature"                 │
│  }                                       │
└──────────────────────────────────────────┘

---

SCENARIO 3: Rate Limit Exceeded
┌──────────────────┐
│  Client          │  (1001st request in 60 seconds)
│  Rate: 1 req/s   │  Authorization: Bearer valid_token
└──────┬───────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  APIM:8243                               │
│  ├─ Token validation: ✓ PASSED           │
│  ├─ Check rate limit:                    │
│  │  ├─ Policy: 1000 req/min               │
│  │  ├─ Current: 1001 req/min              │
│  │  ├─ Status: ✗ EXCEEDED                 │
│  │  └─ Action: Reject request             │
│  └─ Return 429 response                  │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  Response: HTTP 429 Too Many Requests    │
│  {                                       │
│    "error": "rate_limit_exceeded",       │
│    "message": "Rate limit exceeded:      │
│               1000 requests per minute", │
│    "retry_after": 60                     │
│  }                                       │
└──────────────────────────────────────────┘

---

SCENARIO 4: Insufficient Scope
┌──────────────┐
│  Client      │  POST /api/v1/game/actions/start
│              │  Token scope: "dartboard:write"
│              │  Required scope: "game:control"
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  APIM:8243                               │
│  ├─ Token validation: ✓ PASSED           │
│  ├─ Check scopes:                        │
│  │  ├─ Token scope: "dartboard:write"   │
│  │  ├─ Required: "game:control"          │
│  │  ├─ Match: ✗ NO MATCH                 │
│  │  └─ Action: Reject request            │
│  └─ Return 403 response                  │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  Response: HTTP 403 Forbidden            │
│  {                                       │
│    "error": "insufficient_scope",        │
│    "error_description":                  │
│      "Required scope: game:control"      │
│  }                                       │
└──────────────────────────────────────────┘

---

SCENARIO 5: Backend Service Unavailable
┌──────────────┐
│  Client      │  POST /api/v1/dartboard/throw
│              │  Authorization: Bearer valid_token
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  APIM:8243                               │
│  ├─ Token validation: ✓ PASSED           │
│  ├─ Rate limit: ✓ OK                     │
│  ├─ Forward to API Gateway:8080          │
│  ├─ Connection timeout (API unavailable) │
│  └─ Action: Proxy error                  │
└──────┬───────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────┐
│  Response: HTTP 502 Bad Gateway          │
│  {                                       │
│    "error": "service_unavailable",       │
│    "message": "Backend service error"    │
│  }                                       │
└──────────────────────────────────────────┘
```

