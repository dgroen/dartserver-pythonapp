# WSO2 API Manager Integration

This directory contains scripts and documentation for integrating WSO2 API Manager with the Darts Game System.

## Overview

WSO2 APIM provides:
- **API Gateway**: Central entry point for all dartboard and client requests
- **Rate Limiting**: Throttling policies to prevent abuse
- **Analytics**: Request monitoring and reporting
- **Security**: OAuth2 token validation and scope enforcement
- **Versioning**: API version management

## Quick Start

### 1. Start the Stack

```bash
docker-compose -f docker-compose-localhost.yml up -d
```

Wait 2-3 minutes for all services to be healthy:

```bash
docker-compose -f docker-compose-localhost.yml ps
```

### 2. Configure APIM

Run the automated configuration script:

```bash
./helpers/configure_wso2_apim.sh
```

This creates throttling policies, defines the Darts API, and publishes it.

### 3. Test the Integration

```bash
python helpers/test_wso2_apim_integration.py --verbose
```

### 4. Access APIM Portals

- **Publisher Portal**: https://localhost:9444/publisher
- **Developer Portal**: https://localhost:9444/devportal
- **Admin Portal**: https://localhost:9444/admin

Default credentials: `admin` / `admin`

## Architecture

```
Dartboard/Client
      ↓
   Nginx (443)
      ↓
 APIM Gateway (8243)
      ↓ [validates token, rate limits]
 API Gateway (8080)
      ↓
  RabbitMQ
```

## Files

### Scripts

- **setup_wso2_apim.py**: Python script to configure APIM programmatically
- **configure_wso2_apim.sh**: Wrapper script that waits for APIM and runs setup
- **test_wso2_apim_integration.py**: Integration tests for APIM flow

### Documentation

- **doc/WSO2_APIM_CONFIGURATION.md**: Complete APIM configuration guide
- **doc/ARCHITECTURE.md**: System architecture with APIM integration

## API Endpoints (via APIM)

All requests go through `https://your-domain/api/v1/`:

| Endpoint                    | Method | Scope             | Throttle Policy |
| --------------------------- | ------ | ----------------- | --------------- |
| `/v1/dartboard/throw`       | POST   | `dartboard:write` | 1000 req/min    |
| `/v1/scores`                | POST   | `score:write`     | 100 req/min     |
| `/v1/games`                 | POST   | `game:create`     | 100 req/min     |
| `/v1/players`               | POST   | `player:create`   | 100 req/min     |
| `/v1/game/actions/end-turn` | POST   | `game:control`    | 100 req/min     |
| `/v1/game/actions/continue` | POST   | `game:control`    | 100 req/min     |
| `/v1/game/actions/pause`    | POST   | `game:control`    | 100 req/min     |
| `/health`                   | GET    | (none)            | Unlimited       |

## OAuth2 Scopes

- **dartboard:write**: Submit dartboard throws
- **score:write**: Submit manual scores
- **game:create**: Create new games
- **game:control**: Control game flow (pause, continue, end turn)
- **player:create**: Add players to games

## Throttling Policies

Created automatically by setup script:

- **DartboardThrottle**: 1000 requests/minute (for high-volume dartboard throws)
- **GameControlThrottle**: 100 requests/minute (for game management)
- **UnlimitedThrottle**: No limits (for health checks)

## Client Configuration

### Dartboard Hardware

```env
# Token endpoint
WSO2_TOKEN_URL=https://your-domain/auth/oauth2/token

# API endpoint (through APIM)
API_GATEWAY_URL=https://your-domain/api/v1

# OAuth2 credentials
WSO2_CLIENT_ID=<your-client-id>
WSO2_CLIENT_SECRET=<your-client-secret>
OAUTH_SCOPES=dartboard:write
```

### Web Application

```env
WSO2_AUTH_URL=https://your-domain/auth/oauth2/authorize
WSO2_TOKEN_URL=https://your-domain/auth/oauth2/token
API_BASE_URL=https://your-domain/api/v1
WSO2_CLIENT_ID=<your-client-id>
WSO2_CLIENT_SECRET=<your-client-secret>
OAUTH_SCOPES=score:write game:create game:control
```

## Development vs Production

### Development (localhost)

- APIM Gateway: `https://localhost:8243/api/v1/`
- Publisher Portal: `https://localhost:9444/publisher`
- Self-signed certificates (use `-k` with curl)

### Production

- APIM Gateway: `https://api.your-domain.com/api/v1/`
- Publisher Portal: `https://api.your-domain.com/publisher`
- Valid SSL certificates
- Proper DNS configuration

## Troubleshooting

### APIM Not Starting

Check container logs:
```bash
docker logs darts-wso2apim
```

Common issues:
- Insufficient memory (increase to 2GB)
- Port conflicts (9444, 8243, 8280)
- WSO2 IS not healthy

### Setup Script Fails

Run manually with verbose output:
```bash
python helpers/setup_wso2_apim.py --verbose
```

Check:
- APIM is running and healthy
- Admin credentials are correct
- API Gateway is accessible

### Rate Limiting Not Working

Verify throttling policies:
```bash
curl -k https://localhost:9444/api/am/admin/v4/throttling/policies/advanced \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

### Token Validation Fails

Check WSO2 IS integration:
```bash
curl -k https://localhost:9443/oauth2/token \
  -u "CLIENT_ID:CLIENT_SECRET" \
  -d "grant_type=client_credentials"
```

## Direct API Gateway Access (Bypass APIM)

For testing/debugging, you can access the API Gateway directly:

```bash
# Through nginx at /api-direct/v1/
curl -k https://localhost/api-direct/v1/health

# Or directly to API Gateway container
curl http://localhost:8080/health
```

⚠️ **Production**: Direct access should be blocked or firewalled.

## Monitoring

### APIM Analytics

Enable analytics in APIM Admin Portal to track:
- Request count per API
- Response times
- Error rates
- Top clients

### API Gateway Logs

```bash
docker logs -f darts-api-gateway
```

### APIM Logs

```bash
docker logs -f darts-wso2apim
```

## Further Reading

- [WSO2 APIM Documentation](https://apim.docs.wso2.com/en/latest/)
- [doc/WSO2_APIM_CONFIGURATION.md](../doc/WSO2_APIM_CONFIGURATION.md) - Complete configuration guide
- [doc/ARCHITECTURE.md](../doc/ARCHITECTURE.md) - System architecture
- [src/api_gateway/README.md](../src/api_gateway/README.md) - API Gateway documentation
