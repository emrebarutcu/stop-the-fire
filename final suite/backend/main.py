"""FastAPI app exposing the map-to-graph + firefighter pipeline.

Endpoints
---------
POST /api/graph       bbox + n_vertices -> graph (cached)
POST /api/simulate    graph_id + fire_origin + k -> per-strategy SimResult
GET  /api/strategies  list of strategy names

The graph cache is in-memory only; restarting the server clears it.
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

import networkx as nx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from firefighter_engine import all_strategies
from map_to_graph import build_graph
from sim_with_states import simulate_with_states
from tile_cache import read_bbox

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("api")

app = FastAPI(title="Firefighter Web Suite", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GRAPH_CACHE: Dict[str, nx.Graph] = {}


def _graph_id(bbox: Dict[str, float], mode: str, hpv: float, n_vertices: int, mff: float) -> str:
    payload = json.dumps(
        {**bbox, "mode": mode, "hpv": hpv, "n": n_vertices, "mff": mff},
        sort_keys=True,
    )
    return hashlib.sha1(payload.encode()).hexdigest()[:16]


def _serialize_graph(graph_id: str, G: nx.Graph) -> Dict[str, Any]:
    meta = G.graph["meta"]
    nodes = [
        {
            "id": int(v),
            "lon": float(d["pos"][0]),
            "lat": float(d["pos"][1]),
            "area_ha": float(d.get("area_ha", 0.0)),
            "density": float(d.get("density", 0.0)),
        }
        for v, d in G.nodes(data=True)
    ]
    edges = [{"u": int(u), "v": int(v)} for u, v in G.edges()]
    blocked = [
        {"u": int(u), "v": int(v)} for u, v in G.graph.get("blocked_edges", [])
    ]
    block_reasons = [
        {"u": int(u), "v": int(v), "reason": r}
        for u, v, r in G.graph.get("block_reasons", [])
    ]
    return {
        "graph_id": graph_id,
        "nodes": nodes,
        "edges": edges,
        "blocked_edges": blocked,
        "block_reasons": block_reasons,
        "bbox": meta.bbox,
        "settlements": meta.settlements,
        "raster_classes": meta.raster_classes,
        "n_vertices": meta.n_vertices,
        "n_active_edges": meta.n_active_edges,
        "n_blocked_edges": meta.n_blocked_edges,
        "total_forest_ha": meta.total_forest_ha,
        "hectares_per_vertex": meta.hectares_per_vertex,
        "mode": meta.mode,
    }


# ----- /api/graph -----

class GraphReq(BaseModel):
    north: float
    south: float
    east: float
    west: float
    mode: str = Field("density", pattern="^(density|count)$")
    # v2 (density)
    hectares_per_vertex: float = Field(500.0, ge=20.0, le=5000.0)
    min_forest_fraction: float = Field(0.55, ge=0.20, le=0.95)
    # v1 (count)
    n_vertices: int = Field(40, ge=4, le=300)


@app.post("/api/graph")
def post_graph(req: GraphReq):
    if req.north <= req.south or req.east <= req.west:
        raise HTTPException(400, "bbox must satisfy north>south and east>west")
    bbox = {"north": req.north, "south": req.south, "east": req.east, "west": req.west}
    gid = _graph_id(bbox, req.mode, req.hectares_per_vertex, req.n_vertices, req.min_forest_fraction)
    if gid in GRAPH_CACHE:
        log.info(f"graph cache hit {gid}")
        return _serialize_graph(gid, GRAPH_CACHE[gid])

    log.info(
        f"building graph {gid} bbox={bbox} mode={req.mode} "
        f"hpv={req.hectares_per_vertex} n={req.n_vertices} mff={req.min_forest_fraction}"
    )
    try:
        G, _meta = build_graph(
            req.north, req.south, req.east, req.west,
            mode=req.mode,
            hectares_per_vertex=req.hectares_per_vertex,
            min_forest_fraction=req.min_forest_fraction,
            n_vertices=req.n_vertices,
        )
    except Exception as e:
        log.exception("build_graph failed")
        raise HTTPException(500, f"build_graph failed: {e}")
    GRAPH_CACHE[gid] = G
    return _serialize_graph(gid, G)


# ----- /api/simulate -----

class SimReq(BaseModel):
    graph_id: str
    fire_origin: int
    k: int = Field(2, ge=1, le=10)
    strategies: Optional[List[str]] = None  # subset; default = all
    max_turns: int = Field(500, ge=1, le=2000)


@app.post("/api/simulate")
def post_simulate(req: SimReq):
    G = GRAPH_CACHE.get(req.graph_id)
    if G is None:
        raise HTTPException(404, f"graph_id {req.graph_id} not in cache; build it first")
    if req.fire_origin not in G:
        raise HTTPException(400, f"fire_origin {req.fire_origin} is not a vertex")
    strats = all_strategies()
    if req.strategies:
        wanted = set(req.strategies)
        strats = [s for s in strats if s.name in wanted]
        if not strats:
            raise HTTPException(400, f"no matching strategies in {req.strategies}")

    results: List[Dict[str, Any]] = []
    for s in strats:
        try:
            r = simulate_with_states(
                G, req.fire_origin, s, k=req.k, max_turns=req.max_turns
            )
        except Exception as e:
            log.exception(f"strategy {s.name} crashed")
            results.append({"strategy": s.name, "error": str(e)})
            continue
        results.append(
            {
                "strategy": r.strategy,
                "n": r.n,
                "burned": r.burned,
                "saved": r.saved,
                "protected": r.protected,
                "turns": r.turns,
                "runtime_s": r.runtime_s,
                "burned_pct": 100.0 * r.burned / r.n,
                "frames": [
                    {
                        "turn": f.turn,
                        "protected": f.protected,
                        "burned": f.burned,
                        "counts": f.counts,
                    }
                    for f in r.frames
                ],
                "final_state": r.final_state,
            }
        )
    results.sort(key=lambda r: r.get("burned_pct", 1e9))
    return {
        "graph_id": req.graph_id,
        "fire_origin": req.fire_origin,
        "k": req.k,
        "results": results,
    }


# ----- /api/strategies -----

@app.get("/api/strategies")
def get_strategies():
    return [{"name": s.name} for s in all_strategies()]


@app.get("/api/health")
def health():
    return {"status": "ok", "cached_graphs": len(GRAPH_CACHE)}


# ----- /api/landcover/{graph_id}.png -----
# Render the ESA WorldCover raster (the data source the graph was built from)
# as a colored PNG that Leaflet can overlay on the OSM base map.

# Official ESA WorldCover 2021 v200 palette (RGB; A=alpha).
WORLDCOVER_PALETTE: Dict[int, Tuple[int, int, int, int]] = {
    0:   (0, 0, 0, 0),                # no-data → transparent
    10:  (0, 100, 0, 255),            # Tree cover (forest)
    20:  (255, 187, 34, 255),         # Shrubland
    30:  (255, 255, 76, 255),         # Grassland
    40:  (240, 150, 255, 255),        # Cropland
    50:  (250, 0, 0, 255),            # Built-up
    60:  (180, 180, 180, 255),        # Bare / sparse vegetation
    70:  (240, 240, 240, 255),        # Snow / ice
    80:  (0, 100, 200, 255),          # Permanent water
    90:  (0, 150, 160, 255),          # Herbaceous wetland
    95:  (0, 207, 117, 255),          # Mangroves
    100: (250, 230, 160, 255),        # Moss / lichen
}


@app.get("/api/landcover/{graph_id}.png")
def landcover_png(graph_id: str):
    G = GRAPH_CACHE.get(graph_id)
    if G is None:
        raise HTTPException(404, f"graph_id {graph_id} not in cache")
    bbox = G.graph["meta"].bbox
    rw = read_bbox(bbox["north"], bbox["south"], bbox["east"], bbox["west"])

    import numpy as np
    from io import BytesIO
    from PIL import Image

    # build a (rows, cols, 4) RGBA image from the class raster
    rgba = np.zeros((rw.rows, rw.cols, 4), dtype=np.uint8)
    # mask + assign for each known class (vectorized)
    for code, color in WORLDCOVER_PALETTE.items():
        rgba[rw.data == code] = color

    img = Image.fromarray(rgba, mode="RGBA")
    # downsample to keep the response light (the web map doesn't need 10 m res)
    MAX_DIM = 1800
    if max(img.size) > MAX_DIM:
        scale = MAX_DIM / max(img.size)
        img = img.resize(
            (max(1, int(img.size[0] * scale)), max(1, int(img.size[1] * scale))),
            Image.NEAREST,
        )

    buf = BytesIO()
    img.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@app.get("/api/landcover/legend")
def landcover_legend():
    """Class code -> (label, hex color). Frontend uses this to draw the legend."""
    out = {}
    for code, (r, g, b, a) in WORLDCOVER_PALETTE.items():
        if a == 0:
            continue
        out[code] = {
            "label": {
                10: "Forest", 20: "Shrubland", 30: "Grassland", 40: "Cropland",
                50: "Built-up", 60: "Bare", 70: "Snow", 80: "Water",
                90: "Wetland", 95: "Mangroves", 100: "Moss",
            }.get(code, str(code)),
            "color": f"#{r:02x}{g:02x}{b:02x}",
        }
    return out
