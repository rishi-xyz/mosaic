import os
from dotenv import load_dotenv

from mosaic.core.config import configure_cognee
from mosaic.core.memory.query import (
    get_entity_by_name,
    get_timeline,
    get_related,
    cross_source_query,
)


def load_env():
    env_path = os.path.join(os.getcwd(), ".env")
    if os.path.exists(env_path):
        load_dotenv(env_path)


def format_subgraph(data: dict) -> str:
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


def format_timeline(events: list) -> str:
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


def format_result(result: dict) -> str:
    fast_path = result.get("fast_path", False)
    data = result.get("data", "")

    if fast_path:
        if isinstance(data, list):
            if data and isinstance(data[0], dict):
                if "timestamp" in data[0] or "node" in data[0]:
                    return format_timeline(data)
                return f"Found {len(data)} results:\n" + "\n".join(
                    f"  [{n.get('type', '?')}] {n.get('name', n.get('id', '?'))}"
                    for n in data
                )
        if isinstance(data, dict):
            if "nodes" in data:
                return format_subgraph(data)
        return str(data)
    else:
        return str(data)


async def handle_ask(query: str) -> str:
    result = await cross_source_query(query)
    return format_result(result)


async def handle_entity(name: str, source: str = "") -> str:
    result = await get_entity_by_name(name)
    return format_result(result)


async def handle_timeline(topic: str, limit: int = 50) -> str:
    result = await get_timeline(topic)
    return format_result(result)


async def handle_related(entity_id: str, depth: int = 1) -> str:
    result = await get_related(entity_id)
    return format_result(result)


async def handle_pre_change_analysis(file_path: str) -> str:
    result = await cross_source_query(
        f"Risk assessment, owners, history, related files, and decisions for {file_path}"
    )
    return format_result(result)
