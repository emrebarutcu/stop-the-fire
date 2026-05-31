"""Generate analytical plots for the IE 492 final report from benchmark data."""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

FIG_DIR = Path(__file__).parent
SUITE = FIG_DIR.parent / "final suite"
BENCH = SUITE / "benchmark" / "benchmark_results.csv"
SUMMARY = SUITE / "benchmark" / "benchmark_summary.csv"

# Visual identity (mirrors slides build.py)
plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "axes.edgecolor": "#334155",
    "axes.linewidth": 0.8,
    "xtick.color": "#1e293b",
    "ytick.color": "#1e293b",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "figure.dpi": 150,
})

FIRE = "#ea580c"
AMBER = "#fbbf24"
TEAL = "#14b8a6"
BLUE = "#3b82f6"
PURPLE = "#8b5cf6"
ROSE = "#f43f5e"
GREEN = "#10b981"
SLATE = "#64748b"

# Strategy ordering & display names
DISPLAY = {
    "one_step_lookahead":   "One-Step Lookahead",
    "betweenness_front":    "Betweenness Front",
    "max_white_neighbors":  "Max White Neighbours",
    "hybrid_density_aware": "Hybrid Density-Aware",
    "max_degree":           "Max Degree",
    "min_damage_cut":       "Min Damage Cut",
    "min_cut_edge_front":   "Min Cut Edge Front",
    "random":               "Random (baseline)",
}
PHILO = {
    "one_step_lookahead":   ("Lookahead",  PURPLE),
    "betweenness_front":    ("Structural", BLUE),
    "max_white_neighbors":  ("Local greedy", GREEN),
    "hybrid_density_aware": ("Hybrid",     AMBER),
    "max_degree":           ("Local greedy", GREEN),
    "min_damage_cut":       ("Structural", BLUE),
    "min_cut_edge_front":   ("Structural", BLUE),
    "random":               ("Baseline",   SLATE),
}


def load_summary() -> list[dict]:
    rows = []
    with SUMMARY.open() as f:
        for r in csv.DictReader(f):
            rows.append({
                "rank":    int(r["rank"]),
                "strategy": r["strategy"],
                "mean":    float(r["mean_burned_pct"]),
                "std":     float(r["std_burned_pct"]),
                "runtime": float(r["mean_runtime_ms"]),
            })
    return rows


def load_results() -> list[dict]:
    rows = []
    with BENCH.open() as f:
        for r in csv.DictReader(f):
            rows.append({
                "n":        int(r["n"]),
                "strategy": r["strategy"],
                "burned":   float(r["burned_pct"]),
                "runtime":  float(r["runtime_s"]) * 1000.0,
            })
    return rows


# --------------------------------------------------------------------------
# Figure 1 — Strategy ranking bar chart on the synthetic benchmark
# --------------------------------------------------------------------------
def fig_strategy_ranking(summary: list[dict]) -> None:
    summary = sorted(summary, key=lambda x: x["mean"])
    names = [DISPLAY[r["strategy"]] for r in summary]
    means = [r["mean"] for r in summary]
    stds = [r["std"] for r in summary]
    colors = [PHILO[r["strategy"]][1] for r in summary]

    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    ypos = np.arange(len(names))
    bars = ax.barh(ypos, means, xerr=stds, color=colors, edgecolor="#1e293b",
                   linewidth=0.6, alpha=0.85,
                   error_kw=dict(ecolor="#475569", capsize=3, lw=0.8))

    ax.set_yticks(ypos)
    ax.set_yticklabels(names)
    ax.invert_yaxis()
    ax.set_xlabel("Mean burned fraction across 594 paired runs (%)")
    ax.set_xlim(0, 100)
    ax.grid(axis="x", linestyle=":", color="#cbd5e1", alpha=0.7)
    ax.set_axisbelow(True)

    for bar, m, s in zip(bars, means, stds):
        ax.text(min(m + s + 1.5, 96), bar.get_y() + bar.get_height() / 2,
                f"{m:.1f}%", va="center", fontsize=9, color="#1e293b")

    families = []
    seen = set()
    for r in summary:
        fam, col = PHILO[r["strategy"]]
        if fam not in seen:
            families.append((fam, col))
            seen.add(fam)
    handles = [mpatches.Patch(color=c, label=f) for f, c in families]
    ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.02, 1.0),
              frameon=False, fontsize=8.5, title="Philosophy",
              title_fontsize=8.5, borderaxespad=0.0)

    fig.tight_layout()
    out = FIG_DIR / "fig_strategy_ranking.pdf"
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out.with_suffix(".png"), bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


