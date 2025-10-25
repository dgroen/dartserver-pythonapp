# WSO2 User Search Feature

## Overview

The user search feature allows Game Masters to search for and select registered WSO2 users when adding players to a game, instead of manually typing usernames.

## Features

- **Autocomplete Search**: As you type in the player name field, matching users from WSO2 are displayed
- **Keyboard Navigation**: Use arrow keys to navigate suggestions, Enter to select, Escape to close
- **Real-time Search**: Search results update as you type with a 300ms debounce to avoid excessive API calls
- **Permission-based**: Only users with `player:add` permission (Game Master or Admin roles) can search users

## Usage

### Control Panel

1. Navigate to the Control Panel at `/control`
2. In the "Players" section, start typing in the "Search or enter player name" field
3. A dropdown will appear showing matching WSO2 users
4. You can:
   - Click on a user to select them
   - Use arrow keys (↑/↓) to navigate the list
   - Press Enter to select the highlighted user
   - Press Escape to close the dropdown
   - Continue typing to refine the search
5. Click "Add Player" to add the selected user to the game

### API Endpoint

**Endpoint**: `GET /api/users/search`

**Query Parameters**:
- `q` (optional): Search term (username or name)
- `limit` (optional): Maximum number of results (default: 10, max: 50)

**Response**:
```json
[
  {
    "id": "user-uuid",
    "username": "john_doe",
    "name": "John Doe"
  },
  {
    "id": "user-uuid-2",
    "username": "jane_smith",
    "name": "Jane Smith"
  }
]
```

**Permissions**: Requires `player:add` permission (Game Master or Admin role)

## Technical Details

### WSO2 SCIM2 Integration

The feature uses WSO2 Identity Server's SCIM2 (System for Cross-domain Identity Management) API to search for users.

**SCIM2 Endpoint**: `https://{WSO2_IS_URL}/scim2/Users`

**Search Filter**: Uses SCIM2 filter syntax: `userName co "{search_term}"` (case-insensitive contains)

**Authentication**: Uses admin credentials configured in `WSO2_IS_INTROSPECT_USER` and `WSO2_IS_INTROSPECT_PASSWORD`

### Frontend Implementation

- **Debouncing**: 300ms delay before sending search request to avoid excessive API calls
- **Keyboard Navigation**: Full keyboard support for accessibility
- **Responsive UI**: Dropdown adapts to screen size and scrolls when needed

### Security

- **Permission Checking**: Only Game Masters and Admins can search users
- **Token Validation**: All requests are authenticated via WSO2 OAuth2 tokens
- **Input Sanitization**: Search terms are properly encoded and validated

## Configuration

No additional configuration needed beyond standard WSO2 setup:

```env
WSO2_IS_URL=https://localhost:9443
WSO2_IS_INTROSPECT_USER=admin
WSO2_IS_INTROSPECT_PASSWORD=admin
WSO2_IS_VERIFY_SSL=False  # For development only
```

## Testing

### Unit Tests
```bash
pytest tests/unit/test_auth.py::TestSearchUsers -v
```

### Integration Tests
```bash
pytest tests/integration/test_app_endpoints.py -k "search_users" -v
```

## Troubleshooting

### No results appear when searching
- Verify WSO2 Identity Server is running and accessible
- Check WSO2 credentials in `.env` file
- Ensure users exist in WSO2 with the usernames you're searching for
- Check browser console for any API errors

### "403 Forbidden" error
- Ensure the logged-in user has Game Master or Admin role
- Verify role has `player:add` permission

### Search is slow
- Check network connectivity to WSO2 IS
- Consider reducing the debounce timeout if needed (in control.js)
- Verify WSO2 IS is not overloaded

## Future Enhancements

Potential improvements:
- Search by email or other attributes
- Display user avatars in dropdown
- Cache recent search results
- Support for searching within specific user groups
- Advanced filtering options (by role, status, etc.)
