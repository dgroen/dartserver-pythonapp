# Modular Refactoring Plan

## Current Architecture Analysis

### Current Structure
```
dartserver-pythonapp/
├── src/
│   ├── app/              # Flask app, routes, game manager
│   ├── core/             # Auth, config, database, services
│   ├── games/            # Game logic (301, Cricket, etc)
│   └── api_gateway/      # API gateway (optional)
├── tests/
├── static/
├── templates/
└── ... (config, helpers, etc)
```

### Current Dependencies

```
src/app/app.py
  ├── Imports from: src/core/*, src/app/game_manager, src/app/mobile_service
  ├── Imports from: src/games/*

src/core/auth.py
  └── Independent (minimal external deps)

src/core/database_service.py
  ├── Imports: src/core/database_models, config

src/core/rabbitmq_consumer.py
  ├── Imports: src/app/game_manager

src/app/game_manager.py
  ├── Imports: src/core/database_*, src/games/*

src/games/*.py
  ├── Imports: src/core/database_models
  └── Independent from other games
```

## Proposed Module Structure

### Option A: Monorepo with Packages

**Best for:** Teams, rapid development, maintaining consistency

```
dartserver-monorepo/
├── packages/
│   ├── dartserver-core/
│   │   ├── src/dartserver_core/
│   │   │   ├── auth/
│   │   │   ├── config/
│   │   │   ├── database/
│   │   │   └── models/
│   │   ├── pyproject.toml
│   │   ├── tests/
│   │   └── README.md
│   │
│   ├── dartserver-games/
│   │   ├── src/dartserver_games/
│   │   │   ├── game_301/
│   │   │   ├── game_cricket/
│   │   │   ├── game_round_the_clock/
│   │   │   └── base/
│   │   ├── pyproject.toml
│   │   ├── tests/
│   │   └── README.md
│   │
│   ├── dartserver-services/
│   │   ├── src/dartserver_services/
│   │   │   ├── rabbitmq/
│   │   │   ├── dartboard/
│   │   │   ├── tts/
│   │   │   └── mobile/
│   │   ├── pyproject.toml
│   │   ├── tests/
│   │   └── README.md
│   │
│   └── dartserver-app/
│       ├── src/dartserver_app/
│       │   ├── app.py
│       │   ├── routes/
│       │   └── templates/
│       ├── pyproject.toml
│       ├── tests/
│       └── README.md
│
├── tox.ini (workspace-wide testing)
├── pyproject.toml (workspace root)
└── README.md
```

**Advantages:**
- Single git repo - easier collaboration
- Shared CI/CD pipeline
- Atomic commits across packages
- Simplified testing
- Single dependency version management

**Implementation:**
- Use tools/package manager workspaces (Python Poetry, Hatch)
- Run tests across all packages
- Publish individual packages to PyPI

---

### Option B: Separate Git Repos

**Best for:** Large teams, independent releases, clear ownership

```
github.com/yourorg/
├── dartserver-core/              (repo 1)
│   ├── src/dartserver_core/
│   ├── tests/
│   ├── pyproject.toml
│   └── .github/workflows/
│
├── dartserver-games/             (repo 2)
│   ├── src/dartserver_games/
│   ├── tests/
│   ├── pyproject.toml
│   └── .github/workflows/
│
├── dartserver-services/          (repo 3)
│   ├── src/dartserver_services/
│   ├── tests/
│   ├── pyproject.toml
│   └── .github/workflows/
│
└── dartserver-app/               (repo 4)
    ├── src/dartserver_app/
    ├── tests/
    ├── pyproject.toml
    ├── requirements.txt
    └── .github/workflows/
```

**Advantages:**
- Independent versioning
- Clear package ownership
- Separate CI/CD per package
- Can publish to PyPI independently
- Flexible release schedules

**Challenges:**
- Multiple git repos to manage
- Dependency version coordination
- Cross-package testing requires setup
- More complex local development

---

### Option C: Hybrid Approach (Recommended)

**Monorepo for core/games, separate app repo**

```
github.com/yourorg/
├── dartserver-core/              (public packages monorepo)
│   ├── packages/
│   │   ├── dartserver-core/
│   │   └── dartserver-games/
│   ├── pyproject.toml
│   └── tox.ini
│
└── dartserver-app/               (main application)
    ├── src/dartserver_app/
    ├── requirements.txt          (pins dartserver-core, dartserver-games)
    ├── pyproject.toml
    └── .github/workflows/
```

**Advantages:**
- Best of both worlds
- Easy integration testing in monorepo
- Clear separation of concerns
- Flexible independent versioning
- App can upgrade packages independently

**Recommended approach** - balances complexity and flexibility

---

## Module Breakdown Plan

### Core Package (dartserver-core)

**Modules:**
- `auth` - Authentication, WSO2 integration, RBAC decorators
- `config` - Configuration management
- `database` - SQLAlchemy models, database service, migrations
- `services` - Base service classes

