#!/usr/bin/env python3
"""Full multi-strategy comparison for final presentation.

Run from project root:
    cd /Users/emrebarutcu/Documents/Ders/IE\ 492\ Project
    source .venv/bin/activate
    python scripts/run_full_comparison.py
"""
from __future__ import annotations

import sys
import random
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import networkx as nx

sys.path.insert(0, str(Path(__file__).parent.parent / "stop_the_fire"))

from engine.graph_gen import generate_planar_graph
from engine.fire_engine import run_game
from engine.models import VertexState
from engine.strategies import (
    MaxDegreeStrategy,
    MaxWhiteNeighborsStrategy,
    MinCutEdgeFrontStrategy,
    MinCutVertexFrontStrategy,
)
from engine.strategies.base import Strategy
from engine.frontier import get_fire_front


# ── Hybrid strategy ──────────────────────────────────────────────────────────

class HybridStrategy(Strategy):
    """Min-Cut early (sparse fire front) → Max-White-Neighbors when front is large."""

    SWITCH_THRESHOLD = 5  # switch when fire front >= this many nodes

    @property
    def name(self) -> str:
        return "hybrid"

    def select_vertices(
        self,
        graph: nx.Graph,
        vertex_states: dict[int, VertexState],
    ) -> list[int]:
        fire_front = get_fire_front(graph, vertex_states)
        if len(fire_front) >= self.SWITCH_THRESHOLD:
            return MaxWhiteNeighborsStrategy().select_vertices(graph, vertex_states)
        return MinCutEdgeFrontStrategy().select_vertices(graph, vertex_states)


# ── Simulation ───────────────────────────────────────────────────────────────

STRATEGIES: list[Strategy] = [
    MaxDegreeStrategy(),
    MaxWhiteNeighborsStrategy(),
    MinCutEdgeFrontStrategy(),
    MinCutVertexFrontStrategy(),
    HybridStrategy(),
]

STRATEGY_LABELS = {
    "max_degree": "Max Degree",
    "max_white_neighbors": "Max White Neighbors",
    "min_cut_edge_front": "Min-Cut Edge",
    "min_cut_vertex_front": "Min-Cut Vertex",
    "hybrid": "Hybrid",
}

COLORS = {
    "max_degree": "#e41a1c",
    "max_white_neighbors": "#377eb8",
    "min_cut_edge_front": "#4daf4a",
    "min_cut_vertex_front": "#ff7f00",
    "hybrid": "#984ea3",
}

VERTEX_COUNTS = [20, 30, 40, 50]
K_VALUES = [1, 2, 3]
N_RUNS = 30
TARGET_DENSITY = 0.20
OUTPUT_DIR = Path(__file__).parent.parent / "stop_the_fire" / "calibration" / "results" / "final"


def run_full_simulation() -> pd.DataFrame:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = []

    for n in VERTEX_COUNTS:
        for k in K_VALUES:
            for seed in range(1, N_RUNS + 1):
                graph = generate_planar_graph(n=n, target_density=TARGET_DENSITY, seed=seed)
                for strat in STRATEGIES:
                    result = run_game(graph, strat, protect_per_turn=k)
                    m = result.metrics
                    rows.append({
                        "n": n,
                        "k": k,
                        "seed": seed,
                        "strategy": strat.name,
                        "K": m.K,
                        "Y": m.Y,
                        "B": m.B,
                        "turns": result.total_turns,
                        "density": round(result.density, 4),
                    })
                print(f"  n={n} k={k} seed={seed} done", end="\r")

    df = pd.DataFrame(rows)
    csv_path = OUTPUT_DIR / "full_comparison.csv"
    df.to_csv(csv_path, index=False)
    print(f"\nResults saved → {csv_path}")
    return df


# ── Plotting ─────────────────────────────────────────────────────────────────

