# Mosaic — MCP Server + Web App

## Architecture

```
┌──────────────────┐  API (JWT)   ┌──────────────────────┐     ┌──────────────┐
│  Next.js Web App │◀───────────▶│  Python FastAPI       │◀───▶│  PostgreSQL  │
│  (port 3000)     │              │  REST Server          │     │  (shared)    │
│  Auth.js +       │              │  (not yet built)      │     │              │
│  Prisma          │              │  /api/* endpoints     │     │  Users       │
│                  │              │                       │     │  API Keys    │
│  Pages:          │              └──────────────────────┘     │  Configs     │
│  /               │                          ▲                 └──────┬───────┘
│  /login          │                          │                        │
│  /signup         │                          │                        │
│  /dashboard      │                          │                        │
│  /dashboard/     │   MCP over SSE           │                        │
│    api-keys      │   (API Key auth)         │                        │
│  /dashboard/     │                          │                        │
│    settings      └──────────────────────────┼────────────────────────┘
                                              │
                                     ┌────────▼────────┐
                                     │  MCP Server      │
                                     │  (Python)        │
                                     │  port 8001       │
                                     │                  │
                                     │  5 tools:        │
                                     │  ask             │
                                     │  entity          │
                                     │  timeline        │
                                     │  related         │
                                     │  pre_change_     │
                                     │  analysis        │
                                     │                  │
                                     │  Core Engine     │
                                     │  (Cognee+Neo4j)  │
                                     └──────────────────┘
```

## Project Structure

```
mosaic/
├── mosaic/
│   ├── core/               ← Core engine (Cognee, Neo4j, normalizers, enrichers)
│   ├── connectors/         ← GitHub & Slack connectors
│   ├── mcp/
│   │   ├── server.py       ← Stdio MCP server (original entry point)
│   │   ├── http_server.py  ← HTTP/SSE MCP server (FastAPI + FastMCP)
│   │   └── tools.py        ← Shared tool handlers
│   └── api/
│       └── database.py     ← PostgreSQL connection for API key auth
├── client/web/             ← Next.js web app (Next.js 16, Auth.js, Prisma, Tailwind v4)
│   ├── app/
│   │   ├── page.tsx        ← Landing page (untouched)
│   │   ├── layout.tsx      ← Root layout with SessionProvider
│   │   ├── (auth)/
│   │   │   ├── login/      ← Login page
│   │   │   └── signup/     ← Signup page
│   │   ├── (dashboard)/
│   │   │   ├── layout.tsx  ← Dashboard layout with sidebar
│   │   │   ├── page.tsx    ← Dashboard home
│   │   │   ├── api-keys/   ← API key management
│   │   │   └── settings/   ← Brain configuration
│   │   └── api/
│   │       ├── auth/[...nextauth]  ← Auth.js handler
│   │       └── auth/signup         ← Signup endpoint
│   │       ├── keys/       ← API key CRUD
│   │       └── config/     ← User config CRUD
│   ├── lib/
│   │   ├── auth.ts         ← Auth.js configuration
│   │   ├── auth-types.d.ts ← Auth.js type declarations
│   │   └── prisma.ts       ← Prisma client singleton
│   ├── components/
│   │   ├── SessionProvider.tsx
│   │   ├── dashboard/Sidebar.tsx
│   │   └── landing/        ← Landing page components (untouched)
│   └── prisma/
│       └── schema.prisma   ← User, ApiKey, UserConfig models
├── pyproject.toml           ← Python deps + CLI entry points
└── PLAN.md                 ← This file
```

## Database Schema (shared)

All three services (web app, MCP server, REST API) share one PostgreSQL database.

| Table | Purpose | Managed by |
|-------|---------|------------|
| `User` | User accounts | Prisma (web app) |
| `ApiKey` | API keys for MCP auth | Prisma (web app) |
| `UserConfig` | Per-user brain config (JSONB) | Prisma (web app) |

The MCP server reads `ApiKey` (for validation) and `UserConfig` (for per-user Cognee config) directly via asyncpg.

## Getting Started

### Prerequisites

- Python 3.14+
- Node.js 22+
- PostgreSQL 16+
- Neo4j (optional, for fast-path queries)
- Ollama (optional, for local LLM)

### 1. MCP Server

```bash
# Start MCP server in dev mode (no auth)
MCP_DISABLE_AUTH=true uvicorn mosaic.mcp.http_server:app --port 8001 --reload

# Or with a static API key
MCP_API_KEY=my-secret-key uvicorn mosaic.mcp.http_server:app --port 8001 --reload

# Or via CLI entry point
MCP_DISABLE_AUTH=true mosaic-mcp-http
```

AI agents connect to: `http://localhost:8001/mcp`

### 2. Web App

```bash
cd client/web

# Install deps
npm install

# Set up database
# Edit .env with your DATABASE_URL
npx prisma db push

# Start dev server
npm run dev
```

Open `http://localhost:3000`

### 3. Connecting MCP + Web App

1. Sign up at the web app
2. Generate an API key in Settings → API Keys
3. Set `DATABASE_URL` env var on the MCP server (it reads keys from the shared DB)
4. Configure AI agent:

```json
{
  "mcpServers": {
    "mosaic": {
      "url": "http://localhost:8001/mcp",
      "headers": {
        "Authorization": "Bearer mosaic_abc123..."
      }
    }
  }
}
```

## Auth Modes

| Mode | Env Var | Behavior |
|------|---------|----------|
| Dev (no auth) | `MCP_DISABLE_AUTH=true` | No API key required |
| Static key | `MCP_API_KEY=<key>` | Single shared key |
| Dynamic (DB) | `DATABASE_URL=<postgres-url>` | Per-user keys from web app |

## MCP Tools

| Tool | Description |
|------|-------------|
| `ask(query)` | General reasoning over engineering memory |
| `entity(name)` | Get everything about a file/person/concept |
| `timeline(topic)` | Chronological evolution of a topic |
| `related(entity_id)` | Connected graph around an entity |
| `pre_change_analysis(file_path)` | Risk/history before a change |

## Commit History (branch: `mcp`)

```
ac69b32  feat(mcp): add API key auth middleware with dev mode and static key
9adaacb  feat(web): add auth, dashboard, API keys, settings, and API routes
81e7a2b  chore: add asyncpg, fastapi, uvicorn deps and HTTP server entry point
2145654  feat(mcp): add HTTP/SSE MCP server with FastMCP — no auth
fb82232  refactor(mcp): extract tool handlers into shared tools module
```

## Next Steps (Not Yet Implemented)

- Python FastAPI REST server (separate process for `/api/*` endpoints)
- Docker Compose setup for one-command startup
- Ingestion trigger pages in web app
- OAuth providers in Auth.js (GitHub, Google)
