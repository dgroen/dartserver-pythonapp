# Darts Game API - Swagger Documentation

## Overview
The Darts Game API now includes full OpenAPI/Swagger documentation for easy testing and integration.

## Access Points

### Swagger UI (Interactive Documentation)
- **URL**: `http://localhost:5000/api/docs/`
- **Description**: Interactive web interface to explore and test all API endpoints
- **Features**: 
  - Try out API calls directly from the browser
  - View request/response schemas
  - See example payloads
  - Test authentication and parameters

### API Specification (JSON)
- **URL**: `http://localhost:5000/apispec.json`
- **Description**: OpenAPI 2.0 specification in JSON format
- **Use Cases**:
  - Import into Postman, Insomnia, or other API clients
  - Generate client SDKs
  - Automated testing
  - API documentation generation

## API Endpoints Documented

### UI Endpoints
1. **GET /** - Main game interface
2. **GET /control** - Control panel interface
3. **GET /test-refresh** - Test refresh endpoint

### Game Management
4. **GET /api/game/state** - Get current game state
5. **POST /api/game/new** - Start a new game

### Player Management
6. **GET /api/players** - Get all players
7. **POST /api/players** - Add a new player
8. **DELETE /api/players/{id}** - Remove a player

### Score Management
9. **POST /api/score** - Submit a score

## Features

### Comprehensive Documentation
- All endpoints include detailed descriptions
- Request/response schemas with data types
- Example payloads for easy testing
- Parameter validation rules
- Error response documentation

### Organized by Tags
- **UI**: User interface endpoints
- **Game**: Game state and management
- **Players**: Player management operations
- **Score**: Score submission and tracking

### Game Types Supported
- 301 (standard)
- 401
- 501
- Cricket

### Configuration Options
- Double-out rule (enabled/disabled)
- Custom starting scores
- Multiple players support

## Testing

A test script is provided to verify all endpoints:

```bash
# Start the server
./run.sh

# In another terminal, run the test script
source .venv/bin/activate
python test_swagger.py
```

## Implementation Details

### Dependencies Added
- `flasgger==0.9.7.1` - Swagger UI integration for Flask

### Files Modified
- `app.py` - Added Swagger configuration and OpenAPI docstrings
- `requirements.txt` - Added flasgger dependency

### Configuration
The Swagger UI is configured with:
- Custom title: "Darts Game API"
- Version: 1.0.0
- Description: Complete API for managing darts games
- Custom UI path: `/api/docs/`
- Spec path: `/apispec.json`

## Usage Examples

### Using Swagger UI
1. Start the server: `./run.sh`
2. Open browser: `http://localhost:5000/api/docs/`
3. Click on any endpoint to expand
4. Click "Try it out" button
5. Fill in parameters (if required)
6. Click "Execute" to test the endpoint
7. View the response

### Using curl with API Spec
```bash
# Get API specification
curl http://localhost:5000/apispec.json

# Get game state
curl http://localhost:5000/api/game/state

# Start new game
curl -X POST http://localhost:5000/api/game/new \
  -H "Content-Type: application/json" \
  -d '{"game_type": "501", "double_out": true}'

# Add player
curl -X POST http://localhost:5000/api/players \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe"}'

# Submit score
curl -X POST http://localhost:5000/api/score \
  -H "Content-Type: application/json" \
  -d '{"player_id": 0, "value": 20, "multiplier": 3, "type": "TRIPLE"}'
```

## Benefits

1. **Easy Testing**: Test all endpoints directly from the browser
2. **Clear Documentation**: All parameters and responses clearly documented
3. **Integration Ready**: Export OpenAPI spec for client generation
4. **Developer Friendly**: Interactive examples and schemas
5. **Standards Compliant**: OpenAPI 2.0 specification

## Next Steps

To extend the documentation:
1. Add more detailed error responses
2. Include authentication/authorization if needed
3. Add rate limiting documentation
4. Include WebSocket endpoint documentation
5. Add more example scenarios

## Support

For issues or questions about the API:
- Check the Swagger UI for endpoint details
- Review the test script for usage examples
- Examine the OpenAPI spec for complete schema definitions