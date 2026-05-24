import { BBox, GraphMode, GraphResponse, SimulateResponse } from "./api";
import Icon from "./Icon";

interface Props {
  bbox: BBox;
  setBbox: (b: BBox) => void;
  mode: GraphMode;
  setMode: (m: GraphMode) => void;
  hectaresPerVertex: number;
  setHectaresPerVertex: (h: number) => void;
  minForestFraction: number;
  setMinForestFraction: (f: number) => void;
  nVertices: number;
  setNVertices: (n: number) => void;
  fireOrigin: number | null;
  setFireOrigin: (v: number | null) => void;
  k: number;
  setK: (k: number) => void;
  graph: GraphResponse | null;
  sim: SimulateResponse | null;
  activeStep: number;            // 1, 2, or 3
  onBuildGraph: () => void;
  onSimulate: () => void;
  busy: { msg: string; sub?: string } | null;
  error: string | null;
}

interface Preset {
  name: string;
  bbox: BBox;
  hint?: string;
}

// Hand-picked Turkish forest-fire-prone regions where the underlying tile is
// already in the cache from the reference scripts.
const PRESETS: Preset[] = [
  { name: "Köyceğiz", bbox: { north: 37.10, south: 36.87, east: 28.66, west: 28.40 }, hint: "Marmaris–Köyceğiz corridor" },
  { name: "W. Taurus", bbox: { north: 37.56, south: 37.32, east: 30.86, west: 30.60 }, hint: "Western Taurus pine forest" },
  { name: "Marmaris", bbox: { north: 36.92, south: 36.78, east: 28.36, west: 28.18 }, hint: "Marmaris town centre" },
];

function bboxArea(b: BBox): number {
  const lat = (b.north - b.south) * 111;
  const lon = (b.east - b.west) * 111 * Math.cos(((b.north + b.south) * Math.PI) / 360);
  return Math.max(0, lat * lon);
}
function bboxEqual(a: BBox, b: BBox): boolean {
  const eps = 1e-4;
  return (
    Math.abs(a.north - b.north) < eps &&
    Math.abs(a.south - b.south) < eps &&
    Math.abs(a.east - b.east) < eps &&
    Math.abs(a.west - b.west) < eps
  );
}

