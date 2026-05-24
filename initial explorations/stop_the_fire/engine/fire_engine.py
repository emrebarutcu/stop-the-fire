from __future__ import annotations

import networkx as nx

from .frontier import get_fire_front
from .models import GameResult, GameState, Metrics, VertexState
from .strategies.base import Strategy


def _pick_fire_start(graph: nx.Graph) -> int:
    """Highest-degree vertex (tie-break: lowest ID)."""
    return max(graph.nodes(), key=lambda n: (graph.degree(n), -n))


def run_game(
    graph: nx.Graph,
    strategy: Strategy,
    fire_start: int | None = None,
    protect_per_turn: int = 2,
) -> GameResult:
    vertex_states: dict[int, VertexState] = {
        node: VertexState.WHITE for node in graph.nodes()
    }

    if fire_start is None:
        fire_start = _pick_fire_start(graph)
    vertex_states[fire_start] = VertexState.RED

    states: list[GameState] = [
        GameState(
            turn=0,
            vertex_states=dict(vertex_states),
            protected_this_turn=[],
            burned_this_turn=[fire_start],
        )
    ]

    turn = 0
    while True:
        if not get_fire_front(graph, vertex_states):
            break

        turn += 1

        to_protect = strategy.select_vertices(graph, dict(vertex_states))
        protected: list[int] = []
        for v in to_protect[:protect_per_turn]:
            if v in vertex_states and vertex_states[v] == VertexState.WHITE:
                vertex_states[v] = VertexState.GREEN
                protected.append(v)

        burned: list[int] = []
        for v in get_fire_front(graph, vertex_states):
            vertex_states[v] = VertexState.RED
            burned.append(v)

        states.append(
            GameState(
                turn=turn,
                vertex_states=dict(vertex_states),
                protected_this_turn=protected,
                burned_this_turn=burned,
            )
        )

    metrics = Metrics.from_state(vertex_states)

    return GameResult(
        graph_seed=graph.graph.get("generation_seed", -1),
        n_vertices=graph.number_of_nodes(),
        density=nx.density(graph),
        strategy_name=strategy.name,
        total_turns=turn,
        states=states,
        metrics=metrics,
    )
