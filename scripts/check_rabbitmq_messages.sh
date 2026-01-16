#!/bin/bash
# Check if RabbitMQ messages are being published

echo "Checking RabbitMQ for dartboard throw messages..."
echo ""

# Send a test throw
echo "1. Sending test throw..."
python3 /data/dartserver-pythonapp/scripts/dartboard_simulator.py \
  --client-id local_client_id \
  --client-secret local_client_secret

echo ""
echo "2. Checking Flask app logs for consumption..."
docker logs darts-app 2>&1 | tail -200 | grep -A 5 -B 2 -E "Received message|Dartboard throw|Mapped pins|Score processed"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Messages ARE being consumed!"
else
    echo ""
    echo "❌ Messages NOT being consumed. Debugging info:"
    echo ""
    echo "Consumer status:"
    docker logs darts-app 2>&1 | grep -E "RabbitMQ consumer|Connected to RabbitMQ|Waiting for messages"
    echo ""
    echo "Recent Flask logs:"
    docker logs darts-app 2>&1 | tail -20
fi
