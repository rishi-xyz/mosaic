import os
from dotenv import load_dotenv

from mosaic.core.config import configure_cognee
from mosaic.core.memory.query import (
    get_entity_by_name,
    get_timeline,
    get_related,
    cross_source_query,
)


# ── Shared tool definitions ─────────────────────────────────────────────
TOOL_DEFINITIONS = {
    "memory_query": {
        "description": (
            "General-purpose reasoning over the engineering knowledge graph. "
            "Use this to ask open-ended questions about decisions, architecture, "
            "historical context, or relationships between entities. "
            "Returns structured answers with evidence drawn from the memory graph, "
            "including references to PRs, issues, commits, files, and discussions. "
            "Prefer this tool when you don't know exactly which entity you're looking for."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Open-ended question about the codebase, architecture, decisions, or engineering history",
                }
            },
            "required": ["query"],
        },
    },
    "memory_entity_get": {
        "description": (
            "Retrieve all stored knowledge about a specific entity — a file path, "
            "GitHub username, concept name, or component. "
            "Use this when you need the full picture of what the system knows about "
            "a particular thing. "
            "Returns the entity's type, description, metadata, and links to related "
            "PRs, issues, commits, decisions, and discussions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Entity name: file path, person login, or concept name to look up",
                },
                "source": {
                    "type": "string",
                    "description": "Filter by data source (empty for all, 'github' or 'slack')",
                    "enum": ["", "github", "slack"],
                },
            },
            "required": ["name"],
        },
    },
    "memory_timeline": {
        "description": (
            "Show the chronological evolution of a topic, file, feature, or decision over time. "
            "Use this to understand how something changed, key milestones, and when decisions "
            "were made. "
            "Returns events in date order with timestamps, descriptions, and linked entities."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Topic, file, or feature to trace through history",
                },
                "limit": {
                    "type": "number",
                    "description": "Maximum number of timeline events to return (default 50)",
                },
            },
            "required": ["topic"],
        },
    },
    "memory_related_get": {
        "description": (
            "Explore the connected graph around an entity to discover indirect relationships. "
            "Use this to find what's linked to an entity beyond direct connections — such as "
            "PRs that touch related files, decisions connected to a component, or Slack "
            "discussions about a feature. "
            "Returns a subgraph of connected nodes and their relationship edges."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "entity_id": {
                    "type": "string",
                    "description": "Entity ID or name to expand the graph around",
                },
                "depth": {
                    "type": "number",
                    "description": "How many relationship hops deep to traverse (default 1)",
                },
            },
            "required": ["entity_id"],
        },
    },
    "analysis_pre_change": {
        "description": (
            "Analyze risk, ownership, history, and potential impact before modifying a code file. "
            "Use this tool BEFORE making any change to understand who owns the file, "
            "its commit history, related decisions, linked issues and PRs, "
            "and what other files depend on it. "
            "Returns a risk assessment including owners, change frequency, and related entities."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Path of the file about to be changed, relative to repository root",
                },
            },
            "required": ["file_path"],
        },
    },
    "github_ingest": {
        "description": (
            "Fetch issues, pull requests, commits, and reviews from a GitHub repository "
            "and ingest them into the engineering memory graph. "
            "Use this to populate the knowledge graph so the memory tools (memory_query, "
            "memory_entity_get, etc.) can answer questions about the repo. "
            "After ingestion, you can ask about issues, decisions, architecture, and history. "
            "Requires a GITHUB_TOKEN to be configured. "
            "Returns a summary of what was ingested."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "repo": {
                    "type": "string",
                    "description": "GitHub repository in 'owner/name' format (e.g. 'rishi-xyz/mosaic'). Falls back to GITHUB_REPOSITORY env var.",
                },
                "max_issues": {
                    "type": "number",
                    "description": "Maximum issues to fetch (default 100)",
                },
                "max_prs": {
                    "type": "number",
                    "description": "Maximum pull requests to fetch (default 50)",
                },
                "max_commits": {
                    "type": "number",
                    "description": "Maximum commits to fetch (default 100)",
                },
            },
            "required": [],
        },
    },
}


def load_env():
    # Try local mcp/.env first
    local_env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(local_env_path):
        load_dotenv(local_env_path)
        return
    
    # Fallback to root .env
    root_env_path = os.path.join(os.getcwd(), ".env")
    if os.path.exists(root_env_path):
        load_dotenv(root_env_path)


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


async def handle_ask(query: str, config: dict | None = None) -> str:
    """Handle general reasoning query with optional config."""
    if config:
        configure_cognee(config)
    result = await cross_source_query(query)
    return format_result(result)


async def handle_entity(name: str, source: str = "", config: dict | None = None) -> str:
    """Get entity by name with optional config."""
    if config:
        configure_cognee(config)
    result = await get_entity_by_name(name)
    return format_result(result)


async def handle_timeline(topic: str, limit: int = 50, config: dict | None = None) -> str:
    """Get timeline for a topic with optional config."""
    if config:
        configure_cognee(config)
    result = await get_timeline(topic)
    return format_result(result)


async def handle_related(entity_id: str, depth: int = 1, config: dict | None = None) -> str:
    """Get related entities with optional config."""
    if config:
        configure_cognee(config)
    result = await get_related(entity_id)
    return format_result(result)


async def handle_pre_change_analysis(file_path: str, config: dict | None = None) -> str:
    """Analyze file before change with optional config."""
    if config:
        configure_cognee(config)
    result = await cross_source_query(
        f"Risk assessment, owners, history, related files, and decisions for {file_path}"
    )
    return format_result(result)


async def handle_github_ingest(
    repo: str = "",
    max_issues: int = 100,
    max_prs: int = 50,
    max_commits: int = 100,
    config: dict | None = None,
) -> str:
    """Fetch GitHub data and ingest it into the memory graph."""
    import asyncio
    from mosaic.connectors.github.client import get_github_client, get_repo
    from mosaic.connectors.github.events import fetch_all
    from mosaic.core.normalizer.github_normalizer import normalize_entities
    from mosaic.core.memory.service import process_and_ingest

    if config:
        configure_cognee(config)

    client = get_github_client(config)
    repo_name = repo or os.environ.get("GITHUB_REPOSITORY", "")
    if not repo_name:
        return "Error: No repository specified. Set GITHUB_REPOSITORY env var or pass a repo parameter (e.g. 'owner/name')."

    gh_repo = get_repo(client, repo_name)

    raw_data = await asyncio.to_thread(
        fetch_all, gh_repo,
        max_issues=max_issues, max_prs=max_prs, max_commits=max_commits,
    )

    normalized = await asyncio.to_thread(normalize_entities, raw_data)

    enriched = await process_and_ingest(normalized)

    return (
        f"Ingested data from {repo_name}:\n"
        f"  • {len(enriched.get('issues', []))} issues\n"
        f"  • {len(enriched.get('pull_requests', []))} pull requests\n"
        f"  • {len(enriched.get('commits', []))} commits\n"
        f"  • {len(enriched.get('reviews', []))} reviews\n"
        f"  • {len(enriched.get('files', []))} files\n"
        f"  • {len(enriched.get('authors', []))} authors\n"
        f"  • {len(enriched.get('decisions', []))} decisions\n"
        f"Memory graph updated. You can now use memory_query, memory_entity_get, and other tools to explore this data."
    )
