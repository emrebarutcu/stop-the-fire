# Review packets — IE 492 Final Report

Four PDFs in this directory split the full report into reviewable sections,
balanced so each reviewer carries roughly the same effort. Source:
`../IE492_Final_Report_xelatex.pdf` (34 pages, 4.5 MB).

## Distribution

| Packet | File | Source body pp. | PDF pages in packet | Topic |
|---|---|---|---|---|
| A | `packet_A_front_matter_and_problem_framing.pdf` | 3–9 + 31 | 11 | Front matter, problem framing, References |
| B | `packet_B_methodology_and_strategy_development.pdf` | 10–17 | 11 | Methodology + 8 strategies |
| C | `packet_C_comparison_recommendation_and_test_config.pdf` | 18–23 + 32 | 10 | Numerical study, recommendation, Appendix A |
| D | `packet_D_implementation_conclusions_code_map_and_api.pdf` | 24–30 + 32–33 | 12 | Implementation, conclusions, Appendices B & C |

Body-page load: **A=8, B=8, C=7, D=9** (the spread is 2 pages); PDF-page
load: 11/11/10/12. Each packet starts with the title page + 2-page TOC for
navigation. The non-contiguous pages in A, C, D are added precisely to
equalise load — see the "Why this split" section below.

## Why this split

| Where load goes | Why |
|---|---|
| **References → A** | A reviewer's content (§1, §2) cites [11], [12]. They're best placed to cross-check that every body `[n]` resolves to the References list and vice versa. |
| **Appendix A → C** | Appendix A details the test configuration that produced Table 5.1. Naturally extends §5.1's experimental design. |
| **Appendices B + C → D** | Appendix B is the strategy class–file map; Appendix C is the API table — both extend §6.1 implementation. |

**Note on shared physical pages.** Body p. 32 carries Appendix A (top half)
AND the start of Appendix B (bottom half) on the same physical sheet, so
that page appears in *both* C and D — Packet C's reviewer owns the
Appendix A half, Packet D's reviewer owns the Appendix B half. Similarly,
body p. 31 (References, in Packet A) opens with two paragraphs that are
the tail of §7.3 from the previous page — those paragraphs are out of
Packet A's scope; just skim past them.

---

## Packet A — Front matter, framing & References (~8 body pages)

**Content:** Title page, TOC, English Abstract, Turkish Özet, §1 Introduction, §2 Problem Definition / Requirements / Limitations, References list (full).

**Rubric criteria this packet drives**
- Part A · Organization (0.4)
- Part A · Content (0.6) — outline completeness incl. *Turkish abstract* AND citation/reference integrity
- Part B · Problem Framing (1.0)
- Part B · Non-technical issues (0.5) — §2.4

**Checklist**
- [ ] **Outline compliance.** All items from the outline present: Abstract (Eng + Tur), §1.1–1.5, §2.1–2.7.
- [ ] **Turkish Özet.** Reads naturally; technical terms (İtfaiyeci Problemi, ağ eniyilemesi, en küçük kesim, CBS) are correct; numbers (%27,5 / %70,1 / %16,8) match the English abstract.
- [ ] **Problem framing.** Objective (minimise burned vertices), constraints (k = 2, NP-hard, planar APX-hard) explicit.
- [ ] **Context diagram (Figure 1).** Stakeholder, inputs, outputs, system boundary all clear.
- [ ] **Requirements R1–R7.** Each has a clear "why it matters" justification.
- [ ] **Constraints classified.** Operational / Modelling / Computational / Env-Social-Legal-Ethical / Geopolitical all addressed.
- [ ] **Performance criteria** (§2.7): burned fraction, runtime, variance, explainability.
- [ ] **Improvement directions** prioritised (stochastic spread, settlement weighting, multi-period budget, live integration).
- [ ] **References integrity.** Every body citation `[1]–[12]` in §§1–2 resolves to a References entry; every References entry [1]–[12] has full venue/year/DOI.
- [ ] **Headline numbers cross-check.** Verify the headline numbers in the Abstract (27.5%, 70.1%, 16.8%, 43-point gap, 60% relative, 2 ms / call, k=2, n=101, 50,280 ha, 172 active edges) appear consistently in §1.3 (Expected improvements) — open the master PDF if needed.

