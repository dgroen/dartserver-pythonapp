"""
Compatibility wrapper for app module - imports from new location
Re-exports the main Flask app and socketio for backward compatibility
"""

from src.app.app import (  # noqa: F401
    app,
    game_manager,
    on_score_received,
    socketio,
    start_rabbitmq_consumer,
)

# If running as main, use the run.py script instead
if __name__ == "__main__":
    print("Please run 'python run.py' instead to start the application")
    import sys

    sys.exit(1)
