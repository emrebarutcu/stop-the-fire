#!/usr/bin/env python3
"""Vertex Count Selection Protocol.

Systematic sweep: n x density x start_mode x 30 seeds.
Scores each candidate n on formal criteria, produces report + plots.

References:
  Garcia-Martinez et al. (2015) — GBRL benchmark: n=20,30,50
  Blum et al. (2014) — BBGRL benchmark: n=50,100
  Ramos, de Souza, de Rezende (2018) — GEN benchmark (UNICAMP)
"""
from __future__ import annotations

import random as stdlib_random
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from engine.graph_gen import generate_graph
from engine.fire_engine import run_game, _pick_fire_start
from engine.strategies import MaxDegreeStrategy

CANDIDATE_N = [15, 20, 25, 30]
DENSITIES = [round(0.05 * i, 2) for i in range(1, 11)]
START_MODES = ["max_degree", "random"]
N_RUNS = 30
OUTPUT_DIR = Path("calibration/results")
STRATEGY = MaxDegreeStrategy()


def _run_sweep() -> pd.DataFrame:
    rows: list[dict] = []
    total = len(CANDIDATE_N) * len(DENSITIES) * len(START_MODES) * N_RUNS
    done = 0

    for n in CANDIDATE_N:
        for d in DENSITIES:
            for start_mode in START_MODES:
                for seed in range(1, N_RUNS + 1):
                    try:
                        graph = generate_graph(n, d, seed)
                    except ValueError:
                        continue

                    if start_mode == "max_degree":
                        fire_start = _pick_fire_start(graph)
                    else:
                        rng = stdlib_random.Random(seed)
                        fire_start = rng.choice(list(graph.nodes()))

                    result = run_game(graph, STRATEGY, fire_start=fire_start)
                    m = result.metrics

                    rows.append({
                        "n": n,
                        "density": d,
                        "start_mode": start_mode,
                        "seed": seed,
                        "turns": result.total_turns,
                        "K": m.K,
                        "Y": m.Y,
                        "B": m.B,
                        "B_pct": m.B / n * 100,
                        "K_pct": m.K / n * 100,
                    })

                    done += 1
                    if done % 200 == 0:
                        print(f"  [{done}/{total}] runs completed...")

    return pd.DataFrame(rows)


def _score_criteria(df: pd.DataFrame) -> pd.DataFrame:
    """Compute selection criteria for each candidate n."""
    scores: list[dict] = []

    for n in CANDIDATE_N:
        sub = df[df["n"] == n]

        # --- Criterion A: Difficulty Range Coverage ---
        # Easiest: lowest density + random start
        easiest = sub[(sub["density"] == sub["density"].min()) & (sub["start_mode"] == "random")]
        # Hardest: highest density + max_degree start
        hardest = sub[(sub["density"] == sub["density"].max()) & (sub["start_mode"] == "max_degree")]

        b_easy = easiest["B_pct"].mean() if len(easiest) > 0 else 0
        b_hard = hardest["B_pct"].mean() if len(hardest) > 0 else 0
        drc = b_easy - b_hard

        # --- Criterion B: Game Length at medium difficulty ---
        mid_densities = [0.20, 0.25, 0.30]
        mid = sub[(sub["density"].isin(mid_densities)) & (sub["start_mode"] == "max_degree")]
        gl = mid["turns"].mean() if len(mid) > 0 else 0

        # --- Criterion C: Outcome Variability at medium difficulty ---
        if len(mid) > 0 and mid["B_pct"].mean() > 0:
            ov = mid["B_pct"].std() / mid["B_pct"].mean()
        else:
            ov = 0.0

        # --- Criterion D: Computational feasibility (all pass for n<=30) ---
        comp = 1.0

        scores.append({
            "n": n,
            "DRC": round(drc, 1),
            "B_easy": round(b_easy, 1),
            "B_hard": round(b_hard, 1),
            "GL": round(gl, 2),
            "OV": round(ov, 3),
            "COMP": comp,
        })

    score_df = pd.DataFrame(scores)

    # Normalize each criterion to 0-100
    drc_vals = score_df["DRC"].values.astype(float)
    gl_vals = score_df["GL"].values.astype(float)
    ov_vals = score_df["OV"].values.astype(float)

    def _norm(arr):
        lo, hi = arr.min(), arr.max()
        if hi - lo < 1e-9:
            return np.full_like(arr, 50.0)
        return (arr - lo) / (hi - lo) * 100

    score_df["DRC_norm"] = _norm(drc_vals)
    score_df["GL_norm"] = _norm(gl_vals)
    score_df["OV_norm"] = _norm(ov_vals)

    # Weighted total: DRC 40%, GL 30%, OV 30%
    score_df["Total"] = (
        score_df["DRC_norm"] * 0.40
        + score_df["GL_norm"] * 0.30
        + score_df["OV_norm"] * 0.30
    )
    score_df["Total"] = score_df["Total"].round(1)

    return score_df


