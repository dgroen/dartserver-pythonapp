# Dartserver Python App - AI Coding Agent Instructions

## Project Overview

This is an **enterprise darts game management system** with real-time WebSocket updates, RabbitMQ integration, WSO2 OAuth2 authentication, and multi-game session support. It supports 301/401/501 and Cricket game modes with PostgreSQL persistence.

**Key Architecture**: Flask + SocketIO + RabbitMQ + WSO2 Identity Server + PostgreSQL + Docker

## Critical Project Structure

```
dartserver-pythonapp/
├── src/                          # NEW: All source code migrated here
│   ├── app/                      # Flask application layer
│   │   ├── app.py               # Main Flask app with auth routes
│   │   ├── game_manager.py      # Single game state management
│   │   └── game_session_manager.py  # Multi-session support (NEW)
│   ├── core/                     # Core infrastructure
│   │   ├── auth.py              # WSO2 OAuth2 integration + RBAC
│   │   ├── config.py            # Environment-aware configuration
│   │   ├── database_models.py   # SQLAlchemy models
│   │   └── rabbitmq_consumer.py # RabbitMQ AMQP consumer
│   ├── games/                    # Game logic (pluggable)
│   │   ├── game_301.py          # 301/401/501 games
│   │   └── game_cricket.py      # Cricket game
│   └── api_gateway/             # External API gateway service
├── app.py                        # COMPATIBILITY WRAPPER - imports from src/
├── templates/                    # Jinja2 templates (root level)
├── static/                       # CSS/JS (root level)
├── alembic/                      # Database migrations
└── tests/                        # pytest test suite
```

**CRITICAL**: The root `app.py`, `game_manager.py`, etc. are **compatibility wrappers** that import from `src/`. Always edit files in `src/` directory, not the root wrappers.

## Authentication & Authorization

### WSO2 OAuth2 Integration

- **Auth Flow**: OAuth2 Authorization Code flow with PKCE
- **Token Validation**: Introspection mode (default) or JWKS
- **Dynamic Redirect URIs**: Built from `X-Forwarded-Proto`/`X-Forwarded-Host` headers to support multiple domains (production: `letsplaydarts.eu`, dev: `dev.letsplaydarts.eu`, local: `localhost`)

### Role-Based Access Control (RBAC)

Three-tier role model managed in WSO2 IS:

1. **Player**: View game board, submit scores (`game:read`, `score:write`)
2. **Game Master**: All Player + control panel access (`game:write`, `player:write`)
3. **Admin**: Full system access (wildcard `*` permission)

### Auth Decorators Pattern

```python
from src.core.auth import login_required, role_required, permission_required

@app.route('/control')
@login_required
@role_required('Game Master', 'Admin')  # Requires ONE of these roles
def control_panel():
    ...

@app.route('/api/players', methods=['POST'])
@login_required
@permission_required('player:write')  # Requires specific permission
def add_player():
    ...
```

**Always use decorators in this order**: `@route` → `@login_required` → `@role_required`/`@permission_required`

## Multi-Game Session Architecture

**NEW Feature**: Concurrent game sessions support

- **GameSessionManager** (`src/app/game_session_manager.py`): Manages multiple concurrent games
- **Session IDs**: 16-byte URL-safe tokens via `secrets.token_urlsafe(16)`
- **Backward Compatibility**: Default session auto-created via `_get_default_game_manager()`
- **WebSocket Rooms**: Each session has its own Socket.IO room for isolated updates

### Session Management Pattern

```python
# Get session manager (singleton)
game_session_manager = app.game_session_manager

# Create new session
session_id = game_session_manager.create_session(creator_id='user123')

# Get session's game manager
gm = game_session_manager.get_session(session_id)

# Emit to session's room only
socketio.emit('game_state', data, room=session_id)
```

## Environment Configuration

**Multi-Environment Support** via `src/core/config.py`:

- Production: `https://letsplaydarts.eu` (SESSION_COOKIE_SECURE=true)
- Development: `http://dev.letsplaydarts.eu` (SESSION_COOKIE_SECURE=false)
- Localhost: Auto-detects scheme, disables secure cookies for HTTPS + localhost

**Environment Variables**:
- `ENVIRONMENT`: `production` | `development` | `staging`
- `APP_DOMAIN`: Domain without scheme (e.g., `letsplaydarts.eu`)
- `APP_SCHEME`: `https` | `http`
- `WSO2_IS_URL`: Public browser-facing WSO2 URL
- `WSO2_IS_INTERNAL_URL`: Internal Docker network URL (optional, defaults to WSO2_IS_URL)

**Cookie Security**: `SESSION_COOKIE_SECURE` derived from `APP_SCHEME` unless explicitly set. Force to `false` for localhost HTTPS to avoid self-signed cert issues.

## Database Patterns

**SQLAlchemy ORM** with PostgreSQL:

- **Models**: `Player`, `GameResult`, `Score`, `GameType`, `ApiKey`, `Dartboard`
- **Migrations**: Alembic (`alembic upgrade head`)
- **Connection**: Set via `DATABASE_URL` env var (default: `postgresql://postgres:postgres@localhost:5432/dartsdb`)
- **UTC Timestamps**: Always use `utc_now()` helper from `database_models.py`

