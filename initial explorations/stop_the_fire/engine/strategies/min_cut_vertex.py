from __future__ import annotations

import networkx as nx

from ..frontier import get_fire_front
from ..models import VertexState
from .base import Strategy


class MinCutVertexFrontStrategy(Strategy):
    """Approximate separator defense via minimum node cut to distant WHITE targets."""

    @property
    def name(self) -> str:
        return "min_cut_vertex_front"

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

        # Pick distant WHITE vertices as "territory to save".
        distances = nx.multi_source_dijkstra_path_length(graph, red_nodes)
        target_whites = sorted(
            white_nodes,
            key=lambda v: (-distances.get(v, -1), -graph.degree(v), v),
        )[:5]
        if not target_whites:
            return sorted(fire_front, key=lambda n: (-graph.degree(n), n))

        src = "__SRC__"
        sink = "__SINK__"
        augmented = nx.Graph()
        augmented.add_nodes_from(graph.nodes())
        augmented.add_edges_from(graph.edges())
        augmented.add_node(src)
        augmented.add_node(sink)
        augmented.add_edges_from((src, r) for r in red_nodes)
        augmented.add_edges_from((w, sink) for w in target_whites)

        try:
            cut_nodes = nx.minimum_node_cut(augmented, src, sink)
        except nx.NetworkXError:
            return sorted(fire_front, key=lambda n: (-graph.degree(n), n))

        protected = [
            v
            for v in cut_nodes
            if v not in (src, sink) and vertex_states.get(v) == VertexState.WHITE
        ]
        if not protected:
            return sorted(fire_front, key=lambda n: (-graph.degree(n), n))

        preferred = sorted(protected, key=lambda n: (-graph.degree(n), n))
        front_set = set(fire_front)
        preferred_front = [v for v in preferred if v in front_set]
        remainder = [v for v in fire_front if v not in set(preferred_front)]
        return preferred_front + remainder
