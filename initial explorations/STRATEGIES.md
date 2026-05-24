# Firefighting Strategy Documentation

This document explains the firefighting simulation and all implemented strategies, including pseudocode and practical characteristics.

## Simulation Model

- Graph: connected planar graph, default size `n = 30`.
- Vertex states:
  - `WHITE`: not burned, not protected
  - `RED`: burned / burning
  - `GREEN`: protected (cannot burn)

## Turn Order

At each turn:

1. Strategy returns candidate WHITE vertices in priority order.
2. Engine protects first `protect_per_turn` vertices (default: `2`).
3. Fire spreads to all WHITE neighbors of RED vertices.
4. Process stops when no WHITE vertex is adjacent to RED.

## Fire Front

The fire front is:

`F = { v | state(v)=WHITE and exists u in N(v) with state(u)=RED }`

Strategies typically rank vertices in `F`; engine applies top-k based on resources.

---

## Implemented Strategies

## 1) `max_degree`

Protect front vertices with largest degree.

```text
function select_vertices(G, state):
    F <- fire_front(G, state)
    sort F by (-degree(v), v)
    return F
```

**Behavior**

- Good at blocking high-connectivity hubs.
- Deterministic and fast.
- May ignore narrow separators with low degree

---

## 2) `max_white_neighbors`

Protect front vertices that still touch many WHITE neighbors.

```text
function white_neighbors(v):
    return count(u in N(v) where state(u)=WHITE)

function select_vertices(G, state):
    F <- fire_front(G, state)
    sort F by (-white_neighbors(v), -degree(v), v)
    return F
```

**Behavior**

- Preserves larger unburned territories.
- Still local/myopic (one-step structure).

---

## 3) `random_front`

Randomly order front vertices.

```text
function select_vertices(G, state):
    F <- list(fire_front(G, state))
    shuffle(F)
    return F
```

**Behavior**

- Baseline for comparison.
- Needs many seeds for stable conclusions.

---

## 4) `min_cut_edge_front`

Min-edge-cut-inspired global barrier strategy.

Idea:

- Build augmented graph with super-source linked to RED set and super-sink linked to WHITE set.
- Compute minimum edge cut between source/sink.
- Prioritize WHITE endpoints of cut edges, especially those on front.

```text
function select_vertices(G, state):
    F <- fire_front(G, state)
    R <- {v : state(v)=RED}
    W <- {v : state(v)=WHITE}
    if F empty or R empty or W empty: return F

    G' <- copy(G)
    add source s, sink t
    connect s to all r in R
    connect all w in W to t

    C_edges <- minimum_edge_cut(G', s, t)

    for each edge (a,b) in C_edges:
        score WHITE endpoints of (a,b)

    preferred <- sort by (-score, -degree, id)
    return (preferred intersect F) + (F minus preferred)
```

**Behavior**

- Uses global connectivity, not only local degree.
- Finds potential “firewall” areas.
- Approximate because game action is vertex protection, while cut is edge-based.

---

## 5) `min_cut_vertex_front`

Min-node-cut-inspired separator strategy.

Idea:

- Select distant WHITE vertices as valuable targets.
- Compute minimum node cut separating RED territory from those targets.
- Prioritize WHITE cut vertices on front.

```text
function select_vertices(G, state):
    F <- fire_front(G, state)
    R <- {v : state(v)=RED}
    W <- {v : state(v)=WHITE}
    if F empty or R empty or W empty: return F

    dist <- shortest-path distance from RED set to all vertices
    T <- top-k farthest WHITE vertices

    G' <- copy(G)
    add source s, sink t
    connect s to all r in R
    connect each z in T to t

    C_nodes <- minimum_node_cut(G', s, t)
    preferred <- WHITE vertices in C_nodes sorted by (-degree, id)

    return (preferred intersect F) + (F minus preferred)
```

**Behavior**

- Better alignment with vertex-protection mechanics.
- Global and more strategic than greedy local methods.
- Sensitive to target selection (`k`, distance criterion).

---

## Complexity (High Level)

- Local heuristics (`max_degree`, `min_degree_front`, `max_white_neighbors`, `random_front`): mostly front extraction + sorting.
- Cut-based heuristics: heavier due to min-cut computations each turn.

Tradeoff: increased computation for potentially better containment decisions.

---

## How To Run

Generate strategy replays:

```bash
cd stop_the_fire && python demo_n30_strategies.py
```

Outputs:

- Step-by-step PNGs in `stop_the_fire/calibration/results/n30_demo/`

Tunable parameters:

- `PROTECT_PER_TURN` in `stop_the_fire/demo_n30_strategies.py`
- `N_VERTICES`, `TARGET_DENSITY`, `GRAPH_SEED`
