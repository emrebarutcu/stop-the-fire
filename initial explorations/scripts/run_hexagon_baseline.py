#!/usr/bin/env python3
from __future__ import annotations

import random
from collections import deque
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import numpy as np
import pandas as pd

from calibration.runner import print_summary
from engine.fire_engine import run_game
from engine.models import VertexState
from engine.strategies import MaxDegreeStrategy


def _build_hex_base(min_nodes: int) -> nx.Graph:
    """Create a hexagonal lattice with at least min_nodes vertices."""
    side = 2
    while True:
        base = nx.hexagonal_lattice_graph(side, side, with_positions=True)
        if base.number_of_nodes() >= min_nodes:
            return base
        side += 1


def generate_connected_hex_graph(n: int, seed: int) -> nx.Graph:
    """Create a connected n-vertex subgraph from a hexagonal lattice."""
    rng = random.Random(seed)
    base = _build_hex_base(n)

    start = rng.choice(list(base.nodes()))
    selected: set = {start}
    queue = deque([start])

    while queue and len(selected) < n:
        current = queue.popleft()
        neighbors = list(base.neighbors(current))
        rng.shuffle(neighbors)
        for neighbor in neighbors:
            if len(selected) >= n:
                break
            if neighbor not in selected:
                selected.add(neighbor)
                queue.append(neighbor)

    if len(selected) < n:
        remaining = [node for node in base.nodes() if node not in selected]
        rng.shuffle(remaining)
        for node in remaining:
            if len(selected) >= n:
                break
            if any(nb in selected for nb in base.neighbors(node)):
                selected.add(node)

    if len(selected) != n:
        raise ValueError(f"Could not construct connected hex graph with n={n}")

    graph = base.subgraph(selected).copy()
    graph = nx.convert_node_labels_to_integers(graph, ordering="sorted")

    pos = nx.get_node_attributes(base, "pos")
    base_sorted_nodes = sorted(selected)
    for new_id, old_node in enumerate(base_sorted_nodes):
        xy = pos.get(old_node)
        if xy is not None:
            graph.nodes[new_id]["x"] = float(xy[0])
            graph.nodes[new_id]["y"] = float(xy[1])

    if not nx.is_connected(graph):
        raise ValueError(f"Generated hex subgraph is disconnected for n={n}, seed={seed}")

    graph.graph["seed"] = seed
    graph.graph["generation_seed"] = seed
    graph.graph["graph_family"] = "hexagonal_lattice_subgraph"
    return graph


def run_hexagon_baseline(
    vertex_counts: list[int],
    n_runs: int,
    output_dir: Path = Path("calibration/results"),
) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)

    strategy = MaxDegreeStrategy()
    rows: list[dict[str, float | int | str]] = []

    for n in vertex_counts:
        for seed in range(1, n_runs + 1):
            graph = generate_connected_hex_graph(n=n, seed=seed)
            result = run_game(graph, strategy)
            m = result.metrics
            rows.append(
                {
                    "seed": seed,
                    "n_vertices": n,
                    "density": round(result.density, 4),
                    "strategy": result.strategy_name,
                    "turns": result.total_turns,
                    "K": m.K,
                    "Y": m.Y,
                    "B": m.B,
                    "K_over_Y": round(m.K_over_Y, 4),
                    "K_over_B": round(m.K_over_B, 4),
                    "Y_over_B": round(m.Y_over_B, 4),
                }
            )

    df = pd.DataFrame(rows)
    csv_path = output_dir / "max_degree_hex_n30_40_50.csv"
    df.to_csv(csv_path, index=False)
    return df


