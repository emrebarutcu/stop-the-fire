from __future__ import annotations

import networkx as nx

from ..frontier import get_fire_front
from ..models import VertexState
from .base import Strategy


class MaxWhiteNeighborsStrategy(Strategy):
    """Prefer fire-front vertices with the most WHITE neighbors (preserve interior enclaves)."""

    @property
    def name(self) -> str:
        return "max_white_neighbors"

    @staticmethod
    def _white_neighbor_count(
        graph: nx.Graph, vertex_states: dict[int, VertexState], v: int
    ) -> int:
        return sum(
            1 for u in graph.neighbors(v) if vertex_states[u] == VertexState.WHITE
        )

    def select_vertices(
        self,
        graph: nx.Graph,
        vertex_states: dict[int, VertexState],
    ) -> list[int]:
        candidates = get_fire_front(graph, vertex_states)
        if not candidates:
            return []
        return sorted(
            candidates,
            key=lambda n: (
                -self._white_neighbor_count(graph, vertex_states, n),
                -graph.degree(n),
                n,
            ),
        )
