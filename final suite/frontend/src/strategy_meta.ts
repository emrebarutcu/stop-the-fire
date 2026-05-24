// Per-strategy metadata for UI display: philosophy class (from ALGORITHMS.md §13)
// and a one-line description shown in tooltips.

export type Philosophy = "greedy" | "structural" | "lookahead" | "hybrid" | "baseline";

export interface StrategyMeta {
  philosophy: Philosophy;
  short: string;
}

export const STRATEGY_META: Record<string, StrategyMeta> = {
  max_degree: {
    philosophy: "greedy",
    short: "Pick the vertex with most neighbours first. Coarse but fast (§1).",
  },
  max_white_neighbors: {
    philosophy: "greedy",
    short: "Protect the vertex with the most WHITE neighbours. Strongest greedy variant (§2).",
  },
  min_cut_edge_front: {
    philosophy: "structural",
    short: "Edge-based min-cut. Mismatched with vertex protection (§3).",
  },
  min_damage_cut: {
    philosophy: "structural",
    short: "Reformulated min-cut: maximise saved/cost ratio (§4).",
  },
  one_step_lookahead: {
    philosophy: "lookahead",
    short: "Pair-aware 2-turn lookahead. Empirical #1 (§5).",
  },
  hybrid_density_aware: {
    philosophy: "hybrid",
    short: "Switches between greedy and cut depending on front density (§6).",
  },
  betweenness_front: {
    philosophy: "structural",
    short: "Global flow heuristic — protect bridge vertices (§7).",
  },
  random: {
    philosophy: "baseline",
    short: "Sanity baseline. Picks at random (§8).",
  },
};

export const PHILOSOPHY_LABEL: Record<Philosophy, string> = {
  greedy: "Greedy",
  structural: "Structural",
  lookahead: "Lookahead",
  hybrid: "Hybrid",
  baseline: "Baseline",
};

export function getMeta(name: string): StrategyMeta {
  return STRATEGY_META[name] ?? { philosophy: "greedy", short: name };
}
