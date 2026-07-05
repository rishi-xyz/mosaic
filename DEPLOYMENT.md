# Mosaic Deployment Guide

This guide covers production deployment for both the **Web Application** and **MCP Server**.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Database Setup](#database-setup)
4. [Web Application Deployment](#web-application-deployment)
5. [MCP Server Deployment](#mcp-server-deployment)
6. [Multi-Tenant Configuration](#multi-tenant-configuration)
7. [Troubleshooting](#troubleshooting)

---

## Architecture Overview

Mosaic consists of two independent services:

```
┌─────────────────────┐         ┌─────────────────────┐
│   Web Application   │         │    MCP Server       │
│   (Next.js)         │         │    (FastAPI)        │
│                     │         │                     │
│   • User Interface  │         │   • Memory Queries  │
│   • Authentication  │         │   • Reasoning       │
│   • API Management  │         │   • Graph Ops       │
└──────────┬──────────┘         └──────────┬──────────┘
           │                               │
           │         ┌─────────────────────┤
           │         │                     │
           ▼         ▼                     ▼
    ┌──────────────────────┐    ┌──────────────────┐
    │   PostgreSQL         │    │   Neo4j          │
    │   (User/Config)      │    │   (Memory Graph) │
    └──────────────────────┘    └──────────────────┘
```

### Key Design Principles

- **Isolated Configuration**: Each service has its own `.env` file
- **No Race Conditions**: Config is passed through function parameters, not global state
- **Multi-Tenant Support**: User-specific configs stored in PostgreSQL
- **Scalability**: MCP server can scale independently from the web app

---

## Prerequisites

### System Requirements

- **Python**: 3.11+
- **Node.js**: 18+
- **PostgreSQL**: 14+
- **Neo4j**: 5.0+
- **Bun** (optional, for web app): Latest

### Infrastructure

- **Compute**: 2+ CPU cores, 4GB+ RAM recommended
- **Storage**: 10GB+ for databases
- **Network**: HTTPS for production

---

## Database Setup

### PostgreSQL

1. **Create Database**:
   ```bash
   createdb mosaic
   ```

2. **Initialize Schema**:
   ```bash
   cd client/web
   npx prisma migrate deploy
   ```

### Neo4j

1. **Start Neo4j**:
   ```bash
   # Docker
   docker run -d \
     -p 7474:7474 -p 7687:7687 \
     -e NEO4J_AUTH=neo4j/strongPassword123 \
     neo4j:latest

   # Or use Neo4j Desktop / AuraDB
   ```

2. **Verify Connection**:
   ```bash
   # Visit http://localhost:7474
   # Login with neo4j / strongPassword123
   ```

---

## Web Application Deployment

The web app handles user authentication, API key management, and ingestion scheduling.

### 1. Setup Environment

```bash
cd client/web
cp .env.example .env
```

### 2. Configure `.env`

```env
# Database (PostgreSQL)
DATABASE_URL="postgresql://user:password@host:5432/mosaic?schema=public"

# Authentication (NextAuth)
NEXTAUTH_SECRET="generate-random-secret-here"
NEXTAUTH_URL="https://yourdomain.com"

# Optional: OAuth Providers
# GITHUB_ID="..."
# GITHUB_SECRET="..."
```

**Generate `NEXTAUTH_SECRET`**:
```bash
openssl rand -base64 32
```

### 3. Install Dependencies

```bash
# With Bun
bun install

# Or with npm
npm install
```

### 4. Build for Production

```bash
# With Bun
bun run build

# Or with npm
npm run build
```

### 5. Deploy

#### Option A: Vercel (Recommended)

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

**Environment Variables**: Add all `.env` values to Vercel project settings.

#### Option B: Docker

```dockerfile
# client/web/Dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package.json bun.lock ./
RUN npm install
COPY . .
RUN npm run build

FROM node:18-alpine
WORKDIR /app
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
EXPOSE 3000
CMD ["npm", "start"]
```

```bash
docker build -t mosaic-web .
docker run -p 3000:3000 --env-file .env mosaic-web
```

#### Option C: PM2

```bash
pm2 start npm --name "mosaic-web" -- start
pm2 save
pm2 startup
```

---

## MCP Server Deployment

The MCP server provides memory queries and reasoning capabilities. It can be used standalone or integrated with Claude Desktop, Cursor, or other MCP-compatible clients.

### 1. Setup Environment

```bash
cd mosaic/mcp
cp .env.example .env
```

### 2. Configure `mosaic/mcp/.env`

```env
# Database (PostgreSQL) - For multi-tenant user configs
DATABASE_URL=postgresql://user:password@host:5432/mosaic

# MCP Server Port
MCP_PORT=8001

# Optional: Static API Key (for single-tenant deployments)
# MCP_API_KEY=your-secret-key-here

# Optional: Disable auth (for development only)
# MCP_DISABLE_AUTH=true
```

**Important**: The MCP server `.env` is **separate** from the root `.env`. This prevents configuration conflicts.

### 3. Install Dependencies

```bash
# From project root
uv pip install -e .
```

### 4. Deploy

#### Option A: Systemd Service (Linux)

Create `/etc/systemd/system/mosaic-mcp.service`:

```ini
[Unit]
Description=Mosaic MCP Server
After=network.target postgresql.service neo4j.service

[Service]
Type=simple
User=mosaic
WorkingDirectory=/opt/mosaic
ExecStart=/opt/mosaic/.venv/bin/mosaic-mcp-http
Restart=always
RestartSec=10
Environment="PATH=/opt/mosaic/.venv/bin:/usr/local/bin:/usr/bin"

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable mosaic-mcp
sudo systemctl start mosaic-mcp
sudo systemctl status mosaic-mcp
```

#### Option B: Docker

```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e .
EXPOSE 8001
CMD ["mosaic-mcp-http"]
```

```bash
docker build -t mosaic-mcp .
docker run -d -p 8001:8001 --env-file mosaic/mcp/.env mosaic-mcp
```

#### Option C: Fly.io

Create `fly.toml`:

```toml
app = "mosaic-mcp"

[build]
  builder = "paketobuildpacks/builder:base"

[env]
  PORT = "8001"

[[services]]
  http_checks = []
  internal_port = 8001
  protocol = "tcp"

  [[services.ports]]
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443
```

```bash
fly launch
fly secrets set DATABASE_URL="postgresql://..."
fly deploy
```

### 5. Verify Deployment

```bash
# Health check
curl http://localhost:8001/health

# Test query (requires auth)
curl -X POST http://localhost:8001/mcp/tools/call \
  -H "Authorization: Bearer your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ask",
    "arguments": {"query": "What is the latest PR?"}
  }'
```

---

## Multi-Tenant Configuration

Mosaic supports multiple users with isolated configurations.

### How It Works

1. **User Registration**: Users sign up via the web app
2. **API Key Generation**: Web app generates unique API keys per user
3. **Configuration Storage**: User-specific configs (GitHub tokens, Neo4j credentials) stored in PostgreSQL
4. **Request Isolation**: MCP server loads user config per-request using API key
5. **No Global State**: Config passed through function parameters, preventing race conditions

### Database Schema

```sql
-- Users table
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- API keys table
CREATE TABLE api_keys (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  key TEXT UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- User configurations
CREATE TABLE user_configs (
  id SERIAL PRIMARY KEY,
  user_id INTEGER REFERENCES users(id),
  github_token TEXT,
  github_repository TEXT,
  slack_token TEXT,
  neo4j_url TEXT,
  neo4j_username TEXT,
  neo4j_password TEXT,
  -- ... other config fields
);
```

### Authentication Flow

```
Client Request
   │
   ├─→ Authorization: Bearer <api-key>
   │
   ▼
MCP Server
   │
   ├─→ Validate API key in PostgreSQL
   │
   ├─→ Load user_config from database
   │
   ├─→ Convert config (githubToken → GITHUB_TOKEN)
   │
   ├─→ Pass config dict to handlers
   │
   ▼
Handlers (ask, entity, timeline, ...)
   │
   ├─→ configure_cognee(config)
   │
   ├─→ Execute query with user's Neo4j/LLM
   │
   ▼
Response
```

### Single-Tenant Mode

For simple deployments, you can use a static API key:

```env
# mosaic/mcp/.env
MCP_API_KEY=my-secret-key-12345
```

Then authenticate:
```bash
curl -H "Authorization: Bearer my-secret-key-12345" ...
```

---

## Troubleshooting

### Common Issues

#### 1. "Invalid API key" Error

**Cause**: API key not in database or `MCP_API_KEY` not set.

**Fix**:
```bash
# Check environment
cat mosaic/mcp/.env

# Verify database connection
psql $DATABASE_URL -c "SELECT * FROM api_keys;"

# For dev, disable auth temporarily
echo "MCP_DISABLE_AUTH=true" >> mosaic/mcp/.env
```

#### 2. Race Condition / Config Conflicts

**Symptoms**: User A sees User B's data, or environment variables leak between requests.

**Cause**: Using `apply_config()` which modifies `os.environ`.

**Fix**: Ensure you're using the new config-passing approach:
```python
# ❌ OLD (causes race conditions)
apply_config(user_config)
result = await handle_ask(query)

# ✅ NEW (thread-safe)
result = await handle_ask(query, config=user_config)
```

#### 3. "Connection refused" to Neo4j

**Cause**: Neo4j not running or wrong credentials.

**Fix**:
```bash
# Check Neo4j status
docker ps | grep neo4j

# Test connection
cypher-shell -u neo4j -p strongPassword123 "RETURN 1;"

# Verify URL in config
echo $GRAPH_DATABASE_URL
```

#### 4. MCP Server Won't Start

**Symptoms**: `mosaic-mcp-http` command not found or crashes.

**Fix**:
```bash
# Reinstall in development mode
uv pip install -e .

# Check entry point
cat pyproject.toml | grep mosaic-mcp-http

# Verify Python path
which python
python --version  # Should be 3.11+
```

### Logs

#### Web App (Next.js)

```bash
# Development
npm run dev

# Production (PM2)
pm2 logs mosaic-web

# Production (Docker)
docker logs mosaic-web

# Production (Vercel)
# Check Vercel dashboard → Functions → Logs
```

#### MCP Server

```bash
# Systemd
journalctl -u mosaic-mcp -f

# Docker
docker logs -f mosaic-mcp

# Manual run (with debug logs)
MOSAIC_LOG_LEVEL=DEBUG mosaic-mcp-http
```

### Health Checks

```bash
# Web app
curl http://localhost:3000/api/health

# MCP server
curl http://localhost:8001/health

# PostgreSQL
psql $DATABASE_URL -c "SELECT 1;"

# Neo4j
curl -u neo4j:strongPassword123 http://localhost:7474/db/neo4j/tx/commit \
  -H "Content-Type: application/json" \
  -d '{"statements":[{"statement":"RETURN 1"}]}'
```

---

## Security Best Practices

### Production Checklist

- [ ] Use HTTPS (TLS certificates via Let's Encrypt)
- [ ] Rotate `NEXTAUTH_SECRET` regularly
- [ ] Never commit `.env` files
- [ ] Use environment-specific `.env` files (`.env.production`, `.env.staging`)
- [ ] Enable PostgreSQL SSL: `?sslmode=require`
- [ ] Restrict Neo4j access (firewall rules)
- [ ] Set strong Neo4j password (not `strongPassword123`)
- [ ] Rate-limit MCP endpoints (nginx, Cloudflare, etc.)
- [ ] Monitor failed auth attempts
- [ ] Backup PostgreSQL and Neo4j regularly

### API Key Security

```bash
# Generate secure API keys
openssl rand -hex 32

# Rotate keys regularly (invalidate old keys)
psql $DATABASE_URL -c "UPDATE api_keys SET revoked=true WHERE created_at < NOW() - INTERVAL '90 days';"
```

---

## Monitoring

### Metrics to Track

- **Web App**: Request latency, error rate, active users
- **MCP Server**: Query latency, Cognee ingestion time, Neo4j query performance
- **Databases**: Connection pool usage, disk space, query slow logs

### Tools

- **Prometheus + Grafana**: Metrics collection and dashboards
- **Sentry**: Error tracking (for both Next.js and FastAPI)
- **DataDog / New Relic**: APM for distributed tracing
- **Neo4j Enterprise**: Built-in monitoring tools

---

## Scaling

### Horizontal Scaling

```
                      ┌─→ MCP Server 1
Load Balancer (nginx) ─┼─→ MCP Server 2
                      └─→ MCP Server 3
```

**Requirements**:
- Shared PostgreSQL and Neo4j (avoid per-instance databases)
- Stateless MCP server (no in-memory session storage)
- Health checks: `/health` endpoint

### Vertical Scaling

- **Neo4j**: Add RAM for graph caching
- **PostgreSQL**: Tune `shared_buffers`, `work_mem`
- **MCP Server**: Increase workers (`uvicorn --workers 4`)

---

## Backup and Recovery

### PostgreSQL Backup

```bash
# Daily backup
pg_dump $DATABASE_URL > backup-$(date +%Y%m%d).sql

# Restore
psql $DATABASE_URL < backup-20260705.sql
```

### Neo4j Backup

```bash
# Stop Neo4j
neo4j stop

# Backup data directory
tar -czf neo4j-backup-$(date +%Y%m%d).tar.gz /var/lib/neo4j/data

# Start Neo4j
neo4j start

# Or use neo4j-admin dump (Enterprise)
neo4j-admin dump --database=neo4j --to=/backups/neo4j-$(date +%Y%m%d).dump
```

---

## Rollback Strategy

If deployment fails:

1. **Revert code**: `git checkout <previous-commit>`
2. **Rollback database migrations**: `npx prisma migrate resolve --rolled-back <migration-name>`
3. **Restart services**: `systemctl restart mosaic-mcp`
4. **Verify health checks**: `curl http://localhost:8001/health`

---

## Support

- **GitHub Issues**: [mosaic/issues](https://github.com/your-org/mosaic/issues)
- **Documentation**: [mosaic docs](https://docs.mosaic.dev)
- **Community**: [Discord](https://discord.gg/mosaic)

---

**Last Updated**: July 5, 2026