**Dependencies:** Flask, SQLAlchemy, PyJWT, requests

**Exports:**
```python
from dartserver_core import (
    Config,
    init_db,
    get_session,
    login_required,
    role_required,
    Player,
    Game,
    GameHistory,
)
```

---

### Games Package (dartserver-games)

**Modules:**
- `base` - BaseGame abstract class
- `game_301` - 301/401/501 logic
- `game_cricket` - Cricket logic
- `game_round_the_clock` - Round the clock logic
- `game_bull_practice` - Bull practice logic

**Dependencies:** dartserver-core

**Exports:**
```python
from dartserver_games import (
    BaseGame,
    Game301,
    GameCricket,
    GameRoundTheClock,
    GameRegistry,
)
```

---

### Services Package (dartserver-services)

**Modules:**
- `rabbitmq` - RabbitMQ consumer
- `dartboard` - Dartboard mapping service
- `tts` - Text-to-speech service
- `mobile` - Mobile-specific service

**Dependencies:** dartserver-core, pika, gtts, pyttsx3

**Exports:**
```python
from dartserver_services import (
    RabbitMQConsumer,
    DartboardService,
    TTSService,
    MobileService,
)
```

---

### App Package (dartserver-app)

**Modules:**
- `routes` - All Flask routes
- `handlers` - Route handlers
- `socketio_events` - WebSocket event handlers
- `middleware` - Custom middleware

**Dependencies:** dartserver-core, dartserver-games, dartserver-services, Flask, Flask-SocketIO

**Usage:**
```python
from dartserver_app import create_app

app = create_app()
```

---

## Migration Strategy

### Phase 1: Preparation (Week 1)

**Tasks:**
1. Create dependency analysis
2. Define module boundaries
3. Set up new repository structure
4. Create pyproject.toml for each module
5. Document breaking changes

**Output:** Detailed module specs with clear APIs

### Phase 2: Extract Core Module (Week 2)

**Steps:**
1. Create `dartserver-core` repo/directory
2. Move auth, config, database_models
3. Create comprehensive tests
4. Document exports and breaking changes
5. Publish v1.0.0 to PyPI
6. Update main app to import from package

**Verification:**
- [ ] All core tests pass
- [ ] Package installable from PyPI
- [ ] Main app works with packaged core

### Phase 3: Extract Games Module (Week 3)

**Steps:**
1. Create `dartserver-games` repo/directory
2. Move games/ and refactor imports
3. Update to use dartserver_core package
4. Create base game class
5. Document game API
6. Publish v1.0.0 to PyPI

**Verification:**
- [ ] All game tests pass
- [ ] Game registry works
- [ ] Main app works with packaged games

### Phase 4: Extract Services (Week 4)

**Steps:**
1. Create `dartserver-services` repo/directory
2. Move services and refactor
3. Update to use packages
4. Create service initialization helpers
5. Publish v1.0.0 to PyPI

**Verification:**
- [ ] RabbitMQ consumer works
- [ ] All service tests pass
- [ ] Integration tests pass

### Phase 5: Update Main App (Week 5)

**Steps:**
1. Update imports in src/app/
2. Use packaged dependencies
3. Update requirements.txt/pyproject.toml
4. Run full integration tests
5. Update CI/CD pipelines
6. Release v2.0.0

**Verification:**
- [ ] All tests pass
- [ ] Linting clean
- [ ] All services work
- [ ] Documentation updated

---

## Example: Converting a Module

### Before: Monolith

```python
# src/games/game_301.py
from src.core.database_models import GameHistory
from src.core.config import Config

class Game301:
    def __init__(self, game_id):
        self.game_id = game_id
```

### After: Package

**File: packages/dartserver-games/src/dartserver_games/game_301/game.py**

```python
"""301/401/501 game logic."""

from dartserver_core import GameHistory, Config

class Game301:
    def __init__(self, game_id):
        self.game_id = game_id
```

**File: packages/dartserver-games/pyproject.toml**

```toml
[project]
name = "dartserver-games"
version = "1.0.0"
description = "Game logic for Darts application"
dependencies = [
    "dartserver-core>=1.0.0",
]

[project.optional-dependencies]
dev = ["pytest>=7.4.0"]
```

**File: packages/dartserver-games/src/dartserver_games/__init__.py**

```python
from .base import BaseGame
from .game_301 import Game301
from .game_cricket import GameCricket

__all__ = ["BaseGame", "Game301", "GameCricket"]
```

---

## Local Development Setup (Post-Refactoring)

### Monorepo Development

```bash
# Install all packages in editable mode
pip install -e packages/dartserver-core[dev]
pip install -e packages/dartserver-games[dev]
pip install -e packages/dartserver-services[dev]
pip install -e packages/dartserver-app[dev]

# Run tests for all packages
tox

# Run specific package tests
pytest packages/dartserver-games/tests/
```

### Multi-Repo Development

