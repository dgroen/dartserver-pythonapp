# WSO2 Setup Guide for Darts Game System

This guide provides step-by-step instructions for setting up WSO2 Identity Server and API Manager for the Darts Game System.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [WSO2 Identity Server Setup](#wso2-identity-server-setup)
3. [WSO2 API Manager Setup](#wso2-api-manager-setup)
4. [API Gateway Configuration](#api-gateway-configuration)
5. [Testing the Setup](#testing-the-setup)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

- Docker and Docker Compose installed
- At least 8GB RAM available
- Ports 9443, 9444, 8080, 8243, 8280, 5000, 5672 available
- Basic understanding of OAuth2 and JWT

## WSO2 Identity Server Setup

### 1. Start WSO2 Identity Server

```bash
# Start only WSO2 IS first
docker-compose -f docker-compose-wso2.yml up -d wso2is

# Wait for WSO2 IS to start (takes 2-3 minutes)
docker logs -f darts-wso2is
```

### 2. Access WSO2 IS Management Console

- URL: <https://localhost:9443/carbon>
- Username: `admin`
- Password: `admin`

**Note:** You may need to accept the self-signed certificate warning in your browser.

### 3. Create Service Provider for API Gateway

1. Navigate to **Main > Identity > Service Providers > Add**
2. Enter Service Provider Name: `DartsAPIGateway`
3. Click **Register**

4. **Configure Inbound Authentication:**
   - Expand **Inbound Authentication Configuration**
   - Expand **OAuth/OpenID Connect Configuration**
   - Click **Configure**

   Settings:
   - Grant Types: Select `Client Credentials`, `Password`, `Refresh Token`
   - Callback URL: `http://localhost:8080/callback` (for testing)
   - Click **Add**

5. **Note the credentials:**
   - OAuth Client Key (Client ID)
   - OAuth Client Secret
   - Save these for later use

### 4. Create User Roles

1. Navigate to **Main > Identity > Users and Roles > Add**
2. Click **Add New Role**

Create the following roles:

**Role: dartboard_device**

- Permissions: None (will use scopes)

**Role: game_admin**

- Permissions: Login, Manage

**Role: player**

- Permissions: Login

**Role: spectator**

- Permissions: Login

### 5. Create Test Users

1. Navigate to **Main > Identity > Users and Roles > Add > Add New User**

Create test users:

**User: dartboard1**

- Password: `Dartboard@123`
- Roles: `dartboard_device`

**User: admin_user**

- Password: `Admin@123`
- Roles: `game_admin`

**User: player1**

- Password: `Player@123`
- Roles: `player`

### 6. Configure OAuth Scopes

1. Navigate to **Main > Manage > OAuth2/OpenID Connect > Scopes**
2. Click **Add Scope**

Add the following scopes:

- **Scope Name:** `score:write`
  - Description: Submit scores to the game system

- **Scope Name:** `score:read`
  - Description: Read score information

- **Scope Name:** `game:write`
  - Description: Create and manage games

- **Scope Name:** `game:read`
  - Description: Read game information

- **Scope Name:** `player:write`
  - Description: Add and manage players

- **Scope Name:** `player:read`
  - Description: Read player information

### 7. Map Roles to Scopes

1. Go back to **Service Providers > DartsAPIGateway**
2. Expand **Claim Configuration**
3. Add the following role-to-scope mappings:

```
dartboard_device -> score:write
game_admin -> score:write, score:read, game:write, game:read, player:write, player:read
player -> score:write, game:read, player:read
spectator -> game:read
```

## WSO2 API Manager Setup

### 1. Start WSO2 API Manager

```bash
# Start WSO2 APIM
docker-compose -f docker-compose-wso2.yml up -d wso2apim

# Wait for WSO2 APIM to start (takes 3-4 minutes)
docker logs -f darts-wso2apim
```

### 2. Access WSO2 APIM Portals

**Publisher Portal:**

- URL: <https://localhost:9444/publisher>
- Username: `admin`
- Password: `admin`

**Developer Portal:**

- URL: <https://localhost:9444/devportal>
- Username: `admin`
- Password: `admin`

### 3. Configure Key Manager (Connect to WSO2 IS)

1. In Publisher Portal, navigate to **Settings > Key Managers**
2. Click **Add Key Manager**
3. Select **WSO2 Identity Server**

Configuration:

- Name: `WSO2-IS`
- Display Name: `WSO2 Identity Server`
- Issuer: `https://wso2is:9443/oauth2/token`
- Key Manager Type: `WSO2-IS`
- Well-known URL: `https://wso2is:9443/oauth2/oidcdiscovery/.well-known/openid-configuration`
- Introspection Endpoint: `https://wso2is:9443/oauth2/introspect`
- Token Endpoint: `https://wso2is:9443/oauth2/token`
- Revoke Endpoint: `https://wso2is:9443/oauth2/revoke`
- User Info Endpoint: `https://wso2is:9443/oauth2/userinfo`
- Authorize Endpoint: `https://wso2is:9443/oauth2/authorize`
- JWKS Endpoint: `https://wso2is:9443/oauth2/jwks`

Click **Add** to save.

### 4. Create API in Publisher Portal

1. Click **Create API**
2. Select **Design a New REST API**

**API Details:**

- Name: `Darts Game API`
- Context: `/api/v1`
- Version: `1.0.0`
- Endpoint: `http://api-gateway:8080`
- Business Plan: `Unlimited`

3. Click **Create & Publish**

### 5. Define API Resources

Add the following resources:

**Score Submission:**

- URL Pattern: `/scores`
- HTTP Method: `POST`
- Auth Type: `OAuth2`
- Scope: `score:write`
- Rate Limiting: `100 requests per minute`

**Game Management:**

- URL Pattern: `/games`
- HTTP Method: `POST`
- Auth Type: `OAuth2`
- Scope: `game:write`
- Rate Limiting: `10 requests per minute`

- URL Pattern: `/games/{gameId}`
- HTTP Method: `GET`
- Auth Type: `OAuth2`
- Scope: `game:read`
- Rate Limiting: `100 requests per minute`

**Player Management:**

- URL Pattern: `/players`
- HTTP Method: `POST`
- Auth Type: `OAuth2`
- Scope: `player:write`
- Rate Limiting: `20 requests per minute`

- URL Pattern: `/players`
- HTTP Method: `GET`
- Auth Type: `OAuth2`
- Scope: `player:read`
- Rate Limiting: `100 requests per minute`

### 6. Publish API

1. Click **Lifecycle** tab
2. Click **Publish**
3. Confirm publication

### 7. Subscribe to API (Developer Portal)

1. Go to Developer Portal: <https://localhost:9444/devportal>
2. Find **Darts Game API**
3. Click **Subscribe**
4. Create a new application or select existing
5. Select **Unlimited** tier
6. Click **Subscribe**

### 8. Generate API Keys

1. In Developer Portal, go to **Applications**
2. Select your application
3. Go to **Production Keys** tab
4. Click **Generate Keys**
5. Select Key Manager: `WSO2-IS`
6. Grant Types: `Client Credentials`, `Password`
7. Click **Generate**
8. **Save the Consumer Key and Consumer Secret**

## API Gateway Configuration

### 1. Update Environment Variables

Create or update `.env` file:

```bash
# WSO2 Identity Server
WSO2_IS_URL=https://wso2is:9443
WSO2_IS_CLIENT_ID=<your_client_id_from_step_3.5>
WSO2_IS_CLIENT_SECRET=<your_client_secret_from_step_3.5>

# JWT Validation Mode
JWT_VALIDATION_MODE=jwks

# RabbitMQ
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_EXCHANGE=darts_exchange

# API Gateway
API_GATEWAY_HOST=0.0.0.0
API_GATEWAY_PORT=8080

# Security
SECRET_KEY=<generate_a_strong_random_key>
```

### 2. Start API Gateway

```bash
# Start the API Gateway
docker-compose -f docker-compose-wso2.yml up -d api-gateway

# Check logs
docker logs -f darts-api-gateway
```

### 3. Start Complete Stack

```bash
# Start all services
docker-compose -f docker-compose-wso2.yml up -d

# Verify all services are running
docker-compose -f docker-compose-wso2.yml ps
```

## Testing the Setup

### 1. Obtain Access Token

**Using Client Credentials (for devices):**

```bash
curl -k -X POST https://localhost:9443/oauth2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=<your_client_id>" \
  -d "client_secret=<your_client_secret>" \
  -d "scope=score:write"
```

**Using Password Grant (for users):**

```bash
curl -k -X POST https://localhost:9443/oauth2/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=password" \
  -d "username=player1" \
  -d "password=Player@123" \
  -d "client_id=<your_client_id>" \
  -d "client_secret=<your_client_secret>" \
  -d "scope=score:write game:read"
```

Response:

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsICJ...",
  "refresh_token": "5c3c7c5f-...",
  "scope": "score:write",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### 2. Test API Gateway Health

```bash
curl http://localhost:8080/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "darts-api-gateway",
  "timestamp": "2024-01-01T12:00:00.000000"
}
```

### 3. Submit a Score

```bash
curl -X POST http://localhost:8080/api/v1/scores \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "score": 20,
    "multiplier": "TRIPLE",
    "player_id": "player-123",
    "game_id": "game-456"
  }'
```

Expected response:

```json
{
  "status": "success",
  "message": "Score submitted successfully",
  "data": {
    "score": 20,
    "multiplier": "TRIPLE",
    "player_id": "player-123",
    "game_id": "game-456",
    "user": "player1",
    "timestamp": "2024-01-01T12:00:00.000000"
  }
}
```

### 4. Create a Game

```bash
curl -X POST http://localhost:8080/api/v1/games \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "game_type": "301",
    "players": ["Player 1", "Player 2"],
    "double_out": false
  }'
```

### 5. Add a Player

```bash
curl -X POST http://localhost:8080/api/v1/players \
  -H "Authorization: Bearer <your_access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Player 3"
  }'
```

## Troubleshooting

### WSO2 IS Not Starting

**Issue:** Container exits or fails to start

**Solutions:**

1. Check available memory: `docker stats`
2. Increase Docker memory limit to at least 4GB
3. Check logs: `docker logs darts-wso2is`
4. Wait longer (initial startup takes 2-3 minutes)

### JWT Validation Fails

**Issue:** API returns 401 Unauthorized

**Solutions:**

1. Verify token is not expired
2. Check JWKS endpoint is accessible from API Gateway
3. Verify client ID and secret are correct
4. Check token scopes match required scopes
5. Try introspection mode instead of JWKS:

   ```bash
   JWT_VALIDATION_MODE=introspection
   ```

### RabbitMQ Connection Failed

**Issue:** API Gateway cannot connect to RabbitMQ

**Solutions:**

1. Verify RabbitMQ is running: `docker ps | grep rabbitmq`
2. Check RabbitMQ health: `docker exec darts-rabbitmq rabbitmq-diagnostics ping`
3. Verify network connectivity: `docker network inspect darts-network`
4. Check credentials in environment variables

### Certificate Errors

**Issue:** SSL certificate verification fails

**Solutions:**

1. For development, disable SSL verification (already done in code)
2. For production, use proper SSL certificates
3. Add WSO2 certificates to trusted store
4. Use nginx as SSL termination point

### Rate Limiting Issues

**Issue:** Getting 429 Too Many Requests

**Solutions:**

1. Check rate limit configuration in WSO2 APIM
2. Adjust throttling policies
3. Use different subscription tiers
4. Implement exponential backoff in client

## Production Considerations

### Security

1. **Change Default Passwords:**
   - WSO2 admin password
   - RabbitMQ credentials
   - Database passwords

2. **Use Proper SSL Certificates:**
   - Obtain certificates from trusted CA
   - Configure in nginx and WSO2 components

3. **Enable HTTPS Everywhere:**
   - Force HTTPS for all communications
   - Disable HTTP endpoints

4. **Implement Network Segmentation:**
   - Use private networks for backend services
   - Expose only necessary ports

5. **Enable Audit Logging:**
   - Configure WSO2 audit logs
   - Set up log aggregation (ELK stack)

### Performance

1. **Scale Services:**
   - Run multiple API Gateway instances
   - Use RabbitMQ clustering
   - Scale WSO2 components

2. **Database Optimization:**
   - Use external databases (PostgreSQL/MySQL)
   - Configure connection pooling
   - Enable query caching

3. **Caching:**
   - Enable Redis for token caching
   - Cache API responses where appropriate
   - Use CDN for static assets

### Monitoring

1. **Set Up Monitoring:**
   - Prometheus + Grafana
   - WSO2 Analytics
   - RabbitMQ monitoring

2. **Configure Alerts:**
   - Service health checks
   - Error rate thresholds
   - Resource utilization alerts

3. **Log Management:**
   - Centralized logging (ELK/Splunk)
   - Log rotation policies
   - Retention policies

## Additional Resources

- [WSO2 Identity Server Documentation](https://is.docs.wso2.com/)
- [WSO2 API Manager Documentation](https://apim.docs.wso2.com/)
- [OAuth 2.0 Specification](https://oauth.net/2/)
- [JWT.io - JWT Debugger](https://jwt.io/)
- [RabbitMQ Documentation](https://www.rabbitmq.com/documentation.html)

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review WSO2 documentation
3. Check Docker logs for all services
4. Consult the project's issue tracker

---

**Note:** This setup is designed for development and testing. Additional hardening and configuration are required for production deployment.
