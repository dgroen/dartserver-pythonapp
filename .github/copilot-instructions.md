# Repository Overview

## Quick Orientation — quick orientation

This repository is a Flask + Socket.IO web app (Darts game) with PostgreSQL and RabbitMQ integrations. Key components:

- Application entry: `run.py` which imports `app` and `socketio` from `src.app.app` and starts the server (SocketIO + eventlet).
- Core app code: `src/app/` (main routes and game flow) and `src/core/` (auth, helpers).
- Background consumers: `rabbitmq_consumer.py` and `bridge_nodejs_to_rabbitmq.js` for cross-process messaging.
- DB models/migrations: `database_models.py`, `alembic/` and helper `db_manage.py`.
- Tests and CI: `tests/`, `tox.ini`, and pyproject.toml (tooling configuration).

## Immediate developer workflows (commands you'll run)

- Run local dev server:
  - python -m venv .venv && . .venv/bin/activate
  - pip install -r requirements.txt
  - FLASK_DEBUG=True python run.py
    (The Dockerfile runs `python run.py` inside the container.)

- Run tests via tox (matrix for py310/311/312):
  - tox -e py311
  - tox -e py310,py311,py312
    Note: many tests are marked `rabbitmq` and require a running RabbitMQ instance or test fixture.

- Run linting / typing / security as configured in `tox.ini`:
  - tox -e lint
  - tox -e type
  - tox -e security

- Build & run with Docker (dev):
  - docker build -t dartserver:dev .
  - docker run --rm -p 5000:5000 --env-file .env dartserver:dev

## Important project-specific patterns & conventions

- Socket.IO + eventlet: the app uses `flask-socketio` with `eventlet`. Server startup happens in `run.py` using `socketio.run(...)`.

- Auth integration with WSO2 / introspection: `src/core/auth.py` performs token introspection and falls back to a userinfo endpoint. Expect role extraction from 'groups' (see logs). When modifying auth code, check `src/core/auth.py` for decorators used across endpoints.

- DB and SQLAlchemy v2 behaviors: code expects SQLAlchemy 2.x (see pyproject). Avoid using pandas-style `.isna()` on column expressions; use SQLAlchemy `col.is_(None)` / `col.isnot(None)` instead.

- Game persistence: `src/app/game_manager.py` handles game creation and saving; user identities are validated against WSO2-backed users — changes here affect `POST /api/game/start` flow and tests that simulate users.

- Optional/conditional imports and runtime-resilient design: several modules rely on optional system packages (TTS engines, system `aptda` bindings, etc.). See `pyproject.toml` and `tox.ini` for per-file lint exceptions (many files intentionally bypass strict rules).

## Integration points & external dependencies

- PostgreSQL: via `psycopg2-binary` and Alembic migrations in `alembic/`.
- RabbitMQ: used by `rabbitmq_consumer.py` and tests marked `rabbitmq` — tests will fail without RabbitMQ unless mocked.
- WSO2 / OAuth: auth uses introspection and userinfo endpoints; token flows are implemented in `src/core/auth.py` (look for `introspection` / `userinfo` usage).

## Code locations to inspect when making changes

- API endpoints & app wiring: `src/app/app.py`
- Auth decorators and role checks: `src/core/auth.py`
- Game logic and persistence: `src/app/game_manager.py`
- DB models: `database_models.py`
- Consumers / background tasks: `rabbitmq_consumer.py`, `bridge_nodejs_to_rabbitmq.js`
- Entrypoint and server options: `run.py`, `Dockerfile`

## Tests and test flavors

- Unit vs integration: `pytest` configuration in `pyproject.toml` sets markers (`unit`, `integration`, `rabbitmq`, `slow`). Use markers to select tests.
- Coverage: tox runs coverage and produces per-interpreter HTML reports under `build/coverage/html-<env>`.

## Safety and gotchas for automated changes

- Do not change the default `python3` in system images; Dockerfile pins an image `python:3.11-slim` and pyproject supports 3.10–3.12. Prefer adding interpreters to CI instead of altering system links.
- Beware of SQLAlchemy expression differences (v2) when editing filters and merges — prefer `is_(None)` for null checks.
- Many files are intentionally exempted from certain linters (see `pyproject.toml`)—respect per-file ignores when making automated fixes.

## If you're uncertain — quick triage steps

1. Run the dev server locally (`python run.py`) and reproduce the issue from the logs.
2. Check `logs` printed by `src/core/auth.py` for token introspection / userinfo traces.
3. If tests fail in `tox`, run the failing test directly under a virtualenv to get faster feedback.

---

If you'd like, I can merge this into an existing `.github/copilot-instructions.md` (none found) or expand any section with code snippets from the files listed above. What would you like me to prioritize next?
