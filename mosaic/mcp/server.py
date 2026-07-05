import asyncio
import os
from dotenv import load_dotenv

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

from mosaic.core.config import configure_cognee


def _load_env():
    env_path = os.path.join(os.getcwd(), ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)


async def _search_cognee(query: str, dataset: str = "mosaic_engineering_memory") -> str:
    import cognee
    from cognee.modules.search.types import SearchType

    results = await cognee.search(
        query_text=query,
        query_type=SearchType.GRAPH_COMPLETION,
        datasets=[dataset],
    )
    return str(results)


server = Server("mosaic")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="ask",
            description="General reasoning over engineering memory. Ask about decisions, architecture, history.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Question about the codebase or engineering decisions",
                    },
                },
                "required": ["query"],
            },
        ),
        types.Tool(
            name="entity",
            description="Get everything related to a file, person, or concept in the engineering memory.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "File path, person login, or concept name",
                    },
                },
                "required": ["name"],
            },
        ),
        types.Tool(
            name="timeline",
            description="Chronological evolution of a topic, file, or feature.",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "Topic, file, or feature to trace",
                    },
                },
                "required": ["topic"],
            },
        ),
        types.Tool(
            name="related",
            description="Find the connected graph around an entity — linked PRs, issues, decisions, files.",
            inputSchema={
                "type": "object",
                "properties": {
                    "entity_id": {
                        "type": "string",
                        "description": "Entity ID or name to expand around",
                    },
                },
                "required": ["entity_id"],
            },
        ),
        types.Tool(
            name="pre_change_analysis",
            description="Analyze risk, owners, history, and related files before making a change.",
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path of the file about to be changed",
                    },
                },
                "required": ["file_path"],
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent]:
    _load_env()
    configure_cognee()
    if not arguments:
        arguments = {}

    if name == "ask":
        query = arguments.get("query", "")
        result = await _search_cognee(query)
        return [types.TextContent(type="text", text=result)]

    elif name == "entity":
        entity_name = arguments.get("name", "")
        result = await _search_cognee(f"Find everything related to {entity_name}")
        return [types.TextContent(type="text", text=result)]

    elif name == "timeline":
        topic = arguments.get("topic", "")
        result = await _search_cognee(f"Show the chronological evolution of {topic}")
        return [types.TextContent(type="text", text=result)]

    elif name == "related":
        entity_id = arguments.get("entity_id", "")
        result = await _search_cognee(f"What is connected to {entity_id}?")
        return [types.TextContent(type="text", text=result)]

    elif name == "pre_change_analysis":
        file_path = arguments.get("file_path", "")
        result = await _search_cognee(
            f"Risk assessment, owners, history, related files, and decisions for {file_path}"
        )
        return [types.TextContent(type="text", text=result)]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    _load_env()
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
