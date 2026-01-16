#!/bin/bash
# Test RabbitMQ message consumption
# This script sends test throws and monitors the Flask app logs

set -e

echo "=================================================="
echo "RabbitMQ Consumer Test"
echo "=================================================="
echo ""

# Check if containers are running
if ! docker ps | grep -q darts-app; then
    echo "❌ darts-app container not running"
    echo "   Start it with: docker-compose -f docker-compose-localhost.yml up -d"
    exit 1
fi

if ! docker ps | grep -q darts-api-gateway; then
    echo "❌ darts-api-gateway container not running"
    echo "   Start it with: docker-compose -f docker-compose-localhost.yml up -d"
    exit 1
fi

echo "✓ Containers are running"
echo ""

# Start log monitoring in background
echo "Starting log monitor..."
echo "Looking for: RabbitMQ messages, Dartboard throws, Score processing"
echo "=================================================="
echo ""

# Create a temporary file for logs
LOGFILE=$(mktemp)
echo "Logs will be saved to: $LOGFILE"

# Start log tail in background
docker logs darts-app -f 2>&1 | grep --line-buffered -E "RabbitMQ|Received message|Dartboard throw|Mapped pins|Score processed|Error" > "$LOGFILE" &
LOG_PID=$!

# Give it a moment to start
sleep 2

# Send test throw
echo ""
echo "Sending test dartboard throw..."
echo "=================================================="
python3 scripts/dartboard_simulator.py \
    --client-id local_client_id \
    --client-secret local_client_secret &
SIMULATOR_PID=$!

# Wait for simulator to complete
wait $SIMULATOR_PID

# Give logs time to appear
sleep 3

# Show the logs
echo ""
echo "=================================================="
echo "Flask App Consumer Logs (last 20 lines):"
echo "=================================================="
tail -20 "$LOGFILE"

# Stop log monitoring
kill $LOG_PID 2>/dev/null || true

# Cleanup
rm -f "$LOGFILE"

echo ""
echo "=================================================="
echo "Test complete!"
echo ""
echo "What to look for:"
echo "  ✓ 'Received message: {...}'     - RabbitMQ message arrived"
echo "  ✓ 'Dartboard throw received'    - Message routed to handler"
echo "  ✓ 'Mapped pins (X,Y) to...'     - Pin mapping successful"
echo "  ✓ 'Score processed: X Y'        - Game manager processed score"
echo ""
echo "If you don't see these messages, check:"
echo "  1. RabbitMQ consumer started: docker logs darts-app | grep 'RabbitMQ consumer'"
echo "  2. Topic configuration: docker exec darts-app env | grep RABBITMQ_TOPIC"
echo "  3. RabbitMQ connection: docker logs darts-app | grep 'Connected to RabbitMQ'"
echo "=================================================="
