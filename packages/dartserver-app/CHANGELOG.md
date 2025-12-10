# Changelog - dartserver-app

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-27

### Added
- Initial release with app module extracted from monolith
- Flask application factory with CORS and Swagger configuration
- GameManager orchestrating all game logic
- 11 SocketIO event handlers for real-time game updates
- 66 REST API routes organized into 10 logical domains
- Event handler registration system (dartserver_app/events.py)
- Route organization registry (dartserver_app/routes.py)
- Backward compatibility wrappers
- Comprehensive app tests (220+ LOC)
- Full documentation

### Routes
- **Auth** (6): login, callback, logout, profile, debug
- **UI** (15): dashboard, control, training, mobile views
- **Game** (13): game management and state APIs
- **Player** (6): player CRUD and statistics
- **Score** (1): score submission endpoint
- **Dartboard** (7): dartboard configuration
- **TTS** (6): text-to-speech configuration
- **Mobile** (7): mobile API management
- **Training** (4): training mode
- **Debug** (1): session utilities

### Features
- Real-time game state broadcasting via WebSocket
- RESTful API for all game operations
- OAuth2 authentication integration
- Role-based access control
- Swagger API documentation
- Mobile application support
- Training mode for practice

## [Unreleased]

### Planned
- Flask blueprint extraction for modular routes
- Middleware component extraction
- API versioning (v2)
- WebSocket message compression
- Rate limiting
