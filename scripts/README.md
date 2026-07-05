# Mosaic Demo Scripts

Quick start scripts to spin up the Mosaic demo environment.

## Prerequisites

1. **Docker containers running:**
   ```bash
   # PostgreSQL
   docker run -d --name postgres \
     -p 5432:5432 \
     -e POSTGRES_PASSWORD=postgres \
     postgres:latest
   
   # Neo4j
   docker run -d --name neo4j \
     -p 7474:7474 -p 7687:7687 \
     -e NEO4J_AUTH=neo4j/strongPassword123 \
     neo4j:latest
   ```

2. **Ollama (optional but recommended):**
   - Install from: https://ollama.ai
   - Pull model: `ollama pull llama3.2:3b`
   - Pull embeddings: `ollama pull nomic-embed-text`

3. **Environment files:**
   - `.env` in project root
   - `mosaic/mcp/.env` for MCP server

## Scripts

### Start Demo
```bash
./scripts/start_demo.sh
```

Starts the MCP HTTP server and connects to existing databases.

**Features:**
- ✓ Checks all prerequisites
- ✓ Validates database connections
- ✓ Initializes database schema
- ✓ Starts MCP HTTP server on port 8001
- ✓ Logs to `logs/mcp-server.log`

### Stop Demo
```bash
./scripts/stop_demo.sh
```

Stops all demo processes (but leaves Docker containers running).

### Check Status
```bash
./scripts/status_demo.sh
```

Shows the status of all services, processes, and health checks.

## Usage

```bash
# 1. Start the demo
./scripts/start_demo.sh

# 2. In another terminal, check status
./scripts/status_demo.sh

# 3. Test the MCP server
curl http://localhost:8001/health

# 4. View logs
tail -f logs/mcp-server.log

# 5. Stop when done
./scripts/stop_demo.sh
```

## Services

After starting:

| Service | URL | Credentials |
|---------|-----|-------------|
| MCP HTTP Server | http://localhost:8001 | - |
| Neo4j Browser | http://localhost:7474 | neo4j / strongPassword123 |
| PostgreSQL | localhost:5432 | postgres / postgres |
| Ollama | http://localhost:11434 | - |

## Troubleshooting

### PostgreSQL not accessible
```bash
docker ps  # Check if container is running
docker logs postgres  # Check logs
```

### Neo4j not accessible
```bash
docker ps  # Check if container is running
docker logs neo4j  # Check logs
```

### MCP server won't start
```bash
cat logs/mcp-server.log  # Check error logs
source .venv/bin/activate
python -m mosaic.mcp.http_server  # Run in foreground to see errors
```

### Port already in use
```bash
# Find process using port 8001
lsof -i :8001
# Kill it
kill <PID>
```

## Development

To run in development mode with auto-reload:

```bash
source .venv/bin/activate
cd mosaic/mcp
uvicorn mosaic.mcp.http_server:app --reload --port 8001
```

## Next Steps

1. **Test the API**: See [API documentation](../../docs/api.md)
2. **Run the web client**: `cd client/web && bun dev`
3. **Ingest GitHub data**: Run the GitHub connector
4. **Explore the graph**: Open Neo4j Browser and run `MATCH (n) RETURN n LIMIT 25`
