"""Schematic figures for the IE 492 report:
   - Firefighter turn-by-turn mechanics on a small planar graph
   - Map-to-graph pipeline
   - Strategy philosophy comparison
"""
from __future__ import annotations

from pathlib import Path
import math

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle, Rectangle
import numpy as np
import networkx as nx

FIG_DIR = Path(__file__).parent

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.bottom": False,
    "axes.spines.left": False,
    "figure.dpi": 150,
})

# Brand palette
WHITE  = "#f1f5f9"
RED    = "#ea580c"      # burning
GREEN  = "#10b981"      # protected
BLACK  = "#1e293b"
SLATE  = "#475569"
AMBER  = "#fbbf24"
BLUE   = "#3b82f6"
PURPLE = "#8b5cf6"
TEAL   = "#14b8a6"


def save(fig, name: str) -> None:
    out = FIG_DIR / name
    fig.savefig(out.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(out.with_suffix(".png"), bbox_inches="tight")
    plt.close(fig)
    print("wrote", out)


# --------------------------------------------------------------------------
# Figure: Firefighter mechanics — protect then spread (4 turns)
# --------------------------------------------------------------------------
def fig_firefighter_mechanics() -> None:
    # A small planar graph: 13 vertices laid out by hand
    pos = {
        0: (0, 1.5),    1: (1, 2.4),  2: (1.2, 0.7), 3: (2, 1.6),
        4: (2.4, 0.0),  5: (3, 2.4),  6: (3.4, 1.0), 7: (4.4, 1.9),
        8: (4.6, 0.4),  9: (5.5, 1.3),10: (5.2, 2.7),11: (6.4, 0.6),
        12:(6.6, 2.0),
    }
    G = nx.Graph()
    G.add_nodes_from(pos)
    edges = [
        (0,1),(0,2),(1,2),(1,3),(2,3),(2,4),(3,4),(3,5),(3,6),(4,6),
        (5,6),(5,7),(6,7),(6,8),(7,8),(7,9),(7,10),(8,9),(8,11),(9,10),
        (9,11),(9,12),(10,12),(11,12),
    ]
    G.add_edges_from(edges)

    # k = 2; greedy: pick highest-degree white in front
    # Hand-script the trace for the figure
    # Turn 0 initial: fire at vertex 3 (center hub)
    states = []
    s0 = {v: "W" for v in G.nodes()}
    s0[3] = "R"
    states.append(("Turn 0 — fire detected", s0, set(), set()))

    # Turn 1 — protect 2 and 5 (highest-degree neighbours)
    s1 = dict(s0)
    s1[2] = "G"; s1[5] = "G"
    # spread: 3 -> white neighbours (1, 4, 6)
    s1[1] = "R"; s1[4] = "R"; s1[6] = "R"
    states.append(("Turn 1 — protect 2 and 5, then spread",
                   s1, {2, 5}, {3}))

    # Turn 2 — protect 7 and 8 (the next bridges into the right cluster)
    s2 = dict(s1)
    s2[7] = "G"; s2[8] = "G"
    # spread from 1,4,6 to white neighbours (none of {7,8} since protected)
    # 1's neighbours: 0,2,3 → 0 is white
    s2[0] = "R"
    # 4's neighbours: 2,3,6 → none white
    # 6's neighbours: 3,4,5,7,8 → none white
    states.append(("Turn 2 — protect 7 and 8, then spread",
                   s2, {7, 8}, {1, 4, 6}))

    # Turn 3 — fire is contained; nothing left to spread to from {0,1,3,4,6}
    s3 = dict(s2)
    states.append(("Turn 3 — fire contained (no white neighbours of front)",
                   s3, set(), {0}))

    fig, axes = plt.subplots(1, 4, figsize=(14, 3.6))

    for ax, (title, state, protected_this_turn, spread_from) in zip(axes, states):
        ax.set_xlim(-0.6, 7.2)
        ax.set_ylim(-0.6, 3.2)
        ax.set_aspect("equal")
        ax.set_title(title, fontsize=10, color=BLACK)
        ax.set_xticks([]); ax.set_yticks([])

        # Edges
        for u, v in G.edges():
            ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]],
                    color="#cbd5e1", linewidth=1.2, zorder=1)

        # Nodes
        for v in G.nodes():
            st = state[v]
            if st == "W":
                fc, ec = WHITE, BLACK
            elif st == "R":
                fc, ec = RED, "#9a3412"
            else:
                fc, ec = GREEN, "#047857"
            radius = 0.22
            circ = Circle(pos[v], radius, facecolor=fc, edgecolor=ec,
                          linewidth=1.4, zorder=3)
            ax.add_patch(circ)
            # Ring for just-protected
            if v in protected_this_turn:
                ring = Circle(pos[v], radius + 0.10, facecolor="none",
                              edgecolor=GREEN, linewidth=1.6, linestyle="--",
                              zorder=2)
                ax.add_patch(ring)
            ax.text(pos[v][0], pos[v][1], str(v), ha="center", va="center",
                    fontsize=8, color=BLACK, zorder=4)

    # Legend at bottom
    legend_items = [
        Circle((0, 0), 0.1, facecolor=WHITE, edgecolor=BLACK),
        Circle((0, 0), 0.1, facecolor=RED, edgecolor="#9a3412"),
        Circle((0, 0), 0.1, facecolor=GREEN, edgecolor="#047857"),
    ]
    fig.legend(legend_items,
               ["White — safe / can still burn",
                "Red — burning",
                "Green — protected (immune)"],
               loc="lower center", ncol=3, frameon=False, fontsize=9,
               bbox_to_anchor=(0.5, -0.02))
    fig.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.16,
                        wspace=0.05)
    save(fig, "fig_mechanics")


