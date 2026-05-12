# dartserver-core

Core authentication, configuration, and database functionality for the Darts Game Server.

## Features

- **OAuth2/OIDC Authentication** - Integration with WSO2 Identity Server
- **Configuration Management** - Environment-aware settings for dev/prod
- **Database Models** - SQLAlchemy models for players, games, scores
- **Database Service** - Session management and query utilities
- **Role-Based Access Control** - Permission and role decorators for routes

## Installation

```bash
pip install dartserver-core
```

## Quick Start

### Authentication

```python
from dartserver_core import login_required, role_required

@app.route('/protected')
@login_required
def protected_route():
    return {'message': 'Authenticated'}

@app.route('/admin')
@login_required
@role_required('admin')
def admin_route():
    return {'message': 'Admin only'}
```

### Configuration

```python
from dartserver_core import Config

print(Config.APP_URL)           # Application URL
print(Config.is_production())   # Check if production
print(Config.SESSION_COOKIE_SECURE)  # Cookie security setting
```

### Database

```python
from dartserver_core import init_db, get_session
from dartserver_core import Player, GameHistory

# Initialize database
init_db()

# Get database session
session = get_session()

# Query players
players = session.query(Player).all()

# Close session
session.close()
```

## Public Exports

- `Config` - Configuration class
- `init_db()` - Database initialization
- `get_session()` - Get database session
- `set_database_service()` - Set global database service
- `login_required` - Login requirement decorator
- `role_required()` - Role requirement decorator
- `permission_required()` - Permission requirement decorator
- `Player`, `GameHistory`, `GameScore`, `GameSession` - ORM models
- `ApiKey`, `Dartboard`, `HotspotConfig`, `DartboardType`, `DartboardZoneMapping` - Mobile models

## Models

### Player
- `id` - Primary key
- `username` - Unique username
- `email` - User email
- `name` - Display name
- `created_at` - Creation timestamp

### GameHistory
- `id` - Primary key
- `player_id` - Player reference
- `game_type` - Game type (301, Cricket, etc)
- `started_at` - Game start time
- `ended_at` - Game end time
- `winner_id` - Winner reference

### GameScore
- `id` - Primary key
- `game_session_id` - Game session reference
- `player_id` - Player reference
- `round_number` - Round number
- `score` - Score value

## Configuration

Set environment variables:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/dartserver

# Authentication
WSO2_IS_URL=https://wso2is:9443
WSO2_IS_INTERNAL_URL=https://wso2is:9443
OIDC_CLIENT_ID=darts-app
OIDC_CLIENT_SECRET=secret

# Application
APP_URL=https://localhost:5000
CALLBACK_URL=https://localhost:5000/callback
FLASK_ENV=production
```

## Testing

```bash
pytest tests/
```

## License

MIT - See LICENSE file

## Contributing

Pull requests welcome. Please ensure tests pass.
