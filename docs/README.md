# Darts Game System Documentation

Welcome to the Darts Game System documentation! This directory contains comprehensive guides for setting up, configuring, and using the system.

---

## 📚 Documentation Index

### Quick Start
- **[QUICK_START.md](../QUICK_START.md)** - Get up and running in minutes
  - Prerequisites
  - Step-by-step setup
  - Common commands
  - Troubleshooting

### Authentication & Security
- **[AUTHENTICATION_SETUP.md](AUTHENTICATION_SETUP.md)** - Complete authentication guide (500+ lines)
  - Detailed WSO2 configuration
  - Role and user setup
  - OAuth2 application registration
  - Claims configuration
  - Testing procedures
  - Security best practices
  - Production deployment guide

- **[AUTHENTICATION_FLOW.md](AUTHENTICATION_FLOW.md)** - Visual flow diagrams
  - OAuth2 Authorization Code Flow
  - Role-Based Access Control Flow
  - Permission Hierarchy
  - Route Protection Matrix
  - Token Validation Flow
  - Session Lifecycle
  - Component Interaction
  - Security Layers
  - Error Handling Flow

- **[AUTHENTICATION_SUMMARY.md](../AUTHENTICATION_SUMMARY.md)** - Implementation overview
  - Architecture summary
  - Role definitions
  - Files created/modified
  - Configuration requirements
  - Security features
  - Testing guide
  - Production checklist

---

## 🚀 Getting Started

### For First-Time Users

1. **Start Here**: [QUICK_START.md](../QUICK_START.md)
   - Follow the 5-step quick start guide
   - Get the system running quickly

2. **Configure Authentication**: [AUTHENTICATION_SETUP.md](AUTHENTICATION_SETUP.md)
   - Set up WSO2 Identity Server
   - Create roles and users
   - Configure OAuth2

3. **Understand the Flow**: [AUTHENTICATION_FLOW.md](AUTHENTICATION_FLOW.md)
   - Visual diagrams of authentication
   - Understand how everything works together

### For Developers

1. **Architecture Overview**: [AUTHENTICATION_SUMMARY.md](../AUTHENTICATION_SUMMARY.md)
   - Understand the implementation
   - Review security features
   - See what files were created/modified

2. **Code Reference**: 
   - `/auth.py` - Authentication module
   - `/app.py` - Main application with protected routes
   - `/templates/` - UI templates

3. **Testing**: 
   - Run `./test-authentication.sh` for automated tests
   - Follow manual test procedures in documentation

### For System Administrators

