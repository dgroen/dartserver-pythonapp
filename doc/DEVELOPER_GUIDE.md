# Developer Guide

## Development Environment Setup

### Prerequisites

- Python 3.10+
- Docker & Docker Compose
- Git
- Code editor (VS Code recommended)

### Quick Setup

```bash
# Clone and setup
git clone <repository-url>
cd dartserver-pythonapp

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate

# Install all dependencies (including dev tools)
pip install -e ".[dev,lint,test]"

# Start services
docker-compose up -d

# Configure environment
cp .env.example .env

# Initialize database
alembic upgrade head

# Start development server
FLASK_DEBUG=True python run.py
```

Access: http://localhost:5000

## Project Structure

```
dartserver-pythonapp/
├── src/                          # Main application code
│   ├── app/
│   │   ├── app.py               # Flask app and routes
│   │   ├── game_manager.py      # Game logic orchestration
│   │   └── mobile_service.py    # Mobile-specific features
│   ├── core/
│   │   ├── auth.py              # Authentication & RBAC
│   │   ├── config.py            # Configuration management
│   │   ├── database_models.py   # SQLAlchemy models
│   │   ├── database_service.py  # Database operations
│   │   ├── rabbitmq_consumer.py # RabbitMQ integration
│   │   ├── dartboard_service.py # Dartboard calibration
│   │   └── tts_service.py       # Text-to-speech
│   └── games/
│       ├── game_301.py          # 301/401/501 logic
│       ├── game_cricket.py      # Cricket logic
│       ├── game_round_the_clock.py
│       └── game_bull_practice.py
├── tests/
│   ├── unit/                    # Unit tests
│   └── integration/             # Integration tests
├── templates/                   # HTML templates
├── static/
│   ├── css/                     # Stylesheets
│   ├── js/                      # JavaScript
│   └── icons/                   # PWA icons
├── alembic/                     # Database migrations
├── helpers/                     # Utility scripts
├── doc/                         # Documentation
├── requirements.txt
├── pyproject.toml
├── tox.ini
└── Dockerfile
```

## Code Conventions

### Python Style

- **Formatter**: Black (100 char line length)
- **Linter**: Ruff
- **Type Checking**: MyPy
- **Security**: Bandit
- **Pre-commit Hooks**: Enabled

### Running Linting

```bash
# All checks
tox -e lint

# Individual checks
ruff check .
black --check .
mypy .
bandit -r .
```

### Auto-format Code

```bash
black .
ruff check . --fix
isort .
```

## Testing

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific test file
pytest tests/unit/test_game_301.py

# With markers
pytest -m unit
pytest -m integration
pytest -m rabbitmq

# Matrix testing
tox
```

### Writing Tests

```python
# tests/unit/test_example.py
import pytest
from src.core.database_models import Player


class TestPlayer:
    def test_player_creation(self, db_session):
        player = Player(name="Test Player")
        db_session.add(player)
        db_session.commit()

        assert player.name == "Test Player"
        assert player.id is not None
```

### Test Coverage

- Target: >85%
- Run: `pytest --cov=. --cov-report=term-missing`
- HTML Report: `build/coverage/html/`

## Database

### Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head

# View migration history
alembic history
```

### Models

Database models in `src/core/database_models.py`:

```python
from sqlalchemy import Column, String, Integer
from src.core.database_models import Base

class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
```

## Authentication System

### Architecture

```
User Login
    ↓
WSO2 Authorization Endpoint
    ↓
User Approves/Rejects
    ↓
Redirect to /callback with code
    ↓
Exchange code for token
    ↓
Validate token (introspection or JWKS)
    ↓
Extract user info and roles
    ↓
Create session
    ↓
Redirect to game
```

### Adding Permissions

```python
# In src/core/auth.py
@permission_required('play_game')
def game_endpoint():
    return jsonify({"status": "ok"})
```

### Role Configuration

Roles defined in WSO2. Extracted from token:

```python
# In src/core/auth.py
roles = token_payload.get('groups', [])
```

## API Development

### Adding Endpoints

```python
# In src/app/app.py
@app.route('/api/custom', methods=['POST'])
@login_required
def custom_endpoint():
    data = request.get_json()
    return jsonify({"result": data})
```

### WebSocket Events

```python
# In src/app/app.py
from flask_socketio import emit

@socketio.on('custom_event')
def handle_custom(data):
    emit('response', {'data': data}, broadcast=True)
```

## Git Workflow

### Feature Development

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes and commit
git add .
git commit -m "Add my feature"

# Push to remote
git push origin feature/my-feature

# Pre-commit checks will run automatically
# Fix any issues and commit again
```

### Pre-commit Hooks

Automatically runs on commit:
- Black formatting
- Ruff linting
- MyPy type checking
- Bandit security scan

### Common Issues

```bash
# Pre-commit errors - auto-fix and recommit
git add .
git commit -m "Fix linting issues"

# Force commit (not recommended)
git commit --no-verify
```

## Documentation

- **Code**: Use docstrings (Google style)
- **API**: Auto-generated via Swagger at /apidocs
- **Changes**: Update docs/ folder

### Example Docstring

```python
def calculate_score(score, multiplier):
    """
    Calculate final dart score with multiplier.

    Args:
        score: Base score (1-20, 25 for bull)
        multiplier: SINGLE, DOUBLE, TRIPLE, BULL, DBLBULL

    Returns:
        Final score value

    Raises:
        ValueError: If score or multiplier invalid
    """
```

## Deployment

### Docker Build

```bash
docker build -t dartserver:latest .
docker-compose -f docker-compose-wso2.yml up -d
```

### Local Testing

```bash
# Test with auth
docker-compose -f docker-compose-wso2.yml up -d

# Test without auth
docker-compose up -d
```

### Production Checklist

- [ ] All tests passing
- [ ] Linting clean (tox -e lint)
- [ ] Type checks pass (tox -e type)
- [ ] Security checks pass (tox -e security)
- [ ] Coverage >85%
- [ ] Pre-commit passes
- [ ] Environment variables set
- [ ] Database migrations applied
- [ ] SSL certificates configured
- [ ] Nginx reverse proxy configured
- [ ] Systemd service created

## Common Tasks

### Add New Game Type

1. Create `src/games/game_mynewgame.py`
2. Implement base class methods
3. Add to game registry
4. Create tests in `tests/`
5. Update documentation

### Add Authentication Flow

1. Modify `src/core/auth.py`
2. Add decorators as needed
3. Test with WSO2
4. Document changes

### Integrate New Service

1. Create in `src/core/`
2. Add initialization in `app.py`
3. Add error handling
4. Write tests
5. Add to documentation

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Import errors | Verify virtual env activated |
| Database locked | Restart db container |
| WebSocket fails | Check firewall/proxy |
| Tests fail | Run with -v flag for details |

## Resources

- Flask Docs: https://flask.palletsprojects.com/
- SQLAlchemy: https://www.sqlalchemy.org/
- pytest: https://docs.pytest.org/
- Ruff: https://docs.astral.sh/ruff/
