#!/usr/bin/env python3
"""
Main entry point for the Darts Game Web Application
Uses legacy src.app.app until route migration is complete
"""

import logging
import os
import ssl
import sys
import time
from pathlib import Path

# Use legacy app which has all routes registered
from eventlet import wsgi
from src.app.app import app, socketio, start_rabbitmq_consumer

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )
    # Reduce request log noise from Werkzeug in dev
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logger = logging.getLogger(__name__)

    try:
        # Start RabbitMQ consumer before starting the Flask app
        logger.info("Starting RabbitMQ consumer...")
        start_rabbitmq_consumer()

        # Run the Flask application with SocketIO support
        # Bind to 0.0.0.0 to make it accessible from nginx on the Docker network
        # This is safe as it's behind a reverse proxy and not exposed directly
        host = os.getenv("FLASK_HOST", "0.0.0.0")  # nosec: B104
        port = int(os.getenv("FLASK_PORT", 5000))
        debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
        use_ssl = os.getenv("FLASK_USE_SSL", "False").lower() == "true"

        logger.info(f"Starting Flask-SocketIO server on {host}:{port}")
        logger.info(f"Debug mode: {debug}")
        logger.info(f"Using legacy app with {len(list(app.url_map.iter_rules()))} routes")

        # SSL Configuration
        ssl_context = None
        protocol = "http"

        if use_ssl:
            ssl_dir = Path(__file__).parent / "ssl"
            cert_file = ssl_dir / "cert.pem"
            key_file = ssl_dir / "key.pem"

            if cert_file.exists() and key_file.exists():
                # For Flask-SocketIO, pass ssl_context as tuple (cert, key)
                ssl_context = (str(cert_file), str(key_file))
                protocol = "https"

                # Apply SSL error handling patch
                def patch_eventlet_ssl_error_handling():
                    """
                    Monkey-patch eventlet's WSGI handler to suppress SSL protocol errors
                    """
                    original_handle = wsgi.HttpProtocol.handle
                    ssl_error_state = {"count": 0, "last_logged": 0.0}

                    def custom_handle(self):
                        try:
                            original_handle(self)
                        except ssl.SSLError as e:
                            error_msg = str(e)
                            if "HTTP_REQUEST" in error_msg or "http request" in error_msg.lower():
                                current_time = time.time()
                                ssl_error_state["count"] += 1

                                if current_time - ssl_error_state["last_logged"] >= 10:
                                    print("")
                                    print("⚠️  SSL Protocol Mismatch Detected")
                                    print(
                                        f"   {ssl_error_state['count']} HTTP request(s) to HTTPS server (rejected)",
                                    )
                                    print("   Clients must use HTTPS URLs to connect")
                                    print("")
                                    ssl_error_state["last_logged"] = current_time
                                    ssl_error_state["count"] = 0
                                return
                            raise
                        except Exception:
                            raise

                    wsgi.HttpProtocol.handle = custom_handle

                patch_eventlet_ssl_error_handling()
                logger.info("✅ SSL error handling patch applied")

                print("=" * 80)
                print("🔒 Starting Darts Game Server with SSL/HTTPS")
                print(f"   URL: {protocol}://{host}:{port}")
                print("=" * 80)
                print("⚠️  IMPORTANT: Using self-signed SSL certificate")
                print("   - Your browser will show a security warning")
                print("   - This is expected for self-signed certificates")
                print("   - Click 'Advanced' and 'Proceed' to continue")
                print("")
                print("⚠️  SSL ERROR TROUBLESHOOTING:")
                print("   - If you see 'SSL: HTTP_REQUEST' errors, clients are")
                print("     using HTTP instead of HTTPS")
                print("   - Make sure to access the application using: https://")
                print(f"   - Correct URL: {protocol}://{host}:{port}")
                print(f"   - Wrong URL:   http://{host}:{port}")
                print("")
                print("   To disable SSL for development:")
                print("   - Set FLASK_USE_SSL=False in .env file")
                print("=" * 80)
            else:
                logger.warning("SSL is enabled but certificates not found!")
                logger.warning(f"Expected files:")
                logger.warning(f"  - Certificate: {cert_file}")
                logger.warning(f"  - Private Key: {key_file}")
                logger.warning("Falling back to HTTP (insecure)...")
                use_ssl = False

        if not use_ssl:
            print("=" * 80)
            print("🌐 Starting Darts Game Server (HTTP - No SSL)")
            print(f"   URL: {protocol}://{host}:{port}")
            print("=" * 80)
            print("⚠️  Running without SSL encryption")
            print("   For production, enable SSL by:")
            print("   1. Set FLASK_USE_SSL=True in .env")
            print("   2. Generate certificates: ./helpers/generate_ssl_certs.sh letsplaydarts.eu")
            print("=" * 80)

        # Run the Flask application with SocketIO support
        # Disable reloader to avoid hanging issues in Docker
        socketio.run(
            app,
            host=host,
            port=port,
            debug=debug,
            allow_unsafe_werkzeug=True,
            use_reloader=False,
            ssl_context=ssl_context,
        )
    except Exception:
        logger.exception("Failed to start application")
        sys.exit(1)
