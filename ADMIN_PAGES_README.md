# Admin Pages Implementation

This document describes the comprehensive admin pages feature implemented for the dartserver application.

## Overview

The admin pages provide a centralized dashboard for administrators to manage all aspects of the darts game system, including:

- User management (WSO2 integration)
- Game data management
- System testing (dartboard and TTS)
- User statistics and analytics
- Real-time session monitoring

## Features

### 1. Admin Dashboard (`/admin`)

The main admin home page provides navigation to all admin functions:

- **Dartboard Testing** - Test and calibrate GPIO pin mappings
- **TTS Testing** - Test text-to-speech functionality
- **User Management** - Manage WSO2 users, roles, and permissions
- **Game Management** - Manage paused games and archiving
- **Active Users** - Real-time monitoring of logged-in users
- **User Statistics** - View comprehensive user performance metrics

### 2. User Management (`/admin/users`)

Full WSO2 user administration interface:

**Features:**
- Search and list all WSO2 users
- Create new user accounts
- Update user information
- Set/reset user passwords
- Manage user roles (admin, gamemaster, player)
- Activate/deactivate user accounts

**API Endpoints:**
- `GET /api/admin/users/search?q={query}` - Search users
- `GET /api/admin/users` - List all users
- `POST /api/admin/users` - Create new user
- `PUT /api/admin/users/password` - Set user password
- `GET /api/admin/users/{user_id}/roles` - Get user roles
- `PUT /api/admin/users/{user_id}/roles` - Update user roles
- `PUT /api/admin/users/{user_id}/status` - Activate/deactivate user

### 3. TTS Testing (`/admin/tts-testing`)

Test text-to-speech functionality:

**Features:**
- Client-side speech synthesis testing
- Multiple voice selection
- Adjustable speech rate and pitch
- Preset game announcements
- Server-side TTS generation testing

**API Endpoints:**
- `POST /api/admin/tts/test` - Test server-side TTS generation

### 4. Game Management (`/admin/games`)

Manage game data and cleanup:

**Features:**
- List all paused games
- Remove all paused games
- Archive games by user and date range
- User selection dropdown
- Date range pickers

**API Endpoints:**
- `GET /api/admin/games/paused` - List paused games
- `DELETE /api/admin/games/paused` - Remove all paused games
- `POST /api/admin/games/archive` - Archive games by user/date

### 5. Active Users Monitoring (`/admin/active-users`)

Real-time user session monitoring:

**Features:**
- Real-time display of logged-in users
- Username, login time, last activity
- Socket.IO integration for live updates
- Manual refresh capability

**API Endpoints:**
- `GET /api/admin/active-sessions` - Get active user sessions

**Socket.IO Events:**
- `admin_active_sessions_update` - Real-time session updates

### 6. User Statistics (`/admin/statistics`)

Comprehensive user performance analytics:

**Features:**
- Total games played per user
- Win rate calculation
- Average score metrics
- Best game scores
- Sortable table columns
- Date range filtering
- CSV export functionality

**API Endpoints:**
- `GET /api/admin/statistics?start_date={date}&end_date={date}` - Get user statistics

## Security

All admin pages and API endpoints are protected with:

- `@login_required` - User must be authenticated
- `@role_required("admin")` - User must have admin role

## Technical Implementation

### File Structure

```
templates/
├── admin_home.html              # Admin dashboard
├── admin_dartboard_testing.html # Dartboard testing (existing)
├── admin_tts_testing.html       # TTS testing
├── admin_users.html             # User management
├── admin_games.html             # Game management
├── admin_active_users.html      # Active users monitoring
└── admin_statistics.html        # User statistics

src/app/
├── app_admin.py                 # Admin API blueprint
├── app_ui.py                    # UI routes (updated)
└── app.py                       # Main app (blueprint registration)
```

### Dependencies

- **Flask** - Web framework
- **Flask-SocketIO** - Real-time WebSocket communication
- **SQLAlchemy** - Database ORM
- **WSO2 Identity Server** - User authentication and management via SCIM2 API
- **PostgreSQL** - Database backend

### Database Queries

The admin pages use SQLAlchemy to query:

- `Player` - User accounts
- `GameResult` - Game records
- `Score` - Individual throw data

### WSO2 Integration

User management integrates with WSO2 IS via SCIM2 API:

- User creation/updates via `/scim2/Users`
- Role management via `/scim2/Groups`
- Password management via PATCH operations
- Uses admin credentials for API access

## Usage

### Accessing Admin Pages

1. Log in with an account that has the `admin` role
2. Navigate to `/admin`
3. Click on any admin function card to access that feature

### Creating a New User

1. Go to `/admin/users`
2. Click "Create New User"
3. Fill in username, password, email, and name
4. Click "Create User"
5. Optionally manage roles after creation

### Viewing Statistics

1. Go to `/admin/statistics`
2. Optionally set date range filters
3. Click column headers to sort
4. Click "Export to CSV" to download data

### Managing Games

1. Go to `/admin/games`
2. View paused games in the list
3. Click "Remove All Paused Games" to clean up
4. Or use the archive feature to archive specific user's games

### Monitoring Active Users

1. Go to `/admin/active-users`
2. View real-time list of logged-in users
3. Page auto-refreshes every 30 seconds
4. Click "Refresh Now" for manual update

## Design Consistency

All admin pages follow a consistent design pattern:

- Purple gradient background (#667eea to #764ba2)
- White content container with rounded corners
- Header with title and "Back to Admin" link
- Section cards with colored accent bars
- Responsive grid layouts
- Consistent button styling (primary, secondary, danger, success)
- Toast notifications for user feedback
- Modal dialogs for confirmations and forms

## Future Enhancements

Potential improvements:

- Bulk user import from CSV
- User activity logging
- Advanced game analytics
- System health monitoring
- Email notifications for admin actions
- Audit trail for admin operations
- Role-based permission granularity
- Custom report generation

## Testing

To test the admin pages:

1. Ensure WSO2 IS is running and configured
2. Create a test user with admin role
3. Start the Flask application
4. Navigate to `/admin` and test each feature
5. Verify API responses in browser developer tools
6. Check database for expected changes

## API Response Format

All admin API endpoints return JSON responses in this format:

```json
{
  "status": "success" | "error",
  "message": "Optional message",
  "data": { ... }  // Endpoint-specific data
}
```

## Error Handling

The admin pages include:

- Try-catch blocks for all API calls
- User-friendly error messages
- Proper HTTP status codes
- Logging of exceptions
- Graceful degradation for unavailable services

## Browser Compatibility

Tested and compatible with:

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## License

Same as the main dartserver application.
