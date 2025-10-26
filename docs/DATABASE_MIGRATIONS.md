# Database Migrations with Alembic

This project uses Alembic for database version control and migrations. The database runs in a Docker container using PostgreSQL 16.

## Quick Start

### 1. Start PostgreSQL Container

```bash
docker-compose up -d postgres
```

### 2. Run Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Check current migration status
alembic current

# View migration history
alembic history --verbose
```

## Creating New Migrations

### Auto-generate Migration from Model Changes

When you modify the SQLAlchemy models in `database_models.py`, Alembic can automatically detect the changes:

```bash
# Generate a new migration
alembic revision --autogenerate -m "Description of changes"

# Review the generated migration file in alembic/versions/
# Then apply it
alembic upgrade head
```

### Create Empty Migration (for data migrations or custom SQL)

```bash
alembic revision -m "Description of migration"
```

## Common Migration Commands

```bash
# Upgrade to latest version
alembic upgrade head

# Upgrade by one version
alembic upgrade +1

# Downgrade by one version
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade <revision_id>

# Show current version
alembic current

# Show migration history
alembic history

# Show SQL that would be executed (without running it)
alembic upgrade head --sql
```

## Database Configuration

The database connection is configured via the `DATABASE_URL` environment variable in `.env`:

```
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dartsdb
```

For Docker Compose, the URL uses the service name:

```
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/dartsdb
```

## Database Schema

The database consists of four main tables:

### 1. **player**

- Stores player information
- Fields: id, name, created_at

### 2. **gametype**

- Stores game type definitions (301, 401, 501, cricket)
- Fields: id, name, description, created_at

### 3. **gameresults**

- Stores per-player game session data
- Fields: id, game_type_id, player_id, player_order, start_score, final_score, is_winner, double_out_enabled, started_at, finished_at, game_session_id
- The `game_session_id` (UUID) groups all players in the same game

### 4. **scores**

- Stores individual throw data with complete replay capability
- Fields:
  - `id`: Primary key
  - `game_result_id`: Foreign key to gameresults
  - `player_id`: Foreign key to player
  - `throw_sequence`: Auto-incrementing counter per player for replay ordering
  - `turn_number`: Player's turn number in the game
  - `throw_in_turn`: Position in turn (1, 2, or 3)
  - `base_score`: The dartboard segment hit (0-20, 25)
  - `multiplier`: String representation (SINGLE, DOUBLE, TRIPLE, BULLSEYE, DOUBLE_BULLSEYE)
  - `multiplier_value`: Numeric multiplier (1, 2, 3)
  - `actual_score`: The score value for this throw
  - `score_before`: Player's score before this throw
  - `score_after`: Player's score after this throw
  - `dartboard_sends_actual_score`: Configuration setting at throw time
  - `is_bust`: Whether this throw resulted in a bust
  - `is_finish`: Whether this throw finished the game
  - `thrown_at`: Timestamp of the throw

## Docker Compose Integration

The PostgreSQL database is fully integrated into the Docker Compose setup:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: darts-postgres
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: dartsdb
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
```

## Running the Full Application

```bash
# Start all services (PostgreSQL, RabbitMQ, and the app)
docker-compose up -d

# View logs
docker-compose logs -f darts-app

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v
```

## Development Workflow

1. **Make changes to models** in `database_models.py`
2. **Generate migration**: `alembic revision --autogenerate -m "Description"`
3. **Review the migration** in `alembic/versions/`
4. **Apply migration**: `alembic upgrade head`
5. **Test your changes**
6. **Commit both** the model changes and migration file to version control

## Troubleshooting

### Connection Issues

If you can't connect to the database:

```bash
# Check if PostgreSQL container is running
docker ps | grep postgres

# Check PostgreSQL logs
docker logs darts-postgres

# Test connection
docker exec darts-postgres psql -U postgres -d dartsdb -c "SELECT 1"
```

### Reset Database

To completely reset the database:

```bash
# Stop and remove containers and volumes
docker-compose down -v

# Start PostgreSQL again
docker-compose up -d postgres

# Run migrations
alembic upgrade head
```

### View Database Tables

```bash
# List all tables
docker exec darts-postgres psql -U postgres -d dartsdb -c "\dt"

# Describe a specific table
docker exec darts-postgres psql -U postgres -d dartsdb -c "\d scores"

# Query data
docker exec darts-postgres psql -U postgres -d dartsdb -c "SELECT * FROM player;"
```

## Migration Best Practices

1. **Always review auto-generated migrations** before applying them
2. **Test migrations** on a development database first
3. **Keep migrations small and focused** on one change at a time
4. **Write descriptive migration messages**
5. **Never edit applied migrations** - create a new migration instead
6. **Commit migrations to version control** along with model changes
7. **Document complex migrations** with comments in the migration file

## Backup and Restore

### Backup

```bash
# Backup entire database
docker exec darts-postgres pg_dump -U postgres dartsdb > backup.sql

# Backup specific table
docker exec darts-postgres pg_dump -U postgres -t scores dartsdb > scores_backup.sql
```

### Restore

```bash
# Restore from backup
docker exec -i darts-postgres psql -U postgres dartsdb < backup.sql
```
