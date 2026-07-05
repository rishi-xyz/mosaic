import asyncio

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

from mosaic.mcp.tools import (
    load_env,
    configure_cognee,
    handle_ask,
    handle_entity,
    handle_timeline,
    handle_related,
    handle_pre_change_analysis,
)


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
                    "source": {
                        "type": "string",
                        "description": "Filter by source (github, slack, or empty for all)",
                        "enum": ["", "github", "slack"],
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
                    "limit": {
                        "type": "number",
                        "description": "Maximum results to return (default 50)",
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
                    "depth": {
                        "type": "number",
                        "description": "How many hops deep to traverse (default 1)",
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
    if not arguments:
        arguments = {}

    if name == "ask":
        query = arguments.get("query", "")
        text = await handle_ask(query)
        return [types.TextContent(type="text", text=text)]

    elif name == "entity":
        entity_name = arguments.get("name", "")
        text = await handle_entity(entity_name)
        return [types.TextContent(type="text", text=text)]

    elif name == "timeline":
        topic = arguments.get("topic", "")
        text = await handle_timeline(topic)
        return [types.TextContent(type="text", text=text)]

    elif name == "related":
        entity_id = arguments.get("entity_id", "")
        text = await handle_related(entity_id)
        return [types.TextContent(type="text", text=text)]

    elif name == "pre_change_analysis":
        file_path = arguments.get("file_path", "")
        text = await handle_pre_change_analysis(file_path)
        return [types.TextContent(type="text", text=text)]

    else:
        raise ValueError(f"Unknown tool: {name}")


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