**Typos / writing**: highlight any awkward phrasing, undefined acronyms (OGM, ESA, EFFIS, OSM, GIS), missing punctuation.

---

## Packet B — Methodology & Strategy development (~8 body pages)

**Content:** §3 Analysis / Design Methodology (literature, alternatives, assumptions, pipeline, IE skills) and §4 Development of Alternative Solutions (all 8 strategies + Figures 2, 3, 4).

**Rubric criteria this packet drives**
- Part A · Use of visual aids (0.4) — Figures 2, 3, 4
- Part B · Problem Analysis & Method Selection (1.0)
- Part B · Generating & analyzing alternative solutions (1.0)
- Part B · Correct application of selected methods (1.0)

**Checklist**
- [ ] **Literature review (§3.1)** covers Hartnell [1], surveys [2], approximation results [3–6], rollout theory [7]. Citations are IEEE [n] format.
- [ ] **Four alternative approaches (§3.2)** considered: exact IP, RL, pure local greedy, heuristic ensemble. Each has explicit rejection reasoning.
- [ ] **Assumptions (§3.3)** clearly stated: discrete spread, irreversibility, immunity, full observability. Consequences discussed.
- [ ] **Figure 2 (pipeline)** — four-stage flow matches the prose description.
- [ ] **Figure 3 (mechanics)** — turn-by-turn trace is internally consistent (turn 0 → 3, vertices 0–12, k=2 protections per turn).
- [ ] **Figure 4 (philosophies)** — three philosophies labelled correctly; the dashed-ring protections match the philosophy.
- [ ] **8 strategies (§4.2–4.9)** each follow the *find → check → decide* template?
- [ ] **Min Damage Cut (§4.5)** — saved-per-cost ratio explanation clear; the 23% improvement is justified.
- [ ] **One-Step Lookahead (§4.8)** — top-k = 6 cap explained; cost analysis (50 traversals / 2 ms) reasonable.
- [ ] **Random (§4.9)** baseline calibration logic is sound.
- [ ] **§4.10 portfolio table** is consistent with the strategy sections.
- [ ] **IE skills (§3.5)** — every tool listed actually shows up in §4 or §5 (no dangling claims).

---

## Packet C — Comparison, Recommendation & Test config (~7 body pages)

**Content:** §5.1 Numerical study (Table 5.1, Figures 5–8, Köyceğiz case Table 5.2, Figure 9), §5.2 Proposed solution + Limitations + Sensitivity, §5.3 Further assessment, Appendix A (detailed test configuration).

This packet is shorter than A/B/D because *per-page* verification density
is the highest in the report — five figures and two tables packed into six
pages, with most headline numbers appearing in 2–4 places that all have
to agree.

**Rubric criteria this packet drives**
- Part A · Use of visual aids (0.4) — Figures 5, 6, 7, 8, 9; Tables 5.1, 5.2
- Part B · Data analysis & interpretation (0.5)
- Part B · Decision making (1.0)

**Checklist**
- [ ] **Experimental design (§5.1)** — 3 sizes × 18 seeds × 11 starts × 8 strategies = 4,752 runs. Paired-design rationale clear.
- [ ] **Table 5.1** — numbers consistent with the bar chart (Figure 5)? Lookahead 27.5% / random 70.1% appear in both.
- [ ] **Figure 5 (ranking)** — error bars present, philosophy colours legend, all 8 strategies, axis labels.
- [ ] **Figure 6 (cost vs. quality)** — log-scale x-axis, Pareto frontier marked, no overlapping labels.
- [ ] **Figure 7 (distribution)** — boxplot, IQR readable, outliers shown.
- [ ] **Figure 8 (scaling)** — three graph sizes (n = 30, 60, 100), random gap widens with n.
- [ ] **Table 5.2 + Figure 9 (Köyceğiz)** — 16.8% / 19.8% / 31.7% tiers match between table and figure; tie-rankings (2-2, 4-4, 6-6-6) consistent.
- [ ] **Recommendation (§5.2)** — three-strategy ensemble (Lookahead default + Betweenness runner-up + Max White fallback) is justified by data, not by preference.
- [ ] **Limitations** (top-k = 6 cap, rule-based classifier) explicitly stated.
- [ ] **Sensitivity** to k = 1 and k = 3 discussed.
- [ ] **§5.3 further assessment** — consistency with R1–R7, implementability, sustainability, robustness — each addressed.
- [ ] **Appendix A test config** — bbox / area / vertex-density rule / edge counts / fire origin all match the numbers in §5.1 prose and the abstract.
- [ ] **Numerical consistency.** The runtimes in Table 5.1 (2.25, 17.63, 0.25, 36, 0.24, 50.29, 11.10, 0.23 ms) correspond to Figure 6 scatter positions and §4.5/§4.8 cost analyses.

