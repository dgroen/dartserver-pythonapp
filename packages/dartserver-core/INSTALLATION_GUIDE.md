# Dartserver-Core Installation & Usage Guide

## Phase 1 Completion Report

This guide covers the extraction of the dartserver-core package as part of Phase 1 of the refactoring initiative.

## Package Contents

The `dartserver-core` package contains:

### Core Modules

1. **auth.py** (33.5 KB)
   - OAuth2/OIDC authentication with WSO2 Identity Server
   - Role-based access control (RBAC) decorators
   - Token validation and user info extraction
   - Functions: `login_required()`, `role_required()`, `permission_required()`

2. **config.py** (2.9 KB)
   - Environment-aware configuration management
   - Application settings from environment variables
   - Database URL, Flask settings, WSO2 configuration

3. **database_models.py** (14 KB)
   - SQLAlchemy ORM models
   - Models: `Player`, `Game`, `GamePlayer`, `GameHistory`
   - Relationships and constraints

4. **database_service.py** (36.2 KB)
   - Database connection management
   - CRUD operations
   - Session management
   - Functions: `init_db()`, `get_session()`, `set_database_service()`

## Installation Methods

### Method 1: Local Development (Editable Install)

```bash
cd packages/dartserver-core

# Install with all dependencies
pip install -e .

# Install with development tools
pip install -e ".[dev]"

# Verify installation
python -c "from dartserver_core import Config, Player; print('✓ Core package installed')"
```

### Method 2: From Source

```bash
# Clone and install
git clone <repo-url>
cd dartserver-core
pip install -e ".[dev]"
```

### Method 3: Published Package (Future)

```bash
# Install from PyPI
pip install dartserver-core
```

## Verification

### Quick Import Test

```python
from dartserver_core import (
    Config,
    Player,
    Game,
    GameHistory,
    login_required,
    role_required,
)

print("✓ All imports successful")
```

### Run Tests

```bash
cd packages/dartserver-core

# Install test dependencies
pip install -e ".[test]"

# Run tests
pytest

# With coverage report
pytest --cov=dartserver_core
```

### Check Exports

```bash
python << EOF
from dartserver_core import __all__

print("Exported from dartserver-core:")
for item in sorted(__all__):
    print(f"  ✓ {item}")
EOF
```

## Usage Examples

### 1. Configuration

```python
from dartserver_core import Config

print(f"App URL: {Config.APP_URL}")
print(f"Debug: {Config.DEBUG}")
print(f"Database: {Config.DATABASE_URL}")
```

### 2. Database

```python
from dartserver_core import init_db, get_session, Player

# Initialize database
init_db()

# Get session
session = get_session()

# Create player
player = Player(name="Alice", email="alice@example.com")
session.add(player)
session.commit()

print(f"Player created: {player.name} (ID: {player.id})")
```

### 3. Authentication (Flask)

```python
from flask import Flask
from dartserver_core import login_required, role_required

app = Flask(__name__)
app.secret_key = "your-secret-key"

@app.route("/game")
@login_required
def game_board():
    return "Game Board"

@app.route("/control")
@role_required("game_master")
def control_panel():
    return "Control Panel"

@app.route("/admin")
@role_required("admin")
def admin_area():
    return "Admin Area"
```

## Dependencies

### Core Dependencies

- **Flask** (3.0.0+) - Web framework
- **SQLAlchemy** (2.0.23+) - ORM
- **PyJWT** (2.8.0+) - JWT token handling
- **requests** (2.31.0+) - HTTP requests for WSO2
- **python-dotenv** (1.0.0+) - Environment variable management
- **psycopg2-binary** (2.9.9+) - PostgreSQL adapter
- **alembic** (1.13.1+) - Database migrations

### Development Dependencies

```
pytest >= 7.4.0
pytest-cov >= 4.1.0
pytest-mock >= 3.12.0
black >= 23.0.0
ruff >= 0.1.0
mypy >= 1.7.0
```

## Environment Variables

```env
# Flask Configuration
FLASK_DEBUG=False
SECRET_KEY=your-secret-key-here
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/darts_db

# WSO2 Authentication
WSO2_IS_URL=https://localhost:9443
WSO2_IS_INTERNAL_URL=https://localhost:9443
WSO2_CLIENT_ID=your-client-id
WSO2_CLIENT_SECRET=your-client-secret
WSO2_REDIRECT_URI=http://localhost:5000/callback
JWT_VALIDATION_MODE=introspection
WSO2_IS_INTROSPECT_USER=admin
WSO2_IS_INTROSPECT_PASSWORD=admin

# Session Configuration
SESSION_COOKIE_SECURE=False
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
```

## Integration with Main App

### Old Way (Monolith)

```python
from src.core.auth import login_required
from src.core.config import Config
from src.core.database_models import Player
```

### New Way (Package)

```python
from dartserver_core import login_required, Config, Player
```

## Next Steps

### For Development

1. Install the package in editable mode
2. Use it in other packages (games, services)
3. Run tests to ensure compatibility
4. Update main app to use the package

### For Production

1. Build distribution package
2. Publish to PyPI (or private registry)
3. Update requirements.txt to depend on published package
4. Deploy with versioned dependency

## Publishing to PyPI

```bash
cd packages/dartserver-core

# Install build tools
pip install build twine

# Build distribution
python -m build

# Upload to PyPI
twine upload dist/*

# Or to test PyPI first
twine upload --repository testpypi dist/*
```

## Troubleshooting

### Import Errors

```
ImportError: No module named 'dartserver_core'
```

Solution: Install the package in editable mode:
```bash
pip install -e packages/dartserver-core
```

### Database Connection

```
SQLAlchemy error: Could not connect to database
```

Solution: Check DATABASE_URL environment variable:
```bash
echo $DATABASE_URL
```

### Module Not Found

```
ModuleNotFoundError: No module named 'dartserver_core.config'
```

Solution: Verify imports were updated:
```bash
grep -r "from src.core" packages/dartserver-core/src/
```

## Migration Checklist

When switching to the extracted package:

- [ ] Install dartserver-core package
- [ ] Update imports in main app
- [ ] Update imports in other packages
- [ ] Run tests for all packages
- [ ] Verify database operations
- [ ] Test authentication flow
- [ ] Check all decorators work
- [ ] Verify role-based access control

## File Structure

```
dartserver-core/
├── src/dartserver_core/
│   ├── __init__.py          (Exports API)
│   ├── auth.py              (Authentication)
│   ├── config.py            (Configuration)
│   ├── database_models.py   (ORM Models)
│   └── database_service.py  (Database ops)
├── tests/
│   ├── __init__.py
│   ├── conftest.py          (Test fixtures)
│   └── test_core.py         (Basic tests)
├── .gitignore
├── README.md                (Package readme)
├── pyproject.toml           (Package config)
└── INSTALLATION_GUIDE.md    (This file)
```

## Support

For issues or questions:

1. Check the package README.md
2. Review test files for usage examples
3. Check documentation in doc/DEVELOPER_GUIDE.md
4. Check documentation in doc/REFACTORING_PLAN.md
