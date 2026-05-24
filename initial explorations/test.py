"""
Firefighter Problem Simulation (Delaunay Planar Graphs)
========================================================
Includes step-by-step trace for each strategy at n=30,
plus full averaged results across all configurations.

Test Configuration:
  - Graph Sizes:        n = 20, 30, 40 vertices
  - Resources per Turn: k = 1, 2, 3
  - Runs per Config:    15 randomized runs, averaged
  - Strategies:         Max Degree, Max White Neighbors,
                        Min-Cut Edge, Min-Cut Vertex
  - Graph Model:        Delaunay triangulation (planar)
  - Primary Metric:     Burned nodes (K) — lower is better
"""

import random
import numpy as np
import networkx as nx
import pandas as pd
from itertools import product
from scipy.spatial import Delaunay
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


# ── configuration ────────────────────────────────────────────────────
GRAPH_SIZES     = [30]
RESOURCES       = [1, 2, 3]
RUNS_PER_CONFIG = 15
STRATEGIES      = [
    "Max Degree",
    "Max White Neighbors",
    "Min-Cut Edge",
    "Min-Cut Vertex",
]


# ── graph generation ─────────────────────────────────────────────────
def generate_delaunay_graph(n):
    points = np.random.rand(n, 2)
    tri = Delaunay(points)
    G = nx.Graph()
    G.add_nodes_from(range(n))
    for simplex in tri.simplices:
        for i in range(3):
            for j in range(i + 1, 3):
                G.add_edge(simplex[i], simplex[j])
    pos = {i: tuple(points[i]) for i in range(n)}
    return G, pos


# ── strategy implementations ─────────────────────────────────────────
def _unprotected_neighbors(G, node, burned, protected):
    return sum(
        1 for nb in G.neighbors(node)
        if nb not in burned and nb not in protected
    )


def strategy_max_degree(G, white_nodes, burned, protected, k):
    ranked = sorted(white_nodes, key=lambda v: G.degree(v), reverse=True)
    return set(ranked[:k])


def strategy_max_white_neighbors(G, white_nodes, burned, protected, k):
    fire_front = [
        v for v in white_nodes
        if any(nb in burned for nb in G.neighbors(v))
    ]
    if not fire_front:
        return strategy_max_degree(G, white_nodes, burned, protected, k)
    ranked = sorted(
        fire_front,
        key=lambda v: _unprotected_neighbors(G, v, burned, protected),
        reverse=True,
    )
    return set(ranked[:k])