---

## Packet D — Implementation, Conclusions, Code map & API (~9 body pages)

**Content:** §6 Implementation (with Figures 10–13 web suite screenshots), §6.2 Integration, §6.3 Revision cadence, §7 Conclusions (IE tools, merits, economic / environmental / ethical / societal impacts), Appendix B (strategy code map), Appendix C (API endpoints).

**Rubric criteria this packet drives**
- Part A · Use of visual aids (0.4) — Figures 10–13
- Part B · Implementation issues (1.0)
- Part B · Integration of IE techniques/tools (1.0)
- Part B · Non-technical issues (0.5) — §7.3

**Checklist**
- [ ] **§6.1 implementation** — three-click workflow, technology stack (FastAPI/React/Leaflet/Docker/Fly.io) all documented.
- [ ] **Figure 10 (region picker)** — Köyceğiz preset visible, bbox area shown (this figure appears in *Packet C* — refer to it; the reference in §6.1's prose should point to it).
- [ ] **Figure 11 (graph build)** — 101 vertices / 172 active / 106 blocked numbers shown in the screenshot; settlement labels visible.
- [ ] **Figure 12 (results)** — bar chart + sortable table + recommendation card all visible.
- [ ] **Figure 13 (animation)** — final-frame burn pattern is visible; turn counter shows 4/4.
- [ ] **§6.2 integration** — connection to OGM detection layer + secondary integration points listed.
- [ ] **§6.3 revision cadence** — three layers (data annual, strategy doctrinal, classifier failure-driven) explicit.
- [ ] **§7.1 IE tools** — OR + simulation + GIS + remote sensing + software engineering + decision-support design all named.
- [ ] **§7.2 merits** — practical, methodological, educational merits all distinct.
- [ ] **§7.3 impacts** — economic (USD 1.5 B 2021 fires), environmental (15–50 yr regeneration), ethical and societal (settlement weighting trade-off, accountability) each discussed.
- [ ] **Appendix B class–file map** — `MaxDegree.select`, `MaxWhiteNeighbors.select`, …, `OneStepLookahead.select (top_k=6, k_protect=2)`, `HybridDensityAware.select (threshold 0.18)` — every parameter cross-checked against `final suite/backend/firefighter_engine.py`.
- [ ] **Appendix C API endpoints** — `/api/graph`, `/api/simulate`, `/api/recommend`, `/api/strategies`, `/api/health` — verb + body schema match the FastAPI routes in `final suite/backend/main.py`.

---

## Cross-cutting things any reviewer can flag

- **Typos.** Capitalisation of *Köyceğiz, Marmaris, Türkiye, OGM, ESA WorldCover, OpenStreetMap, Leaflet*.
- **Inconsistent numbers.** The headline numbers (27.5%, 70.1%, 16.8%, 31.7%, 43-point gap, 47% relative cut, 4,752 runs, k = 2, n = 101) should be identical everywhere.
- **Inconsistent section refs.** "§3.1" vs "Section 3.1" — both styles appear; flag if jarring.
- **Tense.** Past tense for what was done ("we ran 4,752 simulations"); present for what the tool *does* ("the engine spreads fire to every white neighbour").
- **Figure / table numbering.** 1 context diagram + Figures 2–13 + Tables 5.1, 5.2 — no gaps, no duplicates.

---

When in doubt, defer to the source markdown at `../IE492_Final_Report.md`
and the rendered PDF at `../IE492_Final_Report_xelatex.pdf`. Track findings
either in a shared doc or by writing comments directly into a per-packet
text file in this directory (e.g. `findings_efe.md`, `findings_emre.md`).
