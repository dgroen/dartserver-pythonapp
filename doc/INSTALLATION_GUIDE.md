# Installation Guide

This guide helps you install and run the Dartserver Python application.

## Prerequisites
- Python 3.10, 3.11, or 3.12
- PostgreSQL
- RabbitMQ
- Node.js (for bridge)
- Docker & Docker Compose (recommended)
- Git

## Quick Start (Recommended: Docker)

```bash
git clone <repo-url>
cd dartserver-pythonapp
docker-compose up
```

Access:
- Game Board: http://localhost:5000
- Control Panel: http://localhost:5000/control
- RabbitMQ: http://localhost:15672 (guest/guest)

## Quick Start Script (Alternative)

```bash
./run.sh
```
This script sets up a virtual environment, installs dependencies, and starts the app.

## Manual Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Edit as needed
alembic upgrade head
FLASK_DEBUG=True python run.py
```

## Deployment/Upgrade Steps
1. Stop running containers: `docker-compose down`
2. Rebuild and start: `docker-compose build && docker-compose up -d`
3. Verify: `docker-compose ps`

## Troubleshooting
- Ensure PostgreSQL and RabbitMQ are running and accessible.
- Check logs for errors.
- For WSO2 integration, see `docs/wso2is-7-config/`.
