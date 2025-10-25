# GitHub Copilot Instructions for Dartserver Python App

## Project Overview

This is a Python web application for managing darts games (301, 401, 501, and Cricket) with RabbitMQ integration, real-time updates via WebSocket, and enterprise-grade OAuth2 authentication via WSO2 Identity Server. The application includes text-to-speech (TTS) announcements for game events and scores.

### Key Technologies

- **Backend**: Flask 3.x with Flask-SocketIO for WebSocket communication
- **Message Queue**: RabbitMQ via Pika for dart score events
- **Authentication**: OAuth2 with WSO2 Identity Server, JWT validation
- **Real-time**: Socket.IO for automatic UI refresh across all clients
- **Database**: SQLAlchemy with Alembic migrations
- **TTS**: Text-to-speech with pyttsx3 and gTTS for audio announcements
- **Testing**: pytest with pytest-cov, pytest-mock, pytest-asyncio
- **Linting**: Ruff, Black, isort, Flake8, Pylint, MyPy, Bandit
- **Package Management**: UV (uv pip) for fast dependency installation
- **Containerization**: Docker and Docker Compose

## Development Environment Setup

### Prerequisites

- Python 3.10 or newer (tested on 3.10, 3.11, 3.12)
- UV package manager (`pip install uv`) - used by Makefile for fast dependency installation
- Alternative: Traditional pip with `requirements.txt` (also supported)
- Docker and Docker Compose (for full stack)
- RabbitMQ (optional, included in Docker Compose)

### Quick Setup

**Using Makefile (recommended - uses UV for speed):**

```bash
# Install all development dependencies
make install-dev

# Set up pre-commit hooks and git hooks
make dev-setup

# Run tests to verify setup
make test

# Start the application
make run
```

**Alternative with traditional pip:**

```bash
# Install dependencies
pip install -r requirements.txt

# For development dependencies
pip install -e ".[dev,lint,test]"
```

### Environment Variables

Copy `.env.example` to `.env` and configure:

- **RabbitMQ**: `RABBITMQ_HOST`, `RABBITMQ_PORT`, `RABBITMQ_USER`, `RABBITMQ_PASSWORD`
- **Flask**: `FLASK_HOST`, `FLASK_PORT`, `FLASK_DEBUG`, `SECRET_KEY`
- **WSO2 Auth**: `WSO2_IS_URL`, `WSO2_CLIENT_ID`, `WSO2_CLIENT_SECRET`, `WSO2_REDIRECT_URI`
- **JWT**: `JWT_VALIDATION_MODE` (introspection or jwks)

## Code Style and Conventions

### Python Style

- **Line length**: 100 characters maximum
- **Formatter**: Black with default settings
- **Import sorting**: isort with Black profile
- **Type hints**: Preferred but not strictly enforced (MyPy checks enabled)
- **Docstrings**: Not required for all functions, but encouraged for public APIs

### Naming Conventions

- **Functions/methods**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private members**: Prefix with single underscore `_private_method`
- **Files**: `snake_case.py`

### Import Organization

Use isort's Black profile:

```python
# Standard library imports
import os
import sys

# Third-party imports
from flask import Flask, request
import pika

# Local imports
from game_manager import GameManager
from games.game_301 import Game301
```

### Code Quality Tools

Run these before committing:

```bash
make lint        # Check code style (Ruff, Black, isort, Flake8)
make lint-fix    # Auto-fix linting issues
make type        # Type checking with MyPy
make security    # Security checks with Bandit
make test        # Run all tests
```

Or run all at once:

```bash
make check-all   # Runs lint, type, security, and test
```

## Testing Requirements

### Test Organization

```
tests/
├── unit/              # Unit tests (fast, no external dependencies)
├── integration/       # Integration tests (may require RabbitMQ, database)
└── conftest.py        # Shared pytest fixtures
```

### Test Patterns

```python
import pytest
from unittest.mock import Mock, patch

# Unit test example
def test_game_301_initialization():
    """Test that Game301 initializes with correct starting score."""
    game = Game301(players=["Player1", "Player2"], starting_score=301)
    assert game.players[0]["score"] == 301
    assert game.players[1]["score"] == 301

# Integration test example
@pytest.mark.integration
@pytest.mark.rabbitmq
def test_rabbitmq_score_processing(rabbitmq_connection):
    """Test that scores from RabbitMQ are processed correctly."""
    # Test implementation
    pass
```

### Coverage Requirements

- **Minimum coverage**: 80% (enforced by pytest configuration)
- **Focus areas**: Game logic, authentication, API endpoints
- **Exclusions**: Examples, manual test scripts, alembic migrations

### Running Tests

```bash
make test              # All tests
make test-unit         # Unit tests only
make test-integration  # Integration tests only
make test-cov          # Tests with coverage report
make coverage          # Generate detailed coverage report
```

## Architecture and Key Components

### Core Components

