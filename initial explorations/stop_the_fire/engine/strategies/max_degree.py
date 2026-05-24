from __future__ import annotations

import networkx as nx

from ..frontier import get_fire_front
from ..models import VertexState
from .base import Strategy


class MaxDegreeStrategy(Strategy):
    """Prefer fire-front vertices with the largest degree (aggressive containment)."""

    @property
    def name(self) -> str:
        return "max_degree"

    def select_vertices(
        self,
        graph: nx.Graph,
        vertex_states: dict[int, VertexState],
    ) -> list[int]:
        candidates = get_fire_front(graph, vertex_states)
        if not candidates:
            return []
        return sorted(candidates, key=lambda n: (-graph.degree(n), n))