def plot_main_comparison(df: pd.DataFrame) -> None:
    """Grouped bar chart: avg burned nodes by strategy and k, for n=30."""
    sub = df[df["n"] == 30]
    fig, ax = plt.subplots(figsize=(11, 6))

    strategy_names = [s.name for s in STRATEGIES]
    k_vals = sorted(sub["k"].unique())
    x = np.arange(len(strategy_names))
    width = 0.25
    offsets = np.linspace(-(len(k_vals)-1)/2, (len(k_vals)-1)/2, len(k_vals)) * width

    k_colors = ["#1b7837", "#762a83", "#c51b7d"]
    for i, kv in enumerate(k_vals):
        means = [sub[(sub["strategy"] == s) & (sub["k"] == kv)]["K"].mean() for s in strategy_names]
        stds  = [sub[(sub["strategy"] == s) & (sub["k"] == kv)]["K"].sem() for s in strategy_names]
        bars = ax.bar(x + offsets[i], means, width, label=f"k={kv}", color=k_colors[i],
                      alpha=0.85, yerr=stds, capsize=3, error_kw={"linewidth": 1.2})
        for bar, m in zip(bars, means):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3, f"{m:.1f}",
                    ha="center", va="bottom", fontsize=7.5, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels([STRATEGY_LABELS[s] for s in strategy_names], fontsize=10)
    ax.set_ylabel("Avg. Burned Nodes (K)", fontsize=12)
    ax.set_title("Strategy Comparison — n=30, 30 runs per configuration", fontsize=13, fontweight="bold")
    ax.legend(title="Budget k", fontsize=10)
    ax.grid(axis="y", alpha=0.3)
    ax.set_ylim(0, sub["K"].max() * 1.18)

    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "chart_main_comparison.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Saved: chart_main_comparison.png")


def plot_scalability(df: pd.DataFrame) -> None:
    """Line chart: avg burned nodes vs n for k=2, all strategies."""
    sub = df[df["k"] == 2]
    fig, ax = plt.subplots(figsize=(9, 5))

    for strat in STRATEGIES:
        sdf = sub[sub["strategy"] == strat.name]
        means = [sdf[sdf["n"] == n]["K"].mean() for n in VERTEX_COUNTS]
        stds  = [sdf[sdf["n"] == n]["K"].sem() for n in VERTEX_COUNTS]
        ax.errorbar(VERTEX_COUNTS, means, yerr=stds, marker="o", linewidth=2,
                    capsize=4, label=STRATEGY_LABELS[strat.name], color=COLORS[strat.name])

    ax.set_xlabel("Graph Size (n)", fontsize=12)
    ax.set_ylabel("Avg. Burned Nodes (K)", fontsize=12)
    ax.set_title("Scalability — Avg. Burned Nodes vs. Graph Size (k=2, 30 runs)", fontsize=12, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "chart_scalability.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Saved: chart_scalability.png")


def plot_k_sensitivity(df: pd.DataFrame) -> None:
    """Line chart: avg burned vs k for n=30, all strategies."""
    sub = df[df["n"] == 30]
    fig, ax = plt.subplots(figsize=(8, 5))

    for strat in STRATEGIES:
        sdf = sub[sub["strategy"] == strat.name]
        means = [sdf[sdf["k"] == k]["K"].mean() for k in K_VALUES]
        ax.plot(K_VALUES, means, marker="o", linewidth=2,
                label=STRATEGY_LABELS[strat.name], color=COLORS[strat.name])
        for kv, m in zip(K_VALUES, means):
            ax.annotate(f"{m:.1f}", xy=(kv, m), xytext=(0, 6), textcoords="offset points",
                        ha="center", fontsize=8)

    ax.set_xlabel("Protection Budget k (nodes/turn)", fontsize=12)
    ax.set_ylabel("Avg. Burned Nodes (K)", fontsize=12)
    ax.set_title("Effect of Budget k — n=30, 30 runs per config", fontsize=12, fontweight="bold")
    ax.set_xticks(K_VALUES)
    ax.legend(fontsize=10)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "chart_k_sensitivity.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Saved: chart_k_sensitivity.png")


