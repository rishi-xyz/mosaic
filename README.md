# Mosaic

**Small pieces. Big picture. Forever memory.**

> **The Operating System for Persistent AI Memory**

---

## What is Mosaic?

Mosaic is a platform that enables AI agents to build, evolve, and reason over long-term memory using [Cognee](https://github.com/topoteretes/cognee). Instead of treating memory as retrieved context, Mosaic treats it as a continuously evolving knowledge graph that powers multiple intelligent applications.

Most AI systems work like this:

```
User → Prompt → Vector Search → LLM
```

Every interaction starts from almost zero. Mosaic changes the architecture — memory becomes a living system rather than temporary context.

Mosaic is **not another AI assistant.** It is infrastructure.

Just as Linux is an operating system, Kubernetes manages containers, and Git manages code — Mosaic manages long-term AI memory. Applications are built on top of it.

---

## Quick Start

### Prerequisites

1. **Docker** - Running PostgreSQL and Neo4j containers
2. **Python 3.14+** - With uv or pip
3. **Ollama** (optional) - For local LLM support

### One-Line Demo

```bash
./scripts/demo.sh
```

This launches an interactive menu to:
- ✓ Start the MCP server
- ✓ Check system status
- ✓ Run tests
- ✓ Ingest GitHub data
- ✓ Query the memory graph

### Manual Setup

```bash
# 1. Start databases
docker run -d --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres
docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/strongPassword123 neo4j

# 2. Start the demo
./scripts/start_demo.sh

# 3. Check status
./scripts/status_demo.sh

# 4. Test the API
curl http://localhost:8001/health

# 5. View in browser
open http://localhost:8001/docs  # API documentation
open http://localhost:7474       # Neo4j graph browser
```

### Available Scripts

| Script | Purpose |
|--------|---------|
| `scripts/demo.sh` | Interactive demo controller |
| `scripts/start_demo.sh` | Start MCP server |
| `scripts/stop_demo.sh` | Stop all services |
| `scripts/status_demo.sh` | Check system status |
| `scripts/test_demo.sh` | Run API tests |

---

## Architecture

```
Events
  │
  ▼
Cognee Memory Graph
  │
  ▼
Knowledge Evolution
  │
  ▼
Reasoning Engine
  │
  ▼
Agents
  │
  ▼
Memory Update
  │
  ▼
Smarter Memory
```

### Core Components

#### 1. Event Engine
Continuously ingests events from GitHub, Slack, Jira, Notion, Google Docs, Calendar, and meetings. Everything becomes memory.

#### 2. Memory Engine
Creates entities, updates knowledge, links relationships, removes stale information, and maintains history. Powered by Cognee.

#### 3. Knowledge Graph
Stores relationships between people, projects, files, decisions, issues, conversations, meetings, and architecture. Memory becomes connected instead of isolated.

#### 4. Reasoning Engine
Instead of simple document retrieval, it finds evidence, connects relationships, understands timelines, generates explanations, and updates memory.

#### 5. Plugin System
Every domain becomes a plugin that inherits the Mosaic architecture:

```
MemoryPlugin → ingest() → extract() → reason() → update() → visualize()
```

---

## Directory Structure

```
mosaic/
│
├── core/
│   ├── memory-engine/
│   ├── reasoning-engine/
│   ├── event-engine/
│   ├── graph-engine/
│   └── plugin-engine/
│
├── connectors/
│   ├── github/
│   ├── slack/
│   ├── notion/
│   ├── jira/
│   ├── docs/
│   └── meetings/
│
├── plugins/
│   ├── engineering-brain/
│   ├── research-brain/
│   ├── startup-brain/
│   └── support-brain/
│
├── api/
├── ui/
├── demo/
├── docs/
└── README.md
```

---

## Design Principles

- **Memory over Context** — Don't retrieve; remember.
- **Relationships over Documents** — Connect the dots, don't just find files.
- **Reasoning over Retrieval** — Explain, don't just search.
- **Evolution over Snapshots** — Memory grows, it doesn't reset.
- **Shared Intelligence over Isolated Agents** — Every agent contributes, every agent learns.
- **Infrastructure over Application** — Build the OS, not another app.

---

## Roadmap

### v1
- Mosaic Core
- Cognee Integration
- GitHub Connector
- Engineering Brain
- Knowledge Graph
- Reasoning Engine

### v2
- Slack Connector
- Jira Connector
- Notion Connector
- Meeting Transcripts
- Timeline Replay

### v3
- Multi-Agent Shared Memory
- Memory Conflict Resolution
- Temporal Graph Queries
- Cross-Agent Learning

### v4
- Plugin Marketplace
- Research Brain
- Startup Brain
- Support Brain
- Legal Brain

### v5
- Public SDK
- Memory APIs
- Graph Visualization
- Distributed Memory
- Enterprise Deployment

---

## Tech Stack (Proposed)

| Layer | Technology |
|---|---|
| Frontend | Next.js, React, TailwindCSS |
| Backend | FastAPI, Python |
| Memory Layer | Cognee |
| Knowledge Graph | Neo4j / NetworkX |
| LLMs | OpenAI, Anthropic, Local models |
| Connectors | GitHub API, Slack API, Notion API, Jira API |

---

## Getting Started

Coming soon.

---

## Contributing

Coming soon.

---

## License

[MIT](LICENSE)