# --------------------------------------------------------------------------
# Figure: Map-to-graph pipeline (four stages)
# --------------------------------------------------------------------------
def fig_pipeline() -> None:
    fig, axes = plt.subplots(1, 4, figsize=(13.5, 3.4))

    # ---- Stage 1: bounding box on a stylised land outline
    ax = axes[0]
    ax.set_xlim(0, 5); ax.set_ylim(0, 5); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("Stage 1 — bbox", fontsize=10)
    # stylised land: irregular polygon
    coast = np.array([(0.3, 0.5), (1.5, 0.3), (3.2, 0.6), (4.6, 0.4),
                      (4.7, 2.0), (4.2, 3.5), (3.0, 4.3), (1.7, 4.6),
                      (0.5, 4.2), (0.2, 2.4)])
    ax.fill(coast[:, 0], coast[:, 1], color="#d1fae5", edgecolor="#10b981",
            linewidth=1.0)
    # water around
    ax.fill_between([0, 5], 0, 5, color="#dbeafe", alpha=0.4, zorder=0)
    # bbox
    bb = Rectangle((1.0, 1.2), 2.8, 2.6, facecolor="none",
                   edgecolor=RED, linewidth=2.0, linestyle="--")
    ax.add_patch(bb)
    ax.text(2.4, 4.05, "Köyceğiz–Marmaris", ha="center", fontsize=8.5,
            color=RED)
    ax.text(2.4, 0.3, "user draws bbox on Leaflet", ha="center",
            fontsize=8, color=SLATE, style="italic")

    # ---- Stage 2: raster forest mask (grid)
    ax = axes[1]
    ax.set_xlim(0, 5); ax.set_ylim(0, 5); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("Stage 2 — ESA WorldCover mask", fontsize=10)
    rng = np.random.default_rng(7)
    grid_n = 18
    cell = 5.0 / grid_n
    for i in range(grid_n):
        for j in range(grid_n):
            x, y = i * cell, j * cell
            r = (i - grid_n / 2) ** 2 + (j - grid_n / 2) ** 2
            forest_p = max(0.0, 0.85 - r / 220) + 0.05 * rng.normal()
            forest_p = float(np.clip(forest_p, 0, 1))
            if forest_p > 0.55:
                color = "#16a34a"
            elif forest_p > 0.35:
                color = "#86efac"
            elif forest_p > 0.20:
                color = "#fde68a"
            else:
                color = "#bfdbfe"
            ax.add_patch(Rectangle((x, y), cell, cell, facecolor=color,
                                   edgecolor="white", linewidth=0.25))
    legend_h = [
        mpatches.Patch(color="#16a34a", label="forest"),
        mpatches.Patch(color="#86efac", label="shrubland"),
        mpatches.Patch(color="#fde68a", label="bare / crop"),
        mpatches.Patch(color="#bfdbfe", label="water / built"),
    ]
    ax.legend(handles=legend_h, loc="lower center",
              bbox_to_anchor=(0.5, -0.18), ncol=4, frameon=False,
              fontsize=7.5, handlelength=1.0, columnspacing=0.8)

    # ---- Stage 3: vertex placement (k-means centroids)
    ax = axes[2]
    ax.set_xlim(0, 5); ax.set_ylim(0, 5); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("Stage 3 — Lloyd's k-means centroids", fontsize=10)
    rng = np.random.default_rng(7)
    # background dense cluster
    for i in range(grid_n):
        for j in range(grid_n):
            x, y = i * cell, j * cell
            r = (i - grid_n / 2) ** 2 + (j - grid_n / 2) ** 2
            forest_p = max(0.0, 0.85 - r / 220) + 0.05 * rng.normal()
            if forest_p > 0.45:
                ax.add_patch(Rectangle((x, y), cell, cell,
                                       facecolor="#dcfce7",
                                       edgecolor="white", linewidth=0.2))
    # vertices over forest
    pts = []
    while len(pts) < 22:
        x = rng.uniform(0.5, 4.5); y = rng.uniform(0.5, 4.5)
        r = ((x - 2.5) ** 2 + (y - 2.5) ** 2) ** 0.5
        if r < 2.0 and all(((x - px) ** 2 + (y - py) ** 2) ** 0.5 > 0.55
                            for px, py in pts):
            pts.append((x, y))
    pts = np.array(pts)
    ax.scatter(pts[:, 0], pts[:, 1], s=70, color=BLACK, edgecolor="white",
               linewidth=1.2, zorder=3)
    ax.text(2.5, 0.3, "vertex = density-weighted centroid",
            ha="center", fontsize=8, color=SLATE, style="italic")

    # ---- Stage 4: Delaunay + filtered edges
    ax = axes[3]
    ax.set_xlim(0, 5); ax.set_ylim(0, 5); ax.set_aspect("equal")
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_title("Stage 4 — Delaunay + barrier filter", fontsize=10)

    from scipy.spatial import Delaunay
    tri = Delaunay(pts)
    edges_full = set()
    for s in tri.simplices:
        for a, b in [(s[0], s[1]), (s[1], s[2]), (s[0], s[2])]:
            edges_full.add(tuple(sorted((a, b))))
    # Simulate "blocked by barrier": drop ~30% of edges deterministically
    rng2 = np.random.default_rng(11)
    blocked = set()
    for e in edges_full:
        if rng2.random() < 0.32:
            blocked.add(e)

    # river polygon
    river = np.array([(0.0, 1.8), (5.0, 1.6), (5.0, 1.95), (0.0, 2.15)])
    ax.fill(river[:, 0], river[:, 1], color="#93c5fd",
            edgecolor="#3b82f6", linewidth=0.8, zorder=0)
    # settlement
    ax.add_patch(Rectangle((3.5, 3.2), 0.6, 0.6, facecolor="#fecaca",
                           edgecolor="#dc2626", linewidth=0.8, zorder=0))

    for a, b in edges_full:
        x0, y0 = pts[a]; x1, y1 = pts[b]
        if (a, b) in blocked:
            ax.plot([x0, x1], [y0, y1], color="#cbd5e1", linewidth=0.6,
                    linestyle=":", zorder=1)
        else:
            ax.plot([x0, x1], [y0, y1], color=BLACK, linewidth=1.0,
                    zorder=2)
    ax.scatter(pts[:, 0], pts[:, 1], s=70, color=BLACK, edgecolor="white",
               linewidth=1.2, zorder=3)
    legend_h = [
        mpatches.Patch(color=BLACK, label="active edge"),
        mpatches.Patch(facecolor="#cbd5e1", label="blocked"),
        mpatches.Patch(color="#93c5fd", label="river"),
        mpatches.Patch(color="#fecaca", label="settlement"),
    ]
    ax.legend(handles=legend_h, loc="lower center",
              bbox_to_anchor=(0.5, -0.18), ncol=4, frameon=False,
              fontsize=7.5, handlelength=1.0, columnspacing=0.8)

    # Arrows between stages
    fig.subplots_adjust(left=0.01, right=0.99, top=0.92, bottom=0.18,
                        wspace=0.10)
    for i in range(3):
        # convert axes coords to figure coords using axes' bbox
        ax_l = axes[i]
        ax_r = axes[i + 1]
        bb_l = ax_l.get_position()
        bb_r = ax_r.get_position()
        x0 = bb_l.x1 - 0.005
        x1 = bb_r.x0 + 0.005
        y  = (bb_l.y0 + bb_l.y1) / 2
        arrow = FancyArrowPatch((x0, y), (x1, y), transform=fig.transFigure,
                                arrowstyle="-|>", mutation_scale=14,
                                color=SLATE, linewidth=1.4)
        fig.patches.append(arrow)
    save(fig, "fig_pipeline")


