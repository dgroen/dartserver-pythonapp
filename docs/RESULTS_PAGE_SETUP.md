# Game Results Page Setup Guide

This guide explains how to view game results when developing locally without authentication (with `AUTH_DISABLED=true`).

## Overview

The application now includes:

- ✅ **Web Results Page** at `/history` - View your game history with statistics
- ✅ **Mobile Results Page** at `/mobile/results` - Mobile-optimized game history and leaderboards
- ✅ **REST API Endpoints** for fetching game data
- ✅ **Navigation Links** from main pages to results

## Quick Start

### 1. Generate Sample Game Data

When running locally with `AUTH_DISABLED=true`, the bypass user is automatically created but has no games in the database. Generate sample games for testing:

```bash
# Run the sample data generator
python helpers/generate_sample_game_data.py
```

Output:

```
🎯 Darts Game - Sample Data Generator
==================================================
✅ Created bypass_user player (ID: 1)
✅ Created existing bypass_user player (ID: 1)
✅ Created opponent1 player
✅ Created opponent2 player
✅ Created 301 game (1h ago, winner: Bypass User)
✅ Created 501 game (3h ago, winner: Opponent 2)
✅ Created Cricket game (5h ago, winner: Bypass User)
✅ Created 301 game (24h ago, winner: Bypass User)
✅ Created 501 game (48h ago, winner: Opponent 1)

✨ Successfully created 5 sample games!

📊 You can now:
   1. Visit http://localhost:5000/history to see game history
   2. Visit http://localhost:5000/mobile/results to see mobile results
   3. Check API at http://localhost:5000/api/player/history
```

### 2. Access the Results Pages

#### Web Interface

- **Main Game Board**: <http://localhost:5000/>
  - New navigation links to History and Control Panel
  - 📊 Game History button
  - ⚙️ Control Panel button

- **Game History**: <http://localhost:5000/history>
  - Statistics dashboard (total games, wins, win rate, average score)
  - Filter by game type (301, 401, 501, Cricket)
  - Game cards showing all players and results

- **Control Panel**: <http://localhost:5000/control>
  - New navigation links at the top
  - 🎮 Main Game and 📊 Game History buttons

#### Mobile Interface

- **Mobile App Main**: <http://localhost:5000/mobile>
  - New Game Results action card
  - Link in navigation menu

- **Mobile Results**: <http://localhost:5000/mobile/results>
  - 📜 Your History tab - Past game results
  - 🔥 Active Games tab - Real-time leaderboard
  - Filter by game type
  - Statistics badges (total games, wins)

### 3. API Endpoints (with Authentication)

When `AUTH_DISABLED=true`, all endpoints are automatically available:

#### Get Player History

```bash
curl http://localhost:5000/api/player/history
# Response:
# {
#   "success": true,
#   "games": [
#     {
#       "game_session_id": "...",
#       "game_type": "301",
#       "started_at": "2025-01-15T10:30:00",
#       "finished_at": "2025-01-15T10:45:00",
#       "is_winner": true,
#       "players": [...]
#     }
#   ]
# }
```

#### Get Player Statistics

```bash
curl http://localhost:5000/api/player/statistics
# Response:
# {
#   "success": true,
#   "statistics": {
#     "total_games": 5,
#     "wins": 3,
#     "losses": 2,
#     "win_rate": 60.0,
#     "average_score": 150.5,
#     "by_game_type": {...}
#   }
# }
```

#### Get Active Games

```bash
curl http://localhost:5000/api/active-games
# Response:
# {
#   "success": true,
#   "games": [...]
# }
```

## Database Requirements

The sample data generator requires:

- ✅ Database URL configured in `.env` or environment
- ✅ Database tables created (run migrations)
- ✅ GameType records (301, 401, 501, Cricket)

```bash
# Ensure database is initialized
python db_manage.py init
```

## Running with AUTH_DISABLED

Set environment variable to enable auth bypass:

```bash
# Linux/Mac
export AUTH_DISABLED=true
python run.py

# Or in .env file
AUTH_DISABLED=true
```

## Features

### Statistics Dashboard

- Total games played
- Total wins
- Win rate percentage
- Average score
- Per-game-type breakdown

### Game Filtering

- Filter by game type (301, 401, 501, Cricket)
- View specific game types or all games
- Real-time leaderboard in mobile

### Game Information

- Start and end times
- All players involved
- Final scores
- Winner highlighting
- Double-out setting

### Mobile Features

- Tab-based navigation
- Touch-friendly interface
- Real-time active games leaderboard
- Statistics badges
- Responsive design

## Troubleshooting

### No results appearing?

1. Generate sample data: `python helpers/generate_sample_game_data.py`
2. Verify database connection is working
3. Check that games are in database: `SELECT COUNT(*) FROM gameresults;`

### Database errors?

1. Ensure DATABASE_URL is set in `.env`
2. Run migrations: `python db_manage.py init`
3. Verify PostgreSQL is running

### Auth bypass not working?

1. Set `AUTH_DISABLED=true` in environment
2. Restart Flask app
3. Check Flask logs for messages about auth being bypassed

## Development Notes

- Results are fetched from the database using SQLAlchemy ORM
- Games are grouped by game_session_id for multiplayer sessions
- Statistics are calculated on-demand for up-to-date data
- Mobile and web interfaces share the same API endpoints
- All timestamps use UTC timezone

## See Also

- [API Documentation](./API_GATEWAY_README.md)
- [Authentication Setup](./AUTHENTICATION_SETUP.md)
- [Database Documentation](./DATABASE_MIGRATIONS.md)
