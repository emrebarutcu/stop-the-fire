import { SimulateResponse } from "./api";
import { getMeta, PHILOSOPHY_LABEL } from "./strategy_meta";

interface Props {
  sim: SimulateResponse;
  selectedStrategy: string | null;
  onSelect: (name: string) => void;
}

export default function StrategyBarChart({
  sim,
  selectedStrategy,
  onSelect,
}: Props) {
  const max = Math.max(1, ...sim.results.map((r) => r.burned_pct ?? 0));
  const bestPct = Math.min(...sim.results.map((r) => r.burned_pct ?? 1e9));

  return (
    <div className="chart-card">
      <h3>
        Strategy comparison{" "}
        <span style={{ fontWeight: 400, fontSize: 12, color: "#94a3b8" }}>
          — burned % (lower is better)
        </span>
      </h3>
      <div>
        {sim.results.map((r) => {
          const meta = getMeta(r.strategy);
          const isBest = (r.burned_pct ?? 1e9) === bestPct;
          const isSel = selectedStrategy === r.strategy;
          return (
            <div
              key={r.strategy}
              className={`chart-row ${isSel ? "selected" : ""} ${isBest ? "best" : ""}`}
              onClick={() => onSelect(r.strategy)}
              style={{ cursor: "pointer" }}
              data-tip={meta.short}
            >
              <div className="lbl">
                <span className={`philo-tag ${meta.philosophy}`}>
                  {PHILOSOPHY_LABEL[meta.philosophy].slice(0, 3)}
                </span>
                {r.strategy}
              </div>
              <div className="track">
                <div
                  style={{
                    width: `${(100 * (r.burned_pct ?? 0)) / max}%`,
                  }}
                />
              </div>
              <div className="pct">{(r.burned_pct ?? 0).toFixed(1)}%</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
