# Refactoring Implementation Guide

## Recommended Approach: Hybrid Model

**Structure:** Monorepo for core/games + separate services & app repos

```
3 Git Repositories:
1. dartserver-monorepo (Core + Games)
2. dartserver-services (Services)  
3. dartserver-app (Main Application)
```

---

## Phase 1: Setup Infrastructure

### Step 1: Create Git Branches

```bash
# In current repo
git checkout -b refactor/phase1-core
git checkout -b refactor/phase2-games
git checkout -b refactor/phase3-services
git checkout -b refactor/phase4-app
```

### Step 2: Create Monorepo Directory Structure

```bash
# Create new monorepo structure
mkdir -p packages/dartserver-core/src/dartserver_core
mkdir -p packages/dartserver-core/tests
mkdir -p packages/dartserver-games/src/dartserver_games
mkdir -p packages/dartserver-games/tests
```

---

## Phase 2: Extract Core Module

### Step 1: Create Core Package

**Create: `packages/dartserver-core/pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "dartserver-core"
version = "1.0.0"
description = "Core authentication, config, and database for Darts application"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [{name = "Dartserver Team"}]

dependencies = [
    "Flask>=3.0.0,<4.0.0",
    "SQLAlchemy>=2.0.23,<3.0.0",
    "PyJWT>=2.8.0,<3.0.0",
    "requests>=2.31.0,<3.0.0",
    "python-dotenv>=1.0.0,<2.0.0",
    "psycopg2-binary>=2.9.9,<3.0.0",
    "alembic>=1.13.1,<2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.7.0",
]

[tool.setuptools.packages.find]
where = ["src"]
include = ["dartserver_core*"]
```

### Step 2: Move Core Files

```bash
# Copy core module files
cp src/core/auth.py packages/dartserver-core/src/dartserver_core/
cp src/core/config.py packages/dartserver-core/src/dartserver_core/
cp src/core/database_models.py packages/dartserver-core/src/dartserver_core/
cp src/core/database_service.py packages/dartserver-core/src/dartserver_core/

# Create __init__.py
cat > packages/dartserver-core/src/dartserver_core/__init__.py << 'INIT'
"""Dartserver Core - Authentication, Config, and Database."""

from .auth import (
    get_dynamic_redirect_uri,
    login_required,
    logout_user,
    permission_required,
    role_required,
)
from .config import Config
from .database_models import Game, GameHistory, Player
from .database_service import get_session, init_db, set_database_service

__all__ = [
    "Config",
    "get_session",
    "init_db",
    "set_database_service",
    "login_required",
    "role_required",
    "permission_required",
    "logout_user",
    "get_dynamic_redirect_uri",
    "Player",
    "Game",
    "GameHistory",
]
INIT
```

### Step 3: Update Imports

**In: `packages/dartserver-core/src/dartserver_core/auth.py`**

Change:
```python
from src.core.config import Config
```

To:
```python
from dartserver_core.config import Config
```

**In: `packages/dartserver-core/src/dartserver_core/database_service.py`**

Change:
```python
from src.core.database_models import ...
```

To:
```python
from dartserver_core.database_models import ...
```

### Step 4: Install Locally

```bash
cd packages/dartserver-core
pip install -e ".[dev]"

# Verify
python -c "from dartserver_core import Config, get_session; print('✓ Core package works')"
```

### Step 5: Update Main App to Use Package

**In: `src/app/app.py`**

Change:
```python
from src.core.auth import login_required, role_required
from src.core.config import Config
from src.core.database_models import Player
from src.core.database_service import get_session
```

To:
```python
from dartserver_core import (
    Config,
    Player,
    get_session,
    login_required,
    role_required,
)
```

### Step 6: Tests

```bash
# Copy tests
cp tests/unit/test_auth.py packages/dartserver-core/tests/

# Update imports in tests
sed -i 's/from src.core/from dartserver_core/g' packages/dartserver-core/tests/*.py

# Run tests
cd packages/dartserver-core
pytest tests/
```

---

## Phase 3: Extract Games Module

### Step 1: Create Games Package

**Create: `packages/dartserver-games/pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "dartserver-games"
version = "1.0.0"
description = "Game logic for Darts application (301, Cricket, etc)"
requires-python = ">=3.10"

dependencies = [
    "dartserver-core>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
]

[tool.setuptools.packages.find]
where = ["src"]
include = ["dartserver_games*"]
```

### Step 2: Create Base Game Class

**Create: `packages/dartserver-games/src/dartserver_games/base.py`**

```python
"""Base game class for all game types."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseGame(ABC):
    """Abstract base class for all game types."""

    game_type: str
    max_players: int = 6

    def __init__(self, game_id: str, players: List[str]):
        self.game_id = game_id
        self.players = players
        self.current_player_index = 0

    @abstractmethod
    def apply_score(self, player: str, score: int, multiplier: str) -> Dict[str, Any]:
        """Apply a score to the game."""
        pass

    @abstractmethod
    def get_state(self) -> Dict[str, Any]:
        """Get current game state."""
        pass

    @abstractmethod
    def is_finished(self) -> bool:
        """Check if game is finished."""
        pass

    @abstractmethod
    def get_winner(self) -> Optional[str]:
        """Get winner if game is finished."""
        pass
```

