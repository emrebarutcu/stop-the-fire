"""Convert an arbitrary lon/lat bbox into a fire-spread NetworkX graph.

Two placement modes:

* ``mode="density"`` (v2, default) — given ``hectares_per_vertex``, compute
  the number of vertices from the *actual* forest area in the bbox. Vertices
  are placed by density-weighted Lloyd's relaxation on a coarse forest cell
  grid; each vertex inherits ``area_ha`` (the forest hectares it represents)
  and ``density`` (mean fuel weight). Vertices NEVER land in bare / built /
  cropland / water; the forest mask is strict.

* ``mode="count"`` (v1, legacy) — given ``n_vertices``, place that many
  points using the two-phase coverage-then-density heuristic. Kept for
  backward compatibility; falls back to lower density thresholds if forest
  is sparse, which the user noted leads to vertices in marginal terrain.

Edge filter (shared by both modes) is stricter than v1's original behavior:
  • ``FIRE_CLASSES = {10, 20}`` — grassland excluded (treated as a soft
    barrier so mountain meadows don't carry fire across an edge).
  • ``MIN_AVG_FUEL_WEIGHT = 1.5`` — average WMAP weight along the line must
    exceed this, so edges through "mostly bare" terrain are rejected even
    if no single 60-m gap triggers.
  • ``MIN_GAP_M = 60`` — continuous non-fuel run that kills an edge.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx
import numpy as np
from scipy.ndimage import label as nd_label, uniform_filter
from scipy.spatial import Delaunay
from shapely.geometry import LineString, Point
from shapely.ops import unary_union

from osm_cache import settlements, waterways
from tile_cache import RasterWindow, read_bbox

# ---------------------------------------------------------------------------
# Fire-sensitivity weights per ESA WorldCover class.
# ---------------------------------------------------------------------------
WMAP = {10: 5.0, 20: 3.0, 30: 1.0, 40: 0.0, 50: 0.0, 60: 0.0, 70: 0.0, 80: 0.0, 90: 0.0}
SINIF = {
    10: "Forest", 20: "Shrubland", 30: "Grassland", 40: "Cropland",
    50: "Built", 60: "Bare", 70: "Snow", 80: "Water", 90: "Wetland",
}

# Strict fuel: forest + shrubland only. Grass is allowed to *exist* but is
# not enough on its own — see MIN_AVG_FUEL_WEIGHT below.
FIRE_CLASSES = {10, 20}
SEA_CLASS = 80
NONFUEL_RUN_WEIGHT_THRESHOLD = 0.5  # below this WMAP weight, a sample counts as non-fuel
MIN_GAP_M = 60                      # continuous non-fuel run that kills an edge
MIN_AVG_FUEL_WEIGHT = 1.5           # below this average weight, the edge is rejected
EDGE_PIXEL_SAMPLES = 220

# Vertex placement (v2 / density mode) defaults
VERTEX_FOREST_CLASSES = {10, 20}    # what counts as "forest" for vertex placement
DEFAULT_HECTARES_PER_VERTEX = 500.0
DEFAULT_MIN_FOREST_FRACTION = 0.55  # cell must be >= 55% forest to host a vertex
LLOYD_ITERATIONS = 14


@dataclass
class GraphMeta:
    n_vertices: int
    n_active_edges: int
    n_blocked_edges: int
    bbox: Dict[str, float]
    settlements: List[Dict[str, Any]]
    raster_classes: Dict[int, int]  # class code -> pixel count
    total_forest_ha: float
    hectares_per_vertex: Optional[float]
    mode: str                       # "density" or "count"


# ---------------------------------------------------------------------------
# Pixel <-> lon/lat helpers
# ---------------------------------------------------------------------------

def _pix_to_lonlat(r: int, c: int, rw: RasterWindow) -> Tuple[float, float]:
    lon = rw.west + c * (rw.east - rw.west) / rw.cols
    lat = rw.north + r * (rw.south - rw.north) / rw.rows
    return lon, lat


def _lonlat_to_pix(lon: float, lat: float, rw: RasterWindow) -> Tuple[int, int]:
    r = int((lat - rw.north) / (rw.south - rw.north) * rw.rows)
    c = int((lon - rw.west) / (rw.east - rw.west) * rw.cols)
    return r, c


def _bbox_km(rw: RasterWindow) -> Tuple[float, float]:
    lat_km = (rw.north - rw.south) * 111.0
    lon_km = (rw.east - rw.west) * 111.0 * np.cos(np.deg2rad((rw.north + rw.south) / 2))
    return float(lat_km), float(lon_km)


# ---------------------------------------------------------------------------
# v2 — density-aware vertex placement (Lloyd's relaxation)
# ---------------------------------------------------------------------------

def _build_coarse_grid(
    rw: RasterWindow,
    cell_size_m: float = 100.0,
) -> Tuple[np.ndarray, float, int, int]:
    """Downsample the raster to a coarse forest-fraction grid.

    Each cell is roughly ``cell_size_m × cell_size_m`` and holds the fraction
    of WorldCover-forest pixels inside it. Returns also the per-cell area in
    hectares and the (block_r, block_c) block sizes for unprojecting later.
    """
    rows, cols = rw.rows, rw.cols
    lat_km, lon_km = _bbox_km(rw)
    px_per_m_row = rows / max(1.0, lat_km * 1000)
    px_per_m_col = cols / max(1.0, lon_km * 1000)
    block_r = max(2, int(round(cell_size_m * px_per_m_row)))
    block_c = max(2, int(round(cell_size_m * px_per_m_col)))

    forest = np.zeros_like(rw.data, dtype=np.float32)
    for cls in VERTEX_FOREST_CLASSES:
        forest[rw.data == cls] = 1.0

    crop_r = (rows // block_r) * block_r
    crop_c = (cols // block_c) * block_c
    if crop_r == 0 or crop_c == 0:
        return np.zeros((0, 0), dtype=np.float32), 0.0, block_r, block_c
    crop = forest[:crop_r, :crop_c]
    coarse = crop.reshape(crop_r // block_r, block_r, crop_c // block_c, block_c).mean(axis=(1, 3))

    # cell area in hectares: actual cell size in km × km × 100 ha/km²
    cell_w_km = block_c / cols * lon_km
    cell_h_km = block_r / rows * lat_km
    cell_ha = cell_w_km * cell_h_km * 100.0
    return coarse, float(cell_ha), block_r, block_c


def _coarse_to_lonlat(
    r_coarse: float,
    c_coarse: float,
    block_r: int,
    block_c: int,
    rw: RasterWindow,
) -> Tuple[float, float]:
    fine_r = (r_coarse + 0.5) * block_r
    fine_c = (c_coarse + 0.5) * block_c
    fine_r = float(max(0, min(rw.rows - 1, fine_r)))
    fine_c = float(max(0, min(rw.cols - 1, fine_c)))
    lon = rw.west + fine_c * (rw.east - rw.west) / rw.cols
    lat = rw.north + fine_r * (rw.south - rw.north) / rw.rows
    return lon, lat


def _kmeans_pp_init(coords: np.ndarray, weights: np.ndarray, k: int, rng: np.random.Generator) -> np.ndarray:
    """Standard k-means++ seeding, weighted by ``weights``."""
    n = coords.shape[0]
    if n == 0:
        return np.zeros((0, 2), dtype=np.float64)
    # first center proportional to weights
    p0 = weights / weights.sum()
    idx0 = int(rng.choice(n, p=p0))
    centers = [coords[idx0]]
    d2 = np.sum((coords - centers[0]) ** 2, axis=1)
    for _ in range(1, k):
        prob = d2 * weights
        s = prob.sum()
        if s <= 0:
            # everything already covered; pick uniformly
            idx = int(rng.integers(n))
        else:
            idx = int(rng.choice(n, p=prob / s))
        centers.append(coords[idx])
        new_d2 = np.sum((coords - centers[-1]) ** 2, axis=1)
        d2 = np.minimum(d2, new_d2)
    return np.array(centers, dtype=np.float64)


def _place_vertices_density(
    rw: RasterWindow,
    hectares_per_vertex: float,
    min_forest_fraction: float,
    seed: int = 42,
) -> Tuple[List[Tuple[float, float]], List[float], List[float], float]:
    """Density-weighted Lloyd's algorithm on a coarse forest-fraction grid.

    Returns
    -------
    positions : list of (lon, lat)
    areas_ha  : per-vertex forest area it represents
    density   : per-vertex mean forest fraction (0..1)
    total_forest_ha : total forest area in the bbox
    """
    coarse, cell_ha, block_r, block_c = _build_coarse_grid(rw)
    if coarse.size == 0:
        return [], [], [], 0.0

    # margin: drop a 1-cell band on each side so vertices aren't on the rim
    coarse_margin = coarse.copy()
    coarse_margin[0, :] = 0.0
    coarse_margin[-1, :] = 0.0
    coarse_margin[:, 0] = 0.0
    coarse_margin[:, -1] = 0.0

    eligible = coarse_margin >= min_forest_fraction
    if eligible.sum() == 0:
        # forest is too sparse for the chosen threshold — relax once
        eligible = coarse_margin >= max(0.30, min_forest_fraction - 0.20)

    total_forest_ha = float(coarse.sum() * cell_ha)
    if eligible.sum() == 0:
        return [], [], [], total_forest_ha

    eligible_idx = np.argwhere(eligible)  # (M, 2): rows are (r, c) in coarse coords
    coords = eligible_idx.astype(np.float64)
    weights = coarse_margin[eligible].astype(np.float64)

    n_target = max(4, int(round(total_forest_ha / max(1.0, hectares_per_vertex))))
    n_target = min(n_target, eligible_idx.shape[0])
    if n_target < 4:
        return [], [], [], total_forest_ha

    rng = np.random.default_rng(seed)
    centers = _kmeans_pp_init(coords, weights, n_target, rng)

    # Lloyd's iterations
    last_centers = centers.copy()
    for it in range(LLOYD_ITERATIONS):
        # assign each eligible cell to nearest center (M, K) distance matrix
        d = ((coords[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
        assign = d.argmin(axis=1)
        # density-weighted centroid update
        new_centers = np.zeros_like(centers)
        for k in range(centers.shape[0]):
            mask = assign == k
            if not mask.any():
                new_centers[k] = centers[k]
                continue
            w = weights[mask]
            new_centers[k] = (coords[mask].T @ w) / w.sum()
        delta = np.max(np.linalg.norm(new_centers - last_centers, axis=1))
        centers = new_centers
        last_centers = centers
        if delta < 0.5:  # < half a cell movement
            break

    # final assignment for area/density computation
    d = ((coords[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
    assign = d.argmin(axis=1)

    positions: List[Tuple[float, float]] = []
    areas: List[float] = []
    density: List[float] = []
    for k in range(centers.shape[0]):
        mask = assign == k
        if not mask.any():
            continue
        # snap to the densest cell in the cluster — guarantees we land on a
        # real forest cell rather than a "geometric center" that might fall
        # in a hole (e.g., a settlement inside a forest patch).
        cluster_coords = coords[mask]
        cluster_w = weights[mask]
        best_local = int(np.argmax(cluster_w))
        cr, cc = cluster_coords[best_local]
        lon, lat = _coarse_to_lonlat(cr, cc, block_r, block_c, rw)
        positions.append((lon, lat))
        # area: sum of forest fractions in the cluster × per-cell ha
        areas.append(float(np.sum(cluster_w) * cell_ha))
        density.append(float(np.mean(cluster_w)))

    return positions, areas, density, total_forest_ha


# ---------------------------------------------------------------------------
# v1 — count-based placement (kept for backward compat / comparison)
# ---------------------------------------------------------------------------

def _place_vertices_count(
    rw: RasterWindow,
    n_target: int,
    min_density: float = 0.30,
) -> Tuple[List[Tuple[float, float]], List[float], List[float], float]:
    """Original two-phase placement: grid sweep + density top-up.

    Returns the same shape as ``_place_vertices_density`` (positions, areas,
    density, total_forest_ha). Areas are computed by Voronoi-assignment of
    coarse forest cells to the placed vertices, so the data shape is
    identical between modes.
    """
    rows, cols = rw.rows, rw.cols
    wc = rw.data

    obstacle = np.zeros_like(wc, dtype=bool)
    for code in (0, 40, 50, 60, 70, 80, 90):
        obstacle[wc == code] = True

    lat_km, lon_km = _bbox_km(rw)
    diag_km = float(np.sqrt(lat_km ** 2 + lon_km ** 2))
    min_dist_km = max(0.5, 0.6 * diag_km / np.sqrt(n_target))
    min_dist_deg = min_dist_km / 111.0

    fuel_binary = ((wc == 10) | (wc == 20) | (wc == 30)).astype(np.float32)
    px_per_km = max(rows / max(0.1, lat_km), cols / max(0.1, lon_km))
    kernel = max(11, int(round(px_per_km)))
    if kernel % 2 == 0:
        kernel += 1
    local_density = uniform_filter(fuel_binary, size=kernel)
    local_density[obstacle] = 0.0

    br = max(1, int(1.5 / 111.0 / max(1e-9, (rw.north - rw.south)) * rows))
    bc = max(1, int(1.5 / 111.0 / max(1e-9, (rw.east - rw.west)) * cols))
    bm = np.zeros_like(local_density, dtype=bool)
    bm[:br, :] = True
    bm[-br:, :] = True
    bm[:, :bc] = True
    bm[:, -bc:] = True
    local_density[bm] = 0.0

    eligible = local_density >= min_density
    if eligible.sum() < n_target:
        eligible = local_density > 0.05

    vertices: List[Tuple[float, float]] = []
    seen_rc = set()
    G = max(3, int(round(np.sqrt(n_target))))
    cr, cc_ = max(1, rows // G), max(1, cols // G)
    cands = []
    for gr in range(G):
        for gc in range(G):
            r0, r1 = gr * cr, min((gr + 1) * cr, rows)
            c0, c1 = gc * cc_, min((gc + 1) * cc_, cols)
            cell = local_density[r0:r1, c0:c1].copy()
            cell[~eligible[r0:r1, c0:c1]] = 0.0
            if cell.max() == 0:
                continue
            br2, bc2 = np.unravel_index(int(cell.argmax()), cell.shape)
            cands.append((float(cell[br2, bc2]), int(r0 + br2), int(c0 + bc2)))
    cands.sort(reverse=True)
    for _, r, c in cands:
        lon, lat = _pix_to_lonlat(r, c, rw)
        if any(((lon - vx) ** 2 + (lat - vy) ** 2) ** 0.5 < min_dist_deg for vx, vy in vertices):
            continue
        vertices.append((lon, lat))
        seen_rc.add((r, c))

    step = max(1, min(rows, cols) // 200)
    ri_s = np.arange(0, rows, step)
    ci_s = np.arange(0, cols, step)
    rr_g, cc_g = np.meshgrid(ri_s, ci_s, indexing="ij")
    rr_g, cc_g = rr_g.flatten(), cc_g.flatten()
    ld_f = np.where(eligible[rr_g, cc_g], local_density[rr_g, cc_g], 0.0)
    for idx in np.argsort(-ld_f):
        if len(vertices) >= n_target:
            break
        if ld_f[idx] == 0:
            break
        r, c = int(rr_g[idx]), int(cc_g[idx])
        if (r, c) in seen_rc:
            continue
        lon, lat = _pix_to_lonlat(r, c, rw)
        if any(((lon - vx) ** 2 + (lat - vy) ** 2) ** 0.5 < min_dist_deg for vx, vy in vertices):
            continue
        vertices.append((lon, lat))
        seen_rc.add((r, c))

    # Compute per-vertex area_ha & density via Voronoi assignment on the coarse grid
    coarse, cell_ha, block_r, block_c = _build_coarse_grid(rw)
    total_forest_ha = float(coarse.sum() * cell_ha)
    if not vertices or coarse.size == 0:
        return vertices, [0.0] * len(vertices), [0.0] * len(vertices), total_forest_ha

    pts_arr = np.array(vertices)
    # eligible coarse cells only
    elig = coarse > 0.05
    elig_idx = np.argwhere(elig)
    if elig_idx.size == 0:
        return vertices, [0.0] * len(vertices), [0.0] * len(vertices), total_forest_ha

    # convert coarse cells to lon/lat once
    cell_lons = rw.west + ((elig_idx[:, 1] + 0.5) * block_c) * (rw.east - rw.west) / rw.cols
    cell_lats = rw.north + ((elig_idx[:, 0] + 0.5) * block_r) * (rw.south - rw.north) / rw.rows
    cell_pts = np.stack([cell_lons, cell_lats], axis=1)

    # nearest vertex for each cell
    d2 = ((cell_pts[:, None, :] - pts_arr[None, :, :]) ** 2).sum(axis=2)
    assign = d2.argmin(axis=1)
    cell_w = coarse[elig].astype(np.float64)
    areas = [0.0] * len(vertices)
    n_cells = [0] * len(vertices)
    sum_w = [0.0] * len(vertices)
    for i, k in enumerate(assign):
        areas[int(k)] += cell_w[i] * cell_ha
        n_cells[int(k)] += 1
        sum_w[int(k)] += cell_w[i]
    density = [sum_w[i] / max(1, n_cells[i]) for i in range(len(vertices))]
    return vertices, areas, density, total_forest_ha


# ---------------------------------------------------------------------------
# Edge filter (shared; stricter than v1)
# ---------------------------------------------------------------------------

def _hits_obstacle(
    v1: Tuple[float, float],
    v2: Tuple[float, float],
    rw: RasterWindow,
    river_union,
    village_union,
    n_samp: int = EDGE_PIXEL_SAMPLES,
) -> Tuple[bool, str]:
    """Return (blocked, reason).

    The edge is rejected if any of these hold:
      1. The line crosses a buffered major river / canal.
      2. The line crosses a buffered settlement.
      3. Any sample pixel is water (class 80).
      4. A continuous non-fuel run >= MIN_GAP_M meters appears along the line.
      5. The mean WMAP weight along the line is below MIN_AVG_FUEL_WEIGHT
         (catches edges that are "mostly bare" but never have a 60-m gap).
    """
    line = LineString([v1, v2])
    if river_union is not None and line.intersects(river_union):
        return True, "river"
    if village_union is not None and line.intersects(village_union):
        return True, "village"

    lons = np.linspace(v1[0], v2[0], n_samp)
    lats = np.linspace(v1[1], v2[1], n_samp)
    edge_km = ((v1[0] - v2[0]) ** 2 + (v1[1] - v2[1]) ** 2) ** 0.5 * 111.0
    m_per_s = max(1.0, edge_km * 1000 / n_samp)
    n_tol = max(1, int(MIN_GAP_M / m_per_s))

    rows, cols = rw.rows, rw.cols
    weights = []
    run = 0
    for lon, lat in zip(lons, lats):
        r, c = _lonlat_to_pix(lon, lat, rw)
        if not (0 <= r < rows and 0 <= c < cols):
            continue
        cls = int(rw.data[r, c])
        if cls == SEA_CLASS:
            return True, "water"
        w = WMAP.get(cls, 0.0)
        weights.append(w)
        if w < NONFUEL_RUN_WEIGHT_THRESHOLD:
            run += 1
            if run >= n_tol:
                return True, f"nonfuel-gap≥{MIN_GAP_M}m"
        else:
            run = 0

    if not weights:
        return True, "out-of-bounds"

    avg = float(np.mean(weights))
    if avg < MIN_AVG_FUEL_WEIGHT:
        return True, f"avg-fuel<{MIN_AVG_FUEL_WEIGHT}"
    return False, ""


# ---------------------------------------------------------------------------
# Top-level: build_graph
# ---------------------------------------------------------------------------

def build_graph(
    north: float,
    south: float,
    east: float,
    west: float,
    *,
    mode: str = "density",
    hectares_per_vertex: float = DEFAULT_HECTARES_PER_VERTEX,
    min_forest_fraction: float = DEFAULT_MIN_FOREST_FRACTION,
    n_vertices: int = 40,
    max_edge_km: float = 14.0,
) -> Tuple[nx.Graph, GraphMeta]:
    """Top-level entry point.

    Args
    ----
    mode : "density" (v2, default) or "count" (v1).
    hectares_per_vertex : v2 — forest hectares each vertex should represent.
    min_forest_fraction : v2 — coarse cell must be >= this forest fraction
        to host a vertex.
    n_vertices : v1 — target vertex count.
    max_edge_km : Delaunay edges longer than this are dropped before the
        obstacle filter (planar locality).
    """
    if mode not in ("density", "count"):
        raise ValueError(f"unknown mode {mode!r}; expected 'density' or 'count'")

    rw = read_bbox(north, south, east, west)

    rivers = waterways(north, south, east, west)
    major_river_lines = [
        LineString(r["coords"]) for r in rivers if r["type"] in ("river", "canal")
    ]
    river_union = (
        unary_union([g.buffer(80 / 111_000) for g in major_river_lines])
        if major_river_lines else None
    )
    villages = settlements(north, south, east, west)
    village_union = (
        unary_union([Point(v["lon"], v["lat"]).buffer(600 / 111_000) for v in villages])
        if villages else None
    )

    if mode == "density":
        pts, areas, density, total_forest_ha = _place_vertices_density(
            rw, hectares_per_vertex=hectares_per_vertex,
            min_forest_fraction=min_forest_fraction,
        )
        hpv = hectares_per_vertex
    else:
        if n_vertices < 4:
            raise ValueError("n_vertices must be >= 4")
        pts, areas, density, total_forest_ha = _place_vertices_count(
            rw, n_target=n_vertices,
        )
        hpv = total_forest_ha / max(1, len(pts)) if pts else None

    if len(pts) < 4:
        raise RuntimeError(
            f"only {len(pts)} vertices placed; bbox has too little forest. "
            "Try a larger area, lower min_forest_fraction, or smaller "
            "hectares_per_vertex."
        )

    arr = np.array(pts)
    tri = Delaunay(arr)
    edges_set = set()
    for s in tri.simplices:
        for i in range(3):
            a, b = int(s[i]), int(s[(i + 1) % 3])
            edges_set.add((min(a, b), max(a, b)))

    max_deg = max_edge_km / 111.0
    candidate_edges = [
        (a, b) for (a, b) in edges_set
        if ((arr[a][0] - arr[b][0]) ** 2 + (arr[a][1] - arr[b][1]) ** 2) ** 0.5 <= max_deg
    ]

    valid_edges: List[Tuple[int, int]] = []
    blocked_edges: List[Tuple[int, int]] = []
    block_reasons: List[Tuple[int, int, str]] = []
    for a, b in candidate_edges:
        blocked, reason = _hits_obstacle(tuple(arr[a]), tuple(arr[b]), rw, river_union, village_union)
        if blocked:
            blocked_edges.append((a, b))
            block_reasons.append((a, b, reason))
        else:
            valid_edges.append((a, b))

    G = nx.Graph()
    for i, (lon, lat) in enumerate(pts):
        G.add_node(
            i,
            pos=(float(lon), float(lat)),
            area_ha=float(areas[i]) if i < len(areas) else 0.0,
            density=float(density[i]) if i < len(density) else 0.0,
        )
    for a, b in valid_edges:
        G.add_edge(a, b)

    uniq, cnt = np.unique(rw.data, return_counts=True)
    classes = {int(u): int(c) for u, c in zip(uniq, cnt)}

    meta = GraphMeta(
        n_vertices=len(pts),
        n_active_edges=len(valid_edges),
        n_blocked_edges=len(blocked_edges),
        bbox={"north": north, "south": south, "east": east, "west": west},
        settlements=villages,
        raster_classes=classes,
        total_forest_ha=float(total_forest_ha),
        hectares_per_vertex=float(hpv) if hpv else None,
        mode=mode,
    )
    G.graph["topology"] = "real_world"
    G.graph["meta"] = meta
    G.graph["blocked_edges"] = blocked_edges
    G.graph["block_reasons"] = block_reasons
    return G, meta
