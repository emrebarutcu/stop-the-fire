from __future__ import annotations

import networkx as nx

from .models import VertexState


def get_fire_front(
    graph: nx.Graph, vertex_states: dict[int, VertexState]
) -> list[int]:
    """WHITE vertices adjacent to at least one RED vertex, sorted for determinism."""
    front: set[int] = set()
    for node in graph.nodes():
        if vertex_states[node] == VertexState.RED:
            for neighbor in graph.neighbors(node):
                if vertex_states[neighbor] == VertexState.WHITE:
                    front.add(neighbor)
    return sorted(front)