1. **Production Deployment**: [AUTHENTICATION_SETUP.md](AUTHENTICATION_SETUP.md#production-deployment)
   - Security hardening
   - HTTPS configuration
   - Environment variables
   - Monitoring and logging

2. **Troubleshooting**: [QUICK_START.md](../QUICK_START.md#troubleshooting)
   - Common issues and solutions
   - Service health checks
   - Log analysis

---

## 🎯 Role-Based Access Control

The system implements a three-tier role model:

### 🟢 Player Role
- View game board
- Submit scores
- View game state

### 🟡 Game Master Role
- All Player permissions
- Access control panel
- Create games
- Manage players

### 🔴 Admin Role
- Full system access
- All permissions

**Detailed information**: [AUTHENTICATION_SUMMARY.md](../AUTHENTICATION_SUMMARY.md#role-based-access-control-rbac)

---

## 🔧 Configuration Files

### Environment Configuration
- **`.env`** - Environment variables (create from `.env.example`)
  - WSO2 credentials
  - OAuth2 settings
  - Session configuration

### Docker Configuration
- **`docker-compose-wso2.yml`** - Docker Compose configuration
  - All services defined
  - Environment variables
  - Network configuration
  - Health checks

### Application Configuration
- **`auth.py`** - Authentication module
  - Role definitions
  - Permission mappings
  - OAuth2 flow implementation

---

## 🛠️ Helper Scripts

### Setup Scripts
- **`start-with-auth.sh`** - Quick start script
  - Validates configuration
  - Starts all services
  - Performs health checks
  - Displays access URLs

- **`configure-wso2-roles.sh`** - Configuration helper
  - Step-by-step WSO2 setup
  - Role creation guide
  - User creation guide
  - OAuth2 app registration

### Testing Scripts
- **`test-authentication.sh`** - Authentication testing
  - Automated endpoint tests
  - Service health checks
  - Manual test checklist

---

## 📖 Key Concepts

### OAuth2 Authorization Code Flow
The system uses the OAuth2 Authorization Code Flow for secure authentication:
1. User accesses protected resource
2. Redirected to WSO2 for authentication
3. User logs in with credentials
4. WSO2 redirects back with authorization code
5. App exchanges code for access token
6. Token validated and session created

**Visual diagram**: [AUTHENTICATION_FLOW.md](AUTHENTICATION_FLOW.md#oauth2-authorization-code-flow)

### Token Validation
Two methods supported:
- **JWKS** - JSON Web Key Set signature verification
- **Introspection** - WSO2 token introspection endpoint

**Configuration**: Set `JWT_VALIDATION_MODE` in `.env`

### Session Management
- Secure session cookies (HttpOnly, SameSite)
- Token storage in server-side session
- Automatic session validation on each request

---

## 🔒 Security Features

### Implemented
✅ OAuth2 Authorization Code Flow  
✅ CSRF Protection (state parameter)  
✅ Token Validation (JWKS + Introspection)  
✅ Role-Based Access Control  
✅ Session Security (HttpOnly, SameSite)  
✅ Input Validation  

### Production Requirements
⚠️ Enable HTTPS  
⚠️ Use valid SSL certificates  
⚠️ Set SESSION_COOKIE_SECURE=True  
⚠️ Generate strong SECRET_KEY  
⚠️ Create dedicated service account  

**Full security guide**: [AUTHENTICATION_SETUP.md](AUTHENTICATION_SETUP.md#security-considerations)

---

## 🐛 Troubleshooting

### Common Issues

#### Services Won't Start
- Check Docker is running
- Verify ports are available
- Check Docker resources (4GB+ RAM recommended)

#### Cannot Connect to WSO2
- Wait 2-3 minutes for startup
- Check logs: `docker-compose -f docker-compose-wso2.yml logs wso2is`
- Verify: `curl -k https://localhost:9443/carbon/admin/login.jsp`

#### Authentication Fails
- Verify WSO2 configuration
- Check client credentials in `.env`
- Verify callback URL matches
- Check user has roles assigned

#### 403 Forbidden
- Verify user has required role
- Check permission configuration
- Review route protection decorators

**Full troubleshooting guide**: [QUICK_START.md](../QUICK_START.md#troubleshooting)

---

## 📊 Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| Darts Game | http://localhost:5000 | WSO2 users |
| WSO2 IS Console | https://localhost:9443/carbon | admin / admin |
| RabbitMQ Management | http://localhost:15672 | guest / guest |
| API Gateway | http://localhost:8080 | Token required |

---

## 🧪 Testing

### Automated Tests
```bash
./test-authentication.sh
```

### Manual Tests
1. Test each role (player, gamemaster, admin)
2. Verify access control
3. Test logout functionality
4. Verify session persistence

**Detailed test procedures**: [AUTHENTICATION_SETUP.md](AUTHENTICATION_SETUP.md#testing-the-setup)

---

## 📝 API Endpoints

### Public Endpoints
- `GET /login` - Login page
- `GET /callback` - OAuth2 callback

### Protected Endpoints
- `GET /` - Game board (all roles)
- `GET /control` - Control panel (gamemaster, admin)
- `GET /profile` - User profile (all roles)
- `GET /logout` - Logout (all roles)

### API Endpoints
- `GET /api/game` - Get game state
- `POST /api/game` - Create game (gamemaster, admin)
- `POST /api/player` - Add player (gamemaster, admin)
- `DELETE /api/player/<id>` - Remove player (gamemaster, admin)
- `POST /api/score` - Submit score (all roles)

**Full route protection matrix**: [AUTHENTICATION_FLOW.md](AUTHENTICATION_FLOW.md#route-protection-matrix)

---

## 🔄 Development Workflow

### Making Changes

1. **Modify Code**
   - Edit files in `/data/dartserver-pythonapp/`
   - Update authentication logic in `auth.py`
   - Update routes in `app.py`

2. **Test Changes**
   ```bash
   docker-compose -f docker-compose-wso2.yml restart darts-app
   ./test-authentication.sh
   ```

3. **View Logs**
   ```bash
   docker-compose -f docker-compose-wso2.yml logs -f darts-app
   ```

### Adding New Roles

1. Update `ROLES` dictionary in `auth.py`
2. Create role in WSO2 Console
3. Assign permissions
4. Update documentation

### Adding New Permissions

1. Add permission to role in `auth.py`
2. Apply `@permission_required()` decorator to route
3. Test access control
4. Update documentation

---

## 📚 Additional Resources

### WSO2 Documentation
- [WSO2 Identity Server Documentation](https://is.docs.wso2.com/)
- [OAuth2 Guide](https://is.docs.wso2.com/en/latest/guides/identity-federation/oauth/)
- [Role-Based Access Control](https://is.docs.wso2.com/en/latest/guides/identity-lifecycles/manage-roles-overview/)

### OAuth2 Resources
- [OAuth 2.0 Authorization Code Flow](https://oauth.net/2/grant-types/authorization-code/)
- [OpenID Connect](https://openid.net/connect/)

### Flask Resources
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Flask Sessions](https://flask.palletsprojects.com/en/2.3.x/quickstart/#sessions)

---

## 🤝 Support

### Getting Help

1. **Check Documentation**
   - Review relevant guides above
   - Check troubleshooting sections

2. **Check Logs**
   ```bash
   docker-compose -f docker-compose-wso2.yml logs -f
   ```

3. **Run Tests**
   ```bash
   ./test-authentication.sh
   ```

4. **Verify Configuration**
   - Check `.env` file
   - Verify WSO2 configuration
   - Check Docker resources

---

## 📋 Cheat Sheet

### Quick Commands

```bash
# Start services
./start-with-auth.sh

# Configure WSO2
./configure-wso2-roles.sh

# Test authentication
./test-authentication.sh

# View logs
docker-compose -f docker-compose-wso2.yml logs -f

# Restart service
docker-compose -f docker-compose-wso2.yml restart darts-app

# Stop services
docker-compose -f docker-compose-wso2.yml down

# Clean restart
docker-compose -f docker-compose-wso2.yml down -v
docker-compose -f docker-compose-wso2.yml up -d
```

### Test Users

| Username | Password | Role |
|----------|----------|------|
| testplayer | Player@123 | player |
| testgamemaster | GameMaster@123 | gamemaster |
| testadmin | Admin@123 | admin |

*Note: Create these users in WSO2 Console first*

---

## 📄 Document Versions

| Document | Lines | Last Updated |
|----------|-------|--------------|
| AUTHENTICATION_SETUP.md | 500+ | 2024 |
| AUTHENTICATION_FLOW.md | 400+ | 2024 |
| AUTHENTICATION_SUMMARY.md | 400+ | 2024 |
| QUICK_START.md | 200+ | 2024 |

---

## ✅ Implementation Status

**Status**: ✅ Complete and ready for deployment

- ✅ Authentication module implemented
- ✅ Role-based access control configured
- ✅ UI updated with login/logout
- ✅ All routes protected
- ✅ Documentation complete
- ✅ Helper scripts created
- ✅ Testing scripts ready

---

**Ready to get started? Begin with [QUICK_START.md](../QUICK_START.md)! 🎯**