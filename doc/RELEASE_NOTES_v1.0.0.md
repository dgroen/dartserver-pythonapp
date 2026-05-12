# Release Notes - Version 1.0.0

**Release Date**: November 27, 2025

**Status**: ✅ PRODUCTION READY

## Overview

Dartserver v1.0.0 is the first major release of the Darts Game Server application, featuring a fully modularized architecture with independent, production-ready packages.

## Major Highlights

### 🎯 Modular Architecture

The monolithic application has been successfully refactored into 4 independent packages:

1. **dartserver-core** (1.0.0)
   - Core authentication, configuration, database services
   - 17 public exports, 850+ LOC, 400+ test LOC
   - Full OAuth2/OIDC support with WSO2 IS

2. **dartserver-games** (1.0.0)
   - Game implementations (301, Cricket, Round the Clock, Bull Practice)
   - 6 game types with configurable rules
   - 1,050+ LOC, 900+ test LOC

3. **dartserver-services** (1.0.0)
   - RabbitMQ consumer for message ingestion
   - Text-to-speech service (12+ languages)
   - Dartboard GPIO mapping and Mobile API management
   - 1,345+ LOC, 380+ test LOC

4. **dartserver-app** (1.0.0)
   - Flask web application factory
   - GameManager orchestration
   - 66 REST API routes across 10 domains
   - 11 real-time SocketIO event handlers
   - 1,353+ LOC, 240+ test LOC

### 📦 PyPI Ready

All packages configured for publishing to PyPI:
- ✅ Complete metadata with keywords and classifiers
- ✅ README with usage examples
- ✅ CHANGELOG tracking version history
- ✅ License files (MIT)
- ✅ Security documentation

### 🔒 Security & Quality

- ✅ Security scanning (Bandit, Safety)
- ✅ Comprehensive integration tests
- ✅ Linting (Ruff, Black)
- ✅ Type checking (Mypy)
- ✅ Code coverage reporting
- ✅ Dependency vulnerability checks

### 🚀 CI/CD Pipeline

- ✅ GitHub Actions workflows
- ✅ Automated testing on push/PR
- ✅ Security scanning on every commit
- ✅ Automated PyPI publishing on release
- ✅ Multi-version Python testing (3.10, 3.11)

### 📚 Documentation

- ✅ README for each package with API docs
- ✅ Production deployment guide
- ✅ Troubleshooting guide
- ✅ Security guidelines
- ✅ Repository separation plan
- ✅ Migration checklist

## Package Contents

### dartserver-core

**Exports**: 17 public APIs
- Authentication (login_required, role_required, permission_required)
- Configuration (Config class with environment support)
- Database models (Player, GameHistory, GameSession, GameScore, etc)
- Database service (init_db, get_session, set_database_service)

**Dependencies**: Flask, SQLAlchemy, PyJWT, requests, python-dotenv, psycopg2, alembic

**Tested with**: Python 3.10, 3.11, 3.12

### dartserver-games

**Exports**: 6 public APIs
- BaseGame (abstract base class)
- Game301, Game401, Game501 (300-series games)
- GameCricket (cricket game)
- GameRoundTheClock, GameBullPractice (training games)
- GameFactory (factory for creating games)

**Supported games**: 6 game types with configurable rules
- Double-out option
- Reset-on-miss option
- Configurable player count

**Dependencies**: dartserver-core

### dartserver-services

**Exports**: 5 public APIs
- RabbitMQConsumer (async score ingestion)
- TTSService (text-to-speech with dual engines)
- DartboardService (GPIO pin mapping)
- MobileService (device registration)
- DartboardMappingError (exception type)

**Features**:
- Auto-reconnection and heartbeat handling
- 12+ language support
- Bulk dartboard import
- API key and device lifecycle management

**Dependencies**: dartserver-core, pika, pyttsx3, gTTS

### dartserver-app

**Exports**: 5 public APIs
- create_app (Flask app factory)
- get_app_instance (app singleton)
- GameManager (game orchestration)
- register_events (SocketIO event registration)
- register_routes (route organization)

