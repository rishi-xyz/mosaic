import os
import contextvars
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from mcp.server.fastmcp import FastMCP

from mosaic.core.config import configure_cognee
from mosaic.mcp.tools import (
    load_env,
    handle_ask,
    handle_entity,
    handle_timeline,
    handle_related,
    handle_pre_change_analysis,
)

# Per-request user config for multi-tenant support
current_user_config: contextvars.ContextVar[dict] = contextvars.ContextVar("user_config", default={})


def apply_config(config: dict):
    """Apply user-specific config as environment overrides then reconfigure Cognee."""
    if not config:
        return
    for key, value in config.items():
        if value is not None:
            os.environ[key.upper()] = str(value)
    configure_cognee()


mcp = FastMCP("mosaic")


@mcp.tool(description="General reasoning over engineering memory. Ask about decisions, architecture, history.")
async def ask(query: str) -> str:
    apply_config(current_user_config.get())
    return await handle_ask(query)


@mcp.tool(description="Get everything related to a file, person, or concept in the engineering memory.")
async def entity(name: str) -> str:
    apply_config(current_user_config.get())
    return await handle_entity(name)


@mcp.tool(description="Chronological evolution of a topic, file, or feature.")
async def timeline(topic: str, limit: int = 50) -> str:
    apply_config(current_user_config.get())
    return await handle_timeline(topic, limit)


@mcp.tool(description="Find the connected graph around an entity — linked PRs, issues, decisions, files.")
async def related(entity_id: str, depth: int = 1) -> str:
    apply_config(current_user_config.get())
    return await handle_related(entity_id, depth)


@mcp.tool(description="Analyze risk, owners, history, and related files before making a change.")
async def pre_change_analysis(file_path: str) -> str:
    apply_config(current_user_config.get())
    return await handle_pre_change_analysis(file_path)


def create_app() -> FastAPI:
    load_env()
    configure_cognee()

    app = FastAPI(title="Mosaic MCP Server")

    # API key auth middleware
    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        if request.url.path.startswith("/mcp"):
            auth_header = request.headers.get("Authorization", "")
            api_key_env = os.environ.get("MCP_API_KEY", "")
            disable_auth = os.environ.get("MCP_DISABLE_AUTH", "").lower() == "true"

            if disable_auth:
                # Dev mode — no auth required
                pass
            elif api_key_env:
                # Static API key from env (simple shared key)
                expected = f"Bearer {api_key_env}"
                if auth_header != expected:
                    return JSONResponse(
                        {"error": "Invalid API key"},
                        status_code=401,
                    )
            elif auth_header.startswith("Bearer "):
                # Dynamic API key lookup from shared PostgreSQL database
                api_key = auth_header[7:]
                from mosaic.api.database import validate_api_key, get_user_config
                user_id = await validate_api_key(api_key)
                if user_id is None:
                    return JSONResponse(
                        {"error": "Invalid API key"},
                        status_code=401,
                    )
                config = await get_user_config(user_id)
                current_user_config.set(config)
            else:
                return JSONResponse(
                    {"error": "Missing API key. Set Authorization: Bearer <key>"},
                    status_code=401,
                )

        return await call_next(request)

    sse_app = mcp.sse_app()
    app.mount("/mcp", sse_app)

    @app.get("/health")
    async def health():
        return {"status": "ok", "server": "mosaic-mcp"}

    return app


app = create_app()


def main():
    import uvicorn
    uvicorn.run("mosaic.mcp.http_server:app", host="0.0.0.0", port=8001, reload=True)


if __name__ == "__main__":
    main()