export default function ConfigPanel({
  bbox,
  setBbox,
  mode,
  setMode,
  hectaresPerVertex,
  setHectaresPerVertex,
  minForestFraction,
  setMinForestFraction,
  nVertices,
  setNVertices,
  fireOrigin,
  setFireOrigin,
  k,
  setK,
  graph,
  sim,
  activeStep,
  onBuildGraph,
  onSimulate,
  busy,
  error,
}: Props) {
  const upd = (key: keyof BBox, val: number) => setBbox({ ...bbox, [key]: val });
  const area = bboxArea(bbox);
  const buildingGraph = !!busy && busy.msg.startsWith("Downloading");
  const runningSim = !!busy && busy.msg.startsWith("Running");

  // step states
  const step1 = activeStep === 1 ? "active" : "done";
  const step2 = !graph ? "disabled" : activeStep === 2 ? "active" : "done";
  const step3 = !sim ? "disabled" : "active";

  return (
    <div className="steps">
      {error && (
        <div className="error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* ----- 1. REGION ----- */}
      <div className={`step ${step1}`}>
        <div className="step-head">
          <div className="step-num">1</div>
          <div className="step-title">Region (lon/lat bbox)</div>
          <div className="step-meta">{area.toFixed(0)} km²</div>
        </div>
        <div className="step-body">
          <div className="preset-row">
            {PRESETS.map((p) => (
              <button
                key={p.name}
                className={"preset-chip " + (bboxEqual(bbox, p.bbox) ? "active" : "")}
                onClick={() => setBbox(p.bbox)}
                data-tip={p.hint}
              >
                {p.name}
              </button>
            ))}
          </div>
          <div className="field-row">
            <div className="field">
              <label data-tip="Top-left corner — northern bbox edge">North (lat)</label>
              <input
                type="number"
                step="0.001"
                value={bbox.north}
                onChange={(e) => upd("north", parseFloat(e.target.value))}
              />
            </div>
            <div className="field">
              <label data-tip="Southern bbox edge">South (lat)</label>
              <input
                type="number"
                step="0.001"
                value={bbox.south}
                onChange={(e) => upd("south", parseFloat(e.target.value))}
              />
            </div>
          </div>
          <div className="field-row">
            <div className="field">
              <label data-tip="Western bbox edge">West (lon)</label>
              <input
                type="number"
                step="0.001"
                value={bbox.west}
                onChange={(e) => upd("west", parseFloat(e.target.value))}
              />
            </div>
            <div className="field">
              <label data-tip="Eastern bbox edge">East (lon)</label>
              <input
                type="number"
                step="0.001"
                value={bbox.east}
                onChange={(e) => upd("east", parseFloat(e.target.value))}
              />
            </div>
          </div>
          <div className="note" style={{ margin: "6px 0 4px" }}>
            Hold <strong>Shift</strong> on the map to draw a new bbox.
          </div>
        </div>
      </div>

      {/* ----- 2. RESOLUTION + GRAPH ----- */}
      <div className={`step ${step1}`}>
        <div className="step-head">
          <div className="step-num">2</div>
          <div className="step-title">Vertex resolution</div>
          <div className="step-meta">
            {graph
              ? `→ ${graph.n_vertices} v`
              : mode === "density"
              ? `${hectaresPerVertex} ha/v`
              : `${nVertices} v`}
          </div>
        </div>
        <div className="step-body">
          <div
            className="mode-toggle"
            data-tip="Density: vertex count derived from forest density (recommended). Count: fixed vertex count."
          >
            <button
              className={"mode-opt " + (mode === "density" ? "active" : "")}
              onClick={() => setMode("density")}
            >
              <span className="mode-tag">v2</span>
              Density
              <small>forest ha / vertex</small>
            </button>
            <button
              className={"mode-opt " + (mode === "count" ? "active" : "")}
              onClick={() => setMode("count")}
            >
              <span className="mode-tag">v1</span>
              Count
              <small>fixed count</small>
            </button>
          </div>

          {mode === "density" ? (
            <>
              <div className="field">
                <label data-tip="Each vertex represents this many hectares of forest. Low = fine resolution, many vertices; high = coarse, few vertices.">
                  Forest / vertex
                </label>
                <div className="range-row">
                  <input
                    type="range"
                    min={50}
                    max={2000}
                    step={25}
                    value={hectaresPerVertex}
                    onChange={(e) => setHectaresPerVertex(parseInt(e.target.value))}
                  />
                  <span className="val">{hectaresPerVertex} ha</span>
                </div>
              </div>
              <div className="field">
                <label data-tip="Minimum forest fraction a cell must contain to receive a vertex. Higher = stricter forest mask.">
                  Min forest fraction
                </label>
                <div className="range-row">
                  <input
                    type="range"
                    min={30}
                    max={90}
                    step={5}
                    value={Math.round(minForestFraction * 100)}
                    onChange={(e) =>
                      setMinForestFraction(parseInt(e.target.value) / 100)
                    }
                  />
                  <span className="val">{Math.round(minForestFraction * 100)}%</span>
                </div>
              </div>
            </>
          ) : (
            <div className="field">
              <label data-tip="Target vertex count (legacy v1 behaviour). The threshold may relax if forest cover is insufficient.">
                Target vertices
              </label>
              <div className="range-row">
                <input
                  type="range"
                  min={10}
                  max={150}
                  step={2}
                  value={nVertices}
                  onChange={(e) => setNVertices(parseInt(e.target.value))}
                />
                <span className="val">{nVertices}</span>
              </div>
            </div>
          )}

          <button
            className="primary fire"
            onClick={onBuildGraph}
            disabled={!!busy}
          >
            {buildingGraph ? (
              <>
                <Icon name="spinner" size={13} className="icon-spin" /> Building...
              </>
            ) : (
              <>
                <Icon name="map" size={14} /> Build graph
              </>
            )}
          </button>
          {graph && (
            <div className="bbox-info" style={{ marginTop: 10 }}>
              <strong>{graph.n_vertices}</strong> vertices ·{" "}
              <strong>{graph.n_active_edges}</strong> active ·{" "}
              {graph.n_blocked_edges} blocked
              <br />
              {graph.total_forest_ha != null && (
                <>
                  total forest: <strong>{Math.round(graph.total_forest_ha).toLocaleString()} ha</strong>
                  {graph.hectares_per_vertex != null && (
                    <> · ~{Math.round(graph.hectares_per_vertex)} ha/v</>
                  )}
                  <br />
                </>
              )}
              {graph.settlements.length} settlements · mode: <strong>{graph.mode}</strong>
            </div>
          )}
        </div>
      </div>

      {/* ----- 3. FIRE ORIGIN + k ----- */}
      <div className={`step ${step2}`}>
        <div className="step-head">
          <div className="step-num">3</div>
          <div className="step-title">Fire & budget</div>
          <div className="step-meta">
            {fireOrigin != null && (
              <>
                <Icon name="flame" size={11} style={{ color: "var(--fire)", verticalAlign: "-2px" }} />
                {` v${fireOrigin} · k=${k}`}
              </>
            )}
          </div>
        </div>
        <div className="step-body">
          <div className="field">
            <label data-tip="The vertex where the fire starts. You can also click a vertex in the graph view.">
              Fire origin vertex
            </label>
            <input
              type="number"
              min={0}
              max={(graph?.n_vertices ?? 1) - 1}
              value={fireOrigin ?? 0}
              onChange={(e) => setFireOrigin(parseInt(e.target.value))}
            />
          </div>
          <div className="field">
            <label data-tip="Number of vertices protected per turn (resource budget). Default 2.">
              k (budget / turn)
            </label>
            <div className="range-row">
              <input
                type="range"
                min={1}
                max={6}
                value={k}
                onChange={(e) => setK(parseInt(e.target.value))}
              />
              <span className="val">{k}</span>
            </div>
          </div>
          <button
            className="primary"
            onClick={onSimulate}
            disabled={!!busy || fireOrigin == null}
          >
            {runningSim ? (
              <>
                <Icon name="spinner" size={13} className="icon-spin" /> Running...
              </>
            ) : (
              <>
                <Icon name="rocket" size={14} /> Run all strategies
              </>
            )}
          </button>
        </div>
      </div>

      {/* ----- 4. RESULTS ----- */}
      <div className={`step ${step3}`}>
        <div className="step-head">
          <div className="step-num">4</div>
          <div className="step-title">Results</div>
          <div className="step-meta">
            {sim ? `${sim.results.length} strategies` : "—"}
          </div>
        </div>
        <div className="step-body">
          {sim ? (
            <>
              <div className="bbox-info">
                Best:{" "}
                <strong>{sim.results[0]?.strategy}</strong>
                {" "}— {sim.results[0]?.burned_pct.toFixed(1)}% burned
                <br />
                <span style={{ opacity: 0.7 }}>
                  Worst: {sim.results[sim.results.length - 1]?.strategy}{" "}
                  ({sim.results[sim.results.length - 1]?.burned_pct.toFixed(1)}%)
                </span>
              </div>
              <div className="note">
                Open tab 3 to inspect the table; click <strong>Watch ▶</strong> on
                any row to replay it on the Graph tab.
              </div>
            </>
          ) : (
            <div className="note">
              Run the simulation from step 3 first.
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
