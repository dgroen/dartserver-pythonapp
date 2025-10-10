# Mobile App Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Mobile App (PWA)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ Gameplay │ │Gamemaster│ │ Results  │ │ Account  │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│  ┌──────────┐ ┌──────────┐ ┌──────────────────────┐           │
│  │Dartboard │ │ Hotspot  │ │  Service Worker      │           │
│  │  Setup   │ │ Control  │ │  (Offline Support)   │           │
│  └──────────┘ └──────────┘ └──────────────────────┘           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Flask Application                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Endpoints                         │  │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐        │  │
│  │  │   Mobile   │  │  Dartboard │  │   Game     │        │  │
│  │  │    API     │  │    API     │  │    API     │        │  │
│  │  └────────────┘  └────────────┘  └────────────┘        │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  Authentication                          │  │
│  │  ┌────────────┐              ┌────────────┐            │  │
│  │  │   OAuth2   │              │  API Key   │            │  │
│  │  │  (WSO2 IS) │              │   Auth     │            │  │
│  │  └────────────┘              └────────────┘            │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  Business Logic                          │  │
│  │  ┌────────────────────────────────────────────────────┐ │  │
│  │  │           MobileService                            │ │  │
│  │  │  • Dartboard Management                            │ │  │
│  │  │  • API Key Management                              │ │  │
│  │  │  • Hotspot Configuration                           │ │  │
│  │  └────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                  WebSocket (Socket.IO)                   │  │
│  │  • Real-time game updates                                │  │
│  │  • Score broadcasts                                      │  │
│  │  • Player changes                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ SQLAlchemy ORM
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      PostgreSQL Database                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │  Player  │ │Dartboard │ │ ApiKey   │ │ Hotspot  │          │
│  │          │ │          │ │          │ │  Config  │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## Connectivity Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Dartboard Connectivity                       │
└─────────────────────────────────────────────────────────────────┘

Step 1: Registration
┌──────────────┐
│     User     │
└──────┬───────┘
       │ 1. Register dartboard
       │    (ID: DART-ABC123, WPA Key: secret123)
       ▼
┌──────────────┐      ┌──────────────┐
│  Mobile App  │─────▶│   Database   │
└──────────────┘      └──────────────┘

Step 2: Hotspot Configuration
┌──────────────┐
│     User     │
└──────┬───────┘
       │ 2. Configure hotspot
       │    (SSID: DART-ABC123, Password: secret123)
       ▼
┌──────────────┐      ┌──────────────┐
│  Mobile App  │─────▶│   Database   │
└──────────────┘      └──────────────┘

Step 3: Create Mobile Hotspot
┌──────────────┐
│     User     │
└──────┬───────┘
       │ 3. Create hotspot on phone
       │    (Settings → Hotspot)
       ▼
┌──────────────┐
│ Phone WiFi   │ SSID: DART-ABC123
│   Hotspot    │ Password: secret123
└──────┬───────┘
       │
       │ 4. Dartboard searches for SSID
       │
       ▼
┌──────────────┐
│  Dartboard   │ Connects to hotspot
└──────┬───────┘
       │
       │ 5. Send scores via API
       │    (X-API-Key: generated-key)
       ▼
┌──────────────┐      ┌──────────────┐
│  Flask API   │─────▶│   Database   │
└──────┬───────┘      └──────────────┘
       │
       │ 6. Broadcast via WebSocket
       ▼
