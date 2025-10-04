# Quick Start Guide - Darts Game System with Authentication

This guide will help you get the Darts Game System running with WSO2 Identity Server authentication in minutes.

## Prerequisites

- Docker and Docker Compose installed
- Ports available: 5000, 8080, 9443, 9763, 5672, 15672, 80, 443

## Step 1: Initial Setup

```bash
# Clone or navigate to the project directory
cd /data/dartserver-pythonapp

# Run the quick start script
./start-with-auth.sh
```

If this is your first run, the script will create a `.env` file and prompt you to configure WSO2.

## Step 2: Configure WSO2 Identity Server

```bash
# Run the configuration helper script
./configure-wso2-roles.sh
```

This script provides step-by-step instructions for:
1. Creating roles (player, gamemaster, admin)
2. Creating test users
3. Registering the OAuth2 application
4. Configuring claims

**Follow the manual steps in the WSO2 Management Console** (the script will guide you).

## Step 3: Update Environment Variables

After completing WSO2 configuration, update your `.env` file:

```bash
# Edit .env and add your OAuth2 credentials
nano .env
```

Update these values:
```
WSO2_CLIENT_ID=your_actual_client_id
WSO2_CLIENT_SECRET=your_actual_client_secret
```

## Step 4: Start the System

```bash
# Run the start script again
./start-with-auth.sh
```

Wait for all services to be ready (this may take 2-3 minutes on first run).

## Step 5: Access the Application

Once all services are ready:

1. **Open the Darts Game**: http://localhost:5000
2. **Click "Login with WSO2"**
3. **Login with a test user**:
   - Player: `testplayer` / `Player@123`
   - Game Master: `testgamemaster` / `GameMaster@123`
   - Admin: `testadmin` / `Admin@123`

## Role Capabilities

### 🟢 Player Role
- View game board
- Submit scores
- View game state
- View leaderboard

### 🟡 Game Master Role
- All Player permissions
- Access control panel
- Create new games
- Add/remove players
- Manage game flow

### 🔴 Admin Role
- Full system access
- All Game Master permissions
- System configuration
- User management

## Common Commands

### View Logs
```bash
docker-compose -f docker-compose-wso2.yml logs -f
```

### View Specific Service Logs
```bash
docker-compose -f docker-compose-wso2.yml logs -f darts-app
docker-compose -f docker-compose-wso2.yml logs -f wso2is
```

### Stop Services
```bash
docker-compose -f docker-compose-wso2.yml down
```

### Restart Services
```bash
docker-compose -f docker-compose-wso2.yml restart
```

### Clean Restart (removes volumes)
```bash
docker-compose -f docker-compose-wso2.yml down -v
docker-compose -f docker-compose-wso2.yml up -d
```

## Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| Darts Game | http://localhost:5000 | WSO2 users |
| WSO2 IS Console | https://localhost:9443/carbon | admin / admin |
| RabbitMQ Management | http://localhost:15672 | guest / guest |
| API Gateway | http://localhost:8080 | Token required |

## Troubleshooting

### "WSO2 Client ID not configured"
- Run `./configure-wso2-roles.sh` and follow the steps
- Update `.env` with your Client ID and Secret

### "Cannot connect to WSO2"
- Wait 2-3 minutes for WSO2 IS to fully start
- Check logs: `docker-compose -f docker-compose-wso2.yml logs wso2is`
- Verify WSO2 is accessible: `curl -k https://localhost:9443/carbon/admin/login.jsp`

### "Invalid redirect URI"
- Ensure you registered `http://localhost:5000/callback` in WSO2
- Check the OAuth2 application configuration in WSO2 Console

### "User has no roles"
- Verify the user is assigned a role in WSO2 Console
- Check that claims are configured correctly
- Ensure "groups" claim is included in the token

### "403 Forbidden" on Control Panel
- Only Game Masters and Admins can access the control panel
- Verify your user has the correct role assigned

### Services won't start
- Check if ports are already in use: `netstat -tuln | grep -E '5000|8080|9443|5672|15672'`
- Ensure Docker has enough resources (at least 4GB RAM recommended)

## Next Steps

- Read the full documentation: [docs/AUTHENTICATION_SETUP.md](docs/AUTHENTICATION_SETUP.md)
- Configure production settings (HTTPS, secure cookies, etc.)
- Create additional users and roles as needed
- Customize permissions in `auth.py`

## Security Notes

⚠️ **Development Mode**: The current configuration uses:
- Self-signed certificates (SSL verification disabled)
- HTTP instead of HTTPS for the app
- Default admin credentials for introspection

🔒 **For Production**: See [docs/AUTHENTICATION_SETUP.md](docs/AUTHENTICATION_SETUP.md) for security hardening steps.

## Support

For detailed information, see:
- [AUTHENTICATION_SETUP.md](docs/AUTHENTICATION_SETUP.md) - Complete setup guide
- [README.md](README.md) - Project overview
- WSO2 IS Documentation: https://is.docs.wso2.com/

---

**Ready to play darts! 🎯**