def strategy_min_cut_edge(G, white_nodes, burned, protected, k):
    """Min-edge-cut on white-only subgraph between fire front and
    distant targets.  Prioritise fire-front vertices that touch the
    most cut edges (they 'cover' the barrier best)."""
    fire_front = [
        v for v in white_nodes
        if any(nb in burned for nb in G.neighbors(v))
    ]
    if not fire_front:
        return strategy_max_degree(G, white_nodes, burned, protected, k)

    white_set = set(white_nodes)
    ff_set = set(fire_front)
    safe_white = white_set - ff_set

    if not safe_white:
        return set(sorted(fire_front, key=lambda v: G.degree(v), reverse=True)[:k])

    W_sub = G.subgraph(white_set)
    dist = {}
    for ff in fire_front:
        for node, d in nx.single_source_shortest_path_length(W_sub, ff).items():
            if node in safe_white and (node not in dist or d < dist[node]):
                dist[node] = d

    if not dist:
        return set(sorted(fire_front, key=lambda v: G.degree(v), reverse=True)[:k])

    sorted_targets = sorted(dist.items(), key=lambda x: -x[1])
    n_targets = max(k, len(sorted_targets) // 3)
    targets = {v for v, _ in sorted_targets[:n_targets]}

    H = nx.DiGraph()
    INF = float("inf")
    for u, v in W_sub.edges():
        H.add_edge(u, v, capacity=1)
        H.add_edge(v, u, capacity=1)
    s, t = "s", "t"
    for v in fire_front:
        H.add_edge(s, v, capacity=INF)
    for z in targets:
        H.add_edge(z, t, capacity=INF)

    try:
        _, (reachable, non_reachable) = nx.minimum_cut(H, s, t)
        scores = {}
        for v in fire_front:
            n_cut = 0
            for nb in W_sub.neighbors(v):
                if (v in reachable) != (nb in reachable):
                    n_cut += 1
            scores[v] = n_cut
        ranked = sorted(fire_front, key=lambda v: (-scores.get(v, 0), -G.degree(v)))
    except Exception:
        ranked = sorted(fire_front, key=lambda v: -G.degree(v))

    return set(ranked[:k])


def strategy_min_cut_vertex(G, white_nodes, burned, protected, k):
    """Min-node-cut on white-only subgraph: find the minimum vertex
    separator between fire front and distant targets, then prioritise
    separator members (even behind the front — pre-building a wall)."""
    fire_front = [
        v for v in white_nodes
        if any(nb in burned for nb in G.neighbors(v))
    ]
    if not fire_front:
        return strategy_max_degree(G, white_nodes, burned, protected, k)

    white_set = set(white_nodes)
    ff_set = set(fire_front)
    safe_white = white_set - ff_set

    if not safe_white:
        return set(sorted(fire_front, key=lambda v: G.degree(v), reverse=True)[:k])

    W_sub = G.subgraph(white_set)
    dist = {}
    for ff in fire_front:
        for node, d in nx.single_source_shortest_path_length(W_sub, ff).items():
            if node in safe_white and (node not in dist or d < dist[node]):
                dist[node] = d

    if not dist:
        return set(sorted(fire_front, key=lambda v: G.degree(v), reverse=True)[:k])

    sorted_targets = sorted(dist.items(), key=lambda x: -x[1])
    n_targets = max(k, len(sorted_targets) // 3)
    targets = [v for v, _ in sorted_targets[:n_targets]]

    H = W_sub.copy()
    s, t = "s", "t"
    for v in fire_front:
        H.add_edge(s, v)
    for z in targets:
        H.add_edge(z, t)

    try:
        cut_nodes = nx.minimum_node_cut(H, s, t) - {s, t}
        ff_cut = sorted([v for v in cut_nodes if v in ff_set],
                        key=lambda v: -G.degree(v))
        behind_cut = sorted([v for v in cut_nodes if v in safe_white],
                            key=lambda v: -G.degree(v))
        rest = sorted([v for v in fire_front if v not in cut_nodes],
                      key=lambda v: -G.degree(v))
        ranked = ff_cut + behind_cut + rest
    except Exception:
        ranked = sorted(fire_front, key=lambda v: G.degree(v), reverse=True)

    return set(ranked[:k])


STRATEGY_FN = {
    "Max Degree":          strategy_max_degree,
    "Max White Neighbors": strategy_max_white_neighbors,
    "Min-Cut Edge":        strategy_min_cut_edge,
    "Min-Cut Vertex":      strategy_min_cut_vertex,
}


# ── simulation engine (with optional tracing) ────────────────────────
def simulate_firefighter(G, source, strategy_fn, k, trace=False):
    burned    = {source}
    protected = set()
    turn      = 0
    log       = []

    if trace:
        log.append({
            "Turn": turn,
            "Phase": "Fire Start",
            "Burned (new)": sorted(burned),
            "Protected (new)": [],
            "Total Burned": len(burned),
            "Total Protected": 0,
            "Remaining White": len(G) - len(burned),
        })

    while True:
        turn += 1

        # ── firefighter phase ────────────────────────────────────
        white = [
            v for v in G.nodes()
            if v not in burned and v not in protected
        ]
        if not white:
            if trace:
                log.append({
                    "Turn": turn,
                    "Phase": "END — no white nodes left",
                    "Burned (new)": [],
                    "Protected (new)": [],
                    "Total Burned": len(burned),
                    "Total Protected": len(protected),
                    "Remaining White": 0,
                })
            break

        chosen = strategy_fn(G, white, burned, protected, k)
        protected |= chosen

        if trace:
            log.append({
                "Turn": turn,
                "Phase": "Protect",
                "Burned (new)": [],
                "Protected (new)": sorted(chosen),
                "Total Burned": len(burned),
                "Total Protected": len(protected),
                "Remaining White": len(G) - len(burned) - len(protected),
            })

        # ── fire phase ───────────────────────────────────────────
        new_fire = set()
        for b in burned:
            for nb in G.neighbors(b):
                if nb not in burned and nb not in protected:
                    new_fire.add(nb)

        if not new_fire:
            if trace:
                log.append({
                    "Turn": turn,
                    "Phase": "END — fire contained",
                    "Burned (new)": [],
                    "Protected (new)": [],
                    "Total Burned": len(burned),
                    "Total Protected": len(protected),
                    "Remaining White": len(G) - len(burned) - len(protected),
                })
            break

        burned |= new_fire

        if trace:
            log.append({
                "Turn": turn,
                "Phase": "Fire Spread",
                "Burned (new)": sorted(new_fire),
                "Protected (new)": [],
                "Total Burned": len(burned),
                "Total Protected": len(protected),
                "Remaining White": len(G) - len(burned) - len(protected),
            })

    return len(burned), log


# ══════════════════════════════════════════════════════════════════════
#  PART 1 — STEP-BY-STEP TRACE (n=30, k=2, one run per strategy)
# ══════════════════════════════════════════════════════════════════════
print("=" * 75)
print("  STEP-BY-STEP TRACE  |  n = 30, k = 2, single Delaunay graph")
print("=" * 75)

# Generate one shared graph so strategies are directly comparable
G_trace, pos_trace = generate_delaunay_graph(30)
source_node = random.choice(list(G_trace.nodes()))

print(f"\n  Graph: 30-node Delaunay  |  Edges: {G_trace.number_of_edges()}"
      f"  |  Fire source: node {source_node}")
print(f"  Degree range: {min(dict(G_trace.degree()).values())}"
      f"–{max(dict(G_trace.degree()).values())}"
      f"  |  Avg degree: {2*G_trace.number_of_edges()/30:.1f}")

trace_logs = {}

for strategy_name in STRATEGIES:
    fn = STRATEGY_FN[strategy_name]
    total_burned, log = simulate_firefighter(
        G_trace, source_node, fn, k=2, trace=True
    )
    trace_logs[strategy_name] = log

    print(f"\n{'─' * 75}")
    print(f"  Strategy: {strategy_name}")
    print(f"{'─' * 75}")

    df_log = pd.DataFrame(log)
    df_log["Burned (new)"]    = df_log["Burned (new)"].apply(
        lambda x: ", ".join(map(str, x)) if x else "—"
    )
    df_log["Protected (new)"] = df_log["Protected (new)"].apply(
        lambda x: ", ".join(map(str, x)) if x else "—"
    )

    print(df_log.to_string(index=False))
    print(f"\n  ► Result: {total_burned} nodes burned out of 30")

# ── matplotlib: step-by-step graph snapshots per strategy ─────────────
CLR_BURNED    = "#e74c3c"
CLR_PROTECTED = "#3498db"
CLR_WHITE     = "#2ecc71"
LEGEND_HANDLES = [
    Patch(facecolor=CLR_BURNED,    edgecolor="white", label="Burned"),
    Patch(facecolor=CLR_PROTECTED, edgecolor="white", label="Protected"),
    Patch(facecolor=CLR_WHITE,     edgecolor="white", label="White"),
]

for strategy_name in STRATEGIES:
    log = trace_logs[strategy_name]

    burned_cum = set()
    protected_cum = set()
    snapshots = []
    for entry in log:
        burned_cum |= set(entry["Burned (new)"])
        protected_cum |= set(entry["Protected (new)"])
        phase = entry["Phase"]
        label = (f"T{entry['Turn']}: Final"
                 if phase.startswith("END") else
                 f"T{entry['Turn']}: {phase}")
        snapshots.append({
            "burned": burned_cum.copy(),
            "protected": protected_cum.copy(),
            "label": label,
        })

    n_snap = len(snapshots)
    cols = min(n_snap, 4)
    rows = -(-n_snap // cols)
    fig, axes = plt.subplots(rows, cols, figsize=(4.5 * cols, 4.2 * rows))
    axes = np.atleast_1d(axes).flatten()

    for i, snap in enumerate(snapshots):
        ax = axes[i]
        node_colors = []
        node_sizes = []
        for node in G_trace.nodes():
            if node in snap["burned"]:
                node_colors.append(CLR_BURNED)
            elif node in snap["protected"]:
                node_colors.append(CLR_PROTECTED)
            else:
                node_colors.append(CLR_WHITE)
            node_sizes.append(300 if node == source_node else 160)

        nx.draw_networkx_edges(G_trace, pos_trace, ax=ax,
                               edge_color="#cccccc", width=0.7)
        nx.draw_networkx_nodes(G_trace, pos_trace, ax=ax,
                               node_color=node_colors,
                               node_size=node_sizes,
                               edgecolors="white", linewidths=0.8)
        nx.draw_networkx_labels(G_trace, pos_trace, ax=ax,
                                font_size=6, font_color="white",
                                font_weight="bold")
        ax.set_title(snap["label"], fontsize=9, fontweight="bold")
        ax.axis("off")

    for j in range(n_snap, len(axes)):
        axes[j].axis("off")

    final_burned = len(snapshots[-1]["burned"])
    fig.suptitle(
        f"{strategy_name}  (n=30, k=2, source={source_node}, "
        f"burned={final_burned}/30)",
        fontsize=13, fontweight="bold",
    )
    fig.legend(handles=LEGEND_HANDLES, loc="lower center",
               ncol=3, fontsize=10, frameon=True,
               bbox_to_anchor=(0.5, -0.01))
    plt.tight_layout(rect=[0, 0.04, 1, 0.95])
    safe = strategy_name.lower().replace(" ", "_").replace("-", "")
    fname = f"step_graph_{safe}.png"
    plt.savefig(fname, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ Saved → {fname}")


# ══════════════════════════════════════════════════════════════════════
#  PART 2 — FULL AVERAGED RESULTS (all configs, 15 runs each)
# ══════════════════════════════════════════════════════════════════════
print("\n\n")
print("=" * 75)
print("  FULL SIMULATION — 15 AVERAGED RUNS PER CONFIGURATION")
print("=" * 75)


records = []
burned_by = {(n, k, s): [] for n, k, s in product(GRAPH_SIZES, RESOURCES, STRATEGIES)}

for n, k in product(GRAPH_SIZES, RESOURCES):
    for run in range(RUNS_PER_CONFIG):
        G, _ = generate_delaunay_graph(n)
        source = random.choice(list(G.nodes()))
        for strategy_name in STRATEGIES:
            fn = STRATEGY_FN[strategy_name]
            burned, _ = simulate_firefighter(G, source, fn, k, trace=False)
            burned_by[(n, k, strategy_name)].append(burned)

for n, k, strategy_name in product(GRAPH_SIZES, RESOURCES, STRATEGIES):
    counts = burned_by[(n, k, strategy_name)]
    avg_burned = round(sum(counts) / len(counts), 1)
    records.append({
        "Graph Size (n)":       n,
        "Resources (k)":        k,
        "Strategy":             strategy_name,
        "Avg Burned Nodes (K)": avg_burned,
    })

df = pd.DataFrame(records)

pivot = df.pivot_table(
    index=["Strategy", "Graph Size (n)"],
    columns="Resources (k)",
    values="Avg Burned Nodes (K)",
)
pivot.columns = [f"k = {c}" for c in pivot.columns]
pivot = pivot.reset_index()

print("\n" + df.to_string(index=False))
print(f"\n{'=' * 75}")
print("  PIVOT TABLE (Avg Burned Nodes by Strategy & Graph Size)")
print("=" * 75)
print(pivot.to_string(index=False))