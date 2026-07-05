import os
from datetime import datetime, timezone
from typing import Optional

from neo4j import GraphDatabase

from mosaic.core.memory.models import GraphEdge, GraphNode, GraphSubgraph, TimelineEvent


_DRIVER: Optional[GraphDatabase.driver] = None


def _get_driver() -> Optional[GraphDatabase.driver]:
    global _DRIVER
    if _DRIVER is not None:
        return _DRIVER

    url = os.environ.get("GRAPH_DATABASE_URL", "bolt://localhost:7687")
    user = os.environ.get("GRAPH_DATABASE_USERNAME", "neo4j")
    password = os.environ.get("GRAPH_DATABASE_PASSWORD", "")

    if not password:
        return None

    try:
        _DRIVER = GraphDatabase.driver(url, auth=(user, password))
        return _DRIVER
    except Exception:
        return None


def _node_to_graph_node(n) -> GraphNode:
    props = dict(n)
    return GraphNode(
        id=props.get("id", ""),
        name=props.get("name", ""),
        type=props.get("type", ""),
        description=props.get("description", ""),
        source_id=props.get("source_id", ""),
        source=props.get("source", ""),
        properties={k: v for k, v in props.items() if k not in ("id", "name", "type", "description", "source_id", "source")},
    )


def _edge_to_graph_edge(r, source_id: str, target_id: str) -> GraphEdge:
    props = dict(r)
    return GraphEdge(
        source_node_id=source_id,
        target_node_id=target_id,
        relationship_name=props.get("relationship_name", r.type),
        description=props.get("edge_text", ""),
        properties={k: v for k, v in props.items() if k not in ("relationship_name", "edge_text", "source_node_id", "target_node_id")},
    )


def _ms_to_datetime(ms: Optional[int]) -> Optional[datetime]:
    if ms is None:
        return None
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)


def get_entity_by_name(name: str) -> Optional[GraphSubgraph]:
    driver = _get_driver()
    if driver is None:
        return None

    with driver.session() as session:
        result = session.run(
            "MATCH (n:__Node__) "
            "WHERE n.name CONTAINS $name OR n.id CONTAINS $name "
            "RETURN n LIMIT 20",
            name=name,
        )
        nodes = [_node_to_graph_node(r["n"]) for r in result]

        if not nodes:
            return GraphSubgraph()

        ids = [n.id for n in nodes]
        result = session.run(
            "MATCH (n:__Node__)-[r]-(m:__Node__) "
            "WHERE n.id IN $ids "
            "RETURN n, r, m",
            ids=ids,
        )
        edges = []
        neighbor_ids = set()
        for row in result:
            n = _node_to_graph_node(row["n"])
            m = _node_to_graph_node(row["m"])
            r = row["r"]
            edges.append(_edge_to_graph_edge(r, n.id, m.id))
            neighbor_ids.add(m.id)

        all_ids = set(ids) | neighbor_ids
        if all_ids - set(n.id for n in nodes):
            result = session.run(
                "MATCH (n:__Node__) WHERE n.id IN $ids RETURN n",
                ids=list(all_ids - set(n.id for n in nodes)),
            )
            all_nodes = nodes + [_node_to_graph_node(r["n"]) for r in result]
        else:
            all_nodes = nodes

        return GraphSubgraph(nodes=all_nodes, edges=edges)


def get_neighbors(entity_id: str, max_depth: int = 1) -> Optional[GraphSubgraph]:
    driver = _get_driver()
    if driver is None:
        return None

    with driver.session() as session:
        if max_depth == 1:
            result = session.run(
                "MATCH (n:__Node__ {id: $entity_id})-[r]-(m:__Node__) "
                "RETURN n, r, m",
                entity_id=entity_id,
            )
        else:
            result = session.run(
                "MATCH (n:__Node__ {id: $entity_id})-[r*1..$max_depth]-(m:__Node__) "
                "RETURN n, r, m",
                entity_id=entity_id,
                max_depth=max_depth,
            )

        seen_nodes: dict[str, GraphNode] = {}
        edges: list[GraphEdge] = []
        for row in result:
            n = _node_to_graph_node(row["n"])
            m = _node_to_graph_node(row["m"])
            seen_nodes[n.id] = n
            seen_nodes[m.id] = m
            if max_depth == 1:
                r = row["r"]
                edges.append(_edge_to_graph_edge(r, n.id, m.id))
            else:
                for r in row["r"]:
                    edges.append(_edge_to_graph_edge(r, n.id, m.id))

        if not seen_nodes:
            result = session.run(
                "MATCH (n:__Node__) WHERE n.id = $entity_id RETURN n",
                entity_id=entity_id,
            )
            for row in result:
                seen_nodes[entity_id] = _node_to_graph_node(row["n"])

        return GraphSubgraph(nodes=list(seen_nodes.values()), edges=edges)


def get_timeline(topic: str, limit: int = 50) -> Optional[list[TimelineEvent]]:
    driver = _get_driver()
    if driver is None:
        return None

    with driver.session() as session:
        result = session.run(
            "MATCH (n:__Node__) "
            "WHERE n.name CONTAINS $topic OR n.description CONTAINS $topic "
            "AND n.created_at IS NOT NULL "
            "RETURN n "
            "ORDER BY n.created_at ASC "
            "LIMIT $limit",
            topic=topic,
            limit=limit,
        )

        events = []
        for row in result:
            n = _node_to_graph_node(row["n"])
            ev = TimelineEvent(
                timestamp=_ms_to_datetime(n.properties.get("created_at")),
                node=n,
            )
            events.append(ev)

        if events:
            ids = [e.node.id for e in events]
            result = session.run(
                "MATCH (n:__Node__)-[r]-(m:__Node__) "
                "WHERE n.id IN $ids "
                "RETURN n, r, m",
                ids=ids,
            )
            related: dict[str, set[str]] = {e.node.id: set() for e in events}
            for row in result:
                n_id = row["n"]["id"]
                m = _node_to_graph_node(row["m"])
                if n_id in related:
                    related[n_id].add(m.id)

            for ev in events:
                ev.related_node_ids = list(related.get(ev.node.id, set()))

        return events


def search_entities(search_term: str, limit: int = 20) -> Optional[list[GraphNode]]:
    driver = _get_driver()
    if driver is None:
        return None

    with driver.session() as session:
        result = session.run(
            "MATCH (n:__Node__) "
            "WHERE n.name CONTAINS $search_term "
            "OR n.description CONTAINS $search_term "
            "OR n.id CONTAINS $search_term "
            "RETURN n LIMIT $limit",
            search_term=search_term,
            limit=limit,
        )
        return [_node_to_graph_node(r["n"]) for r in result]


def close():
    global _DRIVER
    if _DRIVER is not None:
        _DRIVER.close()
        _DRIVER = None
