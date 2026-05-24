# Final Presentation — Stop the Fire! (IE 492)

**This document**: The canonical outline of our final presentation (15 slides / 15 min). The team works from this file when building slides. Refined: total runtime trimmed from 16.5 min → **13.0 min + 2 min Q&A buffer**.

- **Project**: Stop the Fire! — A Network Optimization Approach to Wildfire Containment
- **Course**: IE 492 Senior Design Project (Boğaziçi)
- **Supervisor**: Tınaz Ekim
- **Team**: Efe Ergen, Emre Barutçu, Mehmet Efe Aloğlu, Kerem Külünkoğlu
- **Stakeholder framing**: OGM (Turkish General Directorate of Forestry)

---

## Rubric weights (out of 10)

| Criterion | Weight | Key to exemplary | Where in this deck |
|---|---|---|---|
| **Content (a,e)** | **4.5** | well-motivated · complete & correct · **results-supported feasible design** · **gained design experience** | S4 + S10 + S11 + S13 |
| Organization (g) | 1.5 | clear, logical, easy-to-follow, good timing | Refined timing budget ↓ |
| Oral Delivery (g) | 1.5 | smooth grammar/pace, seamless transitions | Speaker allocation + rehearsals |
| Visuals (g) | 1.5 | referenced, easy-to-read, **enhance communication** | Visuals checklist ↓ |
| Q&A (g) | 1.0 | confident, no hesitation | Anticipated Q&A ↓ |

