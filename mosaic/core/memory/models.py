from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class GraphNode:
    id: str
    name: str
    type: str
    description: str = ""
    source_id: str = ""
    source: str = ""
    properties: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "source_id": self.source_id,
            "source": self.source,
            "properties": dict(self.properties),
        }


@dataclass
class GraphEdge:
    source_node_id: str
    target_node_id: str
    relationship_name: str
    description: Optional[str] = None
    properties: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "relationship_name": self.relationship_name,
            "description": self.description,
            "properties": dict(self.properties),
        }


@dataclass
class GraphSubgraph:
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "nodes": [n.to_dict() for n in self.nodes],
            "edges": [e.to_dict() for e in self.edges],
        }


@dataclass
class TimelineEvent:
    timestamp: Optional[datetime]
    node: GraphNode
    related_node_ids: list[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "node": self.node.to_dict(),
            "related_node_ids": list(self.related_node_ids),
            "description": self.description,
        }
