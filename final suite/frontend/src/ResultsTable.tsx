import { useMemo, useState } from "react";
import { SimResult, SimulateResponse } from "./api";
import Icon from "./Icon";
import { getMeta, PHILOSOPHY_LABEL } from "./strategy_meta";

interface Props {
  sim: SimulateResponse;
  selectedStrategy: string | null;
  onSelect: (s: string) => void;
}

type SortKey = "rank" | "burned_pct" | "burned" | "protected" | "turns" | "runtime_s" | "strategy";

const COLUMNS: { key: SortKey; label: string; tip?: string; align?: "right" }[] = [
  { key: "rank", label: "#" },
  { key: "strategy", label: "Strategy" },
  { key: "burned_pct", label: "Burned %", tip: "Final RED vertices / total vertices (lower is better)", align: "right" },
  { key: "burned", label: "Burned", tip: "Final RED vertex count", align: "right" },
  { key: "protected", label: "Protected", tip: "Number of vertices held GREEN", align: "right" },
  { key: "turns", label: "Turns", tip: "Number of turns until the fire stops", align: "right" },
  { key: "runtime_s", label: "Runtime", tip: "Strategy + simulation total time", align: "right" },
];

export default function ResultsTable({ sim, selectedStrategy, onSelect }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>("burned_pct");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");

  const { sorted, bestPct, runtimeMax } = useMemo(() => {
    const rows = [...sim.results];
    rows.sort((a, b) => {
      let av: any = (a as any)[sortKey];
      let bv: any = (b as any)[sortKey];
      if (sortKey === "rank") {
        av = a.burned_pct;
        bv = b.burned_pct;
      }
      if (sortKey === "strategy") {
        return sortDir === "asc"
          ? a.strategy.localeCompare(b.strategy)
          : b.strategy.localeCompare(a.strategy);
      }
      av = av ?? 1e9;
      bv = bv ?? 1e9;
      return sortDir === "asc" ? av - bv : bv - av;
    });
    return {
      sorted: rows,
      bestPct: Math.min(...rows.map((r) => r.burned_pct ?? 1e9)),
      runtimeMax: Math.max(0.001, ...rows.map((r) => r.runtime_s ?? 0)),
    };
  }, [sim.results, sortKey, sortDir]);

  const onHeaderClick = (k: SortKey) => {
    if (k === sortKey) setSortDir(sortDir === "asc" ? "desc" : "asc");
    else {
      setSortKey(k);
      setSortDir(k === "strategy" ? "asc" : "asc");
    }
  };

  return (
    <div className="results-table-wrap">
      <div className="results-table-head">
        <h3>All strategies</h3>
        <span className="head-meta">
          {sim.results.length} algorithms · k={sim.k} ·{" "}
          <Icon name="flame" size={11} style={{ color: "var(--fire)", verticalAlign: "-2px" }} />
          {` v${sim.fire_origin}`}
        </span>
      </div>
      <div className="results-table-scroll">
      <table className="results-table">
        <thead>
          <tr>
            {COLUMNS.map((c) => (
              <th
                key={c.key}
                className={sortKey === c.key ? "sorted" : ""}
                onClick={() => onHeaderClick(c.key)}
                data-tip={c.tip}
                style={{ textAlign: c.align ?? "left" }}
              >
                {c.label}
                {sortKey === c.key && (
                  <span className="sort-arrow">{sortDir === "asc" ? "▲" : "▼"}</span>
                )}
              </th>
            ))}
            <th></th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((r, i) => {
            const isBest = (r.burned_pct ?? 1e9) === bestPct;
            const isSel = r.strategy === selectedStrategy;
            const meta = getMeta(r.strategy);
            return (
              <tr
                key={r.strategy}
                className={`${isBest ? "best" : ""} ${isSel ? "selected" : ""}`}
                onClick={() => onSelect(r.strategy)}
                style={{ cursor: "pointer" }}
              >
                <td>{i + 1}</td>
                <td>
                  <span
                    className={`philo-tag ${meta.philosophy}`}
                    data-tip={`${PHILOSOPHY_LABEL[meta.philosophy]} — ${meta.short}`}
                  >
                    {PHILOSOPHY_LABEL[meta.philosophy].slice(0, 3)}
                  </span>
                  {r.strategy}
                  <span className="row-badges">
                    {isBest && (
                      <span className="row-badge best" data-tip="Lowest burned % in this run">
                        Best
                      </span>
                    )}
                  </span>
                </td>
                <td className="num">
                  <span
                    className="bar"
                    data-tip={`${r.burned} / ${r.n} vertices burned`}
                  >
                    <div style={{ width: `${100 * (r.burned_pct ?? 0) / 100}%` }} />
                  </span>
                  {(r.burned_pct ?? 0).toFixed(1)}%
                </td>
                <td className="num">{r.burned} / {r.n}</td>
                <td className="num">{r.protected}</td>
                <td className="num">{r.turns}</td>
                <td className="num" data-tip={`${(r.runtime_s * 1000).toFixed(2)} ms`}>
                  {(r.runtime_s * 1000).toFixed(2)}
                  <span style={{ color: "#94a3b8", fontSize: 10, marginLeft: 2 }}>ms</span>
                </td>
                <td className="row-action" onClick={(e) => e.stopPropagation()}>
                  <button onClick={() => onSelect(r.strategy)}>
                    Watch <Icon name="play" size={10} />
                  </button>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      </div>
    </div>
  );
}