**API Endpoints**: 66 routes across 10 domains
- Auth (6), UI (15), Game (13), Player (6), Score (1)
- Dartboard (7), TTS (6), Mobile (7), Training (4), Debug (1)

**SocketIO Events**: 11 real-time event handlers
- Game state updates
- Player management
- Score submission
- Test message support

**Dependencies**: dartserver-core, dartserver-games, dartserver-services, Flask, Flask-SocketIO

## Breaking Changes

**NONE** ✅

- All existing functionality preserved
- Backward compatibility maintained
- Compatibility wrappers for existing imports
- No changes to public APIs

## Migration Guide

### From Monolithic to Modular

**Old imports still work**:
```python
# These still work
from src.core.auth import login_required
from src.app.game_manager import GameManager
```

**New recommended imports**:
```python
# Use new package imports
from dartserver_core import login_required
from dartserver_app import GameManager
```

### Installation

```bash
# Old way (monolithic)
pip install -e .

# New way (packages from PyPI)
pip install dartserver-core dartserver-games dartserver-services dartserver-app
```

## Performance Improvements

- ✅ Modular loading reduces memory footprint
- ✅ Selective dependency installation
- ✅ Better code organization improves maintainability
- ✅ Easier to optimize individual packages

## Bug Fixes

- ✅ Fixed circular dependencies (event-based callback pattern)
- ✅ Improved error handling in RabbitMQ consumer
- ✅ Enhanced session management
- ✅ Better TTS engine fallback

## Known Limitations

1. **Repository Separation**: Currently monorepo with separate PyPI packages
   - Plan for individual GitHub repositories in future releases
   - See REPO_SEPARATION.md for migration guide

2. **Database**: PostgreSQL only
   - No support for other databases yet
   - Future: SQLite support for development

3. **TTS Offline Mode**: Limited voices
   - Cloud mode (gTTS) has more options
   - Future: Additional offline engines

## Testing

All packages include:
- ✅ Unit tests
- ✅ Integration tests  
- ✅ Test coverage reports
- ✅ Mock utilities

**Coverage targets**:
- dartserver-core: 85%+
- dartserver-games: 90%+
- dartserver-services: 80%+
- dartserver-app: 75%+

## Future Roadmap

### Phase 5.1 (Q1 2025)
- [ ] Separate GitHub repositories
- [ ] Automated release coordination
- [ ] Enhanced monitoring

### Phase 5.2 (Q2 2025)
- [ ] Mobile app package
- [ ] Docker containerization
- [ ] Kubernetes deployment

### Phase 6 (Q3 2025)
- [ ] Plugin system
- [ ] Custom game types
- [ ] Advanced analytics

## Support & Community

- **Documentation**: See `doc/` directory
- **Issues**: GitHub Issues
- **Security**: See doc/SECURITY.md
- **Contributing**: See CONTRIBUTING.md (coming soon)

## Credits

Developed by the Darts Game Server team.

## License

All packages are licensed under MIT License.
See LICENSE file in each package for details.

---

## Installation

### PyPI (Coming Soon)

```bash
pip install dartserver-core==1.0.0
pip install dartserver-games==1.0.0
pip install dartserver-services==1.0.0
pip install dartserver-app==1.0.0
```

### Development

```bash
git clone https://github.com/letsplaydarts/dartserver-pythonapp.git
cd dartserver-pythonapp

# Install all packages in development mode
cd packages/dartserver-core && pip install -e . && cd ../..
cd packages/dartserver-games && pip install -e . && cd ../..
cd packages/dartserver-services && pip install -e . && cd ../..
cd packages/dartserver-app && pip install -e . && cd ../..
```

## Verification

Run this command to verify all packages are properly installed:

```bash
python -c "
from dartserver_core import Config
from dartserver_games import GameFactory
from dartserver_services import TTSService
from dartserver_app import create_app
print('✓ All packages imported successfully!')
print(f'✓ dartserver-core: {Config}')
print(f'✓ dartserver-games: {GameFactory}')
print(f'✓ dartserver-services: {TTSService}')
app, io = create_app()
print(f'✓ dartserver-app: {app}')
"
```
