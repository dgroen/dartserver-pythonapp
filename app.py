"""
Compatibility wrapper for app module - imports from new location
Re-exports the main Flask app and socketio for backward compatibility
"""

from src.app.app import (  # noqa: F401
    _get_default_game_manager,
    app,
    game_session_manager,
    on_score_received,
    socketio,
    start_rabbitmq_consumer,
)

# For backward compatibility, expose game_manager
# This will lazily initialize the default session
game_manager = None


def __getattr__(name):
    """Lazily get game_manager for backward compatibility"""
    if name == "game_manager":
        global game_manager
        if game_manager is None:
            game_manager = _get_default_game_manager()
        return game_manager
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

# If running as main, use the run.py script instead
if __name__ == "__main__":
    print("Please run 'python run.py' instead to start the application")
    import sys

    sys.exit(1)
