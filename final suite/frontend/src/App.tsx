import { useEffect, useMemo, useState } from "react";
import {
  api,
  BBox,
  GraphMode,
  GraphResponse,
  SimulateResponse,
} from "./api";
import ConfigPanel from "./ConfigPanel";
import GraphView from "./GraphView";
import Icon from "./Icon";
import LoadingOverlay from "./LoadingOverlay";
import MapPicker from "./MapPicker";
import ResultsTable from "./ResultsTable";
import StrategyBarChart from "./StrategyBarChart";

type Tab = "map" | "graph" | "results";

// Defaults match the existing reference script (Köyceğiz–Marmaris).
const DEFAULT_BBOX: BBox = { north: 37.10, south: 36.87, east: 28.66, west: 28.40 };

export default function App() {
  const [bbox, setBbox] = useState<BBox>(DEFAULT_BBOX);
  const [mode, setMode] = useState<GraphMode>("density");
  const [hectaresPerVertex, setHectaresPerVertex] = useState<number>(500);
  const [minForestFraction, setMinForestFraction] = useState<number>(0.55);
  const [nVertices, setNVertices] = useState<number>(40);
  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [fireOrigin, setFireOrigin] = useState<number | null>(null);
  const [k, setK] = useState<number>(2);
  const [sim, setSim] = useState<SimulateResponse | null>(null);

  const [tab, setTab] = useState<Tab>("map");
  const [busy, setBusy] = useState<{ msg: string; sub?: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [selectedStrategy, setSelectedStrategy] = useState<string | null>(null);
  const [currentTurn, setCurrentTurn] = useState<number>(0);
  const [healthy, setHealthy] = useState<boolean>(true);
  // Mobile drawer: below 768 px the sidebar collapses to a slide-in
  // panel. Closed on first paint so a phone user sees the map first; on
  // desktop the toggle button is hidden by CSS and this state is unused.
  const [sidebarOpen, setSidebarOpen] = useState<boolean>(false);

  // ----- backend health probe (cheap; runs every 15 s) -----
  useEffect(() => {
    let alive = true;
    const probe = async () => {
      try {
        const r = await fetch("/api/health");
        if (alive) setHealthy(r.ok);
      } catch {
        if (alive) setHealthy(false);
      }
    };
    probe();
    const t = setInterval(probe, 15000);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, []);

  // ----- step gating: which step is active? -----
  const activeStep = !graph ? 1 : !sim ? 2 : 3;

  const buildGraph = async () => {
    setError(null);
    setBusy({
      msg: "Downloading map & building graph",
      sub: "The ESA WorldCover tile (~50 MB) may take 5–15 s on first download. Subsequent requests come from cache.",
    });
    try {
      const g = await api.buildGraph({
        ...bbox,
        mode,
        hectares_per_vertex: hectaresPerVertex,
        min_forest_fraction: minForestFraction,
        n_vertices: nVertices,
      });
      setGraph(g);
      setSim(null);
      setSelectedStrategy(null);
      setCurrentTurn(0);
      // pick highest-degree vertex as default fire origin (most "interesting" start)
      const deg = new Map<number, number>();
      for (const e of g.edges) {
        deg.set(e.u, (deg.get(e.u) ?? 0) + 1);
        deg.set(e.v, (deg.get(e.v) ?? 0) + 1);
      }
      let best = g.nodes[0]?.id ?? null;
      let bestDeg = -1;
      for (const n of g.nodes) {
        const d = deg.get(n.id) ?? 0;
        if (d > bestDeg) {
          best = n.id;
          bestDeg = d;
        }
      }
      setFireOrigin(best);
      setTab("graph");
      setSidebarOpen(false);   // mobile: close drawer so user sees the graph
    } catch (e: any) {
      setError(e.message ?? String(e));
    } finally {
      setBusy(null);
    }
  };

  const runSimulation = async () => {
    if (!graph || fireOrigin == null) return;
    setError(null);
    setBusy({
      msg: "Running 8 strategies in parallel",
      sub: "Each strategy runs on the same (graph, fire_origin, k); runtime is measured.",
    });
    try {
      const s = await api.simulate({
        graph_id: graph.graph_id,
        fire_origin: fireOrigin,
        k,
      });
      setSim(s);
      // jump to the best-in-run strategy
      setSelectedStrategy(s.results[0]?.strategy ?? null);
      setCurrentTurn(0);
      setTab("results");
      setSidebarOpen(false);   // mobile: close drawer so user sees results
    } catch (e: any) {
      setError(e.message ?? String(e));
    } finally {
      setBusy(null);
    }
  };

  const selectedResult = useMemo(() => {
    if (!sim || !selectedStrategy) return null;
    return sim.results.find((r) => r.strategy === selectedStrategy) ?? null;
  }, [sim, selectedStrategy]);

  return (
    <div className={`app ${sidebarOpen ? "sidebar-open" : ""}`}>
      <aside className="sidebar">
        <div className="hero">
          <div className="logo"><Icon name="flame" size={20} /></div>
          <div>
            <h1>Firefighter Suite</h1>
            <div className="sub">IE 492 — wildfire spread & containment</div>
          </div>
          <div
            className={"health-dot " + (healthy ? "" : "bad")}
            data-tip={healthy ? "Backend is up" : "Backend not responding"}
          />
        </div>

        <ConfigPanel
          bbox={bbox}
          setBbox={setBbox}
          mode={mode}
          setMode={setMode}
          hectaresPerVertex={hectaresPerVertex}
          setHectaresPerVertex={setHectaresPerVertex}
          minForestFraction={minForestFraction}
          setMinForestFraction={setMinForestFraction}
          nVertices={nVertices}
          setNVertices={setNVertices}
          fireOrigin={fireOrigin}
          setFireOrigin={setFireOrigin}
          k={k}
          setK={setK}
          graph={graph}
          sim={sim}
          activeStep={activeStep}
          onBuildGraph={buildGraph}
          onSimulate={runSimulation}
          busy={busy}
          error={error}
        />
      </aside>

      <main className="main">
        <div className="tabs">
          <button
            className="sidebar-toggle"
            onClick={() => setSidebarOpen((o) => !o)}
            aria-label={sidebarOpen ? "Close settings" : "Open settings"}
            data-tip="Settings panel"
          >
            <Icon name={sidebarOpen ? "close" : "menu"} size={18} />
          </button>
          <div
            className={`tab ${tab === "map" ? "active" : ""} ${graph ? "done" : ""}`}
            onClick={() => setTab("map")}
          >
            <span className="tab-dot">1</span>
            Region & bbox
          </div>
          <div
            className={`tab ${tab === "graph" ? "active" : ""} ${sim ? "done" : ""} ${
              !graph ? "disabled" : ""
            }`}
            onClick={() => graph && setTab("graph")}
          >
            <span className="tab-dot">2</span>
            Graph & fire
          </div>
          <div
            className={`tab ${tab === "results" ? "active" : ""} ${!sim ? "disabled" : ""}`}
            onClick={() => sim && setTab("results")}
          >
            <span className="tab-dot">3</span>
            Results
          </div>
          <div className="tabs-spacer" />
          {graph && (
            <div className="tab-status">
              {graph.n_vertices} vertex · {graph.n_active_edges} edge
              {fireOrigin != null && (
                <>
                  {" · "}
                  <Icon name="flame" size={12} style={{ color: "var(--fire)", verticalAlign: "-2px" }} />
                  {` v${fireOrigin}`}
                </>
              )}
              {sim && ` · k=${sim.k}`}
            </div>
          )}
        </div>

        <div className="tab-content">
          {tab === "map" && (
            <MapPicker bbox={bbox} setBbox={setBbox} graph={graph} />
          )}
          {tab === "graph" && graph && (
            <GraphView
              graph={graph}
              fireOrigin={fireOrigin}
              setFireOrigin={setFireOrigin}
              result={selectedResult}
              currentTurn={currentTurn}
              setCurrentTurn={setCurrentTurn}
              selectedStrategy={selectedStrategy}
              setSelectedStrategy={setSelectedStrategy}
              sim={sim}
            />
          )}
          {tab === "graph" && !graph && (
            <div className="empty">
              <div className="ico"><Icon name="map" size={44} /></div>
              <h3>Build a graph first</h3>
              <p>Pick a bbox on tab 1, then click "Build graph" in the sidebar.</p>
            </div>
          )}
          {tab === "results" && sim && (
            <div className="results-wrap">
              <StrategyBarChart
                sim={sim}
                selectedStrategy={selectedStrategy}
                onSelect={(s) => setSelectedStrategy(s)}
              />
              <ResultsTable
                sim={sim}
                selectedStrategy={selectedStrategy}
                onSelect={(s) => {
                  setSelectedStrategy(s);
                  setCurrentTurn(0);
                  setTab("graph");
                }}
              />
            </div>
          )}
          {tab === "results" && !sim && (
            <div className="empty">
              <div className="ico"><Icon name="chart" size={44} /></div>
              <h3>Run the simulation first</h3>
              <p>Pick a fire origin on tab 2, then click "Run all strategies" in the sidebar.</p>
            </div>
          )}
        </div>

        {busy && <LoadingOverlay message={busy.msg} detail={busy.sub} />}
      </main>

      {/* Mobile drawer backdrop — only visible (via CSS) below 768 px
          when the sidebar is open. Click anywhere on it to close. */}
      <div
        className="sidebar-backdrop"
        onClick={() => setSidebarOpen(false)}
        aria-hidden="true"
      />
    </div>
  );
}