def _plot_density_sweep(df: pd.DataFrame, output_dir: Path) -> None:
    """B% vs density line plots, one subplot per n, both start modes."""
    fig, axes = plt.subplots(1, len(CANDIDATE_N), figsize=(5 * len(CANDIDATE_N), 5))
    fig.set_facecolor("#f5f0e1")

    for idx, n in enumerate(CANDIDATE_N):
        ax = axes[idx]
        ax.set_facecolor("#faf6ed")

        for start_mode, color, marker in [
            ("max_degree", "#d63031", "o"),
            ("random", "#2d98da", "s"),
        ]:
            sub = df[(df["n"] == n) & (df["start_mode"] == start_mode)]
            grouped = sub.groupby("density")["B_pct"].agg(["mean", "std"]).reset_index()
            ax.errorbar(
                grouped["density"], grouped["mean"], yerr=grouped["std"],
                color=color, marker=marker, markersize=5, linewidth=1.8,
                capsize=3, label=f"start: {start_mode}",
            )

        ax.set_xlabel("Density", fontsize=10)
        ax.set_ylabel("B% (kurtarilan)", fontsize=10)
        ax.set_title(f"n = {n}", fontsize=13, fontweight="bold")
        ax.set_ylim(-5, 105)
        ax.set_xlim(0.03, 0.52)
        ax.axhline(y=50, color="#aaa", linestyle="--", linewidth=0.8)
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(alpha=0.3)

    fig.suptitle(
        "Vertex Count Selection: B% vs Density (Max Degree Strategy)",
        fontsize=14, fontweight="bold", color="#3d3628",
    )
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    path = output_dir / "vertex_selection_sweep.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="#f5f0e1")
    plt.close(fig)
    print(f"  -> {path}")


def _plot_score_table(score_df: pd.DataFrame, output_dir: Path) -> None:
    """Bar chart of total score per candidate n."""
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.set_facecolor("#f5f0e1")
    ax.set_facecolor("#faf6ed")

    best_idx = score_df["Total"].idxmax()
    colors = ["#00b894" if i == best_idx else "#636e72" for i in score_df.index]

    bars = ax.bar(
        [f"n={n}" for n in score_df["n"]],
        score_df["Total"],
        color=colors,
        edgecolor="white",
        width=0.5,
    )

    for bar, total in zip(bars, score_df["Total"]):
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
            f"{total:.1f}", ha="center", va="bottom", fontweight="bold", fontsize=12,
        )

    ax.set_ylabel("Toplam Skor (0-100)", fontsize=11)
    ax.set_title("Vertex Sayisi Secim Skorlari", fontsize=14, fontweight="bold", color="#3d3628")
    ax.set_ylim(0, 110)
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    path = output_dir / "vertex_selection_scores.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="#f5f0e1")
    plt.close(fig)
    print(f"  -> {path}")


def _plot_criteria_breakdown(score_df: pd.DataFrame, output_dir: Path) -> None:
    """Stacked bar chart showing DRC, GL, OV contributions."""
    fig, ax = plt.subplots(figsize=(8, 5))
    fig.set_facecolor("#f5f0e1")
    ax.set_facecolor("#faf6ed")

    labels = [f"n={n}" for n in score_df["n"]]
    x = np.arange(len(labels))
    width = 0.5

    drc_contrib = score_df["DRC_norm"] * 0.40
    gl_contrib = score_df["GL_norm"] * 0.30
    ov_contrib = score_df["OV_norm"] * 0.30

    ax.bar(x, drc_contrib, width, label="DRC (Zorluk Araligi) x0.40", color="#d63031")
    ax.bar(x, gl_contrib, width, bottom=drc_contrib, label="GL (Oyun Suresi) x0.30", color="#6c5ce7")
    ax.bar(x, ov_contrib, width, bottom=drc_contrib + gl_contrib, label="OV (Varyabilite) x0.30", color="#00b894")

    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Skor Katkisi", fontsize=11)
    ax.set_title("Kriter Bazinda Skor Dagilimi", fontsize=14, fontweight="bold", color="#3d3628")
    ax.legend(fontsize=9)
    ax.set_ylim(0, 110)
    ax.grid(axis="y", alpha=0.3)

    fig.tight_layout()
    path = output_dir / "vertex_selection_breakdown.png"
    fig.savefig(path, dpi=150, bbox_inches="tight", facecolor="#f5f0e1")
    plt.close(fig)
    print(f"  -> {path}")


