#!/bin/bash

# Mosaic Demo Status Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Mosaic Demo Status Check              ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# ── Check Services ───────────────────────────────────────────────────
echo -e "${BLUE}Services Status:${NC}"
echo ""

# PostgreSQL
echo -n "  PostgreSQL (5432):     "
if timeout 2 bash -c "cat < /dev/null > /dev/tcp/localhost/5432" 2>/dev/null; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${RED}✗ Not Running${NC}"
fi

# Neo4j
echo -n "  Neo4j (7687):          "
if timeout 2 bash -c "cat < /dev/null > /dev/tcp/localhost/7687" 2>/dev/null; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${RED}✗ Not Running${NC}"
fi

# MCP HTTP Server
echo -n "  MCP HTTP (8001):       "
if timeout 2 bash -c "cat < /dev/null > /dev/tcp/localhost/8001" 2>/dev/null; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${RED}✗ Not Running${NC}"
fi

# Ollama
echo -n "  Ollama (11434):        "
if timeout 2 bash -c "cat < /dev/null > /dev/tcp/localhost/11434" 2>/dev/null; then
    echo -e "${GREEN}✓ Running${NC}"
else
    echo -e "${YELLOW}⚠ Not Running${NC}"
fi

# ── Check Processes ──────────────────────────────────────────────────
echo ""
echo -e "${BLUE}Processes:${NC}"
echo ""

if [ -f ".demo.pid" ]; then
    MCP_PID=$(cat .demo.pid)
    echo -n "  MCP Server (PID $MCP_PID): "
    if ps -p $MCP_PID > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Running${NC}"
    else
        echo -e "${RED}✗ Not Running (stale PID file)${NC}"
    fi
else
    echo -e "  ${YELLOW}No .demo.pid file found${NC}"
fi

# Check for any MCP processes
MCP_PROCS=$(pgrep -f "mosaic.mcp" || true)
if [ ! -z "$MCP_PROCS" ]; then
    echo ""
    echo -e "  ${BLUE}Other MCP Processes:${NC}"
    echo "$MCP_PROCS" | while read pid; do
        CMD=$(ps -p $pid -o cmd= 2>/dev/null || echo "Unknown")
        echo -e "    PID $pid: ${GREEN}$CMD${NC}"
    done
fi

# ── Check Docker Containers ──────────────────────────────────────────
echo ""
echo -e "${BLUE}Docker Containers:${NC}"
echo ""

POSTGRES_CONTAINER=$(docker ps --filter "expose=5432" --format "{{.ID}}\t{{.Names}}\t{{.Status}}" 2>/dev/null || true)
if [ ! -z "$POSTGRES_CONTAINER" ]; then
    echo -e "  PostgreSQL: ${GREEN}$POSTGRES_CONTAINER${NC}"
else
    echo -e "  PostgreSQL: ${YELLOW}No container found${NC}"
fi

NEO4J_CONTAINER=$(docker ps --filter "expose=7687" --format "{{.ID}}\t{{.Names}}\t{{.Status}}" 2>/dev/null || true)
if [ ! -z "$NEO4J_CONTAINER" ]; then
    echo -e "  Neo4j:      ${GREEN}$NEO4J_CONTAINER${NC}"
else
    echo -e "  Neo4j:      ${YELLOW}No container found${NC}"
fi

# ── API Health Check ─────────────────────────────────────────────────
echo ""
echo -e "${BLUE}API Health:${NC}"
echo ""

if timeout 2 bash -c "cat < /dev/null > /dev/tcp/localhost/8001" 2>/dev/null; then
    HEALTH=$(curl -s http://localhost:8001/health 2>/dev/null || echo "Failed")
    if [ "$HEALTH" != "Failed" ]; then
        echo -e "  ${GREEN}✓ MCP Server: $HEALTH${NC}"
    else
        echo -e "  ${YELLOW}⚠ MCP Server: Cannot reach /health endpoint${NC}"
    fi
else
    echo -e "  ${RED}✗ MCP Server: Not accessible${NC}"
fi

# ── Log Files ────────────────────────────────────────────────────────
echo ""
echo -e "${BLUE}Recent Logs:${NC}"
echo ""

if [ -f "logs/mcp-server.log" ]; then
    echo -e "  ${BLUE}Last 5 lines of logs/mcp-server.log:${NC}"
    tail -n 5 logs/mcp-server.log | sed 's/^/    /'
else
    echo -e "  ${YELLOW}No log file found${NC}"
fi

echo ""
echo -e "${BLUE}─────────────────────────────────────────────────${NC}"
echo ""
