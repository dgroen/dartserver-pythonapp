# Architecture Documentation

## System Overview

### High-Level Architecture

```mermaid
graph TB
    Client["Web Clients<br/>(Browser)"]
    Mobile["Mobile Clients"]
    RMQ["RabbitMQ<br/>(Score Queue)"]
    
    Client -->|HTTP/WebSocket| Flask["Flask App<br/>(Port 5000)"]
    Mobile -->|HTTP/WebSocket| Flask
    RMQ -->|Consumer| Flask
    
    Flask -->|SQL| DB["PostgreSQL<br/>(Database)"]
    Flask -->|Token Validation| WSO2["WSO2 Identity<br/>(Port 9443)"]
    
    Nginx["Nginx<br/>(Reverse Proxy)"]
    Nginx -->|http:5000| Flask
    
    Browser["User Browser"]
    Browser -->|https| Nginx
    
    style Flask fill:#4A90E2
    style DB fill:#50C878
    style WSO2 fill:#FF6B6B
    style RMQ fill:#F5A623
```

## Core Components

### 1. Flask Application (src/app/app.py)

**Responsibilities:**
- HTTP request handling
- WebSocket connection management
- Route definitions
- Session management

**Key Routes:**
- GET / - Game board
- GET /control - Control panel
- POST /api/game/start - Start new game
- POST /api/score - Submit score
- GET /callback - OAuth2 callback

### 2. Game Manager (src/app/game_manager.py)

```mermaid
graph LR
    GM["Game Manager"]
    GM -->|Load| Game["Game Instance"]
    Game -->|301 Logic| G301["Game 301"]
    Game -->|Cricket Logic| GCricket["Game Cricket"]
    GM -->|Persist| DB[(Database)]
    
    style GM fill:#4A90E2
    style G301 fill:#50C878
    style GCricket fill:#50C878
```

**Functions:**
- Create new games
- Load saved games
- Apply scores
- Manage game state
- Handle win conditions

### 3. Authentication (src/core/auth.py)

```mermaid
sequenceDiagram
    participant User
    participant App as Flask App
    participant WSO2
    
    User->>App: Click Login
    App->>WSO2: Redirect to authorize endpoint
    WSO2->>User: Show login form
    User->>WSO2: Enter credentials
    WSO2->>App: Redirect with authorization code
    App->>WSO2: Exchange code for token
    WSO2->>App: Return access token
    App->>App: Extract roles from token
    App->>User: Redirect to game board
```

**Features:**
- OAuth2/OIDC flow
- JWT token validation
- Role extraction
- Permission checking
- Session management

### 4. RabbitMQ Consumer (src/core/rabbitmq_consumer.py)

```mermaid
graph LR
    RMQ["RabbitMQ<br/>Exchange: darts_exchange<br/>Topic: darts.scores.#"]
    Consumer["RabbitMQ Consumer<br/>(Background Thread)"]
    Queue["Dart Scores<br/>(JSON)"]
    GM["Game Manager"]
    WebSocket["WebSocket Emit"]
    
    RMQ -->|Subscribe| Consumer
    Consumer -->|Parse| Queue
    Queue -->|Apply Score| GM
    GM -->|broadcast| WebSocket
    
    style RMQ fill:#F5A623
    style Consumer fill:#4A90E2
```

**Process:**
1. Subscribe to darts_exchange topic
2. Receive score messages: {"score": 20, "multiplier": "TRIPLE"}
3. Parse and validate
4. Apply to current game
5. Broadcast update to connected clients

### 5. Database Models (src/core/database_models.py)

```mermaid
erDiagram
    PLAYER ||--o{ GAME_PLAYER : joins
    GAME ||--o{ GAME_PLAYER : contains
    GAME ||--o{ GAME_HISTORY : tracks
    
    PLAYER {
        int id
        string name
        string email
        datetime created_at
    }
    
    GAME {
        int id
        string game_type
        string status
        datetime created_at
        datetime ended_at
    }
    
    GAME_PLAYER {
        int id
        int game_id
        int player_id
        int initial_score
        int current_score
        int turn_number
    }
    
    GAME_HISTORY {
        int id
        int game_id
        int player_id
        int score
        string multiplier
        datetime timestamp
    }
```

## Request Flow Diagram

### Score Submission Flow

```mermaid
graph TD
    A["User Submits Score"]
    B{"Via Method?"}
    C["RabbitMQ Message"]
    D["REST API POST"]
    E["WebSocket Event"]
    
    A --> B
    B -->|RabbitMQ| C
    B -->|REST API| D
    B -->|WebSocket| E
    
    C -->|Consumer Processes| F["Validate Score"]
    D -->|Route Handler| F
    E -->|Event Handler| F
    
    F -->|Invalid| G["Return Error"]
    F -->|Valid| H["Game Manager<br/>Apply Score"]
    
    H -->|Update| I["Database"]
    I -->|Emit Event| J["WebSocket Broadcast"]
    J -->|Update| K["All Connected Clients"]
    
    style F fill:#FF6B6B
    style H fill:#4A90E2
    style J fill:#F5A623
    style K fill:#50C878
```

## Authentication Flow

```mermaid
stateDiagram-v2
    [*] --> NotAuthenticated
    NotAuthenticated --> LoginPage: User visits app
    LoginPage --> WSO2: Click Login
    WSO2 --> AuthorizationPrompt: Redirect to WSO2
    AuthorizationPrompt --> CredentialEntry: User enters credentials
    CredentialEntry --> TokenGeneration: WSO2 validates
    TokenGeneration --> Callback: Redirect with code
    Callback --> TokenExchange: Exchange code for token
    TokenExchange --> TokenValidation: Validate token
    TokenValidation --> Authenticated: Extract roles
    Authenticated --> GameBoard: Render UI
    
    Authenticated --> Logout: User clicks logout
    Logout --> [*]
```

