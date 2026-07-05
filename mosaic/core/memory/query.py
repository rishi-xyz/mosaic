import os

import cognee
from cognee.modules.search.types import SearchType

from mosaic.core.memory.graph_query import (
    get_entity_by_name as _fast_entity,
    get_neighbors as _fast_neighbors,
    get_timeline as _fast_timeline,
    search_entities as _fast_search,
)
from mosaic.core.memory.models import GraphSubgraph


_DATASET = "mosaic_engineering_memory"


def _use_fast_path() -> bool:
    return bool(os.environ.get("GRAPH_DATABASE_PASSWORD"))


async def _llm_search(query: str, dataset: str = _DATASET) -> str:
    try:
        results = await cognee.search(
            query_text=query,
            query_type=SearchType.GRAPH_COMPLETION,
            datasets=[dataset],
        )
        return str(results)
    except Exception as e:
        return f"Search error: {e}"


async def get_entity(entity_id: str, dataset: str = _DATASET) -> dict:
    if _use_fast_path():
        subgraph = _fast_entity(entity_id)
        if subgraph and subgraph.nodes:
            return {
                "fast_path": True,
                "data": subgraph.to_dict(),
            }

    raw = await _llm_search(
        f"Find the entity with source_id '{entity_id}'. "
        f"Return its type, title, body, metadata, and all linked entities.",
        dataset,
    )
    return {"fast_path": False, "data": raw}


async def get_entity_by_name(name: str, dataset: str = _DATASET) -> dict:
    if _use_fast_path():
        subgraph = _fast_entity(name)
        if subgraph and subgraph.nodes:
            return {
                "fast_path": True,
                "data": subgraph.to_dict(),
            }

    raw = await _llm_search(
        f"Find everything related to '{name}' — files, people, PRs, issues, "
        f"decisions, and Slack messages. Show their relationships.",
        dataset,
    )
    return {"fast_path": False, "data": raw}


async def get_timeline(topic: str, dataset: str = _DATASET) -> dict:
    if _use_fast_path():
        events = _fast_timeline(topic)
        if events:
            return {
                "fast_path": True,
                "data": [e.to_dict() for e in events],
            }

    raw = await _llm_search(
        f"Show the chronological evolution of '{topic}'. "
        f"List all related commits, PRs, issues, decisions, and Slack discussions "
        f"in date order. Include timestamps and linked entities.",
        dataset,
    )
    return {"fast_path": False, "data": raw}


async def get_related(entity_id: str, dataset: str = _DATASET) -> dict:
    if _use_fast_path():
        subgraph = _fast_neighbors(entity_id)
        if subgraph and subgraph.nodes:
            return {
                "fast_path": True,
                "data": subgraph.to_dict(),
            }

    raw = await _llm_search(
        f"What is connected to '{entity_id}'? "
        f"List all directly linked entities and their relationships. "
        f"Include PRs, issues, commits, files, decisions, and Slack messages.",
        dataset,
    )
    return {"fast_path": False, "data": raw}


async def cross_source_query(query: str, dataset: str = _DATASET) -> dict:
    if _use_fast_path():
        nodes = _fast_search(query)
        if nodes:
            return {
                "fast_path": True,
                "data": [n.to_dict() for n in nodes],
            }

    raw = await _llm_search(
        f"Search across both GitHub and Slack sources for: {query}. "
        f"Return matching entities from GitHub (PRs, issues, commits, files, decisions) "
        f"and Slack (messages, threads). Show how they are linked together.",
        dataset,
    )
    return {"fast_path": False, "data": raw}
