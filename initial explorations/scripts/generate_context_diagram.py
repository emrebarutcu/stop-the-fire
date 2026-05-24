#!/usr/bin/env python3
"""Generate a Context Diagram (Level 0 DFD) for the Stop-The-Fire project."""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import matplotlib.patheffects as pe
import numpy as np
from pathlib import Path

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "docs" / "context_diagram.png"

fig, ax = plt.subplots(figsize=(16, 11))
fig.set_facecolor("#0f1923")
ax.set_facecolor("#0f1923")
ax.set_xlim(0, 16)
ax.set_ylim(0, 11)
ax.axis("off")

# ── Title ──────────────────────────────────────────────────────────
ax.text(
    8, 10.4, "Stop-The-Fire Simulation System",
    ha="center", va="center", fontsize=22, fontweight="bold",
    color="#e8e6e3",
    fontfamily="sans-serif",
    path_effects=[pe.withStroke(linewidth=3, foreground="#1a2733")],
)
ax.text(
    8, 9.95, "Context Diagram (Level 0 DFD)",
    ha="center", va="center", fontsize=13, color="#7eb8da",
    fontfamily="sans-serif", fontstyle="italic",
)

# ── Helper functions ───────────────────────────────────────────────

def draw_external_entity(ax, cx, cy, w, h, label, sublabel="", color="#2a4a6b"):
    """Draw a rectangle representing an external entity."""
    rect = FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle="round,pad=0.12",
        facecolor=color, edgecolor="#5ba3d9",
        linewidth=2.0, alpha=0.92, zorder=3,
    )
    ax.add_patch(rect)
    ax.text(cx, cy + (0.12 if sublabel else 0), label,
            ha="center", va="center", fontsize=12, fontweight="bold",
            color="#e8e6e3", zorder=4, fontfamily="sans-serif")
    if sublabel:
        ax.text(cx, cy - 0.22, sublabel,
                ha="center", va="center", fontsize=8.5,
                color="#a0c4e0", zorder=4, fontfamily="sans-serif")


def draw_process(ax, cx, cy, r, label, sublabel=""):
    """Draw a circle representing the central process."""
    # Outer glow
    circle_glow = plt.Circle((cx, cy), r + 0.08, color="#ff6b35", alpha=0.15, zorder=1)
    ax.add_patch(circle_glow)
    circle_glow2 = plt.Circle((cx, cy), r + 0.04, color="#ff6b35", alpha=0.25, zorder=1)
    ax.add_patch(circle_glow2)
    # Main circle
    circle = plt.Circle((cx, cy), r, facecolor="#1c3a52", edgecolor="#ff6b35",
                         linewidth=3.0, zorder=2)
    ax.add_patch(circle)
    ax.text(cx, cy + 0.25, label,
            ha="center", va="center", fontsize=14, fontweight="bold",
            color="#ff9f68", zorder=4, fontfamily="sans-serif")
    if sublabel:
        ax.text(cx, cy - 0.20, sublabel,
                ha="center", va="center", fontsize=9,
                color="#c0c0c0", zorder=4, fontfamily="sans-serif")


def draw_arrow(ax, x1, y1, x2, y2, label, label_side="above", color="#5ba3d9",
               connectionstyle="arc3,rad=0.0", label_offset=(0, 0)):
    """Draw a labeled arrow between two points."""
    arrow = FancyArrowPatch(
        (x1, y1), (x2, y2),
        arrowstyle="-|>",
        mutation_scale=18,
        color=color, linewidth=1.8,
        connectionstyle=connectionstyle,
        zorder=2,
    )
    ax.add_patch(arrow)
    # Label position
    mx = (x1 + x2) / 2 + label_offset[0]
    my = (y1 + y2) / 2 + label_offset[1]
    offset = 0.22 if label_side == "above" else -0.22
    # Determine rotation
    angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
    if abs(angle) > 90:
        angle += 180

    bbox_props = dict(boxstyle="round,pad=0.15", facecolor="#142a3c",
                      edgecolor="#3a6a8a", alpha=0.9)

    ax.text(mx, my + offset, label,
            ha="center", va="center", fontsize=8.5,
            color="#c8e0f0", zorder=5, fontfamily="sans-serif",
            bbox=bbox_props,
            rotation=0)


# ── Central Process ────────────────────────────────────────────────
draw_process(ax, 8, 5.5, 1.5,
             "Stop-The-Fire",
             "Simulation Engine")

# ── External Entities ──────────────────────────────────────────────

# 1. Researcher / User (top-left)
draw_external_entity(ax, 2.5, 9.0, 3.0, 1.2,
                     "Araştırmacı", "(Kullanıcı)", color="#2a4a6b")