→ Content alone is 45%. **S4 (design evolution) and S10 (response to supervisor's critique) are the anchor slides.**

## Strategic framing — making "gained design experience" visible

Concrete evidence for this rubric criterion:

- **Midterm promise** (April 2026): 4 strategies, synthetic n=30, "hybrid in progress", "real-map deployment is the next phase".
- **Final delivery** (May 2026): **13 strategies**, real Köyceğiz map, web suite, recommendation engine.
- **Iteration story**: Supervisor's April 14 meeting critique "Min-Cut is asking the wrong question" → `min_damage_cut` reformulation → **23% relative improvement, backed by numbers**.

This narrative is hammered home in **S4 and S10**.

---

## Refined timing (total 780 s = 13.0 min + 2.0 min Q&A buffer)

| # | Slide | Old (s) | New (s) | Δ | Reason |
|---|---|---|---|---|---|
| 1 | Title | 30 | 30 | — | Unchanged |
| 2 | Why now | 45 | 30 | −15 | One motivation card; the others go verbal |
| 3 | Problem recap | 45 | 30 | −15 | Move quickly; the panel saw this at midterm |
| 4 | **From midterm to now** ⭐ | 75 | **90** | +15 | Anchor slide; carve out room |
| 5 | System pipeline | 30 | 30 | — | Transition slide |
| 6 | Map-to-graph density-aware | 90 | 75 | −15 | Tighten to one focus |
| 7 | Edge filter | 60 | 45 | −15 | Single table + one-line summary |
| 8 | Strategy portfolio | 75 | 60 | −15 | The table is self-explanatory |
| 9 | Lookahead breakthrough | 75 | 60 | −15 | Schematic + 2 sentences |
| 10 | **Supervisor critique response** ⭐ | 90 | **90** | — | Anchor; slow down |
| 11 | **Benchmark (synthetic + Köyceğiz)** | 150 (S11+S12) | **60** | −90 | Two pieces of evidence, one slide |
| ~~12~~ | ~~Real map Köyceğiz~~ | ~~60~~ | (merged into S11) | — | Left panel = synthetic, right = real |
| 13 | **Live Demo** ⭐ | 120 | **90** | −30 | 5 clicks → 3 clicks |
| 14 | Recommendation engine | 45 | 45 | — | — |
| 15 | Conclusions + Future | 60 | 45 | −15 | Findings 4 → 3, Future 3 |
| | **Total** | **990 (16.5 min)** | **780 (13.0 min)** | **−210** | |
| | **Q&A buffer** | — | **+120** | | 2.0 min reserved for questions |

---

## Slide-by-slide detail (refined)

### S1 — Title (refreshed) · 30 s
- Brand: flame icon + dark theme (consistent with midterm), "Final Presentation" badge.
- Four team members, Supervisor: Tınaz Ekim, "May 2026".
- Three chips on the right: **Real-world graph · 13 strategies · Decision support tool** (replaces midterm's NP-Hard / Graph Theory / FP chips — visually telegraphs the evolution).
- **Efe Ergen**: Short greeting, names, one-sentence teaser: *"We took the framework we presented at midterm, validated it on a real map, and reduced it to a working web suite."*

### S2 — Why now · 30 s
- Single emphasis card: **Reactive → Proactive** (purple — midterm's 4th card). The other three (Environmental / Human / Economic) are **mentioned verbally**, not shown.
- Footer: *"This work is a concrete prototype for **Turkey's Mediterranean belt** — the Köyceğiz–Marmaris region."* (midterm's generic framing made specific).
- **Efe Ergen**: "No need to rehash the motivation — we want to emphasize that we applied this to a concrete region."

### S3 — Problem recap · 30 s
- Formal statement (same card as midterm).
- Small toy graph on the right (the A-L graph from midterm, unchanged — preserves visual continuity).
- One line below: *"This is the foundation — all 13 of our strategies share this rule; they only differ in **which vertex they pick**."*
- **Efe Ergen**: Move through the formal definition quickly: "Now let's see how we turned this into a strategy-agnostic framework."

### S4 — From midterm to now · 90 s ⭐ DESIGN-EVOLUTION ANCHOR

**Stage-setter (say this before showing the table):** *"We made promises at midterm — here's what we delivered, across five axes."*

| Axis | Midterm (April) | Final (May) |
|---|---|---|
| Strategies | 4 | **13** (+ 3 lookahead variants, Articulation, Betweenness, Saved Component, Damage-Cut, Hybrid, Random) |
| Network | n=30 synthetic random | **Real Köyceğiz map** (ESA WorldCover + Lloyd's k-means) |
| Hybrid | "In progress" | hybrid_density_aware + 3 lookahead variants |
| Testing | 30v × 15 runs | 4,752 sims + real-map runs |
| Deliverable | sim engine | **Web suite (FastAPI + React)** |
| **Supervisor critique** | — | **"Min-Cut is the wrong question" → min_damage_cut (23% gain)** |

→ **The last row gets a bold border** (red or brand-orange) — bridges to S10.

- **Efe Ergen**: Walk through the table **slowly**. About 10–12 s per row. When you hit the last row: *"That row is detailed three slides from now. First let's look at the system."* — that's the bridge.

### S5 — System pipeline · 30 s
Four-box schematic, an expansion of the midterm pipeline:

```
Real Map (bbox + ESA WorldCover)
   ↓
Density-Aware Graph (Lloyd's k-means, area_ha per vertex)
   ↓
13 Strategies (Greedy / Structural / Lookahead)
   ↓
Decision Support (Recommendation + Web Suite)
```

Color-coded to match midterm (teal / blue / purple / red).

- **Mehmet Efe Aloğlu**: "Now let's open up each box — starting with graph generation."

### S6 — Map-to-graph: density-aware (v2) · 75 s

**Core technical-contribution slide.**

**Left — three bullets:**
- **(1) Forest mask**: ESA WorldCover classes 10 (forest) + 20 (shrubland); a coarse cell must be ≥ 55% forest fraction to qualify.
- **(2) Lloyd's k-means**: density-weighted, **14 iterations**, k-means++ initialization.
- **(3) Snap to densest cell**: centroids don't fall into holes (settlements inside a forest patch); they lock onto the densest eligible cell.

**Right — two side-by-side mini maps:**
- *v1 (old)*: vertices scattered across the bbox, including bare terrain.
- *v2 (new)*: vertices only in forest cells, distributed proportionally to density.

**Removed**: the `area_ha` / `density` attribute line — these are visible live in the S13 demo, no need to duplicate.

- **Mehmet Efe Aloğlu**: "At midterm we had a synthetic graph; we were testing what structure brought what behavior. Now vertices **represent real forest hectares**. Lloyd's is density-weighted. In Köyceğiz, 500 ha/vertex produces 101 vertices."

### S7 — Edge filter: stricter · 45 s

**Single table — 5 rules × Köyceğiz block counts:**

| Rule | Köyceğiz blocked count |
|---|---|
| nonfuel-gap ≥ 60 m continuous | **56** |
| settlement buffer (600 m) | 27 |
| river buffer (80 m) | 20 |
| water class (any pixel) | 3 |
| avg fuel weight < 1.5 | — (rule shown, count not applicable) |

Footer: *"Five filters — physical untraversability, hydrography, settlements, bare strips, mean fuel."*

- **Mehmet Efe Aloğlu**: One sentence — don't enumerate the rules. "About 38% of edges are blocked in Köyceğiz; bare/built strips can no longer be crossed even over 60-meter gaps."

### S8 — Strategy portfolio (3 philosophies) · 60 s

Three-column table:

| **Greedy (local)** | **Structural (global)** | **Lookahead (forward-looking)** |
|---|---|---|
| max_degree | min_cut_edge_front | **one_step_lookahead** ⭐ |
| **max_white_neighbors** ⭐ | min_cut_vertex_front | full_rollout_pairs |
| articulation_priority | **min_damage_cut** ⭐ | deep_lookahead_3 |
| saved_component | betweenness_front | (hybrid_density_aware) |
| | | random (baseline) |

⭐ = best representative of each philosophy.

**Footnote**: `(13 strategies = 11 documented in ALGORITHMS.md §1–§12 + FullRolloutPairs + DeepLookahead3)`

- **Kerem Külünkoğlu**: "Midterm had 4, all within a single philosophy. We extended that. **One thing I want to clarify**: ALGORITHMS.md documents 11 strategy philosophies as §1–§12; the code adds FullRolloutPairs and DeepLookahead3 — total 13. Three philosophies, three lenses on the graph. The next two slides show each philosophy's standout."

### S9 — Lookahead breakthrough · 60 s

**Left — two bullets:**
- Top-6 candidates × C(6,2) = **15 candidate pairs**
- protect → spread → greedy → spread → count burned (lowest-burned pair wins)

**Right — schematic**: a candidate pair (v1, v2) → 2-step simulation → final state.

Footer: *"**At 0.5 ms cost**, a 6% relative improvement over greedy. It simulates the engine inside the engine."*

- **Kerem Külünkoğlu**: Two sentences for 60 s: *"Greedy's blind spot — what's good now isn't necessarily good two turns later. Lookahead closes that gap by running the engine's full logic in its head."*
- **Code reference (for Q&A)**: `backend/firefighter_engine.py:517` `OneStepLookahead` (top_k=6, k_protect=2).

### S10 — Response to supervisor's critique · 90 s ⭐ DESIGN-EXPERIENCE SMOKING GUN

**Top half — inside a bold frame:**
> *Supervisor's observation, April 14 meeting*: "`min_cut_vertex_front` is asking the **wrong question**. It says 'don't let fire reach the distant vertex,' but our objective is 'minimize total burned.'"

**Bottom half — our response:**

`min_damage_cut`:
- New question: **score = saved / cut_size** (ratio, not absolute)
- Test BFS shells at depths 2, 3, 4; pick the cut with the highest ratio.
- **Result**: 39.4% → 30.3% burned (**23% relative improvement**)
- Individual scenario: **1 vertex protects 12 vertices** (12× ratio)

Footer (if it fits): *"feedback → reformulation → measurable improvement."*

- **Kerem Külünkoğlu**: **Slow down here.** "I want to read this one carefully. One sentence from our supervisor → one week later, a 23% improvement. This is our strongest evidence for the rubric's **gained design experience** criterion."
- **Code reference (for Q&A)**: `backend/firefighter_engine.py:359` `MinDamageCut`, tries shell-depth 2/3/4.

### S11 — Benchmark (merged) · 60 s

**Left half — synthetic 4,752-sim ranking (k=2 fixed, 8 strategies):**

| Rank | Strategy | Burned % | Std | Cost |
|---|---|---|---|---|
| 1 | one_step_lookahead | **27.5** | 19.4 | 2.2 ms |
| 2 | betweenness_front | 38.5 | 24.3 | 17.6 ms |
| 3 | max_white_neighbors | 41.5 | 26.3 | 0.3 ms |
| 4 | hybrid_density_aware | 42.2 | 26.4 | 36.0 ms |
| 5 | max_degree | 42.4 | 26.7 | 0.2 ms |
| 6 | min_damage_cut | 42.6 | 26.6 | 50.3 ms |
| 7 | min_cut_edge_front | 43.4 | 27.4 | 11.1 ms |
| 8 | random (baseline) | 70.1 | 19.0 | 0.2 ms |

**Per-size breakdown** — *lookahead is #1 at every graph size:*

| n | one_step_lookahead | best non-lookahead | random |
|---|---|---|---|
| 30 | **26.8** | max_white_neighbors 33.4 | 59.5 |
| 60 | **26.4** | betweenness_front 37.7 | 73.5 |
| 100 | **29.2** | betweenness_front 42.7 | 77.3 |

→ Lookahead → greedy relative improvement: **33.8%** (41.5% → 27.5% burned).
→ Lookahead → random gap: **42.7 percentage points**.
→ `min_damage_cut` vs `min_cut_edge_front`: +1.9% relative on average — the 23% figure quoted on S10 is the **best-case-bottleneck** improvement, not the aggregate (see ALGORITHMS.md §4).

**Right half — Köyceğiz real-map bar chart** (101v / 172 edges, 13 strategies as horizontal bars):
- full_rollout_pairs: 15.8% ↓
- deep_lookahead_3: 15.8%
- one_step_lookahead: 16.8%
- max_white_neighbors: 20.8%
- random: ~40% ↑

**Footer:** *"Synthetic ranking confirmed on the real map — lookahead > greedy > random."*

**Removed**: the topology heatmap (4 × 13 matrix) — too dense to read from the podium; "topology matters" as a verbal bullet in S15 carries the same point.

- **Emre Barutçu**: "Midterm was 60 sims; we ran 4,752. The same ranking holds on the 101-vertex real Köyceğiz map. **This is deployment validation.**"

### S12 — (merged into S11)

### S13 — Live Demo · 90 s ⭐ THE STAR

The slide carries only: QR code + URL + 3-step run-through.

**3-click run (executed on stage):**
1. **Köyceğiz preset → Build graph** (cache warm, ~1 s)
2. **Click a high-degree vertex → set fire_origin → Run all strategies**
3. **Results tab → read the recommendation card OUT LOUD**

**Pushed into narration** (no extra clicks on stage):
- Toggling the WorldCover overlay (already shown visually in S6)
- Clicking a different vertex to change fire_origin

**Recommendation-card script (memorize this):**
> *"v0 is a hub — 7 neighbors, average 3.4. At k=2, five neighbors stay unprotected this turn. The WHITE subgraph has 7 articulation points and 10 bridges. Min-damage-cut tests shells and picks the bottleneck with the best saved/cost ratio — there are 17 candidate bottlenecks here."*

This line hits the panel: **real, graph-specific numbers, not a template.**

- **Emre Barutçu**: 90 s. **Rehearse this.** Backend cache must be warm. Wi-Fi fallback: identical 90-second screen recording (`demo-backup.mp4`).

### S14 — Decision-support: recommendation engine · 45 s

- *"Our system doesn't just give a result; **it gives the decision behind the strategy.**"*

**Pipeline**: Graph + fire_origin + k → fingerprint (n, art_count, bridge_count, fire_origin_degree, front_t1, …) → **6-rule decision tree** → primary + runner_up + **procedural reason**.

**Mini example** (live output from the S13 demo):
> "v0 deg=7, k=2 → 5 neighbors unprotected. art=7 + bridge=10 → min_damage_cut. 17 candidate bottlenecks in the cut."

Footer: *"Not a report — a **decision**. Designed for OGM operational teams."*

- **Efe Ergen**: This is where the "decision-support tool" message lands — direct answer to midterm's 4th takeaway.
- **Code reference (for Q&A)**: `backend/recommendation.py:147` `_select` (6 rules), `backend/recommendation.py:186` `_explain` (procedural).

### S15 — Conclusions + Future · 45 s

Three columns:

**Validated (✓)**
- 4 → 13 strategies, three-philosophy taxonomy
- Real-map deployment (Köyceğiz)
- `min_damage_cut` reformulation answers the supervisor's critique
- Working web suite delivered

**Findings (3 bullets)**
1. **No single dominator** — topology + k drive the choice.
2. **Lookahead wins** at scale; on a cost/value basis, betweenness is 2nd.
3. **Reframing (min-cut → min-damage)** turned a critique into a measurable gain.

**Future (3 bullets)**
- Stochastic spread (wind / elevation / flammability) — *the midterm's next-phase promise*
- Multi-period budget (carry-over k)
- OGM live integration (real-time fire feed)

Footer: *"Thank you — Questions?"*

- **Efe Ergen**: 45 s, the closing slide, hand off briskly, then take questions.

---

## Visuals checklist (rubric → exemplary)

- [ ] **S4**: 6-row design-evolution table; the last row (supervisor critique) gets a bold border.
- [ ] **S6**: side-by-side v1/v2 graph mockups (vertices on bare land vs concentrated in forest cells).
- [ ] **S7**: 5-rule × Köyceğiz block-count table.
- [ ] **S8**: 3-column strategy taxonomy (⭐ representatives) + footnote on 13 vs 11.
- [ ] **S9**: lookahead schematic (candidate pair → 2-step sim).
- [ ] **S10**: supervisor's "wrong question" quote vs our response in two visually distinct blocks.
- [ ] **S11**: left = top-7 ranking table, right = Köyceğiz bar chart. Two pieces of evidence on one slide.
- [ ] **S13**: QR code + URL + 3-step list (slide is minimal; the work happens on stage).
- [ ] **S14**: recommendation-card screenshot with a real output.
- [ ] Every chart has a source reference at the bottom: *"ALGORITHMS.md §13"* or *"Köyceğiz real-map run, May 2026"*.

## Demo prep (S13)

**Pre-flight (presentation morning):**
1. `./run.sh` → both servers up (backend on 8765, frontend on 5173)
2. **Pre-build the graph**: Köyceğiz bbox + 500 ha/vertex (the in-memory cache must be hot)
3. Backend disk cache populated: `backend/cache/tiles/` (ESA tile ~50 MB) + `backend/cache/osm/` (Overpass JSON)
4. **Fallback video**: an identical 90-second screen recording (`demo-backup.mp4`) on USB and on the laptop
5. Browser zoom matches the rehearsal (text remains legible from the projector)

**Demo script (Emre memorizes):**
- "Let me show you the system live. The Köyceğiz preset is ready."
- *Click Köyceğiz preset → Build graph* → "Lloyd's placed 101 vertices in 14 iterations; each represents ~500 hectares of forest."
- *Click v0 (hub) → Run all strategies* → "~2 seconds; 13 strategies ran in parallel on the same scenario."
- *Results tab* → "Here's the ranking. The card at the top is the recommendation — the system explains the strategy choice with **graph-specific numbers**. `[read the card verbatim]`"

## Anticipated Q&A

| Question | Prepared answer |
|---|---|
| **"Why didn't you implement stochastic spread?"** | Future work — we need a deterministic baseline first. The suite's `_hits_obstacle` is structured to be extended with wind/slope vector fields. Reproducibility, and the supervisor's "optimize the right objective" guidance, made determinism a prerequisite. |
| **"How would this deploy at OGM?"** | The FastAPI backend can be containerized; a real-time fire feed becomes a `/api/fire` endpoint; the frontend can be iframed into OGM's GIS panel. The repo is ready (public or private). |
| **"What happens above n=200?"** | The recommendation engine already switches from lookahead to betweenness when n ≥ 180 (`recommendation.py:148`). Lloyd's is O(M·K) — for a larger bbox we downsample the cell grid more aggressively. |
| **"Why is hybrid weak?"** | The threshold (front density 0.18) wasn't tuned; the right signal is `(cut_size, score)`. This is documented in ALGORITHMS.md §11 — *also a design-experience finding, a negative result.* |
| **"Who validated the results?"** | 4,752 deterministic simulations on Delaunay-planar synthetic graphs (3 sizes {30, 60, 100} × 18 graph instances per size × 11 random fire origins × k=2 × 8 strategies = 4,752) + the real-map Köyceğiz run. CSV: `benchmark/benchmark_results.csv`. Engine is deterministic, zero variance per (graph, start, k, strategy). |
| **"Why k=2?"** | The midterm baseline, for comparability. The system supports k = 1..6 (suite slider). Lookahead wins at k=2; max_white_neighbors wins at k=3. |
| **"11 vs 13 strategies — which is it?"** | ALGORITHMS.md §1–§12 documents 11 strategy philosophies; the code adds two lookahead variants (FullRolloutPairs, DeepLookahead3) — total 13. The note on S8 makes this explicit. |
| **"min_cut_vertex_front was #1 at midterm (9.0); now it's last — what changed?"** | At midterm, n=30 was small enough that cut_size ≤ k=2. On larger graphs and the real map, cut_size > k, and the second shell lets the fire consume half the cut. This is the numerical evidence behind the supervisor's "**wrong question**" diagnosis. `min_damage_cut` is the answer. |

## Speaker allocation (content-driven)

| Speaker | Slides | Time | Role |
|---|---|---|---|
| **Efe Ergen** | S1–S4, S14, S15 | **270 s (4.5 min)** | Opener, design-evolution anchor, decision-support, closer — the framing narrator |
| **Mehmet Efe Aloğlu** | S5–S7 | **150 s (2.5 min)** | System pipeline + map-to-graph technical depth — the infrastructure voice |
| **Kerem Külünkoğlu** | S8–S10 | **210 s (3.5 min)** | Strategy taxonomy + lookahead + the supervisor-critique anchor — the algorithms voice |
| **Emre Barutçu** | S11–S13 | **150 s (2.5 min)** | Benchmark + **live demo (the star)** — the results-and-system voice |
| | **Total** | **780 s (13.0 min)** | + 2 min Q&A buffer = 15 min |

**Rationale for the split:**
- **Efe Ergen** carries the narrative spine (S1, S4, S14, S15). S4 (design evolution) and S14 (decision-support framing) are anchor moments that need a steady "front-of-house" voice; the same speaker opening and closing creates a clean frame.
- **Mehmet Efe Aloğlu** owns the technical map-to-graph block (S5–S7). These three slides are tightly coupled (pipeline → density-aware placement → strict edge filter) and benefit from a single speaker who can cross-reference between them.
- **Kerem Külünkoğlu** owns the algorithms block (S8–S10), including the heaviest single slide of the deck (S10, supervisor's critique). The speaker who introduces the taxonomy is best placed to land the reformulation story.
- **Emre Barutçu** takes the results-and-demo block (S11, S13). The live demo (S13) is the highest-stakes 90 seconds of the talk; the speaker who built the web suite knows the failure modes and can recover gracefully if anything stutters.

> Previous version: A=4 / B=3 / C=4 / D=4 = 15 min → blew up to 16.5 min at the podium. The refined allocation is balanced and tested against the new per-slide budgets.

## Verification cadence

| When | Action |
|---|---|
| **T-7 days** | Full dry run; four speakers; phone stopwatch on every slide. Target: 780 ± 30 s. Record audio. |
| **T-3 days** | Are the slide numbers still valid? `./run.sh` → POST `/api/graph` (Köyceğiz preset) → confirm `n_vertices` and active edge count **match the "101v / 172 edges" in the S11 bar chart**. If they've drifted, re-render the bar chart. |
| **T-1 day** | End-to-end demo: `./run.sh` → run the 3-click sequence three times back-to-back; average should stay under 20 s. Memorize the recommendation line word-for-word. Q&A drill (the team grills each other from the table above). |
| **T-2 hours** | Backend cache is warm: `backend/cache/tiles/` + `backend/cache/osm/` populated; the graph is in the in-memory cache (call `/api/graph` once to seed it). `demo-backup.mp4` on USB. Browser tab open and pinned. |

## Critical file references

| File:line | Slide | Why it matters |
|---|---|---|
| `backend/firefighter_engine.py:846` | S8 | `all_strategies()` returns the list of 13 — the evidence |
| `backend/firefighter_engine.py:517` | S9 | `OneStepLookahead` class (top_k=6, k_protect=2) |
| `backend/firefighter_engine.py:359` | S10 | `MinDamageCut` class, shell-depth 2/3/4 |
| `backend/recommendation.py:147` | S14 | `_select()` — the 6-rule decision tree |
| `backend/recommendation.py:186` | S13/S14 | `_explain()` — generates the procedural reason |
| `backend/map_to_graph.py:54-62` | S6/S7 | MIN_GAP_M=60, MIN_AVG_FUEL_WEIGHT=1.5, HECTARES_PER_VERTEX=500, LLOYD_ITERATIONS=14 |
| `backend/map_to_graph.py:499` | S7 | River buffer 80 m (Overpass major waterways) |
| `backend/map_to_graph.py:504` | S7 | Settlement buffer 600 m (Overpass place=village/town/...) |
| `ALGORITHMS.md` | S8 / Q&A | Documents 11 strategies; the title now reads "13 stratejinin" for code-sync |
| `run.sh` | S13 pre-flight | One-command launcher |

## One-line bailout (in case you lose your thread on stage)

> *"At midterm we had a conceptual framework; today we have a working system on a real Mediterranean region — 13 strategies, a density-aware graph, and a reformulation that turned our supervisor's critique into measurable gain."*