```bash
# Clone all repos
git clone <core-repo>
git clone <games-repo>
git clone <services-repo>
git clone <app-repo>

# Install in development mode
pip install -e dartserver-core[dev]
pip install -e dartserver-games[dev]
pip install -e dartserver-services[dev]
pip install -e dartserver-app[dev]
```

---

## CI/CD Changes

### Monorepo Pipeline

```yaml
name: Test All Packages
on: [push, pull_request]

jobs:
  test-core:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: pip install -e packages/dartserver-core[dev]
      - run: pytest packages/dartserver-core/tests/

  test-games:
    runs-on: ubuntu-latest
    needs: test-core
    steps:
      - uses: actions/checkout@v3
      - run: pip install -e packages/dartserver-core
      - run: pip install -e packages/dartserver-games[dev]
      - run: pytest packages/dartserver-games/tests/

  # Similar for other packages...
```

### Multi-Repo: Each repo has own workflow

---

## Tools & Resources

### Python Project Tools
- **Poetry** - Dependency management, monorepo support
- **Hatch** - Simple Python packaging
- **setuptools** - Traditional packaging
- **pdm** - Modern package manager

### Monorepo Tools
- **Turborepo** - (JavaScript, but concepts apply)
- **Lerna** - (JavaScript, not for Python)
- **Python Workspaces** - Poetry or uv support

### Recommended Tools for This Project
- **uv or Poetry** - Faster dependency resolution
- **Monorepo structure** with packages/
- **tox** - Test matrix across packages
- **pre-commit** - Shared hooks across packages

---

## Dependency Resolution Strategy

### Using Poetry (Recommended)

```toml
# root pyproject.toml
[tool.poetry.workspace]
members = [
    "packages/dartserver-core",
    "packages/dartserver-games",
    "packages/dartserver-services",
    "packages/dartserver-app",
]

# Automatically links packages in workspace
```

### Using Setup.py (Traditional)

Each package has independent setup.py, installed with:
```bash
pip install -e packages/dartserver-core
pip install -e packages/dartserver-games
```

---

## Decision Matrix

| Factor | Monorepo | Multi-Repo | Hybrid |
|--------|----------|-----------|--------|
| Ease of Setup | ⭐⭐⭐ | ⭐ | ⭐⭐ |
| Team Collaboration | ⭐⭐⭐ | ⭐ | ⭐⭐⭐ |
| Release Management | ⭐ | ⭐⭐⭐ | ⭐⭐ |
| Testing Speed | ⭐⭐⭐ | ⭐ | ⭐⭐ |
| Package Reusability | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |
| **Recommended** | Small teams | Large orgs | **This project** ✓ |

---

## Recommended Approach for Your Project

### Use Hybrid Model:

1. **dartserver-core** (monorepo packages)
   - auth, config, database_models, services

2. **dartserver-games** (monorepo packages)
   - All game logic

3. **dartserver-app** (separate repo)
   - Main Flask application
   - Depends on core and games packages

**Benefits:**
- Logical separation
- Easy testing
- Independent game updates
- Clear core/app boundary
- PyPI publishable packages
- Small teams can manage easily

---

## Next Steps

**To Proceed:**

1. **Clarify Requirements**
   - Which structure appeals to you? (Monorepo/Multi-repo/Hybrid)
   - Do you want to publish packages to PyPI?
   - Team size and collaboration style?

2. **Dependency Analysis**
   - Create detailed dependency map
   - Identify circular dependencies (if any)
   - Define module APIs

3. **Create Module Specs**
   - Write detailed specs for each module
   - Document exports and contracts
   - Create migration scripts

4. **Execute Refactoring**
   - Start with core module
   - Then games, then services
   - Finally update main app

5. **Set Up Publishing**
   - Configure PyPI or private registry
   - Set up versioning strategy
   - Create release workflow

---

## Estimated Timeline

- **Phase 1 (Prep)**: 3-5 days
- **Phase 2 (Core)**: 2-3 days
- **Phase 3 (Games)**: 2-3 days
- **Phase 4 (Services)**: 2-3 days
- **Phase 5 (App)**: 1-2 days
- **Total**: 2-3 weeks

---

## Risk Mitigation

1. **Keep master branch stable**
   - Use feature branches for refactoring
   - Tag current version before starting

2. **Comprehensive testing**
   - Unit tests for each module
   - Integration tests between modules
   - E2E tests for main app

3. **Documentation**
   - Document module APIs clearly
   - Create migration guides
   - Update architecture docs

4. **Rollback plan**
   - Keep old monolith importable as fallback
   - Tag each phase completion
   - Can revert to specific commits

---

## Questions to Answer

1. **Which structure fits your needs?** (Monorepo/Multi-repo/Hybrid)
2. **Will you publish to PyPI?** (public or private)
3. **Team size and collaboration style?**
4. **Timeline constraints?**
5. **Any existing CI/CD to consider?**
