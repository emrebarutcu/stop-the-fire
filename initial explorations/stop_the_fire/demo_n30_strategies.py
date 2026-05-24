#!/usr/bin/env python3
"""Compare firefighting strategies on a fixed n=30 planar graph (see 24032026.md).

Run from this directory::

    cd stop_the_fire && python demo_n30_strategies.py

Fire spreads to all WHITE neighbors of RED each turn; each turn the strategy
selects up to ``protect_per_turn`` vertices to turn GREEN before spread.
"""

from __future__ import annotations

import random
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx

from engine.fire_engine import run_game
from engine.graph_gen import generate_planar_graph
from engine.models import GameResult, VertexState
from engine.strategies import (
    MaxDegreeStrategy,
    MaxWhiteNeighborsStrategy,
    MinCutEdgeFrontStrategy,
    MinCutVertexFrontStrategy,
    MinDegreeFrontStrategy,
    RandomFrontStrategy,
)
from engine.strategies.base import Strategy

OUTPUT_DIR = Path("calibration/results/n30_demo")
N_VERTICES = 30
TARGET_DENSITY = 0.20
GRAPH_SEED = 1
PROTECT_PER_TURN = 2

COLOR_MAP = {
    VertexState.WHITE: "#d9d9d9",
    VertexState.RED: "#d73027",
    VertexState.GREEN: "#1a9850",
}


def _layout(graph: nx.Graph) -> dict[int, tuple[float, float]]:
    if all("x" in graph.nodes[v] and "y" in graph.nodes[v] for v in graph.nodes()):
        return {
            v: (graph.nodes[v]["x"], graph.nodes[v]["y"])
            for v in graph.nodes()
        }
    try:
        return nx.planar_layout(graph)
    except nx.NetworkXException:
        return nx.spring_layout(graph, seed=graph.graph.get("generation_seed", 0))


def save_replay_png(
    graph: nx.Graph,
    result: GameResult,
    result_path: Path,
) -> None:
    n_states = len(result.states)
    pos = _layout(graph)

    fig, axes = plt.subplots(1, n_states, figsize=(4.2 * n_states, 4.5))
    if n_states == 1:
        axes = [axes]

    node_size = 280
    edge_color = "#b0b0b0"

    for i, state in enumerate(result.states):
        ax = axes[i]
        ax.set_facecolor("white")
        nx.draw_networkx_edges(
            graph, pos, ax=ax, edge_color=edge_color, width=1.2, alpha=0.85,
        )
        for status in [VertexState.WHITE, VertexState.GREEN, VertexState.RED]:
            nodes = [v for v in graph.nodes() if state.vertex_states[v] == status]
            if nodes:
                nx.draw_networkx_nodes(
                    graph,
                    pos,
                    nodelist=nodes,
                    node_color=COLOR_MAP[status],
                    edgecolors="#4d4d4d",
                    linewidths=1.0,
                    node_size=node_size,
                    ax=ax,
                )
        if graph.number_of_nodes() <= 35:
            nx.draw_networkx_labels(graph, pos, ax=ax, font_size=7, font_color="black")

        if state.turn == 0:
            title = f"Turn 0\nFire start: {state.burned_this_turn[0]}"
        else:
            title = (
                f"Turn {state.turn}\n"
                f"Blocked: {state.protected_this_turn or '—'} | "
                f"New fire: {len(state.burned_this_turn)}"
            )
        ax.set_title(title, fontsize=9)
        ax.axis("off")

    legend = [
        mpatches.Patch(color=COLOR_MAP[VertexState.WHITE], label="Unburned"),
        mpatches.Patch(color=COLOR_MAP[VertexState.RED], label="Burned"),
        mpatches.Patch(color=COLOR_MAP[VertexState.GREEN], label="Protected"),
    ]
    fig.legend(handles=legend, loc="lower center", ncol=3, fontsize=9, frameon=False)
    m = result.metrics
    fig.suptitle(
        f"n={graph.number_of_nodes()} planar | seed={graph.graph.get('generation_seed', '-')} | "
        f"{result.strategy_name} | turns={result.total_turns} | "
        f"K={m.K} Y={m.Y} B={m.B}",
        fontsize=11,
    )
    fig.tight_layout(rect=[0, 0.06, 1, 0.93])
    result_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(result_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    graph = generate_planar_graph(N_VERTICES, TARGET_DENSITY, GRAPH_SEED)
    is_planar, _ = nx.check_planarity(graph)
    print(f"Graph: n={N_VERTICES}, target_density={TARGET_DENSITY}, seed={GRAPH_SEED}")
    print(f"  edges={graph.number_of_edges()}, density={nx.density(graph):.4f}, planar={is_planar}")

    strategies: list[Strategy] = [
        MaxDegreeStrategy(),
        MinDegreeFrontStrategy(),
        MaxWhiteNeighborsStrategy(),
        MinCutEdgeFrontStrategy(),
        MinCutVertexFrontStrategy(),
        RandomFrontStrategy(random.Random(42)),
    ]

    rows: list[tuple[str, int, int, int, int]] = []
    for strat in strategies:
        r = run_game(graph, strat, protect_per_turn=PROTECT_PER_TURN)
        m = r.metrics
        rows.append((strat.name, r.total_turns, m.K, m.Y, m.B))
        out = OUTPUT_DIR / f"n30_seed{GRAPH_SEED}_{strat.name}_steps.png"
        save_replay_png(graph, r, out)
        print(f"  {strat.name}: turns={r.total_turns} K={m.K} Y={m.Y} B={m.B} -> {out}")

    print("\nSummary (lower K is better; higher B is better):")
    print(f"{'strategy':<20} {'turns':>6} {'K':>5} {'Y':>5} {'B':>5}")
    for name, turns, k, y, b in rows:
        print(f"{name:<20} {turns:>6} {k:>5} {y:>5} {b:>5}")


if __name__ == "__main__":
    main()
