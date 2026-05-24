from __future__ import annotations

import networkx as nx

from ..frontier import get_fire_front
from ..models import VertexState
from .base import Strategy


class MinCutEdgeFrontStrategy(Strategy):
    """Approximate firewall by protecting WHITE endpoints of a global min edge cut."""

    @property
    def name(self) -> str:
        return "min_cut_edge_front"

    def select_vertices(
        self,
        graph: nx.Graph,
        vertex_states: dict[int, VertexState],
    ) -> list[int]:
        fire_front = get_fire_front(graph, vertex_states)
        if not fire_front:
            return []

        red_nodes = [v for v, s in vertex_states.items() if s == VertexState.RED]
        white_nodes = [v for v, s in vertex_states.items() if s == VertexState.WHITE]
        if not red_nodes or not white_nodes:
            return fire_front

        # Build an augmented graph: source connected to RED, sink to WHITE.
        augmented = nx.Graph()
        augmented.add_nodes_from(graph.nodes())
        augmented.add_edges_from(graph.edges())
        src = "__SRC__"
        sink = "__SINK__"
        augmented.add_node(src)
        augmented.add_node(sink)
        augmented.add_edges_from((src, r) for r in red_nodes)
        augmented.add_edges_from((w, sink) for w in white_nodes)

        try:
            cut_edges = nx.minimum_edge_cut(augmented, src, sink)
        except nx.NetworkXError:
            return fire_front

        endpoint_score: dict[int, int] = {}
        for u, v in cut_edges:
            for node in (u, v):
                if node in (src, sink):
                    continue
                if vertex_states.get(node) == VertexState.WHITE:
                    endpoint_score[node] = endpoint_score.get(node, 0) + 1

        if not endpoint_score:
            return sorted(fire_front, key=lambda n: (-graph.degree(n), n))

        preferred = sorted(
            endpoint_score,
            key=lambda n: (-endpoint_score[n], -graph.degree(n), n),
        )

        front_set = set(fire_front)
        preferred_front = [v for v in preferred if v in front_set]
        remainder = [v for v in fire_front if v not in set(preferred_front)]
        return preferred_front + remainder
