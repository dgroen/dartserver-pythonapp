# Phase 4 Quick Start Guide: Application Module

Get started with the `dartserver-app` package in 5 minutes.

## Installation

### From Local Development

```bash
# Install the package in development mode
cd packages/dartserver-app
pip install -e ".[dev]"
```

### Dependencies

The package automatically installs:
- `dartserver-core>=1.0.0` - Core authentication and database
- `dartserver-games>=1.0.0` - Game implementations
- `dartserver-services>=1.0.0` - Background services
- `Flask>=3.0.0` - Web framework
- `Flask-SocketIO>=5.3.0` - WebSocket support
- Plus additional Flask extensions (CORS, Flasgger, etc.)

## Quick Usage

### 1. Create Flask Application

```python
from dartserver_app import create_app

# Create app and socketio instance
app, socketio = create_app()

# Optional: Configure with custom settings
config = {
    "DEBUG": True,
    "JSON_SORT_KEYS": False,
}
app, socketio = create_app(config=config)
```

### 2. Access GameManager

```python
from dartserver_app import GameManager

# GameManager is created automatically by the factory
# but can also be instantiated directly:
game_manager = GameManager(socketio)

# Initialize a new game
game_manager.init_game(game_type="301", players=[...])

# Process a score
game_manager.process_score({"player": "John", "score": 20, "multiplier": "TRIPLE"})
```

### 3. Run the Application

```python
from dartserver_app import create_app

app, socketio = create_app()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
```

Or using the main src/app/app.py:

```bash
python src/app/app.py
```

## Testing

```bash
# Run all tests
pytest packages/dartserver-app/tests/ -v

# Run with coverage
pytest packages/dartserver-app/tests/ --cov=src/dartserver_app --cov-report=html

# Run specific test
pytest packages/dartserver-app/tests/test_core.py::test_app_factory_returns_tuple -v
```

## Architecture

```
┌──────────────────────────────────┐
│   Main Application               │
│   (src/app/app.py)               │
└─────────────┬──────────────────┘
              │ uses
              ↓
┌──────────────────────────────────┐
│   dartserver-app Package         │
│   ├── Factory (create_app)      │
│   ├── GameManager               │
│   ├── Routes (future)           │
│   ├── Events (future)           │
│   └── Utils                     │
└─────────────┬────────────────────┘
              │ depends on
              ↓
┌──────────────────────────────────┐
│   Supporting Packages            │
│   ├── dartserver-core            │
│   ├── dartserver-games           │
│   └── dartserver-services        │
└──────────────────────────────────┘
```

## Common Patterns

### Creating Multiple App Instances

```python
from dartserver_app import create_app

# Production app
prod_app, prod_socketio = create_app(config={"ENV": "production"})

# Test app
test_app, test_socketio = create_app(config={"TESTING": True})
```

### Accessing GameManager from Routes

```python
from flask import current_app

def some_route():
    game_manager = current_app.game_manager
    game_state = game_manager.get_game_state()
    return game_state
```

### Emitting to Clients via SocketIO

```python
@socketio.on("score_submitted")
def handle_score(data):
    # Process score
    app.game_manager.process_score(data)
    
    # Emit update to all connected clients
    socketio.emit("score_update", {
        "player": data["player"],
        "new_score": app.game_manager.get_player_score(data["player"]),
    }, broadcast=True)
```

## File Organization (Current)

```
src/dartserver_app/
├── __init__.py          - Public API exports
├── factory.py           - Flask app factory
├── game_manager.py      - Game orchestration
├── routes.py            - Route registration (stub)
├── events.py            - Event registration (stub)
├── utils.py             - Utility functions
└── routes/              - Future: individual route modules
    ├── auth.py          - Auth routes (future)
    ├── games.py         - Game routes (future)
    ├── players.py       - Player routes (future)
    ├── scores.py        - Score routes (future)
    └── admin.py         - Admin routes (future)
```

## Current Limitations / TODO

The dartserver-app package is currently in **foundation phase**:

- ✅ Factory pattern implemented
- ✅ GameManager moved to package
- ⏳ Routes still in src/app/app.py (72 routes to extract)
- ⏳ Events still in src/app/app.py (11 handlers to extract)
- ⏳ Middleware not yet extracted
- ⏳ Blueprints not yet implemented

These will be extracted incrementally in Phase 4.1+.

## Error Solutions

### Error: ImportError: cannot import name 'GameManager'

**Solution**: Make sure dartserver-app is installed:
```bash
cd packages/dartserver-app
pip install -e .
```

### Error: No module named 'dartserver_core'

**Solution**: Install dependencies:
```bash
pip install dartserver-core
```

### Error: TemplateNotFound

**Solution**: Ensure root_dir is correct when creating app:
```python
from pathlib import Path

root_dir = Path(__file__).parent.parent.parent  # Adjust as needed
app, socketio = create_app(root_dir=root_dir)
```

## Next Steps

After familiarizing yourself with the factory pattern:

1. **Extract Routes** - Organize 72 routes into blueprint modules
2. **Extract Events** - Move SocketIO handlers to dedicated module
3. **Add Middleware** - Extract custom middleware
4. **Create Tests** - Expand test coverage for routes and events

See PHASE4_COMPLETE.md for architectural details and future enhancement plans.

---

For detailed information, see:
- doc/PHASE4_COMPLETE.md - Full technical report
- packages/dartserver-app/ - Package source code