# --------------------------------------------------------------------------
# Figure 2 — Cost vs. quality scatter (runtime ms vs burned %)
# --------------------------------------------------------------------------
def fig_cost_quality(summary: list[dict]) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    # Per-strategy label offsets (x in points, y in points) to avoid collision
    offsets = {
        "random":               (8,  0,   "left"),
        "max_degree":           (8,  8,   "left"),
        "max_white_neighbors":  (8, -10,  "left"),
        "min_cut_edge_front":   (-8, 8,   "right"),
        "betweenness_front":    (8, -10,  "left"),
        "min_damage_cut":       (8,  8,   "left"),
        "hybrid_density_aware": (-8,-10,  "right"),
        "one_step_lookahead":   (8,  8,   "left"),
    }
    for r in summary:
        fam, col = PHILO[r["strategy"]]
        ax.scatter(r["runtime"], r["mean"], s=140, color=col,
                   edgecolor="#1e293b", linewidth=0.8, zorder=3, alpha=0.9)
        dx, dy, ha = offsets.get(r["strategy"], (8, 0, "left"))
        ax.annotate(DISPLAY[r["strategy"]],
                    (r["runtime"], r["mean"]),
                    xytext=(dx, dy), textcoords="offset points",
                    fontsize=8.5, va="center", ha=ha, color="#1e293b")

    ax.set_xscale("log")
    ax.set_xlabel("Mean runtime per turn (ms, log scale)")
    ax.set_ylabel("Mean burned fraction (%)")
    ax.set_xlim(0.15, 200)
    ax.set_ylim(20, 80)
    ax.grid(True, which="both", linestyle=":", color="#cbd5e1", alpha=0.6)
    ax.set_axisbelow(True)

    ax.axhline(27.5, color=PURPLE, linestyle="--", linewidth=0.8, alpha=0.7)
    ax.text(0.18, 28.5, "Pareto frontier (Lookahead, 27.5%)",
            color=PURPLE, fontsize=8, va="bottom")

    families = []
    seen = set()
    for r in summary:
        fam, col = PHILO[r["strategy"]]
        if fam not in seen:
            families.append((fam, col))
            seen.add(fam)
    handles = [mpatches.Patch(color=c, label=f) for f, c in families]
    ax.legend(handles=handles, loc="upper right", frameon=False, fontsize=8.5,
              title="Philosophy", title_fontsize=8.5)

    fig.tight_layout()
    out = FIG_DIR / "fig_cost_quality.pdf"
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out.with_suffix(".png"), bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


