import asyncio

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

from mosaic.mcp.tools import (
    TOOL_DEFINITIONS,
    load_env,
    configure_cognee,
    handle_ask,
    handle_entity,
    handle_timeline,
    handle_related,
    handle_pre_change_analysis,
    handle_github_ingest,
)


server = Server("mosaic")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name=name,
            description=spec["description"],
            inputSchema=spec["input_schema"],
        )
        for name, spec in TOOL_DEFINITIONS.items()
    ]


_TOOL_HANDLERS = {
    "memory_query": handle_ask,
    "memory_entity_get": handle_entity,
    "memory_timeline": handle_timeline,
    "memory_related_get": handle_related,
    "analysis_pre_change": handle_pre_change_analysis,
    "github_ingest": handle_github_ingest,
}


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    if not arguments:
        arguments = {}

    handler = _TOOL_HANDLERS.get(name)
    if not handler:
        raise ValueError(f"Unknown tool: {name}")

    text = await handler(**arguments)
    return [types.TextContent(type="text", text=text)]


async def main():
    load_env()
    configure_cognee()
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="mosaic",
                server_version="0.1.0",
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