### Step 3: Move Game Files

```bash
# Copy game files
cp src/games/*.py packages/dartserver-games/src/dartserver_games/

# Remove base.py since we created a new one
rm packages/dartserver-games/src/dartserver_games/base.py

# Create __init__.py
cat > packages/dartserver-games/src/dartserver_games/__init__.py << 'INIT'
"""Dartserver Games - Game logic and implementations."""

from .base import BaseGame
from .game_301 import Game301
from .game_cricket import GameCricket
from .game_round_the_clock import GameRoundTheClock

__all__ = [
    "BaseGame",
    "Game301",
    "GameCricket",
    "GameRoundTheClock",
]
INIT
```

### Step 4: Update Game Imports

**In: `packages/dartserver-games/src/dartserver_games/game_301.py`**

Change:
```python
from src.core.database_models import GameHistory
```

To:
```python
from dartserver_core import GameHistory
```

### Step 5: Install

```bash
cd packages/dartserver-games
pip install -e ".[dev]"

# Verify
python -c "from dartserver_games import Game301; print('✓ Games package works')"
```

### Step 6: Update Main App

**In: `src/app/game_manager.py`**

Change:
```python
from src.games.game_301 import Game301
from src.games.game_cricket import GameCricket
```

To:
```python
from dartserver_games import Game301, GameCricket
```

---

## Phase 4: Extract Services Module

### Step 1: Create Services Package

**Create: `packages/dartserver-services/pyproject.toml`**

```toml
[project]
name = "dartserver-services"
version = "1.0.0"
description = "Background services for Darts application"

dependencies = [
    "dartserver-core>=1.0.0",
    "pika>=1.3.2,<2.0.0",
    "gtts>=2.5.0,<3.0.0",
    "pyttsx3>=2.90,<3.0.0",
]
```

### Step 2: Refactor RabbitMQ Consumer (Break Circular Dependency)

**Create: `packages/dartserver-services/src/dartserver_services/rabbitmq/consumer.py`**

```python
"""RabbitMQ consumer with event-based pattern."""

import json
import logging
from typing import Callable, Optional

import pika

logger = logging.getLogger(__name__)


class RabbitMQConsumer:
    """RabbitMQ consumer that emits events."""

    def __init__(self, host: str, user: str, password: str, exchange: str):
        self.host = host
        self.user = user
        self.password = password
        self.exchange = exchange
        self.on_score_received: Optional[Callable] = None

    def set_score_handler(self, callback: Callable) -> None:
        """Register callback for score events."""
        self.on_score_received = callback

    def consume_scores(self, topic: str = "darts.scores.#") -> None:
        """Start consuming score messages."""
        credentials = pika.PlainCredentials(self.user, self.password)
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=self.host, credentials=credentials)
        )

        channel = connection.channel()
        channel.exchange_declare(exchange=self.exchange, exchange_type="topic")

        result = channel.queue_declare(queue="", exclusive=True)
        queue_name = result.method.queue

        channel.queue_bind(exchange=self.exchange, queue=queue_name, routing_key=topic)

        def callback(ch, method, properties, body):
            try:
                score_data = json.loads(body)
                if self.on_score_received:
                    self.on_score_received(score_data)
            except Exception as e:
                logger.error(f"Error processing score: {e}")

        channel.basic_consume(queue=queue_name, on_message_callback=callback)
        channel.start_consuming()
```

### Step 3: Move Service Files

```bash
cp src/core/rabbitmq_consumer.py packages/dartserver-services/src/dartserver_services/rabbitmq/
cp src/core/dartboard_service.py packages/dartserver-services/src/dartserver_services/
cp src/core/tts_service.py packages/dartserver-services/src/dartserver_services/
cp src/app/mobile_service.py packages/dartserver-services/src/dartserver_services/
```

### Step 4: Install

```bash
cd packages/dartserver-services
pip install -e ".[dev]"
```

### Step 5: Update Main App

**In: `src/app/app.py`**

Change:
```python
from src.core.rabbitmq_consumer import RabbitMQConsumer
from src.core.tts_service import TTSService
from src.app.mobile_service import MobileService
```

To:
```python
from dartserver_services import RabbitMQConsumer, TTSService, MobileService
```

And update the consumer initialization:

Change:
```python
consumer = RabbitMQConsumer(...)
consumer.on_score_received = on_score_received
```

To:
```python
consumer = RabbitMQConsumer(...)
consumer.set_score_handler(on_score_received)
```

---

## Phase 5: Create Separate Repos

### Step 1: Create dartserver-monorepo

```bash
# Create new repo with monorepo structure
git init dartserver-monorepo
cd dartserver-monorepo

# Copy packages
cp -r ../dartserver-pythonapp/packages/* .

# Create root pyproject.toml
cat > pyproject.toml << 'EOF'
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "dartserver-monorepo"
version = "1.0.0"
description = "Dartserver core packages monorepo"

# Workspace configuration (Poetry example)
# [tool.poetry.packages]
# {include = "dartserver_core", from = "packages/dartserver-core/src"}
# {include = "dartserver_games", from = "packages/dartserver-games/src"}