1. **app.py**: Main Flask application with routes, WebSocket handlers, authentication
2. **game_manager.py**: Central game state manager (singleton pattern)
3. **auth.py**: OAuth2 authentication, JWT validation, role-based access control
4. **rabbitmq_consumer.py**: RabbitMQ message consumer for dart scores
5. **tts_service.py**: Text-to-speech service for audio announcements of scores and game events
6. **games/**: Game logic modules (game_301.py, game_cricket.py)
7. **database_models.py**: SQLAlchemy models
8. **database_service.py**: Database operations layer
9. **api_gateway.py**: API gateway with OAuth2 authentication

### Game Logic

- **Game Manager**: Singleton managing current game state
- **Game Types**: Each game type is a separate class (Game301, GameCricket)
- **State Management**: In-memory state with optional database persistence
- **Event Emission**: Automatic WebSocket broadcast on state changes

### Authentication Flow

1. User visits protected route → redirected to `/login`
2. `/login` redirects to WSO2 OAuth2 authorization endpoint
3. WSO2 redirects back to `/callback` with authorization code
4. App exchanges code for access token
5. Token validated via introspection or JWKS
6. User session created with roles/permissions
7. Protected routes check roles via `@require_role()` decorator

### Role-Based Access Control

- **Player**: Basic game participation (view board, submit scores)
- **Game Master**: Player + control panel access, game management
- **Admin**: Full system access (wildcard `*` permission)

## Common Tasks and Workflows

### Adding a New Game Type

1. Create new game class in `games/game_newtype.py`:

   ```python
   class GameNewType:
       def __init__(self, players, **options):
           self.players = players
           # Initialize game state

       def process_score(self, player_index, score, multiplier):
           # Process dart score
           pass

       def get_state(self):
           # Return current game state
           pass
   ```

2. Register in `game_manager.py`:

   ```python
   GAME_TYPES = {
       "301": Game301,
       "cricket": GameCricket,
       "newtype": GameNewType,  # Add new type
   }
   ```

3. Add tests in `tests/unit/test_game_newtype.py`
4. Update documentation

### Adding a New API Endpoint

1. Add route in `app.py`:

   ```python
   @app.route('/api/my-endpoint', methods=['POST'])
   @require_role(['GameMaster', 'Admin'])  # If authentication required
   def my_endpoint():
       data = request.get_json()
       # Process request
       emit_game_state()  # Trigger UI refresh if game state changed
       return jsonify({"status": "success"})
   ```

2. Add tests in `tests/unit/test_api.py` or `tests/integration/test_api_integration.py`
3. Document in README.md API Endpoints section

### Adding a New WebSocket Event

1. Add handler in `app.py`:

   ```python
   @socketio.on('my_event')
   def handle_my_event(data):
       # Process event
       emit_game_state()  # Broadcast updated state
   ```

2. Update client JavaScript in `static/js/main.js` or `static/js/control.js`
3. Add tests for the handler

### Modifying Game Logic

1. Update game class in `games/`
2. Update tests to match new behavior
3. Run `make test` to ensure no regressions
4. Test manually via control panel or API
5. Update documentation if behavior changes

## Security Considerations

### Authentication

- **Always use decorators**: `@require_login`, `@require_role(['GameMaster'])`, `@require_permission('control_panel')`
- **Session security**: Sessions use HttpOnly cookies, configurable secure flag
- **Token validation**: JWT tokens validated on every request via introspection or JWKS
- **No credentials in code**: Use environment variables for secrets

### Input Validation

- **API inputs**: Validate JSON schemas, sanitize user inputs
- **SQL Injection**: Use SQLAlchemy ORM, never raw SQL with user input
- **XSS Prevention**: Flask auto-escapes templates, use `|safe` carefully

### Secrets Management

- **Never commit secrets**: Use `.env` file (gitignored)
- **Baseline scanning**: `.secrets.baseline` tracks known false positives
- **Pre-commit hooks**: Detect-secrets hook prevents accidental commits

### Security Scanning

```bash
make security     # Run Bandit and Safety checks
```

- **Bandit**: Static security analysis for Python code
- **Safety**: Check dependencies for known vulnerabilities
- **Pre-commit**: Automated security checks on every commit

## Linting and Formatting

### Auto-formatting Workflow

The project uses a two-attempt approach in pre-commit hooks:

1. **First attempt**: Check-only mode (fails if issues found)
2. **Second attempt**: Auto-fix mode (automatically fixes issues)

### Manual Formatting

```bash
make lint-fix    # Auto-fix with Ruff, Black, isort
make lint        # Check without fixing
```

### Linter Configuration

All linting rules are defined in `pyproject.toml`:

- **Ruff**: Fast Python linter with extensive rule sets
- **Black**: Opinionated code formatter (line length 100)
- **isort**: Import sorting with Black profile
- **Flake8**: Additional style checks
- **Pylint**: Code quality and error detection
- **MyPy**: Static type checking (permissive mode)
- **Bandit**: Security issue detection

### Ignored Rules

See `pyproject.toml` `[tool.ruff.lint.ignore]` for exceptions:

- `S101`: pytest assert statements allowed
- `T201`: print statements allowed (logging preferred)
- `PLR0913`: Many arguments allowed for some functions
- See full list in `pyproject.toml`

## File Structure and Organization

```
dartserver-pythonapp/
├── app.py                    # Main application entry point
├── auth.py                   # Authentication and authorization
├── game_manager.py           # Game state management
├── rabbitmq_consumer.py      # RabbitMQ integration
├── database_models.py        # SQLAlchemy models
├── database_service.py       # Database operations
├── tts_service.py           # Text-to-speech service
├── api_gateway.py           # API gateway with OAuth2
├── games/                   # Game logic modules
│   ├── game_301.py
│   └── game_cricket.py
├── templates/               # Jinja2 HTML templates
├── static/                  # CSS, JavaScript, media
├── tests/                   # Test suite
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── examples/                # Example scripts and clients
├── helpers/                 # Verification and test scripts
├── docs/                    # Documentation
├── alembic/                 # Database migrations
├── .github/                 # GitHub configuration
├── pyproject.toml          # Project metadata and tool config
├── Makefile                # Development commands
├── docker-compose.yml      # Docker Compose configuration
└── requirements.txt        # Python dependencies
```

## Working with Dependencies

### Adding Dependencies

1. Add to `pyproject.toml` in appropriate section:

   ```toml
   dependencies = [
       "new-package>=1.0.0,<2.0.0",
   ]
   ```

2. Install with UV:

   ```bash
   make install-dev
   ```

3. Update `requirements.txt` if needed:
   ```bash
   uv pip freeze > requirements.txt
   ```

### Dependency Constraints

- Use version ranges: `>=1.0.0,<2.0.0`
- Pin major versions to prevent breaking changes
- Document reason for specific version constraints

## WebSocket and Real-time Updates

### Emitting Game State

Always emit game state after modifications:

```python
def emit_game_state():
    """Broadcast current game state to all connected clients."""
    socketio.emit('game_state', game_manager.get_state())
```

### Client-Side Updates

JavaScript clients auto-update on `game_state` events:

```javascript
socket.on("game_state", function (data) {
  // Update UI with new game state
  updateGameBoard(data);
});
```

## Database Migrations

### Creating Migrations

```bash
alembic revision --autogenerate -m "Description of changes"
alembic upgrade head
```

### Migration Best Practices

- Review auto-generated migrations before applying
- Test migrations on a copy of production data
- Include both upgrade and downgrade paths
- Document complex migrations in comments

## Docker Development

### Local Development Stack

```bash
make docker-up       # Start all services
make docker-logs     # View logs
make docker-down     # Stop all services
```

### Services

- **App**: Flask application (port 5000)
- **RabbitMQ**: Message broker (ports 5672, 15672)
- **WSO2 IS**: Identity server (port 9443)
- **API Gateway**: Secure API layer (port 8080)

## Documentation

### Updating Documentation

- **README.md**: User-facing documentation, getting started
- **docs/**: Detailed guides and architecture documentation
- **QUICK_START.md**: Fast onboarding guide
- **AUTHENTICATION_SETUP.md**: Complete auth configuration
- **Inline comments**: For complex logic only

### Documentation Style

- Use clear, concise language
- Include code examples
- Keep documentation in sync with code
- Use Markdown formatting consistently

## Troubleshooting Common Issues

### Tests Failing

1. Check if all dependencies are installed: `make install-dev`
2. Check if RabbitMQ is required: `@pytest.mark.rabbitmq` tests need RabbitMQ running
3. Run specific test: `pytest tests/unit/test_specific.py -v`

### Linting Errors

1. Auto-fix most issues: `make lint-fix`
2. Check remaining issues: `make lint`
3. Review `pyproject.toml` for ignored rules
4. Add `# noqa: <code>` for intentional violations (rare)

### Authentication Issues

1. Verify `.env` configuration
2. Check WSO2 IS is running and accessible
3. Verify client ID and secret are correct
4. Check callback URL matches WSO2 configuration

### WebSocket Not Working

1. Check browser console for connection errors
2. Verify Socket.IO client library is loaded
3. Test with `/test-refresh` endpoint
4. Check for CORS issues

## Best Practices Summary

1. **Always run tests** before committing: `make test`
2. **Use type hints** where they add clarity
3. **Follow the security guidelines** for authentication and input validation
4. **Emit game state** after any modification to trigger UI updates
5. **Write tests** for new features and bug fixes
6. **Use existing patterns** from the codebase
7. **Document complex logic** with clear comments
8. **Keep functions focused** and modular
9. **Use environment variables** for configuration
10. **Run pre-commit hooks** to catch issues early

## Getting Help

- **Documentation**: See `docs/` directory and README.md
- **Examples**: Check `examples/` for usage patterns
- **Tests**: Review test files for expected behavior
- **Makefile**: Run `make help` for available commands

## Continuous Integration

The project uses automated CI/CD:

- Pre-commit hooks run on every commit
- Full test suite runs on pull requests
- Coverage reports generated automatically
- Security scans run automatically

Simulate CI locally:

```bash
make ci    # Run full CI pipeline locally
```