# --------------------------------------------------------------------------
# Figure 3 — Köyceğiz real-map case study bar chart
# --------------------------------------------------------------------------
def fig_koycegiz_case() -> None:
    # From Table 5.2 in the report
    data = [
        ("one_step_lookahead",   16.8),
        ("min_damage_cut",       19.8),
        ("hybrid_density_aware", 19.8),
        ("max_white_neighbors",  20.8),
        ("betweenness_front",    20.8),
        ("max_degree",           31.7),
        ("min_cut_edge_front",   31.7),
        ("random",               31.7),
    ]
    names = [DISPLAY[s] for s, _ in data]
    vals = [v for _, v in data]
    colors = [PHILO[s][1] for s, _ in data]

    fig, ax = plt.subplots(figsize=(7.6, 4.0))
    ypos = np.arange(len(names))
    bars = ax.barh(ypos, vals, color=colors, edgecolor="#1e293b",
                   linewidth=0.6, alpha=0.85)
    ax.set_yticks(ypos)
    ax.set_yticklabels(names)
    ax.invert_yaxis()
    ax.set_xlabel("Burned fraction on Köyceğiz–Marmaris real map (%)")
    ax.set_xlim(0, 40)
    ax.grid(axis="x", linestyle=":", color="#cbd5e1", alpha=0.7)
    ax.set_axisbelow(True)
    for bar, v in zip(bars, vals):
        ax.text(v + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{v:.1f}%", va="center", fontsize=9, color="#1e293b")

    ax.axvline(31.7, color=SLATE, linestyle="--", linewidth=0.8, alpha=0.6)
    ax.text(31.7, -0.7, "Random baseline (31.7%)", color=SLATE,
            fontsize=8.5, ha="center", va="bottom")

    fig.tight_layout()
    out = FIG_DIR / "fig_koycegiz_bars.pdf"
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out.with_suffix(".png"), bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


# --------------------------------------------------------------------------
# Figure 4 — Burned-% distribution per strategy (boxplot across 594 runs)
# --------------------------------------------------------------------------
def fig_distribution(results: list[dict], summary: list[dict]) -> None:
    order = [r["strategy"] for r in sorted(summary, key=lambda x: x["mean"])]
    by_strat = {s: [] for s in order}
    for r in results:
        if r["strategy"] in by_strat:
            by_strat[r["strategy"]].append(r["burned"])

    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    data = [by_strat[s] for s in order]
    positions = np.arange(len(order))
    bp = ax.boxplot(
        data, positions=positions, widths=0.6, patch_artist=True,
        medianprops=dict(color="#1e293b", linewidth=1.2),
        flierprops=dict(marker=".", markersize=2.5, markerfacecolor="#94a3b8",
                        markeredgecolor="#94a3b8", alpha=0.4),
        whiskerprops=dict(color="#475569", linewidth=0.8),
        capprops=dict(color="#475569", linewidth=0.8),
    )
    for patch, s in zip(bp["boxes"], order):
        patch.set_facecolor(PHILO[s][1])
        patch.set_alpha(0.55)
        patch.set_edgecolor("#1e293b")
        patch.set_linewidth(0.6)

    ax.set_xticks(positions)
    ax.set_xticklabels([DISPLAY[s] for s in order], rotation=28, ha="right")
    ax.set_ylabel("Burned fraction (%)")
    ax.set_ylim(0, 105)
    ax.grid(axis="y", linestyle=":", color="#cbd5e1", alpha=0.7)
    ax.set_axisbelow(True)

    fig.tight_layout()
    out = FIG_DIR / "fig_distribution.pdf"
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out.with_suffix(".png"), bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


# --------------------------------------------------------------------------
# Figure 5 — Scaling: mean burned % by graph size, per strategy
# --------------------------------------------------------------------------
def fig_size_scaling(results: list[dict]) -> None:
    sizes = sorted({r["n"] for r in results})
    strategies = ["one_step_lookahead", "betweenness_front",
                  "max_white_neighbors", "min_damage_cut",
                  "max_degree", "random"]

    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    for s in strategies:
        means = []
        for n in sizes:
            vals = [r["burned"] for r in results
                    if r["strategy"] == s and r["n"] == n]
            means.append(np.mean(vals) if vals else np.nan)
        col = PHILO[s][1]
        ax.plot(sizes, means, marker="o", color=col, linewidth=1.6,
                label=DISPLAY[s], markersize=6, markeredgecolor="#1e293b",
                markeredgewidth=0.6)

    ax.set_xticks(sizes)
    ax.set_xlabel("Graph size (vertices)")
    ax.set_ylabel("Mean burned fraction (%)")
    ax.grid(True, linestyle=":", color="#cbd5e1", alpha=0.6)
    ax.set_axisbelow(True)
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), frameon=False,
              fontsize=8.5, borderaxespad=0.0)
    ax.set_ylim(0, 85)
    fig.tight_layout()
    out = FIG_DIR / "fig_size_scaling.pdf"
    fig.savefig(out, bbox_inches="tight")
    fig.savefig(out.with_suffix(".png"), bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


if __name__ == "__main__":
    summary = load_summary()
    results = load_results()
    fig_strategy_ranking(summary)
    fig_cost_quality(summary)
    fig_koycegiz_case()
    fig_distribution(results, summary)
    fig_size_scaling(results)
    print("done.")
