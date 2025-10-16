# Modular Structure Quick Reference

## Directory Map

```
darts-app/
├── src/
│   ├── app/              ← Flask app, game logic
│   │   ├── app.py        ← Main Flask application
│   │   ├── game_manager.py    ← Game orchestration
│   │   └── mobile_service.py  ← Mobile endpoints
│   ├── api/              ← REST API (future expansion)
│   ├── api_gateway/      ← API Gateway service
│   ├── core/             ← Shared utilities
│   │   ├── auth.py       ← Authentication/authorization
│   │   ├── database_*.py ← Database layer
│   │   ├── tts_service.py    ← Text-to-speech
│   │   └── rabbitmq_consumer.py
│   └── games/            ← Game implementations
│       ├── game_301.py
│       └── game_cricket.py
├── run.py                ← NEW: Main entry point
├── app.py                ← Compatibility wrapper
└── tests/                ← All test files
```

## Common Tasks

### Starting the App
```bash
# Use new entry point (recommended)
python run.py

# Or old way (still works)
python app.py
```

### Adding a New Feature

#### In app logic (`src/app/`)
```python
from src.core.auth import login_required
from src.core.database_service import DatabaseService

@app.route('/api/my-endpoint')
@login_required
def my_endpoint():
    # Implementation
    pass
```

#### In game logic (`src/games/`)
```python
from src.games.game_301 import Game301
# or
from games.game_301 import Game301  # Still works via wrapper
```

#### In core utilities (`src/core/`)
```python
# These are imported by other modules
from src.core.auth import validate_token
from src.core.database_service import DatabaseService
```

### Importing Modules

#### New way (recommended)
```python
from src.app.app import app, socketio
from src.core.auth import login_required, validate_token
from src.core.database_service import DatabaseService
from src.games.game_301 import Game301
```

#### Old way (still works via compatibility wrappers)
```python
from app import app, socketio
from auth import validate_token
from database_service import DatabaseService
from games.game_301 import Game301
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/unit/test_auth.py

# Specific test
pytest tests/unit/test_auth.py::TestValidateToken::test_validate_token_jwks_success

# Integration tests only
pytest tests/integration/

# Watch mode (requires pytest-watch)
ptw
```

### Code Quality

```bash
# Format code
python -m black src/

# Lint check
python -m ruff check src/

# Type checking
mypy src/

# Security check
bandit -r src/
```

## Module Import Paths

| Module | Old Path | New Path | Status |
|--------|----------|----------|--------|
| Flask app | `app` | `src.app.app` | ✅ Both work |
| Game manager | `game_manager` | `src.app.game_manager` | ✅ Both work |
| Mobile service | `mobile_service` | `src.app.mobile_service` | ✅ Both work |
| Auth | `auth` | `src.core.auth` | ✅ Both work |
| Database models | `database_models` | `src.core.database_models` | ✅ Both work |
| Database service | `database_service` | `src.core.database_service` | ✅ Both work |
| TTS service | `tts_service` | `src.core.tts_service` | ✅ Both work |
| RabbitMQ | `rabbitmq_consumer` | `src.core.rabbitmq_consumer` | ✅ Both work |
| Games | `games.game_301` | `src.games.game_301` | ✅ Both work |
| API Gateway | `api_gateway` | `src.api_gateway.app` | ✅ Both work |

## File Organization Tips

### When to put code in `src/core/`
- Shared utilities used by multiple modules
- Authentication/authorization logic
- Database operations
- Configuration management
- External service clients (RabbitMQ, gTTS)

### When to put code in `src/app/`
- Flask application setup
- Route handlers (API endpoints)
- Game orchestration
- Business logic specific to the web app

### When to put code in `src/games/`
- Game rules implementations
- Game state management
- Game-specific logic (301, Cricket, etc.)

### When to put code in `src/api/`
- Future REST API endpoints
- API-specific decorators/middleware
- API response formatting

## Entry Points

### Main Application
```python
# NEW way
from run import app, socketio
app.run(debug=True)

# OLD way (still works)
from app import app, socketio
app.run(debug=True)
```

### API Gateway
```python
from src.api_gateway.app import app as gateway_app
gateway_app.run()
```

## Backward Compatibility

All root-level files are **compatibility wrappers**:
- ✅ `app.py` - re-exports from `src.app.app`
- ✅ `auth.py` - re-exports from `src.core.auth`
- ✅ `database_*.py` - re-export from `src.core/`
- ✅ `tts_service.py` - re-exports from `src.core.tts_service`
- ✅ `game_manager.py` - re-exports from `src.app.game_manager`

**Existing code will continue to work** without changes, but new code should use the `src.*` import paths.

## Migration Path

### For Existing Code
No changes needed - compatibility wrappers keep everything working.

### For New Code
Use new import paths directly:
```python
# Instead of:
from auth import validate_token
# Use:
from src.core.auth import validate_token
```

### Gradual Migration
If refactoring old code, update imports gradually as you modify each file:
```python
# Before
from game_manager import GameManager

# After
from src.app.game_manager import GameManager
```

## Troubleshooting

### Import Error: Module not found
- Check you're using correct path (e.g., `src.core.auth` not `src.auth`)
- Verify file is in the correct directory

### Tests failing with import errors
- Update test imports to use new paths
- Verify `@patch` decorators use full module paths like `src.core.auth.validate_token`
- Check conftest.py has correct imports

### Template not found
- Flask paths are configured in `/src/app/app.py`
- Should automatically resolve to root-level `templates/` directory

## Key Differences from Old Structure

| Aspect | Old | New |
|--------|-----|-----|
| Entry point | `python app.py` | `python run.py` |
| Auth import | `from auth import ...` | `from src.core.auth import ...` |
| Database | `from database_service import ...` | `from src.core.database_service import ...` |
| Games | `from games.game_301 import ...` | `from src.games.game_301 import ...` |
| Main app | `from app import app` | `from src.app.app import app` |

## Performance Impact

- ✅ No performance impact
- ✅ Same code execution paths
- ✅ Compatibility wrappers have negligible overhead

## Future Improvements

1. **API Development** - Expand `/src/api/` with REST endpoints
2. **Microservices** - Easier to extract `/src/games/` or other modules into services
3. **Plugins** - Structure supports plugin architecture for additional games
4. **Documentation** - Each `/src/*/` can have README.md explaining that module

## Questions?

Refer to:
- `REFACTORING_COMPLETE.md` - Full refactoring details
- `tests/` - Working examples in test files
- Repository README - General project info