# 2. Graph Generator (top-right)
draw_external_entity(ax, 13.5, 9.0, 3.0, 1.2,
                     "Graph Üretici", "(NetworkX)", color="#2a5a4b")

# 3. Strategy Algorithms (left)
draw_external_entity(ax, 1.5, 5.5, 2.6, 1.4,
                     "Strateji", "Algoritmaları", color="#4a2a6b")

# 4. Visualization Module (right)
draw_external_entity(ax, 14.5, 5.5, 2.6, 1.2,
                     "Görselleştirme", "(Matplotlib)", color="#6b4a2a")

# 5. Calibration Module (bottom-left)
draw_external_entity(ax, 2.5, 2.0, 3.0, 1.2,
                     "Kalibrasyon", "Modülü", color="#2a4a4a")

# 6. Output / Results (bottom-right)
draw_external_entity(ax, 13.5, 2.0, 3.0, 1.2,
                     "Çıktı Dosyaları", "(PNG, CSV)", color="#5a3a2a")


# ── Data Flows (Arrows) ───────────────────────────────────────────

# Researcher → Process
draw_arrow(ax, 3.8, 8.5, 6.7, 6.6,
           "Parametre Girişi\n(n, density, seed, protect_per_turn)",
           label_side="above", color="#5ba3d9")

# Process → Researcher
draw_arrow(ax, 6.7, 6.2, 3.5, 8.2,
           "Sonuçlar & Metrikler\n(K, Y, B, K/Y, K/B)",
           label_side="below", color="#5ba3d9",
           label_offset=(-0.3, -0.3))

# Graph Generator → Process
draw_arrow(ax, 12.2, 8.5, 9.3, 6.6,
           "Planar/RGG Graf\n(vertex, edge, pos)",
           label_side="above", color="#4ac9a0")

# Process → Graph Generator
draw_arrow(ax, 9.5, 6.8, 12.5, 9.0,
           "Graf Parametreleri\n(n, density, seed)",
           label_side="above", color="#4ac9a0",
           label_offset=(0.3, 0.3))

# Strategy → Process
draw_arrow(ax, 2.8, 5.0, 6.5, 5.2,
           "Koruma Kararları\n(vertex listesi)",
           label_side="below", color="#b07ad9",
           label_offset=(0, -0.15))

# Process → Strategy
draw_arrow(ax, 6.5, 5.8, 2.8, 6.0,
           "Graf Durumu\n(vertex_states, graph)",
           label_side="above", color="#b07ad9",
           label_offset=(0, 0.15))

# Process → Visualization
draw_arrow(ax, 9.5, 5.5, 13.2, 5.5,
           "GameResult\n(states, metrics)",
           label_side="above", color="#d9a04a")

# Visualization → Output
draw_arrow(ax, 14.5, 4.9, 14.0, 2.6,
           "PNG Görseller",
           label_side="above", color="#d97a4a",
           label_offset=(0.5, 0))

# Calibration → Process
draw_arrow(ax, 3.7, 2.5, 6.8, 4.2,
           "Deneysel Konfigürasyon\n(vertex_counts, n_runs)",
           label_side="below", color="#4ac9c9",
           label_offset=(0, -0.1))

# Process → Calibration
draw_arrow(ax, 7.0, 4.0, 3.5, 2.0,
           "Toplu Sonuçlar\n(GameResult listesi)",
           label_side="above", color="#4ac9c9",
           label_offset=(-0.2, 0.2))

# Calibration → Output
draw_arrow(ax, 4.0, 1.5, 12.0, 1.7,
           "CSV Veri Dosyaları",
           label_side="below", color="#7a9a8a",
           label_offset=(0, -0.15))


# ── Legend ─────────────────────────────────────────────────────────
legend_y = 0.5
legend_items = [
    ("⬤", "#ff6b35", "Merkezi Süreç (Process)"),
    ("■", "#5ba3d9", "Dış Varlık (External Entity)"),
    ("→", "#5ba3d9", "Veri Akışı (Data Flow)"),
]
x_start = 4.5
for i, (icon, color, desc) in enumerate(legend_items):
    ax.text(x_start + i * 3.5, legend_y, f"{icon} {desc}",
            ha="center", va="center", fontsize=9,
            color=color, fontfamily="sans-serif",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#142a3c",
                      edgecolor="#3a6a8a", alpha=0.7))


# ── Save ───────────────────────────────────────────────────────────
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUTPUT_PATH, dpi=200, bbox_inches="tight", facecolor="#0f1923")
plt.close(fig)
print(f"Context diagram saved to: {OUTPUT_PATH}")
