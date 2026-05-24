#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx
import numpy as np
import pandas as pd

from calibration.runner import print_summary
from engine.graph_gen import generate_planar_graph
from engine.models import VertexState
from engine.fire_engine import run_game
from engine.strategies import MaxDegreeStrategy


def run_planar_baseline(
    vertex_counts: list[int],
    n_runs: int,
    target_density: float = 0.20,
    output_dir: Path = Path("calibration/results"),
) -> pd.DataFrame:
    output_dir.mkdir(parents=True, exist_ok=True)

    strategy = MaxDegreeStrategy()
    rows: list[dict[str, float | int | str]] = []

    for n in vertex_counts:
        for seed in range(1, n_runs + 1):
            graph = generate_planar_graph(
                n=n,
                target_density=target_density,
                seed=seed,
            )
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
    csv_path = output_dir / "max_degree_planar_n30_40_50.csv"
    df.to_csv(csv_path, index=False)
    return df


def save_planar_summary_plot(df: pd.DataFrame, output_dir: Path, target_density: float) -> Path:
    """Save summary figure for planar baseline runs."""
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

    fig.suptitle(f"Planar Greedy Baseline Summary (target density={target_density})")
    fig.tight_layout(rect=[0, 0, 1, 0.96])

    summary_path = output_dir / "max_degree_planar_n30_40_50_summary.png"
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

    try:
        pos = nx.planar_layout(graph)
    except nx.NetworkXException:
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
        f"Planar run replay: n={graph.number_of_nodes()}, seed={graph.graph.get('generation_seed', '-')}, "
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
    target_density = 0.20
    replay_seed = 1

    print("Running planar baseline calibration")
    print(f"  strategy = max_degree (greedy)")
    print(f"  vertex counts = {vertex_counts}")
    print(f"  runs per config = {n_runs}")
    print(f"  target density = {target_density}")
    print(f"  replay seed = {replay_seed}")

    dataframe = run_planar_baseline(
        vertex_counts=vertex_counts,
        n_runs=n_runs,
        target_density=target_density,
    )
    print_summary(dataframe, input_density=target_density)
    print("CSV saved to: calibration/results/max_degree_planar_n30_40_50.csv")
    summary_plot_path = save_planar_summary_plot(dataframe, Path("calibration/results"), target_density)
    print(f"Summary plot saved to: {summary_plot_path}")

    replay_strategy = MaxDegreeStrategy()
    for n in vertex_counts:
        replay_graph = generate_planar_graph(
            n=n,
            target_density=target_density,
            seed=replay_seed,
        )
        replay_path = Path("calibration/results") / f"planar_run_n{n}_d{target_density}_seed{replay_seed}_steps.png"
        save_step_by_step_run_plot(replay_graph, replay_path, replay_strategy)
        print(f"Step-by-step replay saved to: {replay_path}")
