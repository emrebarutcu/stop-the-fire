from __future__ import annotations

import csv
import os
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from engine.graph_gen import generate_graph
from engine.fire_engine import run_game
from engine.models import GameResult
from engine.strategies.base import Strategy


@dataclass
class CalibrationConfig:
    density: float
    vertex_counts: list[int]
    n_runs: int
    strategy: Strategy
    output_dir: Path = Path("calibration/results")


def run_calibration(config: CalibrationConfig) -> pd.DataFrame:
    config.output_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict] = []

    for n in config.vertex_counts:
        for seed in range(1, config.n_runs + 1):
            graph = generate_graph(n, config.density, seed)
            result = run_game(graph, config.strategy)
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

    csv_path = config.output_dir / f"{config.strategy.name}_d{config.density}.csv"
    df.to_csv(csv_path, index=False)

    return df


def print_summary(df: pd.DataFrame, input_density: float | None = None) -> None:
    strategy = df["strategy"].iloc[0]
    density_label = input_density if input_density is not None else df["density"].iloc[0]

    print(f"\n{'='*60}")
    print(f"  Kalibrasyon Sonuclari: {strategy}, density={density_label}")
    print(f"{'='*60}")

    for n in sorted(df["n_vertices"].unique()):
        sub = df[df["n_vertices"] == n]
        print(f"\n  n={n}  ({len(sub)} runs)")
        print(f"  {'-'*50}")
        for col in ["turns", "K", "Y", "B", "K_over_Y", "K_over_B", "Y_over_B"]:
            finite = sub[col].replace([float("inf"), float("-inf")], pd.NA).dropna()
            if finite.empty:
                label = col.ljust(10)
                print(f"    {label} all inf (B=0 in every run)")
                continue
            mean = finite.mean()
            std = finite.std() if len(finite) > 1 else 0.0
            lo = finite.min()
            hi = finite.max()
            n_inf = len(sub) - len(finite)
            label = col.ljust(10)
            inf_note = f"  ({n_inf} inf)" if n_inf > 0 else ""
            print(f"    {label} avg={mean:6.2f} ± {std:5.2f}   [{lo:.2f} .. {hi:.2f}]{inf_note}")

    print(f"\n{'='*60}\n")
