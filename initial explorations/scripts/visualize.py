#!/usr/bin/env python3
"""Visualize calibration results: per-game map replay + aggregate metric charts."""

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import networkx as nx
import pandas as pd
import numpy as np

from engine import generate_graph, run_game
from engine.models import VertexState
from engine.strategies import MaxDegreeStrategy

OUTPUT_DIR = Path("calibration/results")
DENSITY = 0.30
VERTEX_COUNTS = [15, 20, 25]
DEMO_SEED = 1

BG_COLOR = "#f5f0e1"
TERRAIN_BORDER = "#c4b99a"

COLOR_MAP = {
    VertexState.WHITE: "#ddd8c4",
    VertexState.RED: "#d63031",
    VertexState.GREEN: "#00b894",
}
EDGE_COLOR = "#b0a890"
NODE_BORDER_MAP = {
    VertexState.WHITE: "#8a8473",
    VertexState.RED: "#922b21",
    VertexState.GREEN: "#0a7a5a",
}
LABEL_COLOR_MAP = {
    VertexState.WHITE: "#4a4637",
    VertexState.RED: "#ffffff",
    VertexState.GREEN: "#ffffff",
}


def _draw_game_state(ax, graph, vertex_states, turn_label, pos):
    ax.set_facecolor(BG_COLOR)

    nx.draw_networkx_edges(
        graph, pos, ax=ax,
        edge_color=EDGE_COLOR, width=1.4, alpha=0.7,
        style="solid",
    )

    for state_type in [VertexState.WHITE, VertexState.GREEN, VertexState.RED]:
        nodelist = [n for n in graph.nodes() if vertex_states[n] == state_type]
        if not nodelist:
            continue
        nx.draw_networkx_nodes(
            graph, pos, ax=ax,
            nodelist=nodelist,
            node_color=COLOR_MAP[state_type],
            edgecolors=NODE_BORDER_MAP[state_type],
            linewidths=1.8,
            node_size=380 if graph.number_of_nodes() <= 30 else 100,
        )

    if graph.number_of_nodes() <= 30:
        for node in graph.nodes():
            x, y = pos[node]
            ax.text(
                x, y, str(node),
                ha="center", va="center",
                fontsize=7, fontweight="bold",
                color=LABEL_COLOR_MAP[vertex_states[node]],
                zorder=5,
            )

    ax.set_title(turn_label, fontsize=10, fontweight="bold", color="#3d3628")
    ax.axis("off")

    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color(TERRAIN_BORDER)
        spine.set_linewidth(1.5)


def visualize_single_game(n: int, density: float, seed: int) -> plt.Figure:
    graph = generate_graph(n, density, seed)
    strategy = MaxDegreeStrategy()
    result = run_game(graph, strategy)

    pos = {node: (graph.nodes[node]["x"], graph.nodes[node]["y"]) for node in graph.nodes()}

    n_states = len(result.states)
    fig, axes = plt.subplots(1, n_states, figsize=(5 * n_states, 5))
    fig.set_facecolor(BG_COLOR)
    if n_states == 1:
        axes = [axes]

    for i, state in enumerate(result.states):
        if i == 0:
            label = f"Tur 0: Ates baslar\n(bolge {result.states[0].burned_this_turn[0]})"
        else:
            p = state.protected_this_turn
            b = state.burned_this_turn
            label = (
                f"Tur {state.turn}\n"
                f"Korunan: {p if p else '—'}  |  Yanan: {len(b)} bolge"
            )
        _draw_game_state(axes[i], graph, state.vertex_states, label, pos)

    m = result.metrics
    fig.suptitle(
        f"Harita: {n} bolge, yogunluk={density}, strateji={result.strategy_name}\n"
        f"Sonuc: Yanmis={m.K}  Korunmus={m.Y}  Kurtulmus={m.B}  ({result.total_turns} tur)",
        fontsize=13, fontweight="bold", y=1.02, color="#3d3628",
    )

    legend_patches = [
        mpatches.Patch(facecolor=COLOR_MAP[VertexState.WHITE], edgecolor=NODE_BORDER_MAP[VertexState.WHITE], label="Bos bolge", linewidth=1.5),
        mpatches.Patch(facecolor=COLOR_MAP[VertexState.RED], edgecolor=NODE_BORDER_MAP[VertexState.RED], label="Yanmis bolge", linewidth=1.5),
        mpatches.Patch(facecolor=COLOR_MAP[VertexState.GREEN], edgecolor=NODE_BORDER_MAP[VertexState.GREEN], label="Korunmus bolge", linewidth=1.5),
    ]
    fig.legend(
        handles=legend_patches, loc="lower center", ncol=3,
        fontsize=9, frameon=True, facecolor=BG_COLOR, edgecolor=TERRAIN_BORDER,
    )

    fig.tight_layout(rect=[0, 0.07, 1, 0.95])
    return fig