def plot_saved_fraction(df: pd.DataFrame) -> None:
    """Stacked bar: fraction saved vs burned for n=30, k=2."""
    sub = df[(df["n"] == 30) & (df["k"] == 2)]
    strategy_names = [s.name for s in STRATEGIES]
    labels = [STRATEGY_LABELS[s] for s in strategy_names]

    avg_K = [sub[sub["strategy"] == s]["K"].mean() for s in strategy_names]
    avg_Y = [sub[sub["strategy"] == s]["Y"].mean() for s in strategy_names]
    avg_B = [sub[sub["strategy"] == s]["B"].mean() for s in strategy_names]

    x = np.arange(len(strategy_names))
    fig, ax = plt.subplots(figsize=(9, 5))

    b1 = ax.bar(x, avg_K, label="Burned (K)", color="#d73027", alpha=0.85)
    b2 = ax.bar(x, avg_Y, bottom=avg_K, label="Protected (Y)", color="#1a9850", alpha=0.85)
    b3 = ax.bar(x, avg_B, bottom=[k+y for k,y in zip(avg_K, avg_Y)], label="Saved untouched (B)", color="#2b83ba", alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("Average Vertices", fontsize=12)
    ax.set_title("Outcome Breakdown — n=30, k=2, 30 runs", fontsize=12, fontweight="bold")
    ax.legend(fontsize=10)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "chart_outcome_breakdown.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Saved: chart_outcome_breakdown.png")


def plot_heatmap(df: pd.DataFrame) -> None:
    """Heatmap: avg K for each (strategy, n) at k=2."""
    sub = df[df["k"] == 2]
    strategy_names = [s.name for s in STRATEGIES]
    labels = [STRATEGY_LABELS[s] for s in strategy_names]

    data = np.array([[sub[(sub["strategy"]==s)&(sub["n"]==n)]["K"].mean()
                      for n in VERTEX_COUNTS] for s in strategy_names])

    fig, ax = plt.subplots(figsize=(8, 4))
    im = ax.imshow(data, cmap="RdYlGn_r", aspect="auto")
    plt.colorbar(im, ax=ax, label="Avg. Burned Nodes (K)")

    ax.set_xticks(range(len(VERTEX_COUNTS)))
    ax.set_xticklabels([f"n={n}" for n in VERTEX_COUNTS], fontsize=11)
    ax.set_yticks(range(len(strategy_names)))
    ax.set_yticklabels(labels, fontsize=10)

    for i in range(len(strategy_names)):
        for j in range(len(VERTEX_COUNTS)):
            ax.text(j, i, f"{data[i,j]:.1f}", ha="center", va="center",
                    fontsize=10, fontweight="bold",
                    color="white" if data[i,j] > data.max()*0.6 else "black")

    ax.set_title("Average Burned Nodes — k=2, 30 runs (lower = better)", fontsize=12, fontweight="bold")
    fig.tight_layout()
    fig.savefig(OUTPUT_DIR / "chart_heatmap.png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("Saved: chart_heatmap.png")


def print_summary_table(df: pd.DataFrame) -> None:
    print("\n=== SUMMARY TABLE (n=30, 30 runs) ===")
    sub = df[df["n"] == 30]
    print(f"{'Strategy':<22} {'k=1 K':>7} {'k=2 K':>7} {'k=3 K':>7}")
    print("-" * 47)
    for strat in STRATEGIES:
        row = []
        for k in K_VALUES:
            mean_k = sub[(sub["strategy"] == strat.name) & (sub["k"] == k)]["K"].mean()
            row.append(f"{mean_k:.1f}")
        print(f"{STRATEGY_LABELS[strat.name]:<22} {row[0]:>7} {row[1]:>7} {row[2]:>7}")


if __name__ == "__main__":
    print("Running full multi-strategy simulation...")
    print(f"  Strategies: {[s.name for s in STRATEGIES]}")
    print(f"  Graph sizes: {VERTEX_COUNTS}")
    print(f"  k values: {K_VALUES}")
    print(f"  Runs: {N_RUNS}")
    print()

    csv_path = OUTPUT_DIR / "full_comparison.csv"
    if csv_path.exists():
        print(f"Loading cached results from {csv_path}")
        df = pd.read_csv(csv_path)
    else:
        df = run_full_simulation()

    print("\nGenerating charts...")
    plot_main_comparison(df)
    plot_scalability(df)
    plot_k_sensitivity(df)
    plot_saved_fraction(df)
    plot_heatmap(df)
    print_summary_table(df)
    print(f"\nAll outputs in: {OUTPUT_DIR}")
