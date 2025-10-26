"""
Compatibility wrapper for api_gateway module - imports from new location
Starts the API Gateway Flask application with RabbitMQ integration
"""

import os

from src.api_gateway.app import app, logger, rabbitmq_publisher

if __name__ == "__main__":
    # Start Flask app
    host = os.getenv("API_GATEWAY_HOST", "0.0.0.0")
    port = int(os.getenv("API_GATEWAY_PORT", 8080))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"

    logger.info(f"Starting API Gateway on {host}:{port}")
    logger.info(f"Flask Debug Mode: {debug}")

    try:
        app.run(host=host, port=port, debug=debug, use_reloader=False, threaded=True)
    except KeyboardInterrupt:
        logger.info("Shutting down API Gateway")
    finally:
        # Clean up
        logger.info("Closing RabbitMQ connection")
        rabbitmq_publisher.close()