**Session Management**:
```python
from src.core.database_models import DatabaseManager

db_manager = DatabaseManager()
db = db_manager.get_session()
try:
    # Query/modify database
    db.commit()
except:
    db.rollback()
finally:
    db.close()
```

## RabbitMQ Integration

**Message Flow**: Dartboard/External System → RabbitMQ → `rabbitmq_consumer.py` → `GameManager` → WebSocket Broadcast

**Message Format**:
```json
{
  "score": 20,
  "multiplier": "TRIPLE",  // SINGLE|DOUBLE|TRIPLE|BULL|DBLBULL
  "user": "Player 1"
}
```

**Consumer Pattern**: Background thread with auto-reconnect. Configure via `RABBITMQ_*` env vars (host, port, user, password, exchange, topic).

## WebSocket (Socket.IO) Patterns

**Automatic State Broadcast**: All game state changes emit to ALL connected clients

**Critical Events**:
- `game_state`: Full state update (emitted after EVERY change)
- `play_sound`: Trigger client sound effect
- `play_video`: Trigger client video effect

**Client → Server Events**: `new_game`, `add_player`, `manual_score`, `next_player`

**ProxyFix Middleware**: Flask behind nginx requires `ProxyFix` to trust `X-Forwarded-*` headers (already configured in `app.py`)

## Testing & Quality Tools

**Test Stack**: pytest + pytest-flask + pytest-cov + pytest-mock

**Run Tests**:
```bash
make test              # All tests
make test-unit         # Unit tests only
make test-integration  # Integration tests
make coverage          # With coverage report
```

**Linting & Type Checking**:
```bash
make lint              # Ruff + Black + isort + flake8
make lint-fix          # Auto-fix issues
make type              # mypy type checking
make security          # Bandit + safety
```

**Tox Multi-Python**: Tests run on Python 3.10/3.11/3.12 via `tox` (see `tox.ini`)

## Docker Development Workflow

**Start Full Stack** (includes WSO2 IS, RabbitMQ, PostgreSQL, nginx):
```bash
docker-compose -f docker-compose-localhost.yml up -d  # Local with WSO2
```

**Service URLs**:
- App: `http://localhost:5000`
- WSO2 Console: `https://localhost:9443/carbon` (admin/admin)
- RabbitMQ Management: `http://localhost:15672` (guest/guest)
- API Gateway: `http://localhost:8080`

**Health Checks**: All services have health checks. Wait for healthy state before accessing.

## Game Logic Implementation

**Pluggable Game Modes**: Each game type is a separate class in `src/games/`

**301/401/501 Logic** (`game_301.py`):
- Countdown from starting score
- Bust detection (score goes negative)
- Double-out support
- Win condition: exactly 0

**Cricket Logic** (`game_cricket.py`):
- Targets: 15-20 + Bull (25)
- 3 hits to "open" a target
- Score points on open targets
- First to open all + highest score wins

**Adding New Game**: Create class in `src/games/`, implement `process_score()` and `check_winner()`, register in `GameManager.start_new_game()`.

## API Gateway Service

**Separate Service** (`src/api_gateway/`): External-facing REST API with JWT auth for dartboard devices

**Purpose**: Secure score submission from electronic dartboards via RabbitMQ publishing

**Pattern**: JWT validation → Publish to RabbitMQ → Returns 202 Accepted (async processing)

## Critical Conventions

1. **Import from src/**: Always `from src.app.app import ...`, never import root-level wrappers
2. **Logging**: Use module-level logger: `logger = logging.getLogger(__name__)`
3. **Secrets**: Use `secrets.token_urlsafe()` for session IDs, NOT `uuid.uuid4()`
4. **Type Hints**: Required for new code (enforced by mypy with `check_untyped_defs=true`)
5. **Docstrings**: Google style for functions/classes (enforced by flake8-docstrings)
6. **Line Length**: 100 characters (Black/Ruff/Flake8 all set to 100)
7. **Error Handling**: Return JSON responses with status codes, log exceptions, never expose stack traces in production

## Common Pitfalls

- **Don't edit root wrappers**: Edit files in `src/`, not root `app.py`/`game_manager.py`
- **Session cookie security**: Localhost HTTPS needs `SESSION_COOKIE_SECURE=false`
- **Dynamic redirect URIs**: Use `get_dynamic_redirect_uri()`, not hardcoded `WSO2_REDIRECT_URI`
- **WebSocket rooms**: Emit to session room (`room=session_id`), not broadcast for multi-session
- **Database sessions**: Always close sessions in `finally` block
- **RabbitMQ reconnect**: Consumer has auto-reconnect, don't disable it

## Deployment Notes

**Production Differences**:
- Set `ENVIRONMENT=production`
- Use valid SSL certificates (not self-signed)
- Set strong `SECRET_KEY`
- Enable `SESSION_COOKIE_SECURE=true`
- Use dedicated service account for WSO2 introspection (not admin)
- Configure nginx with proper TLS settings

**Alembic Migrations**: Run `alembic upgrade head` before starting app in production

## Documentation Resources

- **Auth Setup**: `docs/AUTHENTICATION_SETUP.md` (500+ lines, complete guide)
- **Architecture**: `docs/ARCHITECTURE.md` (system diagrams, data flows)
- **Quick Start**: `QUICK_START.md` (5-step setup guide)
- **API Docs**: Available at `/api/docs/` (Swagger UI)