# --------------------------------------------------------------------------
# Figure: Strategy philosophies (three side-by-side small graphs)
# --------------------------------------------------------------------------
def fig_philosophies() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(13.0, 3.8))
    pos = {
        0:(0.4, 1.5), 1:(1.2, 2.3), 2:(1.0, 0.6), 3:(2.0, 1.5),
        4:(2.7, 2.4), 5:(2.7, 0.5), 6:(3.6, 1.5), 7:(4.4, 2.3),
        8:(4.2, 0.5), 9:(5.0, 1.5),
    }
    edges = [(0,1),(0,2),(1,2),(1,3),(2,3),(3,4),(3,5),(3,6),(4,6),(5,6),
             (6,7),(6,8),(7,9),(8,9),(7,8)]
    G = nx.Graph()
    G.add_nodes_from(pos)
    G.add_edges_from(edges)

    # Three views: same fire (red set), three different strategies'
    # protect picks (green dashed rings).
    red = {0}
    picks = {
        "Local greedy\n(max neighbours)": ({1, 2},
            "Pick the white vertex that has the most white neighbours."),
        "Structural\n(min damage cut)":  ({3, 6},
            "Find a vertex cut that separates red from a dense saved set."),
        "Lookahead\n(simulate two turns)":({1, 3},
            "Try every pair, simulate, pick the lowest burned count."),
    }
    accent = [GREEN, BLUE, PURPLE]

    for ax, ((title, (sel, blurb)), col) in zip(axes,
                                               zip(picks.items(), accent)):
        ax.set_xlim(-0.4, 5.6); ax.set_ylim(-0.6, 3.4)
        ax.set_aspect("equal")
        ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(title, fontsize=10, color=BLACK)

        for u, v in G.edges():
            ax.plot([pos[u][0], pos[v][0]], [pos[u][1], pos[v][1]],
                    color="#cbd5e1", linewidth=1.2, zorder=1)

        for v in G.nodes():
            if v in red:
                fc, ec = RED, "#9a3412"
            else:
                fc, ec = WHITE, BLACK
            ax.add_patch(Circle(pos[v], 0.22, facecolor=fc, edgecolor=ec,
                                linewidth=1.4, zorder=3))
            ax.text(pos[v][0], pos[v][1], str(v), ha="center", va="center",
                    fontsize=8, color=BLACK, zorder=4)
            if v in sel:
                ax.add_patch(Circle(pos[v], 0.34, facecolor="none",
                                    edgecolor=col, linewidth=2.0,
                                    linestyle="--", zorder=2))

        ax.text(2.6, -0.25, blurb, ha="center", fontsize=8.5, color=SLATE,
                style="italic")

    save(fig, "fig_philosophies")


if __name__ == "__main__":
    fig_firefighter_mechanics()
    fig_pipeline()
    fig_philosophies()
    print("done.")
