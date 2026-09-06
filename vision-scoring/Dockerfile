FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src ./src
RUN pip install --no-cache-dir -e .

RUN mkdir -p /app/calibration
VOLUME ["/app/calibration"]

EXPOSE 5901

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:5901/health || exit 1

# Single worker: SessionManager keeps calibration/detector/throw state in
# memory, per board_id -- multiple worker processes would each have their own
# inconsistent copy of that state. Revisit if this ever needs to scale out
# (e.g. move session state to Redis).
CMD ["gunicorn", "--bind", "0.0.0.0:5901", "--workers", "1", "vision_scoring.server:app"]
