# Authentication Bypass Mode

## Overview

The Darts Game application includes an authentication bypass mode that allows
you to disable all authentication and authorization checks. This is useful for
development, testing, and scenarios where you want to run the application
without WSO2 Identity Server.

## Configuration

To enable authentication bypass mode, set the `AUTH_DISABLED` environment
variable to `true`:

```bash
AUTH_DISABLED=true
```

### Environment Variable Options

- `AUTH_DISABLED=true` - Disables all authentication and role checks
- `AUTH_DISABLED=false` - Enables normal authentication (default)

## Behavior When Enabled

When `AUTH_DISABLED=true`, the following changes occur:

### 1. Login Not Required

All routes decorated with `@login_required` will be accessible without
authentication. Users will not be redirected to the login page.

### 2. Role Checks Bypassed

All routes decorated with `@role_required()` will be accessible regardless of
user roles. The role check is completely bypassed.

### 3. Permission Checks Bypassed

All routes decorated with `@permission_required()` will be accessible
regardless of user permissions. The permission check is completely bypassed.

### 4. Default User Context

When authentication is bypassed, the following default user context is set:

```python
request.user_claims = {"sub": "bypass_user", "username": "bypass_user"}
request.user_roles = ["admin"]  # Admin role granted in bypass mode
```

This ensures that any code checking for user information will still work correctly.

## Use Cases

### Development

Enable bypass mode during local development to avoid setting up WSO2 Identity Server:

```bash
# .env file
AUTH_DISABLED=true
FLASK_DEBUG=true
```

### Testing

Use bypass mode in automated tests to focus on application logic without
authentication complexity:

```python
@patch("auth.AUTH_DISABLED", True)
def test_game_creation():
    # Test game creation without authentication
    response = client.post("/api/game/new", json={"game_type": "301"})
    assert response.status_code == 200
```

### Standalone Deployment

Deploy the application without WSO2 Identity Server for simple, single-user
scenarios:

```bash
docker run -e AUTH_DISABLED=true -p 5000:5000 darts-app
```

## Security Considerations

⚠️ **WARNING**: Never enable `AUTH_DISABLED=true` in production environments
with public access!

When authentication is disabled:

- All users have full admin privileges
- No access control is enforced
- No audit trail of user actions
- Session management is bypassed

### Recommended Usage

✅ **Safe to use:**

- Local development environments
- Automated testing
- Private networks with trusted users only
- Single-user deployments

❌ **Never use:**

- Production environments
- Public-facing deployments
- Multi-user environments
- Any scenario requiring access control

## Configuration Examples

### Development Environment

```bash
# .env
AUTH_DISABLED=true
FLASK_DEBUG=true
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
```

### Production Environment

```bash
# .env
AUTH_DISABLED=false
WSO2_IS_URL=https://identity.example.com
WSO2_CLIENT_ID=your_client_id
WSO2_CLIENT_SECRET=your_client_secret
SESSION_COOKIE_SECURE=true
```

## Logging

When authentication bypass is active, the application logs informational
messages:

```text
INFO - Authentication bypassed - AUTH_DISABLED is true
INFO - Role check bypassed - AUTH_DISABLED is true (required: ('admin', 'gamemaster'))
INFO - Permission check bypassed - AUTH_DISABLED is true (required: game:create)
```

These logs help identify when bypass mode is active and which checks are being
skipped.

## Testing

The authentication bypass functionality includes comprehensive unit tests:

```bash
# Run bypass mode tests
pytest tests/unit/test_auth.py::TestAuthDisabled -v

# Run all authentication tests
pytest tests/unit/test_auth.py -v
```

## Implementation Details

The bypass mode is implemented in the `auth.py` module:

1. **Environment Variable**: `AUTH_DISABLED` is read at module load time
2. **Decorator Modification**: All auth decorators check `AUTH_DISABLED` first
3. **Early Return**: If bypass is enabled, decorators return immediately
   without checks
4. **Default Context**: Bypass mode sets default user claims and admin role

### Code Example

```python
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Bypass authentication if disabled
        if AUTH_DISABLED:
            request.user_claims = {
                "sub": "bypass_user",
                "username": "bypass_user"
            }
            request.user_roles = ["admin"]
            logger.info("Authentication bypassed - AUTH_DISABLED is true")
            return f(*args, **kwargs)

        # Normal authentication flow
        # ...
```

## Troubleshooting

### Bypass Not Working

If authentication is still required after setting `AUTH_DISABLED=true`:

1. Verify the environment variable is set correctly:

   ```bash
   echo $AUTH_DISABLED
   ```

2. Restart the application to reload environment variables

3. Check application logs for bypass messages

4. Ensure `.env` file is in the correct location

### Unexpected Behavior

If you experience issues with bypass mode:

1. Check that `AUTH_DISABLED` is exactly `true` (case-insensitive)
2. Verify no other authentication middleware is interfering
3. Review application logs for error messages
4. Test with a simple endpoint first

## Related Documentation

- [Authentication Setup](AUTHENTICATION_SETUP.md)
- [WSO2 Integration](WSO2_INTEGRATION.md)
- [Development Guide](DEVELOPMENT.md)
- [Testing Guide](TESTING.md)

## Summary

Authentication bypass mode provides a convenient way to run the Darts Game
application without authentication infrastructure. Use it responsibly in
development and testing environments, but never in production with public
access.
