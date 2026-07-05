#!/bin/bash

# Mosaic Demo Test Script
# Tests the MCP server API endpoints

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║         Mosaic Demo Test Script               ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════╝${NC}"
echo ""

BASE_URL="http://localhost:8001"

# Test 1: Health Check
echo -e "${YELLOW}[1/5] Testing Health Endpoint...${NC}"
HEALTH=$(curl -s "$BASE_URL/health")
if echo "$HEALTH" | grep -q "ok"; then
    echo -e "${GREEN}✓ Health check passed${NC}"
    echo "  Response: $HEALTH"
else
    echo -e "${RED}✗ Health check failed${NC}"
    exit 1
fi

echo ""

# Test 2: OpenAPI Docs
echo -e "${YELLOW}[2/5] Testing OpenAPI Documentation...${NC}"
OPENAPI=$(curl -s "$BASE_URL/openapi.json" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('info', {}).get('title', 'Unknown'))" 2>/dev/null)
if [ ! -z "$OPENAPI" ]; then
    echo -e "${GREEN}✓ OpenAPI docs available${NC}"
    echo "  Title: $OPENAPI"
    echo "  URL: ${BLUE}$BASE_URL/docs${NC}"
else
    echo -e "${YELLOW}⚠ Could not fetch OpenAPI docs${NC}"
fi

echo ""

# Test 3: List Available Tools
echo -e "${YELLOW}[3/5] Listing Available MCP Tools...${NC}"
TOOLS=$(curl -s -X POST "$BASE_URL/mcp/tools/list" \
    -H "Content-Type: application/json" \
    -d '{}' 2>/dev/null)

if echo "$TOOLS" | grep -q "tools"; then
    echo -e "${GREEN}✓ Tools endpoint working${NC}"
    # Parse and display tool names
    echo "$TOOLS" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    tools = data.get('tools', [])
    if tools:
        print('  Available tools:')
        for tool in tools:
            name = tool.get('name', 'Unknown')
            desc = tool.get('description', 'No description')
            print(f'    - {name}: {desc[:60]}...' if len(desc) > 60 else f'    - {name}: {desc}')
    else:
        print('  No tools found')
except:
    pass
" 2>/dev/null || echo "  (Could not parse tools)"
else
    echo -e "${YELLOW}⚠ Could not list tools${NC}"
fi

echo ""

# Test 4: Database Connections
echo -e "${YELLOW}[4/5] Testing Database Connections...${NC}"

# PostgreSQL
echo -n "  PostgreSQL: "
if timeout 2 bash -c "cat < /dev/null > /dev/tcp/localhost/5432" 2>/dev/null; then
    echo -e "${GREEN}✓ Connected${NC}"
else
    echo -e "${RED}✗ Not accessible${NC}"
fi

# Neo4j
echo -n "  Neo4j:      "
if timeout 2 bash -c "cat < /dev/null > /dev/tcp/localhost/7687" 2>/dev/null; then
    echo -e "${GREEN}✓ Connected${NC}"
else
    echo -e "${RED}✗ Not accessible${NC}"
fi

echo ""

# Test 5: System Info
echo -e "${YELLOW}[5/5] System Information...${NC}"

# Check if web client is running
echo -n "  Web Client (3000): "
if timeout 2 bash -c "cat < /dev/null > /dev/tcp/localhost/3000" 2>/dev/null; then
    echo -e "${GREEN}✓ Running${NC}"
    echo "     URL: ${BLUE}http://localhost:3000${NC}"
else
    echo -e "${YELLOW}⚠ Not running${NC}"
    echo "     Start with: cd client/web && bun dev"
fi

echo ""

# Summary
echo -e "${GREEN}╔════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Test Summary                         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}MCP Server:${NC}"
echo -e "  Health:      ${GREEN}✓${NC}"
echo -e "  API Docs:    ${BLUE}http://localhost:8001/docs${NC}"
echo -e "  Swagger UI:  ${BLUE}http://localhost:8001/docs${NC}"
echo -e "  ReDoc:       ${BLUE}http://localhost:8001/redoc${NC}"
echo ""
echo -e "${BLUE}Databases:${NC}"
echo -e "  Neo4j UI:    ${BLUE}http://localhost:7474${NC}"
echo -e "  PostgreSQL:  ${BLUE}localhost:5432${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo -e "  1. Explore API:    ${BLUE}http://localhost:8001/docs${NC}"
echo -e "  2. View graph:     ${BLUE}http://localhost:7474${NC}"
echo -e "  3. Start web UI:   ${BLUE}cd client/web && bun dev${NC}"
echo -e "  4. Ingest data:    ${BLUE}python -m mosaic.connectors.github${NC}"
echo ""
echo -e "${GREEN}✓ All tests completed!${NC}"
