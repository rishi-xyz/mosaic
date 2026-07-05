import asyncio
import os
from dotenv import load_dotenv

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

from mosaic.core.config import configure_cognee
from mosaic.core.memory.query import (
    get_entity_by_name,
    get_timeline,
    get_related,
    cross_source_query,
)


def _load_env():
    env_path = os.path.join(os.getcwd(), ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)


server = Server("mosaic")


def _format_subgraph(data: dict) -> str:
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    lines = [f"Found {len(nodes)} nodes, {len(edges)} edges"]

    for n in nodes:
        label = f"[{n.get('type', '?')}] {n.get('name', n.get('id', '?'))}"
        if n.get("description"):
            label += f" — {n['description']}"
        lines.append(f"  {label}")

    for e in edges:
        lines.append(
            f"  {e['source_node_id']} -[{e['relationship_name']}]-> {e['target_node_id']}"
        )

    return "\n".join(lines)


def _format_timeline(events: list) -> str:
    lines = [f"Timeline: {len(events)} events"]
    for ev in events:
        ts = ev.get("timestamp") or "(no date)"
        node = ev.get("node", {})
        label = f"[{node.get('type', '?')}] {node.get('name', node.get('id', '?'))}"
        desc = ev.get("description", "")
        related = ev.get("related_node_ids", [])
        extra = f" ({len(related)} related)" if related else ""
        lines.append(f"  {ts}  {label}{extra}")
        if desc:
            lines.append(f"    {desc}")
    return "\n".join(lines)


def _format_result(result: dict) -> str:
    fast_path = result.get("fast_path", False)
    data = result.get("data", "")

    if fast_path:
        if isinstance(data, list):
            if data and isinstance(data[0], dict):
                if "timestamp" in data[0] or "node" in data[0]:
                    return _format_timeline(data)
                return f"Found {len(data)} results:\n" + "\n".join(
                    f"  [{n.get('type', '?')}] {n.get('name', n.get('id', '?'))}"
                    for n in data
                )
        if isinstance(data, dict):
            if "nodes" in data:
                return _format_subgraph(data)
        return str(data)
    else:
        return str(data)


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
    _load_env()
    configure_cognee()
    if not arguments:
        arguments = {}

    if name == "ask":
        query = arguments.get("query", "")
        result = await cross_source_query(query)
        return [types.TextContent(type="text", text=_format_result(result))]

    elif name == "entity":
        entity_name = arguments.get("name", "")
        result = await get_entity_by_name(entity_name)
        return [types.TextContent(type="text", text=_format_result(result))]

    elif name == "timeline":
        topic = arguments.get("topic", "")
        result = await get_timeline(topic)
        return [types.TextContent(type="text", text=_format_result(result))]

    elif name == "related":
        entity_id = arguments.get("entity_id", "")
        result = await get_related(entity_id)
        return [types.TextContent(type="text", text=_format_result(result))]

    elif name == "pre_change_analysis":
        file_path = arguments.get("file_path", "")
        result = await cross_source_query(
            f"Risk assessment, owners, history, related files, and decisions for {file_path}"
        )
        return [types.TextContent(type="text", text=_format_result(result))]

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
