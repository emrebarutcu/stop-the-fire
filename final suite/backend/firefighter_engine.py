"""
IE 492 — Stop the Fire!
Simulation engine + strategies for the Firefighter Problem on planar graphs.

Vertex states: WHITE (safe) / RED (burning) / GREEN (protected).

Turn order:
    1. strategy.select(G, state) returns priority-ranked WHITE candidates
    2. engine protects top-k of those that are still WHITE
    3. fire spreads to every WHITE neighbor of any RED vertex
    4. stop when fire front F is empty (no WHITE vertex adjacent to RED)

Objective: minimize K = |{v : state(v) = RED}| at termination.
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Tuple

import networkx as nx
import numpy as np
from scipy.spatial import Delaunay

WHITE, RED, GREEN = 0, 1, 2
STATE_NAMES = {WHITE: "WHITE", RED: "RED", GREEN: "GREEN"}


# ---------------------------------------------------------------------------
# Graph generators
# ---------------------------------------------------------------------------

def _delaunay_graph_from_points(pts: np.ndarray) -> nx.Graph:
    G = nx.Graph()
    for i, (x, y) in enumerate(pts):
        G.add_node(i, pos=(float(x), float(y)))
    if len(pts) < 3:
        for i in range(len(pts) - 1):
            G.add_edge(i, i + 1)
        return G
    tri = Delaunay(pts)
    for simplex in tri.simplices:
        a, b, c = simplex
        G.add_edge(int(a), int(b))
        G.add_edge(int(b), int(c))
        G.add_edge(int(a), int(c))
    return G


def make_delaunay_planar(n: int, seed: int = 0) -> nx.Graph:
    rng = np.random.default_rng(seed)
    pts = rng.uniform(0.0, 1.0, size=(n, 2))
    G = _delaunay_graph_from_points(pts)
    G.graph["topology"] = "delaunay"
    return G


def make_long_thin_delaunay(n: int, seed: int = 0, aspect: float = 6.0) -> nx.Graph:
    """Long-thin form (per 14 Apr meeting: 'ince uzun hatlar')."""
    rng = np.random.default_rng(seed)
    pts = rng.uniform(0.0, 1.0, size=(n, 2))
    pts[:, 0] *= aspect  # stretch horizontally
    G = _delaunay_graph_from_points(pts)
    G.graph["topology"] = "long_thin"
    return G


def make_hex_grid(rows: int, cols: int) -> nx.Graph:
    """Hexagonal lattice subset (≈ rows*cols vertices)."""
    G = nx.hexagonal_lattice_graph(rows, cols)
    G = nx.convert_node_labels_to_integers(G, label_attribute="hex_coord")
    # add planar positions
    for v, data in G.nodes(data=True):
        coord = data.get("hex_coord", (0, 0))
        r, c = coord
        x = c + 0.5 * (r % 2)
        y = r * math.sqrt(3) / 2
        data["pos"] = (float(x), float(y))
    G.graph["topology"] = "hex"
    return G


def make_delaunay_with_obstacles(
    n: int, seed: int = 0, obstacle_frac: float = 0.18
) -> nx.Graph:
    """Delaunay with random edge removal to mimic mountains/lakes."""
    G = make_delaunay_planar(n, seed=seed)
    rng = np.random.default_rng(seed + 1001)
    edges = list(G.edges())
    rng.shuffle(edges)
    n_drop = int(len(edges) * obstacle_frac)
    dropped = 0
    for u, v in edges:
        if dropped >= n_drop:
            break
        # protect connectivity: only drop if removing keeps graph connected
        G.remove_edge(u, v)
        if nx.is_connected(G):
            dropped += 1
        else:
            G.add_edge(u, v)
    G.graph["topology"] = "obstacles"
    return G


GRAPH_FACTORIES: Dict[str, Callable[..., nx.Graph]] = {
    "delaunay": lambda n, seed: make_delaunay_planar(n, seed=seed),
    "long_thin": lambda n, seed: make_long_thin_delaunay(n, seed=seed),
    "hex": lambda n, seed: make_hex_grid(
        rows=max(3, int(round(math.sqrt(n / 2)))),
        cols=max(3, int(round(math.sqrt(n / 2)))),
    ),
    "obstacles": lambda n, seed: make_delaunay_with_obstacles(n, seed=seed),
}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

@dataclass
class SimResult:
    burned: int
    saved: int
    protected: int
    n: int
    turns: int
    runtime_s: float
    history: List[Tuple[int, int, int]] = field(default_factory=list)  # (white,red,green)


def fire_front(G: nx.Graph, state: Dict[int, int]) -> List[int]:
    front = []
    for v in G.nodes():
        if state[v] != WHITE:
            continue
        for u in G.neighbors(v):
            if state[u] == RED:
                front.append(v)
                break
    return front


def simulate(
    G: nx.Graph,
    state: Dict[int, int],
    strategy: "Strategy",
    protect_per_turn: int = 2,
    max_turns: int = 1000,
) -> SimResult:
    state = dict(state)  # copy
    n = G.number_of_nodes()
    history = []
    t0 = time.perf_counter()
    turns = 0
    while True:
        front = fire_front(G, state)
        if not front:
            break
        candidates = strategy.select(G, state)
        # filter: only WHITE candidates, dedup, preserve order
        seen = set()
        chosen: List[int] = []
        for v in candidates:
            if v in seen:
                continue
            seen.add(v)
            if state.get(v, RED) == WHITE:
                chosen.append(v)
                if len(chosen) >= protect_per_turn:
                    break
        for v in chosen:
            state[v] = GREEN
        # spread
        new_red = []
        for v in G.nodes():
            if state[v] != WHITE:
                continue
            for u in G.neighbors(v):
                if state[u] == RED:
                    new_red.append(v)
                    break
        for v in new_red:
            state[v] = RED
        turns += 1
        c = (
            sum(1 for s in state.values() if s == WHITE),
            sum(1 for s in state.values() if s == RED),
            sum(1 for s in state.values() if s == GREEN),
        )
        history.append(c)
        if turns >= max_turns:
            break
    runtime = time.perf_counter() - t0
    burned = sum(1 for s in state.values() if s == RED)
    protected = sum(1 for s in state.values() if s == GREEN)
    saved = sum(1 for s in state.values() if s == WHITE)
    return SimResult(
        burned=burned,
        saved=saved + protected,
        protected=protected,
        n=n,
        turns=turns,
        runtime_s=runtime,
        history=history,
    )


def init_state(G: nx.Graph, fire_origin: int) -> Dict[int, int]:
    state = {v: WHITE for v in G.nodes()}
    state[fire_origin] = RED
    return state


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

class Strategy:
    name: str = "base"

    def select(self, G: nx.Graph, state: Dict[int, int]) -> List[int]:
        raise NotImplementedError


def _front_set(G, state):
    return set(fire_front(G, state))


def _white_subgraph(G, state):
    return G.subgraph([v for v in G.nodes() if state[v] == WHITE]).copy()


# 1. max_degree -------------------------------------------------------------

class MaxDegree(Strategy):
    name = "max_degree"

    def select(self, G, state):
        F = fire_front(G, state)
        F.sort(key=lambda v: (-G.degree(v), v))
        return F


# 2. max_white_neighbors ----------------------------------------------------

class MaxWhiteNeighbors(Strategy):
    name = "max_white_neighbors"

    def select(self, G, state):
        F = fire_front(G, state)

        def white_n(v):
            return sum(1 for u in G.neighbors(v) if state[u] == WHITE)

        F.sort(key=lambda v: (-white_n(v), -G.degree(v), v))
        return F


# 3. min_cut_edge_front -----------------------------------------------------

class MinCutEdgeFront(Strategy):
    name = "min_cut_edge_front"

    def select(self, G, state):
        F = fire_front(G, state)
        R = [v for v in G.nodes() if state[v] == RED]
        W = [v for v in G.nodes() if state[v] == WHITE]
        if not F or not R or not W:
            return F
        H = nx.Graph()
        H.add_nodes_from(G.nodes())
        H.add_edges_from(G.edges())
        s, t = "__s__", "__t__"
        H.add_node(s); H.add_node(t)
        for r in R:
            H.add_edge(s, r)
        for w in W:
            H.add_edge(w, t)
        try:
            cut_value, partition = nx.minimum_cut(H, s, t, capacity=None)
        except Exception:
            try:
                cut_edges = nx.minimum_edge_cut(H, s, t)
            except Exception:
                return F
            score = {v: 0 for v in F}
            for a, b in cut_edges:
                for end in (a, b):
                    if end in score:
                        score[end] += 1
            preferred = sorted(F, key=lambda v: (-score[v], -G.degree(v), v))
            return preferred
        # use partition to get cut edges
        reachable, non_reachable = partition
        cut_edges = [
            (u, v) for u in reachable for v in G.neighbors(u) if v in non_reachable
        ]
        score = {v: 0 for v in F}
        for a, b in cut_edges:
            for end in (a, b):
                if end in score:
                    score[end] += 1
        preferred = sorted(F, key=lambda v: (-score[v], -G.degree(v), v))
        return preferred


# 4. min_damage_cut (reformulated min-cut, per 14 Apr meeting) -------------

class MinDamageCut(Strategy):
    """Reformulated min-cut around min-damage (per 14 Apr meeting).

    For each large WHITE component (or BFS shell at depth d), compute min vertex
    cut RED -> shell, score it by saved_size / cut_size, pick the top-scoring
    cut, prefer its WHITE cut vertices on the front.
    """
    name = "min_damage_cut"

    def select(self, G, state):
        F = fire_front(G, state)
        R = [v for v in G.nodes() if state[v] == RED]
        W = [v for v in G.nodes() if state[v] == WHITE]
        if not F or not R or not W:
            return F

        # candidate target shells: BFS from RED at increasing depth
        try:
            dist = {}
            for r in R:
                d = nx.single_source_shortest_path_length(G, r)
                for v, dv in d.items():
                    if state.get(v, RED) == WHITE:
                        dist[v] = min(dist.get(v, math.inf), dv)
        except Exception:
            return F
        if not dist:
            return F

        max_d = max(dist.values())
        best_score = -1.0
        best_cut: List[int] = []
        H = G.copy()
        s, t = "__s__", "__t__"
        H.add_node(s); H.add_node(t)
        for r in R:
            H.add_edge(s, r)

        # try shells at various depths >= 2
        depths = [d for d in [2, 3, 4, max(2, int(max_d))] if d <= max_d]
        depths = sorted(set(depths))
        if not depths:
            depths = [max_d]

        for d_thresh in depths:
            shell = [v for v, dv in dist.items() if dv >= d_thresh]
            if not shell:
                continue
            # link shell to sink
            H_copy = H.copy()
            for z in shell:
                H_copy.add_edge(z, t)
            try:
                cut = nx.minimum_node_cut(H_copy, s, t)
            except Exception:
                continue
            cut_white = [v for v in cut if v in G and state.get(v, RED) == WHITE]
            if not cut_white:
                continue
            saved_size = len(shell)
            cut_size = max(1, len(cut_white))
            score = saved_size / cut_size
            if score > best_score:
                best_score = score
                best_cut = cut_white

        preferred_front = [v for v in best_cut if v in set(F)]
        # tie-break: degree
        preferred_front.sort(key=lambda v: (-G.degree(v), v))
        rest = [v for v in F if v not in preferred_front]

        def white_n(v):
            return sum(1 for u in G.neighbors(v) if state[u] == WHITE)

        rest.sort(key=lambda v: (-white_n(v), -G.degree(v), v))
        return preferred_front + rest


# 6. betweenness_front (NEW) ------------------------------------------------

class BetweennessFront(Strategy):
    name = "betweenness_front"

    def select(self, G, state):
        F = fire_front(G, state)
        if not F:
            return F
        Hw = _white_subgraph(G, state)
        try:
            bc = nx.betweenness_centrality(Hw, normalized=True)
        except Exception:
            bc = {v: 0.0 for v in F}
        F.sort(key=lambda v: (-bc.get(v, 0.0), -G.degree(v), v))
        return F


# 7. one_step_lookahead (pair-aware 2-turn lookahead) ----------------------

class OneStepLookahead(Strategy):
    """Pair-aware 2-turn lookahead.

    For top-`top_k` candidate pairs (v1, v2) on the front, simulate:
        protect(v1, v2) -> spread -> greedy(2 best) -> spread
    Pick the v1 that participates in the lowest-burned pair.

    This matches the engine's actual k=2 protection behavior, addressing the
    weakness that single-vertex lookahead drifted close to greedy.
    """
    name = "one_step_lookahead"

    def __init__(self, top_k: int = 6, k_protect: int = 2):
        self.top_k = top_k
        self.k_protect = k_protect

    @staticmethod
    def _greedy_top(G, state, k):
        F = fire_front(G, state)
        if not F:
            return []

        def score(v):
            return (
                sum(1 for u in G.neighbors(v) if state[u] == WHITE),
                G.degree(v),
            )

        F.sort(key=lambda v: (-score(v)[0], -score(v)[1], v))
        return F[:k]

    @staticmethod
    def _spread_one(state, G):
        new_red = []
        for u in G.nodes():
            if state[u] != WHITE:
                continue
            for w in G.neighbors(u):
                if state[w] == RED:
                    new_red.append(u)
                    break
        for u in new_red:
            state[u] = RED

    def select(self, G, state):
        F = fire_front(G, state)
        if not F:
            return F

        # rank front by greedy-white as candidate set
        cand = sorted(F, key=lambda v: (
            -sum(1 for u in G.neighbors(v) if state[u] == WHITE),
            -G.degree(v),
            v,
        ))[: self.top_k]

        if len(cand) <= self.k_protect:
            return cand + [v for v in F if v not in cand]

        best_pair = None
        best_burned = math.inf
        # try all pairs from candidates
        for i in range(len(cand)):
            for j in range(i + 1, len(cand)):
                v1, v2 = cand[i], cand[j]
                sim = dict(state)
                sim[v1] = GREEN
                sim[v2] = GREEN
                # spread once
                self._spread_one(sim, G)
                # second turn: greedy top-k_protect
                top2 = self._greedy_top(G, sim, self.k_protect)
                for u in top2:
                    if sim[u] == WHITE:
                        sim[u] = GREEN
                self._spread_one(sim, G)
                burned = sum(1 for s in sim.values() if s == RED)
                if burned < best_burned:
                    best_burned = burned
                    best_pair = (v1, v2)
        if best_pair is None:
            return cand + [v for v in F if v not in cand]
        # return best pair first, then remaining candidates in greedy order
        head = list(best_pair)
        tail = [v for v in cand if v not in head] + [v for v in F if v not in cand]
        return head + tail


# 10. hybrid_density_aware (NEW) -------------------------------------------

class HybridDensityAware(Strategy):
    """If front is small (bottleneck-shaped) use min_damage_cut; else greedy."""
    name = "hybrid_density_aware"

    def __init__(self, density_threshold: float = 0.18):
        self.threshold = density_threshold
        self.cut_strat = MinDamageCut()
        self.greedy_strat = MaxWhiteNeighbors()

    def select(self, G, state):
        F = fire_front(G, state)
        if not F:
            return F
        white_count = sum(1 for s in state.values() if s == WHITE)
        density = len(F) / max(1, white_count)
        if density < self.threshold:
            return self.cut_strat.select(G, state)
        return self.greedy_strat.select(G, state)


# 11. random (sanity baseline) ----------------------------------------------

class RandomStrategy(Strategy):
    name = "random"

    def __init__(self, seed: int = 0):
        self.rng = random.Random(seed)

    def select(self, G, state):
        F = fire_front(G, state)
        F = list(F)
        self.rng.shuffle(F)
        return F


def all_strategies(seed: int = 0) -> List[Strategy]:
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
