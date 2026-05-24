"""ESA WorldCover 2021 v200 — 10 m land-cover raster.

Tiles are 3° × 3°, named after their SW corner with increments of 3°:
    e.g. N36E027 covers 36–39 N, 27–30 E.

Public S3 mirror:
    https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/<tile>.tif

For an arbitrary bbox we figure out which tiles intersect it, download the
missing ones into a local cache, and return a single rasterio dataset that
covers the bbox (merging if necessary).
"""
from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

import numpy as np
import rasterio
import requests
from rasterio.io import MemoryFile
from rasterio.merge import merge as rio_merge

CACHE_DIR = Path(__file__).resolve().parent / "cache" / "tiles"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

S3_BASE = (
    "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/"
    "ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"
)


@dataclass
class TileId:
    lat_sw: int  # SW corner latitude, multiple of 3
    lon_sw: int  # SW corner longitude, multiple of 3

    @property
    def name(self) -> str:
        ns = "N" if self.lat_sw >= 0 else "S"
        ew = "E" if self.lon_sw >= 0 else "W"
        return f"{ns}{abs(self.lat_sw):02d}{ew}{abs(self.lon_sw):03d}"


def _floor3(x: float) -> int:
    return int(math.floor(x / 3.0) * 3)


def tiles_for_bbox(north: float, south: float, east: float, west: float) -> List[TileId]:
    """All 3°x3° tiles that intersect the bbox."""
    if north <= south or east <= west:
        raise ValueError("bbox must satisfy north>south and east>west")
    lat_lo = _floor3(south)
    lat_hi = _floor3(north - 1e-9)  # tile that contains the top edge
    lon_lo = _floor3(west)
    lon_hi = _floor3(east - 1e-9)
    out: List[TileId] = []
    for lat in range(lat_lo, lat_hi + 1, 3):
        for lon in range(lon_lo, lon_hi + 1, 3):
            out.append(TileId(lat_sw=lat, lon_sw=lon))
    return out


def _download(tile: TileId, dest: Path) -> None:
    url = S3_BASE.format(tile=tile.name)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                if chunk:
                    f.write(chunk)
    os.replace(tmp, dest)


def ensure_tile(tile: TileId) -> Path:
    path = CACHE_DIR / f"{tile.name}.tif"
    if not path.exists():
        _download(tile, path)
    return path


@dataclass
class RasterWindow:
    """Rasterized land-cover values inside the requested bbox."""

    data: np.ndarray   # uint8, shape (rows, cols)
    rows: int
    cols: int
    north: float
    south: float
    east: float
    west: float


def read_bbox(north: float, south: float, east: float, west: float) -> RasterWindow:
    """Return the land-cover raster clipped to the bbox.

    If the bbox spans multiple tiles, they are merged in-memory first.
    """
    tiles = tiles_for_bbox(north, south, east, west)
    if not tiles:
        raise ValueError("no tiles intersect bbox")

    paths = [ensure_tile(t) for t in tiles]

    if len(paths) == 1:
        src = rasterio.open(paths[0])
        sources = [src]
    else:
        sources = [rasterio.open(p) for p in paths]

    try:
        if len(sources) == 1:
            src = sources[0]
            wnd = src.window(west, south, east, north)
            data = src.read(1, window=wnd)
            transform = src.window_transform(wnd)
        else:
            data, transform = rio_merge(sources, bounds=(west, south, east, north))
            data = data[0]
    finally:
        for s in sources:
            s.close()

    rows, cols = data.shape
    return RasterWindow(
        data=data.astype(np.uint8, copy=False),
        rows=int(rows),
        cols=int(cols),
        north=float(north),
        south=float(south),
        east=float(east),
        west=float(west),
    )
