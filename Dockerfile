FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including PostgreSQL client for pg_isready
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        gcc \
        libpq-dev \
        postgresql-client \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Alembic configuration and migrations (needed before running migrations in entrypoint)
COPY alembic.ini .
COPY alembic ./alembic

# Copy application code
COPY src ./src
COPY run.py .
COPY database_models.py .

# Copy remaining application files
COPY . .

# Copy and set up entrypoint script that runs migrations
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Use custom entrypoint that runs Alembic migrations before starting the app
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