┌──────────────┐
│  Mobile App  │ Real-time updates
└──────────────┘
```

## Authentication Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Dual Authentication                          │
└─────────────────────────────────────────────────────────────────┘

Web Users (OAuth2):
┌──────────────┐
│     User     │
└──────┬───────┘
       │ 1. Login
       ▼
┌──────────────┐      ┌──────────────┐
│  WSO2 IS     │◀────▶│  Flask App   │
└──────┬───────┘      └──────┬───────┘
       │                     │
       │ 2. OAuth2 token     │ 3. Session cookie
       ▼                     ▼
┌──────────────┐      ┌──────────────┐
│  Flask App   │─────▶│  Mobile App  │
└──────────────┘      └──────────────┘

Dartboards (API Key):
┌──────────────┐
│  Dartboard   │
└──────┬───────┘
       │ 1. Send score with API key
       │    (X-API-Key: abc123...)
       ▼
┌──────────────┐
│  Flask API   │
└──────┬───────┘
       │ 2. Validate API key
       ▼
┌──────────────┐      ┌──────────────┐
│   Database   │◀────▶│  Flask API   │
└──────────────┘      └──────┬───────┘
                             │ 3. Process score
                             ▼
                      ┌──────────────┐
                      │  WebSocket   │
                      └──────┬───────┘
                             │ 4. Broadcast
                             ▼
                      ┌──────────────┐
                      │  Mobile App  │
                      └──────────────┘
```

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      Request/Response Flow                      │
└─────────────────────────────────────────────────────────────────┘

Mobile App Request:
┌──────────────┐
│  Mobile App  │
└──────┬───────┘
       │ GET /api/mobile/dartboards
       │ Cookie: session=...
       ▼
┌──────────────┐
│  Flask App   │
└──────┬───────┘
       │ @login_required
       │ @role_required
       ▼
┌──────────────┐
│ MobileService│
└──────┬───────┘
       │ get_dartboards(player_id)
       ▼
┌──────────────┐
│   Database   │
└──────┬───────┘
       │ SELECT * FROM dartboard WHERE player_id=...
       ▼
┌──────────────┐
│ MobileService│
└──────┬───────┘
       │ Return dartboards
       ▼
┌──────────────┐
│  Flask App   │
└──────┬───────┘
       │ jsonify(dartboards)
       ▼
┌──────────────┐
│  Mobile App  │ Display dartboards
└──────────────┘

Dartboard Request:
┌──────────────┐
│  Dartboard   │
└──────┬───────┘
       │ POST /api/dartboard/score
       │ X-API-Key: abc123...
       │ {"dartboard_id": "DART-ABC123", "score": 180}
       ▼
┌──────────────┐
│  Flask App   │
└──────┬───────┘
       │ @api_key_required
       ▼
┌──────────────┐
│ MobileService│
└──────┬───────┘
       │ validate_api_key(key)
       ▼
┌──────────────┐
│   Database   │
└──────┬───────┘
       │ SELECT * FROM api_key WHERE key_hash=...
       ▼
┌──────────────┐
│  Flask App   │
└──────┬───────┘
       │ Process score
       │ Update game state
       ▼
┌──────────────┐
│  WebSocket   │
└──────┬───────┘
       │ emit('score_update', data)
       ▼
┌──────────────┐
│  Mobile App  │ Real-time update
└──────────────┘
```

## Database Schema

```
┌─────────────────────────────────────────────────────────────────┐
│                      Database Relationships                     │
└─────────────────────────────────────────────────────────────────┘

