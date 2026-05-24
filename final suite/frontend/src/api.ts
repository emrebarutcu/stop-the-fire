export interface BBox {
  north: number;
  south: number;
  east: number;
  west: number;
}

export interface GraphNode {
  id: number;
  lon: number;
  lat: number;
  area_ha: number;
  density: number;
}
export interface GraphEdge {
  u: number;
  v: number;
}
export interface BlockedReason {
  u: number;
  v: number;
  reason: string;
}

export interface Settlement {
  lon: number;
  lat: number;
  name: string;
  type: string;
}

export type GraphMode = "density" | "count";

export interface GraphResponse {
  graph_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  blocked_edges: GraphEdge[];
  block_reasons: BlockedReason[];
  bbox: BBox;
  settlements: Settlement[];
  raster_classes: Record<string, number>;
  n_vertices: number;
  n_active_edges: number;
  n_blocked_edges: number;
  total_forest_ha: number;
  hectares_per_vertex: number | null;
  mode: GraphMode;
}

export interface BuildGraphReq {
  north: number;
  south: number;
  east: number;
  west: number;
  mode: GraphMode;
  hectares_per_vertex: number;
  min_forest_fraction: number;
  n_vertices: number;
}

export interface TurnFrame {
  turn: number;
  protected: number[];
  burned: number[];
  counts: { white: number; red: number; green: number };
}

export interface SimResult {
  strategy: string;
  n: number;
  burned: number;
  saved: number;
  protected: number;
  turns: number;
  runtime_s: number;
  burned_pct: number;
  frames: TurnFrame[];
  final_state: Record<string, "WHITE" | "RED" | "GREEN">;
  error?: string;
}

export interface SimulateResponse {
  graph_id: string;
  fire_origin: number;
  k: number;
  results: SimResult[];
}

async function post<T>(url: string, body: unknown): Promise<T> {
  const r = await fetch(url, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const text = await r.text();
    throw new Error(`${r.status} ${r.statusText}: ${text}`);
  }
  return r.json();
}

export const api = {
  buildGraph: (req: BuildGraphReq) =>
    post<GraphResponse>("/api/graph", req),
  simulate: (req: { graph_id: string; fire_origin: number; k: number; max_turns?: number }) =>
    post<SimulateResponse>("/api/simulate", { max_turns: 500, ...req }),
};
