from __future__ import annotations

import math
import random
import networkx as nx


def _orientation(ax: float, ay: float, bx: float, by: float, cx: float, cy: float) -> float:
    return (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)


def _segments_intersect(
    p1: tuple[float, float],
    p2: tuple[float, float],
    q1: tuple[float, float],
    q2: tuple[float, float],
) -> bool:
    """Return True if line segments p1-p2 and q1-q2 cross in their interiors."""
    o1 = _orientation(*p1, *p2, *q1)
    o2 = _orientation(*p1, *p2, *q2)
    o3 = _orientation(*q1, *q2, *p1)
    o4 = _orientation(*q1, *q2, *p2)
    return (o1 * o2 < 0) and (o3 * o4 < 0)


def _would_cross_existing_edge(
    graph: nx.Graph,
    pos: dict[int, tuple[float, float]],
    u: int,
    v: int,
) -> bool:
    p1, p2 = pos[u], pos[v]
    for a, b in graph.edges():
        if a in (u, v) or b in (u, v):
            continue
        if _segments_intersect(p1, p2, pos[a], pos[b]):
            return True
    return False


def _radius_for_density(density: float) -> float:
    """Convert target density to RGG radius in unit square.

    For n uniform points in [0,1]², P(edge) ≈ π·r², so r = sqrt(density/π).
    """
    return math.sqrt(density / math.pi)


def generate_graph(n: int, density: float, seed: int) -> nx.Graph:
    """Generate a connected Random Geometric Graph with uniform placement.

    Nodes are placed uniformly in [0,1]²; edges connect pairs within
    a radius derived from the target density.
    Retries with incremented seed until the graph is connected.
    """
    radius = _radius_for_density(density)

    attempt = 0
    while True:
        current_seed = seed + attempt
        G = nx.random_geometric_graph(n, radius, seed=current_seed)
        if nx.is_connected(G):
            break
        attempt += 1
        if attempt > 1000:
            raise ValueError(
                f"Could not generate a connected graph after 1000 attempts "
                f"(n={n}, density={density}, radius={radius:.4f}, base_seed={seed})"
            )

    for node in G.nodes():
        px, py = G.nodes[node]["pos"]
        G.nodes[node]["x"] = float(px)
        G.nodes[node]["y"] = float(py)

    G.graph["seed"] = current_seed
    G.graph["generation_seed"] = seed
    G.graph["radius"] = radius
    return G


def generate_planar_graph(n: int, target_density: float, seed: int) -> nx.Graph:
    """Build a connected planar graph with map-like geometry in [0,1]^2.

    Procedure:
    1) Sample random 2D points (one per vertex).
    2) Build the Euclidean MST (connected, planar as straight-line embedding).
    3) Add shortest remaining non-edges that do not create straight-line crossings
       until target edge count is reached (capped by 3n-6).
    """
    rng = random.Random(seed)
    complete = nx.Graph()
    complete.add_nodes_from(range(n))

    pos: dict[int, tuple[float, float]] = {
        i: (rng.random(), rng.random()) for i in range(n)
    }
    for u in range(n):
        for v in range(u + 1, n):
            x1, y1 = pos[u]
            x2, y2 = pos[v]
            dist = math.hypot(x1 - x2, y1 - y2)
            complete.add_edge(u, v, weight=dist)

    graph = nx.minimum_spanning_tree(complete, weight="weight")

    max_planar_edges = 3 * n - 6 if n >= 3 else n - 1
    target_edges = int(round(target_density * (n * (n - 1) / 2)))
    target_edges = max(n - 1, min(target_edges, max_planar_edges))

    candidate_edges: list[tuple[float, int, int]] = []
    for u in range(n):
        for v in range(u + 1, n):
            if graph.has_edge(u, v):
                continue
            x1, y1 = pos[u]
            x2, y2 = pos[v]
            candidate_edges.append((math.hypot(x1 - x2, y1 - y2), u, v))
    candidate_edges.sort(key=lambda t: t[0])

    for _, u, v in candidate_edges:
        if graph.number_of_edges() >= target_edges:
            break
        if _would_cross_existing_edge(graph, pos, u, v):
            continue
        graph.add_edge(u, v)

    for node in graph.nodes():
        graph.nodes[node]["x"] = pos[node][0]
        graph.nodes[node]["y"] = pos[node][1]
    graph.graph["seed"] = seed
    graph.graph["generation_seed"] = seed
    graph.graph["target_density"] = target_density
    return graph
