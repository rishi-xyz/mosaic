import cognee
from cognee.modules.search.types import SearchType


_DATASET = "mosaic_engineering_memory"


async def _search(query: str, dataset: str = _DATASET) -> str:
    try:
        results = await cognee.search(
            query_text=query,
            query_type=SearchType.GRAPH_COMPLETION,
            datasets=[dataset],
        )
        return str(results)
    except Exception as e:
        return f"Search error: {e}"


async def get_entity(entity_id: str, dataset: str = _DATASET) -> str:
    return await _search(
        f"Find the entity with source_id '{entity_id}'. "
        f"Return its type, title, body, metadata, and all linked entities.",
        dataset,
    )


async def get_entity_by_name(name: str, dataset: str = _DATASET) -> str:
    return await _search(
        f"Find everything related to '{name}' — files, people, PRs, issues, "
        f"decisions, and Slack messages. Show their relationships.",
        dataset,
    )


async def get_timeline(topic: str, dataset: str = _DATASET) -> str:
    return await _search(
        f"Show the chronological evolution of '{topic}'. "
        f"List all related commits, PRs, issues, decisions, and Slack discussions "
        f"in date order. Include timestamps and linked entities.",
        dataset,
    )


async def get_related(entity_id: str, dataset: str = _DATASET) -> str:
    return await _search(
        f"What is connected to '{entity_id}'? "
        f"List all directly linked entities and their relationships. "
        f"Include PRs, issues, commits, files, decisions, and Slack messages.",
        dataset,
    )


async def cross_source_query(query: str, dataset: str = _DATASET) -> str:
    return await _search(
        f"Search across both GitHub and Slack sources for: {query}. "
        f"Return matching entities from GitHub (PRs, issues, commits, files, decisions) "
        f"and Slack (messages, threads). Show how they are linked together.",
        dataset,
    )
