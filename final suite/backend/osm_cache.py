"""Overpass API queries for waterways and settlements, cached on disk."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict

import requests

CACHE_DIR = Path(__file__).resolve().parent / "cache" / "osm"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

OVERPASS = "https://overpass-api.de/api/interpreter"

# Overpass rejects requests without a UA; pretending to be a browser is fine.
HEADERS = {
    "User-Agent": "ie492-firefighter-suite/0.1 (academic; ie492 project)",
    "Accept": "application/json",
}


def _cache_path(query: str) -> Path:
    h = hashlib.sha1(query.encode("utf-8")).hexdigest()[:16]
    return CACHE_DIR / f"{h}.json"


def _post(query: str) -> Dict[str, Any]:
    p = _cache_path(query)
    if p.exists():
        return json.loads(p.read_text())
    resp = requests.post(OVERPASS, data={"data": query}, headers=HEADERS, timeout=180)
    resp.raise_for_status()
    data = resp.json()
    p.write_text(json.dumps(data))
    return data


def waterways(north: float, south: float, east: float, west: float) -> list[Dict[str, Any]]:
    q = (
        f"[out:json][timeout:90];\n"
        f'(way["waterway"]({south},{west},{north},{east}););\n'
        f"out geom;"
    )
    try:
        data = _post(q)
    except Exception as e:
        print(f"[osm] waterways failed: {e}")
        return []
    out = []
    for el in data.get("elements", []):
        if el.get("type") != "way" or "geometry" not in el:
            continue
        coords = [(p["lon"], p["lat"]) for p in el["geometry"]]
        if len(coords) < 2:
            continue
        tags = el.get("tags", {})
        out.append(
            {
                "coords": coords,
                "type": tags.get("waterway", "stream"),
                "name": tags.get("name", ""),
            }
        )
    return out


def settlements(north: float, south: float, east: float, west: float) -> list[Dict[str, Any]]:
    q = (
        f"[out:json][timeout:60];\n"
        f'(node["place"~"^(village|hamlet|town|suburb|city)$"]({south},{west},{north},{east}););\n'
        f"out body;"
    )
    try:
        data = _post(q)
    except Exception as e:
        print(f"[osm] settlements failed: {e}")
        return []
    out = []
    for el in data.get("elements", []):
        if el.get("type") != "node":
            continue
        tags = el.get("tags", {})
        out.append(
            {
                "lon": el["lon"],
                "lat": el["lat"],
                "name": tags.get("name", tags.get("name:tr", "?")),
                "type": tags.get("place", "village"),
            }
        )
    return out