def save_hex_summary_plot(df: pd.DataFrame, output_dir: Path) -> Path:
    """Save summary figure for hex baseline runs."""
    vertex_counts = sorted(df["n_vertices"].unique())
    x = np.arange(len(vertex_counts))

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))

    ax = axes[0, 0]
    for col, color, label in [
        ("K", "#d73027", "K (burned)"),
        ("Y", "#1a9850", "Y (protected)"),
        ("B", "#2b83ba", "B (saved)"),
    ]:
        means = [df[df["n_vertices"] == n][col].mean() for n in vertex_counts]
        ax.plot(x, means, marker="o", linewidth=2, color=color, label=label)
    ax.set_xticks(x)
    ax.set_xticklabels([f"n={n}" for n in vertex_counts])
    ax.set_title("Mean K / Y / B")
    ax.set_ylabel("Vertex count")
    ax.grid(alpha=0.25)
    ax.legend()

    ax = axes[0, 1]
    turns_means = [df[df["n_vertices"] == n]["turns"].mean() for n in vertex_counts]
    turns_std = [df[df["n_vertices"] == n]["turns"].std(ddof=0) for n in vertex_counts]
    ax.errorbar(x, turns_means, yerr=turns_std, fmt="o-", capsize=4, linewidth=2, color="#6a3d9a")
    ax.set_xticks(x)
    ax.set_xticklabels([f"n={n}" for n in vertex_counts])
    ax.set_title("Turns (mean ± std)")
    ax.set_ylabel("Turns")
    ax.grid(alpha=0.25)

    ax = axes[1, 0]
    data_ky = [df[df["n_vertices"] == n]["K_over_Y"].values for n in vertex_counts]
    bp = ax.boxplot(data_ky, tick_labels=[f"n={n}" for n in vertex_counts], patch_artist=True)
    for patch in bp["boxes"]:
        patch.set_facecolor("#fdae61")
        patch.set_alpha(0.7)
    ax.set_title("K / Y distribution")
    ax.set_ylabel("K / Y")
    ax.grid(alpha=0.2)

    ax = axes[1, 1]
    densities = [df[df["n_vertices"] == n]["density"].mean() for n in vertex_counts]
    ax.bar([f"n={n}" for n in vertex_counts], densities, color="#3288bd")
    ax.set_title("Mean realized density")
    ax.set_ylabel("Density")
    ax.set_ylim(0, max(densities) * 1.2 if densities else 1)
    ax.grid(axis="y", alpha=0.25)

    fig.suptitle("Hexagonal Lattice Greedy Baseline Summary")
    fig.tight_layout(rect=[0, 0, 1, 0.96])

    summary_path = output_dir / "max_degree_hex_n30_40_50_summary.png"
    fig.savefig(summary_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return summary_path


def save_step_by_step_run_plot(
    graph: nx.Graph,
    output_path: Path,
    strategy: MaxDegreeStrategy,
) -> None:
    """Save a full turn-by-turn replay for a single run."""
    result = run_game(graph, strategy)
    n_states = len(result.states)

    if all("x" in graph.nodes[v] and "y" in graph.nodes[v] for v in graph.nodes()):
        pos = {v: (graph.nodes[v]["x"], graph.nodes[v]["y"]) for v in graph.nodes()}
    else:
        pos = nx.spring_layout(graph, seed=graph.graph.get("generation_seed", 1))

    fig, axes = plt.subplots(1, n_states, figsize=(4.8 * n_states, 4.8))
    if n_states == 1:
        axes = [axes]

    node_size = 300 if graph.number_of_nodes() <= 40 else 220
    edge_color = "#b0b0b0"
    color_map = {
        VertexState.WHITE: "#d9d9d9",
        VertexState.RED: "#d73027",
        VertexState.GREEN: "#1a9850",
    }

    for i, state in enumerate(result.states):
        ax = axes[i]
        ax.set_facecolor("white")
        nx.draw_networkx_edges(graph, pos, ax=ax, edge_color=edge_color, width=1.3, alpha=0.8)

        for status in [VertexState.WHITE, VertexState.GREEN, VertexState.RED]:
            nodes = [v for v in graph.nodes() if state.vertex_states[v] == status]
            if nodes:
                nx.draw_networkx_nodes(
                    graph,
                    pos,
                    nodelist=nodes,
                    node_color=color_map[status],
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
                f"Protected: {state.protected_this_turn or '-'} | Burned: {len(state.burned_this_turn)}"
            )
        ax.set_title(title, fontsize=9)
        ax.axis("off")

    legend = [
        mpatches.Patch(color=color_map[VertexState.WHITE], label="White"),
        mpatches.Patch(color=color_map[VertexState.RED], label="Red (burned)"),
        mpatches.Patch(color=color_map[VertexState.GREEN], label="Green (protected)"),
    ]
    fig.legend(handles=legend, loc="lower center", ncol=3, fontsize=9, frameon=False)
    fig.suptitle(
        f"Hex run replay: n={graph.number_of_nodes()}, seed={graph.graph.get('generation_seed', '-')}, "
        f"turns={result.total_turns}, strategy={strategy.name}",
        fontsize=12,
    )
    fig.tight_layout(rect=[0, 0.06, 1, 0.93])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    vertex_counts = [30, 40, 50]
    n_runs = 30
    replay_seed = 1
    output_dir = Path("calibration/results")

    print("Running hex baseline calibration")
    print("  strategy = max_degree (greedy)")
    print(f"  vertex counts = {vertex_counts}")
    print(f"  runs per config = {n_runs}")
    print(f"  replay seed = {replay_seed}")

    dataframe = run_hexagon_baseline(
        vertex_counts=vertex_counts,
        n_runs=n_runs,
        output_dir=output_dir,
    )
    print_summary(dataframe, input_density=None)
    print(f"CSV saved to: {output_dir / 'max_degree_hex_n30_40_50.csv'}")

    summary_plot_path = save_hex_summary_plot(dataframe, output_dir)
    print(f"Summary plot saved to: {summary_plot_path}")

    replay_strategy = MaxDegreeStrategy()
    for n in vertex_counts:
        replay_graph = generate_connected_hex_graph(n=n, seed=replay_seed)
        replay_path = output_dir / f"hex_run_n{n}_seed{replay_seed}_steps.png"
        save_step_by_step_run_plot(replay_graph, replay_path, replay_strategy)
        print(f"Step-by-step replay saved to: {replay_path}")
