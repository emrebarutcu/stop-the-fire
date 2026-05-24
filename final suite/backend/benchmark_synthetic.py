"""Synthetic benchmark for the firefighter engine.

Design (per the IE 492 final presentation S11 claim):
    1 run = (graph_size, starting_point, strategy, k)

Configuration:
    Topology  : delaunay (planar)            [1]
    Sizes     : n in {30, 60, 100}           [3]
    Seeds     : 18 graph instances per size  [18]
    Starts    : 11 random fire origins each  [11]
    k value   : 2 (midterm-comparable)       [1]
    Strategies: 8 (all_strategies)           [8]
    -------------------------------------------------
    Total     : 1 * 3 * 18 * 11 * 1 * 8 = 4752 runs

Outputs:
    backend/benchmark_results.csv   - one row per run
    backend/benchmark_summary.csv   - aggregated per-strategy ranking
"""

from __future__ import annotations

import csv
import random
import sys
import time
from pathlib import Path

# Allow running as a script: `python backend/benchmark_synthetic.py`
sys.path.insert(0, str(Path(__file__).parent))

from firefighter_engine import (
    BetweennessFront,
    HybridDensityAware,
    MaxDegree,
    MaxWhiteNeighbors,
    MinCutEdgeFront,
    MinDamageCut,
    OneStepLookahead,
    RandomStrategy,
    init_state,
    make_delaunay_planar,
    simulate,
)


SIZES = [30, 60, 100]
SEEDS = list(range(18))          # 18 graph instances per size
N_STARTS = 11                    # random fire origins per graph
K_VALUES = [2]                   # midterm-comparable resource level


def fresh_strategies(seed: int):
    """Re-instantiate strategies per run; RandomStrategy is seeded so it is
    reproducible while still varying with the run index."""
    return [
        MaxDegree(),
        MaxWhiteNeighbors(),
        MinCutEdgeFront(),
        MinDamageCut(),
        BetweennessFront(),
        OneStepLookahead(),
        HybridDensityAware(),
        RandomStrategy(seed=seed),
    ]


def main(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    results_path = out_dir / "benchmark_results.csv"
    summary_path = out_dir / "benchmark_summary.csv"

    rows = []
    total_runs = len(SIZES) * len(SEEDS) * N_STARTS * len(K_VALUES) * len(
        fresh_strategies(0)
    )
    print(f"Planned runs: {total_runs}", flush=True)

    run_idx = 0
    t_global = time.perf_counter()

    for n in SIZES:
        for graph_seed in SEEDS:
            G = make_delaunay_planar(n, seed=graph_seed)
            # deterministic but graph-dependent fire-origin sample
            rng = random.Random(graph_seed * 1000 + n)
            nodes = list(G.nodes())
            if len(nodes) <= N_STARTS:
                starts = nodes
            else:
                starts = rng.sample(nodes, N_STARTS)

            for start in starts:
                for k in K_VALUES:
                    strategies = fresh_strategies(
                        seed=graph_seed * 100000 + int(start) * 10 + k
                    )
                    for strat in strategies:
                        state = init_state(G, start)
                        res = simulate(
                            G, state, strat, protect_per_turn=k, max_turns=1000
                        )
                        burned_pct = 100.0 * res.burned / max(1, res.n)
                        rows.append({
                            "n": n,
                            "graph_seed": graph_seed,
                            "start": int(start),
                            "k": k,
                            "strategy": strat.name,
                            "burned": res.burned,
                            "burned_pct": round(burned_pct, 4),
                            "saved": res.saved,
                            "protected": res.protected,
                            "turns": res.turns,
                            "runtime_s": round(res.runtime_s, 6),
                        })
                        run_idx += 1
                        if run_idx % 200 == 0:
                            elapsed = time.perf_counter() - t_global
                            rate = run_idx / elapsed
                            eta = (total_runs - run_idx) / rate
                            print(
                                f"  {run_idx}/{total_runs} runs "
                                f"({100*run_idx/total_runs:.1f}%) "
                                f"elapsed {elapsed:.1f}s eta {eta:.1f}s",
                                flush=True,
                            )

    elapsed = time.perf_counter() - t_global
    print(f"Completed {run_idx} runs in {elapsed:.1f}s", flush=True)

    # write detailed CSV
    fieldnames = list(rows[0].keys())
    with results_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {results_path}", flush=True)

    # aggregate per-strategy summary
    by_strat: dict[str, list[dict]] = {}
    for r in rows:
        by_strat.setdefault(r["strategy"], []).append(r)

    summary = []
    for strat_name, recs in by_strat.items():
        n_runs = len(recs)
        mean_burned_pct = sum(r["burned_pct"] for r in recs) / n_runs
        mean_runtime_ms = 1000.0 * sum(r["runtime_s"] for r in recs) / n_runs
        # std (population)
        mu = mean_burned_pct
        var = sum((r["burned_pct"] - mu) ** 2 for r in recs) / n_runs
        std = var ** 0.5
        summary.append({
            "strategy": strat_name,
            "n_runs": n_runs,
            "mean_burned_pct": round(mean_burned_pct, 3),
            "std_burned_pct": round(std, 3),
            "mean_runtime_ms": round(mean_runtime_ms, 4),
        })

    summary.sort(key=lambda d: d["mean_burned_pct"])
    print()
    print(f"{'Rank':>4}  {'Strategy':24}  {'Burned %':>10}  {'Std':>7}  {'ms':>9}  {'#runs':>6}")
    print("-" * 75)
    for i, s in enumerate(summary, start=1):
        print(
            f"{i:>4}  {s['strategy']:24}  "
            f"{s['mean_burned_pct']:>10.3f}  {s['std_burned_pct']:>7.3f}  "
            f"{s['mean_runtime_ms']:>9.4f}  {s['n_runs']:>6}"
        )

    with summary_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["rank", "strategy", "n_runs",
                           "mean_burned_pct", "std_burned_pct", "mean_runtime_ms"]
        )
        writer.writeheader()
        for i, s in enumerate(summary, start=1):
            writer.writerow({"rank": i, **s})
    print(f"\nWrote {summary_path}", flush=True)


if __name__ == "__main__":
    out = Path(__file__).parent.parent / "benchmark"
    main(out)
