# Docker Network Configuration Explained

## The Problem: Why Localhost Failed in Docker

### Before (Broken)

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dartsdb  # pragma: allowlist secret
RABBITMQ_HOST=localhost
```

When running in Docker, **each container has its own localhost**. The `darts-app` container's localhost only refers to itself, NOT to the postgres or rabbitmq containers.

```
┌─────────────────────────────────┐
│   Docker Host (your machine)    │
├─────────────────────────────────┤
│                                 │
│  ┌─────────────────────────┐   │
│  │  darts-app container    │   │
│  │                         │   │
│  │  localhost:5432 ← ERROR │   │  (points to itself, not postgres!)
│  │                         │   │
│  └─────────────────────────┘   │
│                                 │
│  ┌─────────────────────────┐   │
│  │  postgres container     │   │
│  │  (port 5432)            │   │
│  └─────────────────────────┘   │
│                                 │
│  ┌─────────────────────────┐   │
│  │  rabbitmq container     │   │
│  │  (port 5672)            │   │
│  └─────────────────────────┘   │
│                                 │
└─────────────────────────────────┘

Result: darts-app can't find database! ❌
```

### After (Fixed)

```env
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/dartsdb  # pragma: allowlist secret
RABBITMQ_HOST=rabbitmq
```

Using service names, Docker's embedded DNS resolves them to container IPs on the internal network.

```
┌─────────────────────────────────────────────────────┐
│   Docker Compose Network (darts-network)            │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  darts-app container                         │  │
│  │                                              │  │
│  │  postgres:5432                              │  │
│  │  ↓ (Docker DNS resolves to IP of postgres   │  │
│  │     container on darts-network)             │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  postgres container (IP: 172.20.0.2)        │  │
│  │  ← Accessible via hostname "postgres"       │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  rabbitmq container (IP: 172.20.0.3)        │  │
│  │  ← Accessible via hostname "rabbitmq"       │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │  wso2is container (IP: 172.20.0.4)          │  │
│  │  ← Accessible via hostname "wso2is"         │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘

Result: All services can communicate! ✅
```

---

## Docker Compose Service Names

The `docker-compose-wso2.yml` file defines these services:

```yaml
services:
  postgres: # Service name for database
  rabbitmq: # Service name for message broker
  wso2is: # Service name for authentication
  wso2apim: # Service name for API manager
  api-gateway: # Service name for gateway
  darts-app: # Service name for main app
```

Each service name is resolvable **within the Docker network** as a hostname.

---

## How Service Discovery Works

### 1. Docker's Embedded DNS Server (127.0.0.11:53)

Each container has an embedded DNS resolver that:

- Intercepts DNS queries
- Checks if hostname matches a service name in the docker-compose.yml
- Returns the container's IP address on the internal network

### 2. Example: darts-app → postgres Connection

```
Step 1: Application code attempts connection
   database_url = "postgresql://postgres:5432/..."

Step 2: Python DNS resolution
   socket.getaddrinfo("postgres")

Step 3: DNS Query to 127.0.0.11:53
   Q: "What is the IP for 'postgres'?"

