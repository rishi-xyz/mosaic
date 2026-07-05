#!/bin/bash

# Mosaic Demo Stop Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Mosaic Demo Stop Script               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

# Check if PID file exists
if [ ! -f ".demo.pid" ]; then
    echo -e "${YELLOW}⚠ No running demo found (.demo.pid not found)${NC}"
    echo -e "${YELLOW}  Checking for any running processes...${NC}"
else
    MCP_PID=$(cat .demo.pid)
    
    echo -e "${YELLOW}Stopping MCP Server (PID: $MCP_PID)...${NC}"
    if ps -p $MCP_PID > /dev/null; then
        kill $MCP_PID
        echo -e "${GREEN}✓ MCP Server stopped${NC}"
    else
        echo -e "${YELLOW}⚠ MCP Server (PID: $MCP_PID) not running${NC}"
    fi
    
    rm .demo.pid
fi

# Find and kill any remaining processes
echo ""
echo -e "${YELLOW}Checking for remaining processes...${NC}"

# Kill any remaining MCP servers
pkill -f "mosaic.mcp.http_server" && echo -e "${GREEN}✓ Stopped remaining MCP servers${NC}" || true
pkill -f "mosaic.mcp.server" && echo -e "${GREEN}✓ Stopped remaining MCP servers${NC}" || true

echo ""
echo -e "${GREEN}✓ All demo processes stopped${NC}"
echo ""
echo -e "${YELLOW}Note: Database containers (PostgreSQL, Neo4j) are still running${NC}"
echo -e "To stop them:"
echo -e "  docker ps  # Find container IDs"
echo -e "  docker stop <container_id>"
echo ""
