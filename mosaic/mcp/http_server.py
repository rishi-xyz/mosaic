from fastapi import FastAPI
from mcp.server.fastmcp import FastMCP

from mosaic.mcp.tools import (
    load_env,
    configure_cognee,
    handle_ask,
    handle_entity,
    handle_timeline,
    handle_related,
    handle_pre_change_analysis,
)

mcp = FastMCP("mosaic")


@mcp.tool(description="General reasoning over engineering memory. Ask about decisions, architecture, history.")
async def ask(query: str) -> str:
    return await handle_ask(query)


@mcp.tool(description="Get everything related to a file, person, or concept in the engineering memory.")
async def entity(name: str) -> str:
    return await handle_entity(name)


@mcp.tool(description="Chronological evolution of a topic, file, or feature.")
async def timeline(topic: str, limit: int = 50) -> str:
    return await handle_timeline(topic, limit)


@mcp.tool(description="Find the connected graph around an entity — linked PRs, issues, decisions, files.")
async def related(entity_id: str, depth: int = 1) -> str:
    return await handle_related(entity_id, depth)


@mcp.tool(description="Analyze risk, owners, history, and related files before making a change.")
async def pre_change_analysis(file_path: str) -> str:
    return await handle_pre_change_analysis(file_path)


def create_app() -> FastAPI:
    load_env()
    configure_cognee()

    app = FastAPI(title="Mosaic MCP Server")
    sse_app = mcp.sse_app()
    app.mount("/mcp", sse_app)

    @app.get("/health")
    async def health():
        return {"status": "ok", "server": "mosaic-mcp"}

    return app


app = create_app()