Step 4: Docker DNS Response
   A: "172.20.0.2" (postgres container's IP)

Step 5: Connection established
   darts-app connects to 172.20.0.2:5432

Result: ✅ Database connection successful
```

---

## Network Configuration Details

### darts-network

Defined in `docker-compose-wso2.yml`:

```yaml
networks:
  darts-network:
    driver: bridge
```

All services are connected to this network:

```yaml
services:
  darts-app:
    networks:
      - darts-network
  postgres:
    networks:
      - darts-network
  rabbitmq:
    networks:
      - darts-network
  # ... etc
```

---

## Important Distinctions

### Internal vs External Access

| Access Pattern          | How It Works                         | Example                       |
| ----------------------- | ------------------------------------ | ----------------------------- |
| **Container→Container** | Use service name on internal network | `postgresql://postgres:5432`  |
| **Host→Container**      | Use localhost + exposed port         | `postgresql://localhost:5432` |
| **Browser→Service**     | Use public domain + reverse proxy    | `https://letsplaydarts.eu`    |

### Example: PostgreSQL Access

```
┌─────────────────────────────────────────────────┐
│ From darts-app container                        │
├─────────────────────────────────────────────────┤
│ postgresql://postgres:5432/dartsdb              │
│ ✅ Works - uses service name on Docker network  │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ From Docker host machine (your computer)        │
├─────────────────────────────────────────────────┤
│ postgresql://localhost:5432/dartsdb             │
│ ✅ Works - postgres exposes port 5432           │
└─────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────┐
│ From browser via internet                       │
├─────────────────────────────────────────────────┤
│ https://letsplaydarts.eu/api/...                │
│ ✅ Works - nginx reverse proxy handles it       │
└─────────────────────────────────────────────────┘
```

---

## Environment Variables: Local vs Docker

### Running Locally (NOT in Docker)

```env
ENVIRONMENT=development
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/dartsdb  # pragma: allowlist secret
RABBITMQ_HOST=localhost
APP_DOMAIN=localhost:5000
APP_SCHEME=http
```

**Why?** Because your Flask app runs on your machine, and postgres/rabbitmq also run locally on the same machine.

### Running in Docker

```env
ENVIRONMENT=production
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/dartsdb  # pragma: allowlist secret
RABBITMQ_HOST=rabbitmq
APP_DOMAIN=letsplaydarts.eu
APP_SCHEME=https
```

**Why?** Because your Flask app runs in a container that needs to reach other containers via service names on the Docker network.

---

## WSO2 Dual URL Configuration

This is a special case where we need **two URLs** for the same service:

```env
WSO2_IS_URL=https://letsplaydarts.eu/auth
WSO2_IS_INTERNAL_URL=https://wso2is:9443
```

### Why Two URLs?

```
┌──────────────────────────────────────────────────────┐
│ Browser OAuth2 Flow                                  │
├──────────────────────────────────────────────────────┤
│                                                      │
│ Step 1: User clicks "Login"                         │
│ Step 2: Browser redirects to:                       │
│         https://letsplaydarts.eu/auth/authorize... │
│         (Uses WSO2_IS_URL - public domain)          │
│                                                      │
│ Step 3: WSO2 redirects to callback:                 │
│         https://letsplaydarts.eu/callback           │
│         (Browser can access public domain)          │
│                                                      │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ Backend Token Validation Flow                        │
├──────────────────────────────────────────────────────┤
│                                                      │
│ Step 1: darts-app gets token from user              │
│ Step 2: App validates token with WSO2:              │
│         POST https://wso2is:9443/introspect         │
│         (Uses WSO2_IS_INTERNAL_URL - service name   │
│          on Docker network, faster, more reliable)  │
│                                                      │
│ Step 3: WSO2 validates and returns token info       │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### Benefits of Dual URLs

- **Browsers** can access public domain (<https://letsplaydarts.eu>) via reverse proxy
- **Containers** can access efficiently via service name (<https://wso2is:9443>) on Docker network
- **Performance**: No need to go through reverse proxy for backend API calls
- **Reliability**: Direct container-to-container communication

---

## Checking Container Connectivity

### List All Containers and IPs

```bash
docker-compose -f docker-compose-wso2.yml ps -a
docker network inspect darts-network
```

### Test Connectivity from darts-app Container

```bash
# From host, run command inside container
docker-compose -f docker-compose-wso2.yml exec darts-app \
  bash -c "apt-get update && apt-get install -y telnet && \
  telnet postgres 5432"

# Should show: Connected to postgres
# Type: quit
```

### Test DNS Resolution

```bash
docker-compose -f docker-compose-wso2.yml exec darts-app \
  bash -c "apt-get update && apt-get install -y dnsutils && \
  nslookup postgres"

# Should show IP address of postgres container
```

---

## Port Mapping vs Service Names

### Port Mapping (for external access from host)

```yaml
postgres:
  ports:
    - "5432:5432" # Format: host_port:container_port
```

Allows: `postgresql://localhost:5432` from host machine

### Service Names (for internal Docker network)

Service names don't need port mappings! They're only for host access.

```yaml
postgres:
  # No ports needed for container-to-container communication!
  networks:
    - darts-network
```

Allows: `postgresql://postgres:5432` from other containers on `darts-network`

---

## Debugging Tips

### Q: Why is my connection failing?

**Check 1**: Is the service name correct?

```bash
# List services in docker-compose
grep "^  [a-z]:" docker-compose-wso2.yml
```

**Check 2**: Is the container running?

```bash
docker-compose -f docker-compose-wso2.yml ps
# Should show all services with status "Up"
```

**Check 3**: Is the container on the right network?

```bash
docker network inspect darts-network | grep -A 20 "Containers"
# Should list: darts-app, postgres, rabbitmq, wso2is, etc.
```

**Check 4**: Is the port correct?

```bash
# Check what port the service is listening on inside container
docker-compose -f docker-compose-wso2.yml exec postgres \
  ss -tlnp | grep LISTEN
```

---

## Quick Reference: Service Names & Ports

```
Service       | Hostname    | Internal Port | Host Port | Usage
──────────────┼─────────────┼───────────────┼───────────┼──────────────
postgres      | postgres    | 5432          | 5432      | Database
rabbitmq      | rabbitmq    | 5672          | 5672      | Message Broker
wso2is        | wso2is      | 9443          | 9443      | Auth (HTTPS)
wso2is        | wso2is      | 9763          | 9763      | Auth (HTTP)
wso2apim      | wso2apim    | 9443          | 9444      | API Manager
darts-app     | darts-app   | 5000          | 5000      | Main App
api-gateway   | api-gateway | 8080          | 8080      | API Gateway
```

---

## Summary

| Concept                   | Local Development       | Docker Development                     |
| ------------------------- | ----------------------- | -------------------------------------- |
| **Database Connection**   | `localhost:5432`        | `postgres:5432`                        |
| **RabbitMQ Connection**   | `localhost:5672`        | `rabbitmq:5672`                        |
| **WSO2 Connection**       | `localhost:9443`        | `wso2is:9443`                          |
| **Access from Host**      | Direct to `localhost`   | Via exposed ports to `localhost`       |
| **Access from Container** | N/A                     | Via service name on Docker network     |
| **Access from Browser**   | `http://localhost:5000` | `https://letsplaydarts.eu` (via nginx) |

---

**Key Takeaway**: Always use **service names** for container-to-container communication in Docker, not localhost!
