import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import { BBox, GraphResponse } from "./api";
import Icon from "./Icon";

interface Props {
  bbox: BBox;
  setBbox: (b: BBox) => void;
  graph: GraphResponse | null;
}

interface LegendEntry {
  label: string;
  color: string;
}

// fetched once on mount; cached at module scope
let LEGEND_CACHE: Record<string, LegendEntry> | null = null;

export default function MapPicker({ bbox, setBbox, graph }: Props) {
  const mapDivRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<L.Map | null>(null);
  const rectRef = useRef<L.Rectangle | null>(null);
  const graphLayerRef = useRef<L.LayerGroup | null>(null);
  const overlayRef = useRef<L.ImageOverlay | null>(null);
  const externalChangeRef = useRef(false);

  const [showLandcover, setShowLandcover] = useState<boolean>(false);
  const [overlayOpacity, setOverlayOpacity] = useState<number>(0.65);
  const [legend, setLegend] = useState<Record<string, LegendEntry> | null>(LEGEND_CACHE);

  // legend (one-time)
  useEffect(() => {
    if (legend) return;
    fetch("/api/landcover/legend")
      .then((r) => r.json())
      .then((j) => { LEGEND_CACHE = j; setLegend(j); })
      .catch(() => {});
  }, [legend]);

  // ---- map init ----
  useEffect(() => {
    if (!mapDivRef.current || mapRef.current) return;
    const map = L.map(mapDivRef.current, { zoomControl: true }).setView(
      [(bbox.north + bbox.south) / 2, (bbox.east + bbox.west) / 2],
      10
    );
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "© OpenStreetMap",
    }).addTo(map);

    const rect = L.rectangle(
      [
        [bbox.south, bbox.west],
        [bbox.north, bbox.east],
      ],
      {
        color: "#ea580c",
        weight: 2.5,
        fillColor: "#ea580c",
        fillOpacity: 0.06,
      }
    ).addTo(map);
    rectRef.current = rect;

    graphLayerRef.current = L.layerGroup().addTo(map);
    map.fitBounds(rect.getBounds(), { padding: [40, 40] });

    let downAt: L.LatLng | null = null;
    map.on("mousedown", (e) => {
      const ev = e.originalEvent as MouseEvent;
      if (!ev.shiftKey) return;
      ev.preventDefault();
      map.dragging.disable();
      downAt = e.latlng;
    });
    map.on("mousemove", (e) => {
      if (!downAt) return;
      const a = downAt;
      const b = e.latlng;
      rect.setBounds([
        [Math.min(a.lat, b.lat), Math.min(a.lng, b.lng)],
        [Math.max(a.lat, b.lat), Math.max(a.lng, b.lng)],
      ]);
    });
    map.on("mouseup", (e) => {
      if (!downAt) return;
      const a = downAt;
      const b = e.latlng;
      downAt = null;
      map.dragging.enable();
      setBbox({
        north: Math.max(a.lat, b.lat),
        south: Math.min(a.lat, b.lat),
        east: Math.max(a.lng, b.lng),
        west: Math.min(a.lng, b.lng),
      });
    });

    mapRef.current = map;
  }, []);

  // sync rectangle to bbox
  useEffect(() => {
    if (!rectRef.current || !mapRef.current) return;
    rectRef.current.setBounds([
      [bbox.south, bbox.west],
      [bbox.north, bbox.east],
    ]);
    if (externalChangeRef.current) {
      externalChangeRef.current = false;
      mapRef.current.fitBounds(rectRef.current.getBounds(), {
        padding: [60, 60],
        animate: true,
      });
    }
  }, [bbox.north, bbox.south, bbox.east, bbox.west]);

  const lastBboxRef = useRef(bbox);
  useEffect(() => {
    const prev = lastBboxRef.current;
    const dLat = Math.abs(bbox.north - prev.north) + Math.abs(bbox.south - prev.south);
    const dLon = Math.abs(bbox.east - prev.east) + Math.abs(bbox.west - prev.west);
    if (dLat > 0.05 || dLon > 0.05) externalChangeRef.current = true;
    lastBboxRef.current = bbox;
  }, [bbox]);

  // ---- WorldCover overlay (image layer) ----
  useEffect(() => {
    if (!mapRef.current) return;
    // tear down any previous overlay
    if (overlayRef.current) {
      mapRef.current.removeLayer(overlayRef.current);
      overlayRef.current = null;
    }
    if (!showLandcover || !graph) return;
    const url = `/api/landcover/${graph.graph_id}.png`;
    const layer = L.imageOverlay(
      url,
      [
        [graph.bbox.south, graph.bbox.west],
        [graph.bbox.north, graph.bbox.east],
      ],
      { opacity: overlayOpacity, interactive: false }
    );
    layer.addTo(mapRef.current);
    overlayRef.current = layer;
  }, [showLandcover, graph]);

  // opacity updates without recreating
  useEffect(() => {
    if (overlayRef.current) overlayRef.current.setOpacity(overlayOpacity);
  }, [overlayOpacity]);

  // ---- graph overlay (vertices, edges, settlements) ----
  useEffect(() => {
    if (!graphLayerRef.current) return;
    graphLayerRef.current.clearLayers();
    if (!graph) return;
    const idToPos = new Map<number, [number, number]>();
    for (const n of graph.nodes) idToPos.set(n.id, [n.lat, n.lon]);

    for (const e of graph.edges) {
      const a = idToPos.get(e.u);
      const b = idToPos.get(e.v);
      if (!a || !b) continue;
      L.polyline([a, b], { color: "#16a34a", weight: 1.8, opacity: 0.95 }).addTo(
        graphLayerRef.current!
      );
    }
    for (const e of graph.blocked_edges) {
      const a = idToPos.get(e.u);
      const b = idToPos.get(e.v);
      if (!a || !b) continue;
      L.polyline([a, b], {
        color: "#dc2626",
        weight: 1,
        opacity: 0.4,
        dashArray: "4 4",
      }).addTo(graphLayerRef.current!);
    }
    const sortedA = [...graph.nodes].map((n) => n.area_ha || 0).sort((a, b) => a - b);
    const medianA = sortedA[Math.floor(sortedA.length / 2)] || 1;
    for (const n of graph.nodes) {
      const r = n.area_ha && medianA > 0
        ? Math.max(3, Math.min(9, 4.5 * Math.sqrt(n.area_ha / medianA)))
        : 4.5;
      const haStr = n.area_ha ? ` · ${Math.round(n.area_ha)} ha` : "";
      const dStr = n.density ? ` · ${(n.density * 100).toFixed(0)}% forest` : "";
      L.circleMarker([n.lat, n.lon], {
        radius: r,
        color: "#0f172a",
        fillColor: "#ffffff",
        fillOpacity: 1,
        weight: 1.5,
      })
        .bindTooltip(`v${n.id}${haStr}${dStr}`, { permanent: false, direction: "top" })
        .addTo(graphLayerRef.current!);
    }
    for (const s of graph.settlements) {
      L.circleMarker([s.lat, s.lon], {
        radius: 6,
        color: "#ea580c",
        fillColor: "#fdba74",
        fillOpacity: 0.7,
        weight: 1.5,
      })
        .bindTooltip(s.name || s.type, { permanent: false, direction: "top" })
        .addTo(graphLayerRef.current!);
    }
  }, [graph]);

  const latKm = (bbox.north - bbox.south) * 111;
  const lonKm =
    (bbox.east - bbox.west) *
    111 *
    Math.cos(((bbox.north + bbox.south) * Math.PI) / 360);

  return (
    <div style={{ position: "relative", height: "100%" }}>
      <div ref={mapDivRef} className="map-container" />

      {/* bbox info card */}
      <div className="map-overlay">
        <strong>Selected bbox</strong>
        <div className="bbox-info" style={{ marginTop: 6 }}>
          N {bbox.north.toFixed(3)}  S {bbox.south.toFixed(3)}
          <br />
          E {bbox.east.toFixed(3)}  W {bbox.west.toFixed(3)}
          <br />
          {latKm.toFixed(1)} km × {lonKm.toFixed(1)} km{" "}
          ≈ {(latKm * lonKm).toFixed(0)} km²
        </div>
        {graph && (
          <div style={{ fontSize: 11, color: "#047857", marginTop: 6, display: "inline-flex", alignItems: "center", gap: 5 }}>
            <Icon name="check" size={12} /> Graph loaded ({graph.n_vertices} vertices)
          </div>
        )}
      </div>

      {/* WorldCover overlay control */}
      {graph && (
        <div className="lc-control">
          <label className="lc-toggle">
            <input
              type="checkbox"
              checked={showLandcover}
              onChange={(e) => setShowLandcover(e.target.checked)}
            />
            <span>
              <strong>ESA WorldCover</strong>
              <small>land cover overlay</small>
            </span>
          </label>
          {showLandcover && (
            <>
              <div className="lc-opacity">
                <span>opacity</span>
                <input
                  type="range"
                  min={20}
                  max={100}
                  value={Math.round(overlayOpacity * 100)}
                  onChange={(e) => setOverlayOpacity(parseInt(e.target.value) / 100)}
                />
                <span className="lc-opacity-val">{Math.round(overlayOpacity * 100)}%</span>
              </div>
              {legend && (
                <div className="lc-legend">
                  {Object.entries(legend).map(([code, e]) => (
                    <div key={code} className="lc-legend-row">
                      <span className="lc-sw" style={{ background: e.color }} />
                      {e.label}
                    </div>
                  ))}
                </div>
              )}
              <div className="lc-note">
                Source: ESA WorldCover 2021 v200 (10 m, Sentinel-2). The OSM
                basemap is independent of this classification; an area that
                doesn't look green on OSM may still be classified as forest by
                ESA (Mediterranean maquis is often unlabelled on OSM).
              </div>
            </>
          )}
        </div>
      )}

      <div className="map-help-pill">
        <kbd>Shift</kbd> + drag → new bbox · or pick a panel preset
      </div>
    </div>
  );
}
