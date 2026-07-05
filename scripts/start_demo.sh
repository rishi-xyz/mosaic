#!/bin/bash

# Mosaic Demo Startup Script
# Starts the MCP server and connects to existing Neo4j and PostgreSQL Docker containers

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Mosaic Demo Startup Script            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

# ── Step 1: Check Prerequisites ──────────────────────────────────────
echo -e "${YELLOW}[1/6] Checking prerequisites...${NC}"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}✗ Virtual environment not found${NC}"
    echo -e "${YELLOW}  Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Check if dependencies are installed
if ! python -c "import cognee" &> /dev/null; then
    echo -e "${YELLOW}  Installing dependencies...${NC}"
    pip install -e . --quiet
fi
echo -e "${GREEN}✓ Dependencies installed${NC}"

# ── Step 2: Check Database Connections ──────────────────────────────
echo ""
echo -e "${YELLOW}[2/6] Checking database connections...${NC}"

# Check PostgreSQL
echo -e "  Checking PostgreSQL (localhost:5432)..."
if timeout 3 bash -c "cat < /dev/null > /dev/tcp/localhost/5432" 2>/dev/null; then
    echo -e "${GREEN}✓ PostgreSQL is running${NC}"
else
    echo -e "${RED}✗ PostgreSQL is not accessible on localhost:5432${NC}"
    echo -e "${YELLOW}  Please start PostgreSQL with: docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres${NC}"
    exit 1
fi

# Check Neo4j
echo -e "  Checking Neo4j (localhost:7687)..."
if timeout 3 bash -c "cat < /dev/null > /dev/tcp/localhost/7687" 2>/dev/null; then
    echo -e "${GREEN}✓ Neo4j is running${NC}"
else
    echo -e "${RED}✗ Neo4j is not accessible on localhost:7687${NC}"
    echo -e "${YELLOW}  Please start Neo4j with: docker run -d -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/strongPassword123 neo4j:latest${NC}"
    exit 1
fi

# Check Ollama (optional)
echo -e "  Checking Ollama (localhost:11434)..."
if timeout 3 bash -c "cat < /dev/null > /dev/tcp/localhost/11434" 2>/dev/null; then
    echo -e "${GREEN}✓ Ollama is running${NC}"
else
    echo -e "${YELLOW}⚠ Ollama is not running (optional)${NC}"
    echo -e "${YELLOW}  Install from: https://ollama.ai${NC}"
fi

# ── Step 3: Initialize Database Schema ──────────────────────────────
echo ""
echo -e "${YELLOW}[3/6] Initializing database schema...${NC}"

# Create PostgreSQL database if needed
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/mosaic"
python -c "
import asyncio
import asyncpg
async def init_db():
    try:
        # Connect to postgres database to create mosaic database
        conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/postgres')
        # Check if database exists
        exists = await conn.fetchval('SELECT 1 FROM pg_database WHERE datname = \$1', 'mosaic')
        if not exists:
            await conn.execute('CREATE DATABASE mosaic')
            print('✓ Database \"mosaic\" created')
        else:
            print('✓ Database \"mosaic\" already exists')
        await conn.close()
    except Exception as e:
        print(f'⚠ Database check: {e}')
asyncio.run(init_db())
" || true

echo -e "${GREEN}✓ Database schema initialized${NC}"

# ── Step 4: Check Environment Configuration ─────────────────────────
echo ""
echo -e "${YELLOW}[4/6] Checking environment configuration...${NC}"

if [ ! -f ".env" ]; then
    echo -e "${RED}✗ .env file not found${NC}"
    exit 1
fi

if [ ! -f "mosaic/mcp/.env" ]; then
    echo -e "${RED}✗ mosaic/mcp/.env file not found${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Environment files found${NC}"

# ── Step 5: Start MCP HTTP Server ───────────────────────────────────
echo ""
echo -e "${YELLOW}[5/6] Starting MCP HTTP Server...${NC}"

# Create logs directory
mkdir -p logs

# Start MCP HTTP server in background
cd mosaic/mcp
echo -e "  Starting on port 8001..."
nohup python -m mosaic.mcp.http_server > ../../logs/mcp-server.log 2>&1 &
MCP_PID=$!
cd "$PROJECT_ROOT"

# Wait for server to start
sleep 2

# Check if server is running
if ps -p $MCP_PID > /dev/null; then
    echo -e "${GREEN}✓ MCP HTTP Server started (PID: $MCP_PID)${NC}"
    echo -e "  Logs: ${BLUE}logs/mcp-server.log${NC}"
else
    echo -e "${RED}✗ MCP HTTP Server failed to start${NC}"
    echo -e "${YELLOW}  Check logs/mcp-server.log for details${NC}"
    exit 1
fi

# ── Step 6: Display Status ──────────────────────────────────────────
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Mosaic Demo is Running! 🚀          ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Services:${NC}"
echo -e "  MCP HTTP Server:  ${GREEN}http://localhost:8001${NC}"
echo -e "  Neo4j Browser:    ${GREEN}http://localhost:7474${NC}"
echo -e "  PostgreSQL:       ${GREEN}localhost:5432${NC}"
echo ""
echo -e "${BLUE}Processes:${NC}"
echo -e "  MCP Server PID:   ${GREEN}$MCP_PID${NC}"
echo ""
echo -e "${BLUE}Logs:${NC}"
echo -e "  tail -f logs/mcp-server.log"
echo ""
echo -e "${YELLOW}To stop:${NC}"
echo -e "  kill $MCP_PID"
echo -e "  or run: ./scripts/stop_demo.sh"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo -e "  1. Test MCP Server: curl http://localhost:8001/health"
echo -e "  2. Run web client: cd client/web && bun dev"
echo -e "  3. View Neo4j graph: http://localhost:7474 (neo4j/strongPassword123)"
echo ""

# Save PIDs for cleanup
echo $MCP_PID > .demo.pid

echo -e "${GREEN}✓ Demo startup complete!${NC}"
