#!/bin/bash

# Mosaic Complete Demo Runner
# Shows a full workflow: start → test → interact

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

clear

echo -e "${MAGENTA}"
cat << "EOF"
███╗   ███╗ ██████╗ ███████╗ █████╗ ██╗ ██████╗
████╗ ████║██╔═══██╗██╔════╝██╔══██╗██║██╔════╝
██╔████╔██║██║   ██║███████╗███████║██║██║     
██║╚██╔╝██║██║   ██║╚════██║██╔══██║██║██║     
██║ ╚═╝ ██║╚██████╔╝███████║██║  ██║██║╚██████╗
╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝ ╚═════╝
EOF
echo -e "${NC}"

echo -e "${CYAN}The Operating System for Persistent AI Memory${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# ── Menu ─────────────────────────────────────────────────────────────
show_menu() {
    echo -e "${BLUE}What would you like to do?${NC}"
    echo ""
    echo "  1) 🚀 Start Demo (Full Setup)"
    echo "  2) 📊 Check Status"
    echo "  3) 🧪 Run Tests"
    echo "  4) 📖 View Logs"
    echo "  5) 🌐 Open Interfaces"
    echo "  6) 📥 Ingest GitHub Data"
    echo "  7) 🔍 Query Memory"
    echo "  8) 🛑 Stop Demo"
    echo "  9) ℹ️  Help"
    echo "  0) 👋 Exit"
    echo ""
    echo -n "Choose an option: "
}

# ── Actions ──────────────────────────────────────────────────────────

start_demo() {
    echo ""
    echo -e "${YELLOW}Starting Mosaic Demo...${NC}"
    echo ""
    ./scripts/start_demo.sh
    echo ""
    read -p "Press Enter to continue..."
}

check_status() {
    echo ""
    ./scripts/status_demo.sh
    echo ""
    read -p "Press Enter to continue..."
}

run_tests() {
    echo ""
    ./scripts/test_demo.sh
    echo ""
    read -p "Press Enter to continue..."
}

view_logs() {
    echo ""
    echo -e "${YELLOW}Recent logs (last 20 lines):${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    if [ -f "logs/mcp-server.log" ]; then
        tail -n 20 logs/mcp-server.log
        echo ""
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        echo -e "Full logs: ${CYAN}tail -f logs/mcp-server.log${NC}"
    else
        echo -e "${RED}No logs found${NC}"
    fi
    echo ""
    read -p "Press Enter to continue..."
}

open_interfaces() {
    echo ""
    echo -e "${YELLOW}Opening interfaces...${NC}"
    echo ""
    
    # Detect OS and open browser
    if command -v xdg-open &> /dev/null; then
        OPEN_CMD="xdg-open"
    elif command -v open &> /dev/null; then
        OPEN_CMD="open"
    else
        echo -e "${YELLOW}Could not detect browser command${NC}"
        echo "Please open manually:"
        echo ""
        echo -e "  ${CYAN}http://localhost:8001/docs${NC}  - MCP API"
        echo -e "  ${CYAN}http://localhost:7474${NC}       - Neo4j Browser"
        echo ""
        read -p "Press Enter to continue..."
        return
    fi
    
    echo "Opening:"
    echo -e "  ${CYAN}http://localhost:8001/docs${NC}  - MCP API"
    $OPEN_CMD "http://localhost:8001/docs" 2>/dev/null &
    
    sleep 1
    
    echo -e "  ${CYAN}http://localhost:7474${NC}       - Neo4j Browser"
    $OPEN_CMD "http://localhost:7474" 2>/dev/null &
    
    echo ""
    echo -e "${GREEN}✓ Interfaces opened in browser${NC}"
    echo ""
    read -p "Press Enter to continue..."
}

ingest_github() {
    echo ""
    echo -e "${YELLOW}Ingesting GitHub Data...${NC}"
    echo ""
    echo "This will fetch and process GitHub data from the configured repository."
    echo ""
    read -p "Continue? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        source .venv/bin/activate
        echo ""
        python -m mosaic.connectors.github
        echo ""
        echo -e "${GREEN}✓ GitHub data ingestion complete${NC}"
    else
        echo -e "${YELLOW}Cancelled${NC}"
    fi
    echo ""
    read -p "Press Enter to continue..."
}

query_memory() {
    echo ""
    echo -e "${YELLOW}Query Memory System${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Example queries:"
    echo ""
    echo "1. Get all tools:"
    echo -e "   ${CYAN}curl -X POST http://localhost:8001/mcp/tools/list -H 'Content-Type: application/json' -d '{}'${NC}"
    echo ""
    echo "2. Query memory:"
    echo -e "   ${CYAN}curl -X POST http://localhost:8001/mcp/tools/call -H 'Content-Type: application/json' -d '{...}'${NC}"
    echo ""
    echo "3. View Neo4j graph:"
    echo -e "   ${CYAN}Open http://localhost:7474 and run: MATCH (n) RETURN n LIMIT 25${NC}"
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    read -p "Press Enter to continue..."
}

stop_demo() {
    echo ""
    echo -e "${YELLOW}Stopping Mosaic Demo...${NC}"
    echo ""
    ./scripts/stop_demo.sh
    echo ""
    read -p "Press Enter to continue..."
}

show_help() {
    echo ""
    echo -e "${CYAN}Mosaic Demo Help${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}Quick Start:${NC}"
    echo "  1. Select 'Start Demo' to launch all services"
    echo "  2. Select 'Open Interfaces' to view in browser"
    echo "  3. Select 'Ingest GitHub Data' to populate memory"
    echo "  4. Explore the API and Neo4j graph"
    echo ""
    echo -e "${YELLOW}Architecture:${NC}"
    echo "  • MCP Server (port 8001) - Memory interface"
    echo "  • PostgreSQL (port 5432) - Relational data"
    echo "  • Neo4j (port 7687/7474) - Knowledge graph"
    echo "  • Ollama (port 11434) - Local LLM"
    echo ""
    echo -e "${YELLOW}Key Features:${NC}"
    echo "  • Persistent memory across sessions"
    echo "  • Knowledge graph relationships"
    echo "  • GitHub/Slack integration"
    echo "  • MCP protocol for AI agents"
    echo ""
    echo -e "${YELLOW}Documentation:${NC}"
    echo "  • README:  ${CYAN}cat README.md${NC}"
    echo "  • Scripts: ${CYAN}ls -la scripts/${NC}"
    echo "  • API:     ${CYAN}http://localhost:8001/docs${NC}"
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    read -p "Press Enter to continue..."
}

# ── Main Loop ────────────────────────────────────────────────────────

while true; do
    clear
    echo -e "${MAGENTA}╔════════════════════════════════════════════════╗${NC}"
    echo -e "${MAGENTA}║           Mosaic Demo Controller              ║${NC}"
    echo -e "${MAGENTA}╚════════════════════════════════════════════════╝${NC}"
    echo ""
    
    show_menu
    read -r choice
    
    case $choice in
        1) start_demo ;;
        2) check_status ;;
        3) run_tests ;;
        4) view_logs ;;
        5) open_interfaces ;;
        6) ingest_github ;;
        7) query_memory ;;
        8) stop_demo ;;
        9) show_help ;;
        0) 
            echo ""
            echo -e "${GREEN}Thanks for using Mosaic! 👋${NC}"
            echo ""
            exit 0
            ;;
        *)
            echo ""
            echo -e "${RED}Invalid option${NC}"
            sleep 1
            ;;
    esac
done
