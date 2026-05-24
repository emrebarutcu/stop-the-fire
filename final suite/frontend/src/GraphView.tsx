import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  GraphResponse,
  SimResult,
  SimulateResponse,
} from "./api";
import Icon from "./Icon";
import { getMeta, PHILOSOPHY_LABEL } from "./strategy_meta";

interface Props {
  graph: GraphResponse;
  fireOrigin: number | null;
  setFireOrigin: (v: number) => void;
  result: SimResult | null;
  currentTurn: number;
  setCurrentTurn: (n: number | ((prev: number) => number)) => void;
  selectedStrategy: string | null;
  setSelectedStrategy: (s: string) => void;
  sim: SimulateResponse | null;
}

type State = "WHITE" | "RED" | "GREEN";

const COLORS: Record<State, string> = {
  WHITE: "#ffffff",
  RED: "#dc2626",
  GREEN: "#10b981",
};
const FIRE_ORIGIN_RING = "#f59e0b";

const W = 1000;
const H = 700;
const PAD = 40;

export default function GraphView({
  graph,
  fireOrigin,
  setFireOrigin,
  result,
  currentTurn,
  setCurrentTurn,
  selectedStrategy,
  setSelectedStrategy,
  sim,
}: Props) {
  const svgWrapRef = useRef<HTMLDivElement | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);

  const [playing, setPlaying] = useState(false);
  const [speedMs, setSpeedMs] = useState<number>(700);
  const [showLabels, setShowLabels] = useState<boolean>(true);

  // ---- pan + zoom (manipulating SVG viewBox) ----
  const [view, setView] = useState({ x: 0, y: 0, w: W, h: H });
  const dragRef = useRef<{ startX: number; startY: number; vx: number; vy: number } | null>(null);

  const fitView = useCallback(() => setView({ x: 0, y: 0, w: W, h: H }), []);

  const onWheel = (e: React.WheelEvent) => {
    if (!svgRef.current) return;
    e.preventDefault();
    const rect = svgRef.current.getBoundingClientRect();
    const px = (e.clientX - rect.left) / rect.width;
    const py = (e.clientY - rect.top) / rect.height;
    const factor = e.deltaY > 0 ? 1.18 : 1 / 1.18;
    const newW = Math.max(W * 0.18, Math.min(W * 2.5, view.w * factor));
    const newH = (newW / view.w) * view.h;
    const cursorX = view.x + px * view.w;
    const cursorY = view.y + py * view.h;
    setView({
      x: cursorX - px * newW,
      y: cursorY - py * newH,
      w: newW,
      h: newH,
    });
  };

  const onMouseDown = (e: React.MouseEvent) => {
    if (e.button !== 0) return;
    if ((e.target as Element).tagName === "circle" && (e.target as Element).hasAttribute("data-vertex")) {
      // vertex click (no drag)
      return;
    }
    dragRef.current = { startX: e.clientX, startY: e.clientY, vx: view.x, vy: view.y };
  };
  const onMouseMove = (e: React.MouseEvent) => {
    if (!dragRef.current || !svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    const dx = ((e.clientX - dragRef.current.startX) / rect.width) * view.w;
    const dy = ((e.clientY - dragRef.current.startY) / rect.height) * view.h;
    setView((v) => ({ ...v, x: dragRef.current!.vx - dx, y: dragRef.current!.vy - dy }));
  };
  const onMouseUp = () => { dragRef.current = null; };

  // ---- coordinate mapping ----
  const { x, y } = useMemo(() => {
    const lons = graph.nodes.map((n) => n.lon);
    const lats = graph.nodes.map((n) => n.lat);
    const minLon = Math.min(...lons);
    const maxLon = Math.max(...lons);
    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const lonSpan = Math.max(1e-6, maxLon - minLon);
    const latSpan = Math.max(1e-6, maxLat - minLat);
    return {
      x: (lon: number) => PAD + ((lon - minLon) / lonSpan) * (W - 2 * PAD),
      y: (lat: number) => PAD + ((maxLat - lat) / latSpan) * (H - 2 * PAD),
    };
  }, [graph.nodes]);

  // ---- animation: derive vertex states from frames ----
  const stateMap: Record<number, State> = useMemo(() => {
    const m: Record<number, State> = {};
    for (const n of graph.nodes) m[n.id] = "WHITE";
    if (fireOrigin != null) m[fireOrigin] = "RED";
    if (!result) return m;

    const frames = result.frames;
    const cap = Math.min(currentTurn, frames.length);
    for (let i = 0; i < cap; i++) {
      const f = frames[i];
      for (const v of f.protected) m[v] = "GREEN";
      for (const v of f.burned) m[v] = "RED";
    }
    if (cap >= frames.length && result.final_state) {
      for (const [k, v] of Object.entries(result.final_state)) {
        m[parseInt(k)] = v;
      }
    }
    return m;
  }, [graph.nodes, fireOrigin, result, currentTurn]);

  const totalTurns = result?.frames.length ?? 0;

  // ---- highlight: vertices that turned RED/GREEN this very turn ----
  const flash = useMemo(() => {
    const protectedNow = new Set<number>();
    const burnedNow = new Set<number>();
    if (!result || currentTurn < 1 || currentTurn > result.frames.length) {
      return { protectedNow, burnedNow };
    }
    const f = result.frames[currentTurn - 1];
    for (const v of f.protected) protectedNow.add(v);
    for (const v of f.burned) burnedNow.add(v);
    return { protectedNow, burnedNow };
  }, [result, currentTurn]);

  // ---- play loop using interval; turning ourselves off at the end ----
  useEffect(() => {
    if (!playing) return;
    if (!result) { setPlaying(false); return; }
    const id = window.setInterval(() => {
      setCurrentTurn((t) => {
        if (t >= totalTurns) {
          setPlaying(false);
          return t;
        }
        return t + 1;
      });
    }, speedMs);
    return () => window.clearInterval(id);
  }, [playing, speedMs, result, totalTurns, setCurrentTurn]);

  // ---- keyboard shortcuts ----
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      // ignore when user is typing
      const tgt = e.target as HTMLElement;
      if (tgt && (tgt.tagName === "INPUT" || tgt.tagName === "SELECT" || tgt.tagName === "TEXTAREA")) return;
      if (!result) return;
      if (e.code === "Space") {
        e.preventDefault();
        setPlaying((p) => !p);
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        setCurrentTurn((t) => Math.min(totalTurns, t + 1));
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        setCurrentTurn((t) => Math.max(0, t - 1));
      } else if (e.key.toLowerCase() === "r") {
        e.preventDefault();
        setCurrentTurn(0);
        setPlaying(false);
      } else if (e.key.toLowerCase() === "f") {
        e.preventDefault();
        fitView();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [result, totalTurns, setCurrentTurn, fitView]);

  const counts = useMemo(() => {
    let w = 0, r = 0, g = 0;
    for (const v of Object.values(stateMap)) {
      if (v === "WHITE") w++;
      else if (v === "RED") r++;
      else g++;
    }
    return { w, r, g };
  }, [stateMap]);

  const meta = selectedStrategy ? getMeta(selectedStrategy) : null;
  const baseRadius = Math.max(4, Math.min(9, 7 * (W / view.w) ** 0.5));

  // Vertex radius scales with area_ha so the user can read how much forest
  // each vertex represents at a glance. Scale relative to the median so
  // outliers don't dominate.
  const areas = graph.nodes.map((n) => n.area_ha || 0);
  const sortedAreas = [...areas].sort((a, b) => a - b);
  const medianArea = sortedAreas[Math.floor(sortedAreas.length / 2)] || 1;
  const radiusFor = (n: typeof graph.nodes[number]) => {
    if (!n.area_ha || medianArea <= 0) return baseRadius;
    // sqrt scaling so area maps to a circle area perception
    const ratio = Math.sqrt(n.area_ha / medianArea);
    return baseRadius * Math.max(0.6, Math.min(1.8, ratio));
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", minHeight: 0 }}>
      {sim && (
        <div className="graph-toolbar">
          <strong>Strateji:</strong>
          <select
            value={selectedStrategy ?? ""}
            onChange={(e) => {
              setSelectedStrategy(e.target.value);
              setCurrentTurn(0);
              setPlaying(false);
            }}
          >
            {sim.results.map((r) => (
              <option key={r.strategy} value={r.strategy}>
                {r.strategy} — {r.burned_pct.toFixed(1)}%
              </option>
            ))}
          </select>
          {meta && (
            <span className={`philo-tag ${meta.philosophy}`}>
              {PHILOSOPHY_LABEL[meta.philosophy]}
            </span>
          )}
          {result && (
            <>
              <span className="toolbar-stat">
                burned <strong>{result.burned}/{result.n}</strong>
                {" "}({result.burned_pct.toFixed(1)}%)
              </span>
              <span className="toolbar-stat">
                turn <strong>{result.turns}</strong>
              </span>
              <span className="toolbar-stat">
                {(result.runtime_s * 1000).toFixed(2)} ms
              </span>
            </>
          )}
          <span style={{ flex: 1 }} />
          <button
            className="secondary"
            onClick={fitView}
            data-tip="Reset view (F)"
          >
            ⤢ Fit
          </button>
          <label data-tip="Toggle vertex labels" style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 12, color: "#475569", cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={showLabels}
              onChange={(e) => setShowLabels(e.target.checked)}
            />
            labels
          </label>
        </div>
      )}

      <div ref={svgWrapRef} className="graph-svg-wrap" style={{ position: "relative" }}>
        <svg
          ref={svgRef}
          viewBox={`${view.x} ${view.y} ${view.w} ${view.h}`}
          onWheel={onWheel}
          onMouseDown={onMouseDown}
          onMouseMove={onMouseMove}
          onMouseUp={onMouseUp}
          onMouseLeave={onMouseUp}
          style={{ cursor: dragRef.current ? "grabbing" : "grab" }}
        >
          {/* blocked edges first */}
          {graph.blocked_edges.map((e, i) => {
            const a = graph.nodes.find((n) => n.id === e.u);
            const b = graph.nodes.find((n) => n.id === e.v);
            if (!a || !b) return null;
            return (
              <line
                key={`b${i}`}
                x1={x(a.lon)} y1={y(a.lat)}
                x2={x(b.lon)} y2={y(b.lat)}
                stroke="#dc2626"
                strokeOpacity={0.18}
                strokeDasharray="4 4"
                strokeWidth={1}
              />
            );
          })}
          {graph.edges.map((e, i) => {
            const a = graph.nodes.find((n) => n.id === e.u);
            const b = graph.nodes.find((n) => n.id === e.v);
            if (!a || !b) return null;
            const sa = stateMap[a.id];
            const sb = stateMap[b.id];
            const onFire = sa === "RED" || sb === "RED";
            return (
              <line
                key={`e${i}`}
                x1={x(a.lon)} y1={y(a.lat)}
                x2={x(b.lon)} y2={y(b.lat)}
                stroke={onFire ? "#fb923c" : "#16a34a"}
                strokeOpacity={onFire ? 0.7 : 0.45}
                strokeWidth={onFire ? 1.8 : 1.4}
              />
            );
          })}
          {graph.settlements.map((s, i) => (
            <g key={`s${i}`}>
              <circle
                cx={x(s.lon)} cy={y(s.lat)}
                r={9}
                fill="none"
                stroke="#ea580c"
                strokeWidth={1.5}
              />
              {showLabels && (
                <text
                  x={x(s.lon)} y={y(s.lat) - 13}
                  textAnchor="middle"
                  fontSize={9}
                  fill="#9a3412"
                >
                  {s.name}
                </text>
              )}
            </g>
          ))}
          {graph.nodes.map((n) => {
            const st = stateMap[n.id] ?? "WHITE";
            const isFire = n.id === fireOrigin;
            const isProtFlash = flash.protectedNow.has(n.id);
            const isBurnFlash = flash.burnedNow.has(n.id);
            const r = radiusFor(n);
            return (
              <g
                key={n.id}
                transform={`translate(${x(n.lon)},${y(n.lat)})`}
                onClick={(e) => {
                  e.stopPropagation();
                  if (!sim) setFireOrigin(n.id);
                }}
                style={{ cursor: "pointer" }}
              >
                {isFire && (
                  <circle r={r + 5} fill="none" stroke={FIRE_ORIGIN_RING} strokeWidth={2} />
                )}
                {(isProtFlash || isBurnFlash) && (
                  <circle
                    r={r + 4}
                    fill="none"
                    stroke={isProtFlash ? "#10b981" : "#dc2626"}
                    strokeWidth={2}
                    opacity={0.7}
                  >
                    <animate
                      attributeName="r"
                      from={r + 2}
                      to={r + 8}
                      dur="0.8s"
                      repeatCount="1"
                    />
                  </circle>
                )}
                <circle
                  data-vertex={n.id}
                  r={r}
                  fill={COLORS[st]}
                  stroke="#0f172a"
                  strokeWidth={1}
                >
                  <title>
                    v{n.id} · {n.area_ha ? `${Math.round(n.area_ha)} ha orman` : ""}
                    {n.density ? ` · density ${(n.density * 100).toFixed(0)}%` : ""}
                  </title>
                </circle>
                {showLabels && r >= 5 && (
                  <text
                    className="vertex-label"
                    x={0} y={3}
                    textAnchor="middle"
                    fill={st === "WHITE" ? "#0f172a" : "white"}
                  >
                    {n.id}
                  </text>
                )}
              </g>
            );
          })}
        </svg>

        <div className="graph-help-pill">
          <kbd>Space</kbd> play · <kbd>←</kbd>/<kbd>→</kbd> turn · <kbd>R</kbd> reset · <kbd>F</kbd> fit
          <br />
          Scroll: zoom · Drag: pan · Click vertex{!sim ? " to set fire origin" : ""}
        </div>
      </div>

      {!sim && fireOrigin != null && (
        <div className="fire-banner">
          <Icon name="flame" size={14} />
          Fire origin: <strong>v{fireOrigin}</strong>. Click another vertex to
          change it, then hit <strong>Run all strategies</strong> in the sidebar.
        </div>
      )}

      {result && (
        <div className="timeline">
          <button onClick={() => { setCurrentTurn(0); setPlaying(false); }} data-tip="Back to start (R)">
            <Icon name="skipBack" size={14} />
          </button>
          <button
            onClick={() => setCurrentTurn((t) => Math.max(0, t - 1))}
            data-tip="Previous turn (←)"
          >
            <Icon name="rewind" size={14} />
          </button>
          <button
            className="play"
            onClick={() => setPlaying((p) => !p)}
            data-tip="Play / pause (Space)"
          >
            <Icon name={playing ? "pause" : "play"} size={14} />
          </button>
          <button
            onClick={() => setCurrentTurn((t) => Math.min(totalTurns, t + 1))}
            data-tip="Next turn (→)"
          >
            <Icon name="fastForward" size={14} />
          </button>
          <button onClick={() => setCurrentTurn(totalTurns)} data-tip="Skip to end">
            <Icon name="skipForward" size={14} />
          </button>
          <input
            type="range"
            min={0}
            max={totalTurns}
            value={currentTurn}
            onChange={(e) => { setCurrentTurn(parseInt(e.target.value)); setPlaying(false); }}
          />
          <span className="turn-label">
            turn {currentTurn} / {totalTurns}
          </span>
          <label
            data-tip="Playback speed (ms between turns)"
            style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11, color: "#64748b" }}
          >
            <span>speed</span>
            <input
              type="range"
              min={150}
              max={1500}
              step={50}
              value={speedMs}
              onChange={(e) => setSpeedMs(parseInt(e.target.value))}
              style={{ width: 80 }}
            />
            <span style={{ fontVariantNumeric: "tabular-nums", fontWeight: 600 }}>
              {speedMs}ms
            </span>
          </label>
          <div className="legend">
            <span>
              <span className="swatch" style={{ background: COLORS.WHITE }} />
              safe {counts.w}
            </span>
            <span>
              <span className="swatch" style={{ background: COLORS.RED }} />
              burned {counts.r}
            </span>
            <span>
              <span className="swatch" style={{ background: COLORS.GREEN }} />
              protected {counts.g}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
