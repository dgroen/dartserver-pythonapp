"""
Compatibility wrapper for app module - imports from dartserver_app package
Re-exports the main Flask app and socketio for backward compatibility
"""

from dartserver_app import create_app

app, socketio = create_app()
game_manager = app.game_manager

if __name__ == "__main__":
    print("Use run.py to start the main application")
    print("Please run 'python run.py' instead to start the application")