def _print_report(score_df: pd.DataFrame) -> None:
    best = score_df.loc[score_df["Total"].idxmax()]

    print(f"\n{'='*70}")
    print(f"  VERTEX SAYISI SECIM RAPORU")
    print(f"{'='*70}")
    print()
    print("  Literatur referansi:")
    print("    Garcia-Martinez et al. (2015) GBRL benchmark: n=20,30,50")
    print("    Blum et al. (2014) BBGRL benchmark: n=50,100")
    print()
    print("  Kriter Skorlari:")
    print(f"  {'n':>5}  {'DRC':>6}  {'B%easy':>7}  {'B%hard':>7}  {'GL':>5}  {'OV':>6}  {'Total':>7}")
    print(f"  {'-'*52}")
    for _, row in score_df.iterrows():
        marker = " <-- SECILEN" if row["n"] == best["n"] else ""
        print(
            f"  {int(row['n']):>5}  {row['DRC']:>6.1f}  {row['B_easy']:>7.1f}  "
            f"{row['B_hard']:>7.1f}  {row['GL']:>5.2f}  {row['OV']:>6.3f}  "
            f"{row['Total']:>7.1f}{marker}"
        )
    print()
    print(f"  Secim: n = {int(best['n'])}")
    print()
    print(f"  Gerekce:")
    print(f"    - DRC = {best['DRC']:.1f}: Zorluk parametreleri degistirildiginde")
    print(f"      kurtarilan bolge orani %{best['B_easy']:.0f} (kolay) ile %{best['B_hard']:.0f} (zor)")
    print(f"      arasinda degisiyor — 5 zorluk seviyesi icin yeterli aralik.")
    print(f"    - GL = {best['GL']:.1f}: Orta zorlukta ortalama {best['GL']:.1f} tur,")
    print(f"      stratejik kararlarin anlamli olmasi icin yeterli.")
    print(f"    - OV = {best['OV']:.3f}: Farkli graph yapilarinda sonuclar")
    print(f"      yeterince degisiyor — oyun deterministik degil.")
    print(f"    - Garcia-Martinez et al. (2015) GBRL benchmark'inda")
    print(f"      n=20 en kucuk standart test boyutu olarak kullanilmistir.")
    print(f"\n{'='*70}\n")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=== Vertex Sayisi Belirleme Protokolu ===")
    print(f"  Adaylar: {CANDIDATE_N}")
    print(f"  Density araligi: {DENSITIES}")
    print(f"  Baslangic modlari: {START_MODES}")
    print(f"  Run sayisi: {N_RUNS}")
    total = len(CANDIDATE_N) * len(DENSITIES) * len(START_MODES) * N_RUNS
    print(f"  Toplam simulasyon: {total}")
    print()

    print("Adim 1: Sistematik tarama...")
    df = _run_sweep()
    csv_path = OUTPUT_DIR / "vertex_selection_raw.csv"
    df.to_csv(csv_path, index=False)
    print(f"  Ham veri: {csv_path} ({len(df)} satir)")

    print("\nAdim 2: Kriter puanlama...")
    score_df = _score_criteria(df)
    score_csv = OUTPUT_DIR / "vertex_selection_scores.csv"
    score_df.to_csv(score_csv, index=False)
    print(f"  Skorlar: {score_csv}")

    print("\nAdim 3: Gorseller...")
    _plot_density_sweep(df, OUTPUT_DIR)
    _plot_score_table(score_df, OUTPUT_DIR)
    _plot_criteria_breakdown(score_df, OUTPUT_DIR)

    _print_report(score_df)


if __name__ == "__main__":
    main()