┌──────────────────────┐
│       Player         │
│──────────────────────│
│ id (PK)              │
│ name                 │
│ username (unique)    │◀─────┐
│ email                │      │
│ created_at           │      │
└──────────────────────┘      │
                              │ player_id (FK)
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Dartboard   │    │   ApiKey     │    │HotspotConfig │
│──────────────│    │──────────────│    │──────────────│
│ id (PK)      │    │ id (PK)      │    │ id (PK)      │
│ player_id(FK)│    │ player_id(FK)│    │ player_id(FK)│
│ dartboard_id │    │ key_hash     │    │ dartboard_id │
│ wpa_key      │    │ key_prefix   │    │ wpa_key      │
│ name         │    │ name         │    │ is_active    │
│ is_connected │    │ is_active    │    │ created_at   │
│ last_conn_at │    │ last_used_at │    │ updated_at   │
│ created_at   │    │ created_at   │    └──────────────┘
└──────────────┘    └──────────────┘
```

## Component Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Frontend Components                        │
└─────────────────────────────────────────────────────────────────┘

Mobile App (PWA)
├── Templates (HTML)
│   ├── mobile.html              # Main landing page
│   ├── mobile_gameplay.html     # Gameplay interface
│   ├── mobile_gamemaster.html   # Game control
│   ├── mobile_dartboard_setup.html  # Dartboard registration
│   ├── mobile_results.html      # Game results
│   ├── mobile_account.html      # Account management
│   └── mobile_hotspot.html      # Hotspot control
│
├── JavaScript Modules
│   ├── mobile.js                # Main app logic
│   ├── mobile_gameplay.js       # WebSocket integration
│   ├── mobile_gamemaster.js     # Game control logic
│   ├── mobile_dartboard_setup.js  # Setup logic
│   ├── mobile_results.js        # Results display
│   ├── mobile_account.js        # Account management
│   └── mobile_hotspot.js        # Hotspot control
│
├── Styles
│   └── mobile.css               # Mobile-first responsive design
│
└── PWA Files
    ├── manifest.json            # App manifest
    └── service-worker.js        # Offline support

┌─────────────────────────────────────────────────────────────────┐
│                      Backend Components                         │
└─────────────────────────────────────────────────────────────────┘

Flask Application
├── Routes (app.py)
│   ├── Mobile UI Routes (7)
│   ├── API Key Management (4)
│   ├── Dartboard Management (3)
│   ├── Hotspot Configuration (3)
│   └── Dartboard Device API (2)
│
├── Services (src/)
│   └── mobile_service.py
│       ├── MobileService class
│       ├── Dartboard management
│       ├── API key management
│       └── Hotspot configuration
│
├── Models (database_models.py)
│   ├── Player (extended)
│   ├── Dartboard
│   ├── ApiKey
│   └── HotspotConfig
│
└── Migrations (alembic/)
    └── d55f29e75045_add_mobile_app_tables.py
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Security Layers                            │
└─────────────────────────────────────────────────────────────────┘

Layer 1: Transport Security
┌──────────────────────────────────────────────────────────────┐
│                         HTTPS/TLS                            │
│  • Encrypted communication                                   │
│  • Certificate validation                                    │
└──────────────────────────────────────────────────────────────┘

Layer 2: Authentication
┌──────────────────────────────────────────────────────────────┐
│  Web Users              │  Dartboards                        │
│  ┌──────────────────┐   │  ┌──────────────────┐            │
│  │  OAuth2 (WSO2)   │   │  │  API Key Auth    │            │
│  │  • Session cookie│   │  │  • X-API-Key hdr │            │
│  │  • Token refresh │   │  │  • SHA-256 hash  │            │
│  └──────────────────┘   │  └──────────────────┘            │
└──────────────────────────────────────────────────────────────┘

Layer 3: Authorization
┌──────────────────────────────────────────────────────────────┐
│  • @login_required decorator                                 │
│  • @role_required decorator                                  │
│  • @api_key_required decorator                               │
│  • Player-specific data filtering                            │
└──────────────────────────────────────────────────────────────┘

Layer 4: Data Protection
┌──────────────────────────────────────────────────────────────┐
│  • API key hashing (SHA-256)                                 │
│  • WPA key encryption                                        │
│  • SQL injection protection (SQLAlchemy ORM)                 │
│  • XSS protection (template escaping)                        │
│  • CSRF protection (Flask-WTF)                               │
└──────────────────────────────────────────────────────────────┘
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Production Deployment                      │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐
│   Internet   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  HTTPS (443) │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│    Nginx     │ Reverse Proxy
│  (SSL Term)  │ Load Balancer
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Gunicorn   │ WSGI Server
│  (Workers)   │ Process Manager
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Flask App   │ Application Server
│  (Socket.IO) │ WebSocket Server
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  PostgreSQL  │ Database Server
│  (Primary)   │ Data Storage
└──────────────┘
```

---

This architecture provides:

- ✅ Scalability (horizontal scaling of Flask workers)
- ✅ Security (multiple layers of protection)
- ✅ Real-time updates (WebSocket integration)
- ✅ Offline support (PWA with service worker)
- ✅ Mobile-first design (responsive UI)
- ✅ Dual authentication (OAuth2 + API keys)
- ✅ Database integrity (foreign keys, indexes)