def visualize_calibration_summary(csv_path: Path) -> plt.Figure:
    df = pd.read_csv(csv_path)

    fig, axes = plt.subplots(2, 2, figsize=(12, 9))
    fig.set_facecolor(BG_COLOR)
    for row in axes:
        for ax in row:
            ax.set_facecolor("#faf6ed")

    vertex_counts = sorted(df["n_vertices"].unique())
    x = np.arange(len(vertex_counts))
    width = 0.25

    ax = axes[0, 0]
    for i, (col, color, label) in enumerate([
        ("K", "#d63031", "K (yanmis)"),
        ("Y", "#00b894", "Y (korunan)"),
        ("B", "#2d98da", "B (kurtulmus)"),
    ]):
        means = [df[df["n_vertices"] == n][col].mean() for n in vertex_counts]
        ax.bar(x + i * width, means, width, color=color, label=label, edgecolor="white")
    ax.set_xticks(x + width)
    ax.set_xticklabels([f"n={n}" for n in vertex_counts])
    ax.set_ylabel("Bolge sayisi")
    ax.set_title("Ortalama K / Y / B", fontweight="bold")
    ax.legend(fontsize=8)

    ax = axes[0, 1]
    data_ky = [df[df["n_vertices"] == n]["K_over_Y"].values for n in vertex_counts]
    bp = ax.boxplot(data_ky, tick_labels=[f"n={n}" for n in vertex_counts], patch_artist=True)
    for patch in bp["boxes"]:
        patch.set_facecolor("#d63031")
        patch.set_alpha(0.6)
    ax.set_ylabel("K / Y orani")
    ax.set_title("K/Y Dagilimi (dusuk = iyi)", fontweight="bold")

    ax = axes[1, 0]
    for n_val, xpos in zip(vertex_counts, x):
        sub = df[df["n_vertices"] == n_val]
        k_pct = sub["K"].mean() / n_val * 100
        y_pct = sub["Y"].mean() / n_val * 100
        b_pct = sub["B"].mean() / n_val * 100
        ax.bar(xpos, k_pct, color="#d63031", edgecolor="white")
        ax.bar(xpos, y_pct, bottom=k_pct, color="#00b894", edgecolor="white")
        ax.bar(xpos, b_pct, bottom=k_pct + y_pct, color="#2d98da", edgecolor="white")
    ax.set_xticks(x)
    ax.set_xticklabels([f"n={n}" for n in vertex_counts])
    ax.set_ylabel("Yuzde (%)")
    ax.set_title("Bolge Durum Dagilimi (%)", fontweight="bold")
    ax.set_ylim(0, 105)

    ax = axes[1, 1]
    data_turns = [df[df["n_vertices"] == n]["turns"].values for n in vertex_counts]
    bp2 = ax.boxplot(data_turns, tick_labels=[f"n={n}" for n in vertex_counts], patch_artist=True)
    for patch in bp2["boxes"]:
        patch.set_facecolor("#6c5ce7")
        patch.set_alpha(0.6)
    ax.set_ylabel("Tur sayisi")
    ax.set_title("Oyun Suresi (tur)", fontweight="bold")

    fig.suptitle(
        f"Kalibrasyon Ozeti: max_degree, yogunluk={DENSITY}",
        fontsize=14, fontweight="bold", color="#3d3628",
    )
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    return fig


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("Harita gorsellestirmeleri olusturuluyor...")
    for n in VERTEX_COUNTS:
        fig = visualize_single_game(n, DENSITY, DEMO_SEED)
        path = OUTPUT_DIR / f"game_n{n}_d{DENSITY}_seed{DEMO_SEED}.png"
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
        plt.close(fig)
        print(f"  -> {path}")

    csv_path = OUTPUT_DIR / f"max_degree_d{DENSITY}.csv"
    if csv_path.exists():
        print("Kalibrasyon ozet grafikleri olusturuluyor...")
        fig = visualize_calibration_summary(csv_path)
        path = OUTPUT_DIR / f"summary_d{DENSITY}.png"
        fig.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG_COLOR)
        plt.close(fig)
        print(f"  -> {path}")

    print("Tamamlandi.")
