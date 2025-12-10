# Phase 1 Quick Start - Dartserver-Core Package

## What Was Created

A standalone Python package called `dartserver-core` with all authentication, configuration, and database logic extracted from the monolith.

**Location:** `/packages/dartserver-core/`

## Package Contents

```
dartserver-core/
├── src/dartserver_core/
│   ├── __init__.py           ← Single import point
│   ├── auth.py               ← OAuth2, RBAC, decorators
│   ├── config.py             ← Environment config
│   ├── database_models.py    ← SQLAlchemy models
│   └── database_service.py   ← Database operations
├── tests/                    ← Unit tests
├── pyproject.toml            ← Package configuration
├── README.md                 ← Documentation
└── INSTALLATION_GUIDE.md     ← Installation help
```

## Installation

### Option 1: For Development

```bash
cd packages/dartserver-core
pip install -e ".[dev]"
python -c "from dartserver_core import Config; print('✓ Success')"
```

### Option 2: From Main Project

```bash
pip install -e packages/dartserver-core[dev]
```

## What You Can Import

```python
from dartserver_core import (
    Config,                    # Configuration
    Player, Game, GameHistory, # Models
    init_db, get_session,      # Database
    login_required,            # Decorator
    role_required,             # Decorator
)
```

## Quick Usage

### Configuration

```python
from dartserver_core import Config
print(Config.APP_URL)
```

### Database

```python
from dartserver_core import init_db, get_session, Player

init_db()
session = get_session()
player = Player(name="Alice")
session.add(player)
session.commit()
```

### Protected Routes

```python
from flask import Flask
from dartserver_core import login_required, role_required

@app.route("/game")
@login_required
def game(): return "Game Board"

@app.route("/admin")
@role_required("admin")
def admin(): return "Admin"
```

## Testing

```bash
cd packages/dartserver-core
pytest tests/
pytest tests/ --cov=dartserver_core
```

## Documentation

- `/doc/PHASE1_COMPLETE.md` - Phase 1 summary
- `/packages/dartserver-core/README.md` - Package docs
- `/packages/dartserver-core/INSTALLATION_GUIDE.md` - Installation

## Success Indicators ✅

- ✅ Package structure created
- ✅ All core modules moved
- ✅ Imports updated
- ✅ Exports defined
- ✅ Tests configured
- ✅ Documentation complete
- ✅ Ready for Phase 2

## Next: Phase 2 (Games Module)

Extract game logic to `packages/dartserver-games/` following the same pattern.

---

**Status:** ✅ PHASE 1 COMPLETE