## Game State Machine

```mermaid
stateDiagram-v2
    [*] --> Created: Game created
    Created --> Started: Players ready
    Started --> InProgress: Turn started
    InProgress --> Scoring: Score submitted
    Scoring --> NextTurn: Turn complete
    NextTurn --> InProgress: Continue game
    NextTurn --> Finished: Win condition met
    Finished --> [*]
    
    InProgress --> Paused: Pause requested
    Paused --> InProgress: Resume requested
    
    Created --> Cancelled: Game cancelled
    Cancelled --> [*]
```

## Deployment Architecture

```mermaid
graph TB
    subgraph Internet["Internet"]
        User["Users"]
    end
    
    subgraph CloudFlare["CloudFlare / DNS"]
        DNS["DNS: yourdomain.com"]
    end
    
    subgraph Production["Production Server"]
        subgraph Nginx["Nginx Reverse Proxy"]
            NginxServer["Port 443<br/>(HTTPS)"]
        end
        
        subgraph App["Flask Application"]
            Flask["Flask-SocketIO<br/>Port 5000"]
        end
        
        subgraph Services["Background Services"]
            RabbitMQ["RabbitMQ<br/>Port 5672"]
            PostgreSQL["PostgreSQL<br/>Port 5432"]
        end
    end
    
    User -->|HTTPS| DNS
    DNS -->|Resolves| NginxServer
    NginxServer -->|Proxy| Flask
    Flask -->|Consume| RabbitMQ
    Flask -->|Query| PostgreSQL
    
    style NginxServer fill:#FFA500
    style Flask fill:#4A90E2
    style RabbitMQ fill:#F5A623
    style PostgreSQL fill:#50C878
```

## Technology Stack

### Backend
- **Framework**: Flask 3.0.0
- **Real-time**: Flask-SocketIO 5.3.5
- **ORM**: SQLAlchemy 2.0.23
- **Message Queue**: RabbitMQ (Pika 1.3.2)
- **Authentication**: PyJWT, WSO2 IS
- **API Documentation**: Flasgger 0.9.7.1

### Frontend
- **HTML5**: Responsive design
- **CSS3**: Modern styling
- **JavaScript**: Real-time updates
- **WebSocket**: Socket.io client
- **PWA**: Service Worker support

### Database
- **Production**: PostgreSQL 16
- **Development**: SQLite
- **Migrations**: Alembic

### Deployment
- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **Reverse Proxy**: Nginx
- **Process Manager**: Systemd

### Development
- **Testing**: pytest
- **Code Quality**: Ruff, Black, MyPy
- **Security**: Bandit
- **CI/CD**: Pre-commit hooks

## Scaling Considerations

### Horizontal Scaling

```mermaid
graph TB
    LB["Load Balancer"]
    
    LB --> Flask1["Flask 1<br/>Port 5000"]
    LB --> Flask2["Flask 2<br/>Port 5001"]
    LB --> Flask3["Flask 3<br/>Port 5002"]
    
    Flask1 --> RMQ["Shared RabbitMQ"]
    Flask2 --> RMQ
    Flask3 --> RMQ
    
    Flask1 --> DB["Shared PostgreSQL"]
    Flask2 --> DB
    Flask3 --> DB
    
    RMQ --> Redis["Redis Cache<br/>(Optional)"]
```

**Strategies:**
- Run multiple Flask instances
- Use load balancer (HAProxy, Nginx)
- Shared RabbitMQ queue
- Shared PostgreSQL database
- Optional caching layer (Redis)

### Performance Optimization

- WebSocket for real-time updates (vs polling)
- Connection pooling for database
- Message queue for async operations
- Lazy loading of game state
- Frontend caching

## Security Architecture

```mermaid
graph LR
    User["User"]
    Nginx["Nginx<br/>(HTTPS, Headers)"]
    App["Flask<br/>(Input Validation)"]
    Auth["Auth Module<br/>(Token Validation)"]
    DB["Database<br/>(SQL Injection Prevention)"]
    
    User -->|HTTPS Only| Nginx
    Nginx -->|Security Headers| App
    App -->|Validate Input| Auth
    Auth -->|Check Permissions| App
    App -->|Parameterized Queries| DB
    
    style Nginx fill:#FF6B6B
    style Auth fill:#FF6B6B
```

**Security Measures:**
- HTTPS/TLS encryption
- OAuth2/OIDC authentication
- Role-based access control
- Input validation and sanitization
- SQL injection prevention (ORM)
- CSRF protection
- Secure cookies (HttpOnly, SameSite)
- Security headers (CSP, HSTS, X-Frame-Options)

## Performance Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Page Load | <2s | 1.2s |
| Score Update | <100ms | 50ms |
| API Response | <500ms | 200ms |
| Database Query | <50ms | 30ms |
| Memory Usage | <512MB | 250MB |
| Concurrent Users | 100+ | Tested with 50 |

## Monitoring

**Key Metrics to Monitor:**
- Flask request latency
- RabbitMQ queue depth
- PostgreSQL connection pool
- WebSocket connection count
- Error rates and exceptions
- CPU and memory usage
- Network I/O

**Recommended Tools:**
- Prometheus (metrics collection)
- Grafana (visualization)
- ELK Stack (logging)
- Sentry (error tracking)
