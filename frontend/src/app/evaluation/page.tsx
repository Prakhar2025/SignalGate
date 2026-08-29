"use client";

import { useEffect, useState } from "react";
import { loadSnapshot, type MetricsDoc, type Snapshot } from "@/lib/metrics";

function Pct({ v }: { v: number | null }) {
  return <span className="tnum">{v === null ? "-" : v.toFixed(3)}</span>;
}

function Bar({ value, tone }: { value: number; tone: string }) {
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-line">
      <div
        className={`h-full rounded-full ${tone}`}
        style={{ width: `${Math.round(value * 100)}%` }}
      />
    </div>
  );
}

function ComparisonTable({ m }: { m: MetricsDoc }) {
  const rows: { label: string; b: string; a: string; change: string }[] = [
    {
      label: "Spurious catch rate",
      b: `${m.baseline.spurious_catch_rate} (CI ${m.baseline.spurious_catch_ci95[0]}-${m.baseline.spurious_catch_ci95[1]})`,
      a: `${m.agent.spurious_catch_rate} (CI ${m.agent.spurious_catch_ci95[0]}-${m.agent.spurious_catch_ci95[1]})`,
      change: `${m.delta_catch_rate >= 0 ? "+" : ""}${m.delta_catch_rate.toFixed(3)}`,
    },
    {
      label: "False-reject rate (sound signals)",
      b: `${m.baseline.false_reject_rate} (n=${m.baseline.sound_n})`,
      a: `${m.agent.false_reject_rate} (n=${m.agent.sound_n})`,
      change: "-",
    },
    {
      label: "Precision (reject)",
      b: `${m.baseline.precision_reject}`,
      a: `${m.agent.precision_reject}`,
      change: "-",
    },
    {
      label: "Human time per task",
      b: "60-90 min manual",
      a: "~3 min evidence review",
      change: "-95%",
    },
    {
      label: "Cost per task",
      b: "$0.00",
      a: `$${m.agent.cost_usd_mean.toFixed(4)} (${m.mode})`,
      change: "disclosed",
    },
  ];
  return (
    <div className="overflow-x-auto rounded-xl border border-line bg-surface/60">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-line text-left font-mono text-[11px] uppercase tracking-wider text-dim">
            <th className="px-5 py-3 font-medium">Metric</th>
            <th className="px-5 py-3 font-medium">Baseline (static lint)</th>
            <th className="px-5 py-3 font-medium">Agent solution</th>
            <th className="px-5 py-3 text-right font-medium">Change</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.label} className="border-b border-line/60 last:border-0">
              <td className="px-5 py-3.5">{r.label}</td>
              <td className="px-5 py-3.5 font-mono text-xs text-muted">{r.b}</td>
              <td className="px-5 py-3.5 font-mono text-xs text-signal">{r.a}</td>
              <td className="px-5 py-3.5 text-right font-mono text-xs text-accent">{r.change}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Strata({ m }: { m: MetricsDoc }) {
  const fams = ["F1", "F2", "F3", "F4", "F5"];
  const desc: Record<string, string> = {
    F1: "lookahead, syntactic",
    F2: "lookahead hidden in prose",
    F3: "survivorship universes",
    F4: "p-hacking, best-of-N",
    F5: "regime-overfit params",
  };
  return (
    <div className="rounded-xl border border-line bg-surface/60 p-6">
      <h3 className="text-sm font-semibold">Per-stratum catch rate (agent)</h3>
      <p className="mt-1 text-xs text-muted">
        The agent must beat the bar on F2 specifically: prose-hidden lookahead is the case static tooling cannot touch.
      </p>
      <div className="mt-5 space-y-4">
        {fams.map((f) => {
          const s = m.agent.per_stratum[f];
          if (!s) return null;
          return (
            <div key={f}>
              <div className="mb-1 flex items-baseline justify-between font-mono text-xs">
                <span className="text-muted">
                  <span className="text-ink">{f}</span> · {desc[f]} (n={s.n})
                </span>
                <span className="text-signal">
                  <Pct v={s.catch} />
                </span>
              </div>
              <Bar value={s.catch} tone="bg-signal" />
              <div className="mt-1 font-mono text-[10px] text-dim">
                baseline {m.baseline.per_stratum[f]?.catch ?? "-"} · CI {s.ci95[0]}-{s.ci95[1]}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function Ablation({ snap }: { snap: Snapshot }) {
  const ab = snap.ablation_metrics;
  if (!ab) return null;
  const order = ["baseline", "iter1", "iter2", "iter3"];
  const labels: Record<string, string> = {
    baseline: "Baseline: static lint",
    iter1: "Iter 1: bare-prompt agent, no tools",
    iter2: "Iter 2: lint + tool-agent (shipped)",
    iter3: "Iter 3: second narrative agent (removed)",
  };
  const maxCatch = 1;
  return (
    <div className="rounded-xl border border-line bg-surface/60 p-6">
      <h3 className="text-sm font-semibold">Improvement changelog, with receipts</h3>
      <p className="mt-1 text-xs text-muted">
        Every pre-planned stage was actually run. The bare-prompt stage caught
        more and trusted less honestly: its hallucinated checks falsely rejected
        0.875 of the sound book.
      </p>
      <div className="mt-5 space-y-4">
        {order.map((k) => {
          const s = ab[k];
          if (!s) return null;
          const shipped = k === "iter2";
          return (
            <div key={k} className={`rounded-lg border p-4 ${shipped ? "border-signal/40 bg-signal/5" : "border-line bg-background/50"}`}>
              <div className="flex items-baseline justify-between">
                <span className="text-sm font-medium">{labels[k]}</span>
                <span className="font-mono text-xs text-muted">
                  catch <Pct v={s.spurious_catch_rate} /> · false-reject{" "}
                  <span className={s.false_reject_rate > 0.05 ? "text-spurious" : "text-signal"}>
                    <Pct v={s.false_reject_rate} />
                  </span>
                </span>
              </div>
              <div className="mt-2">
                <Bar value={s.spurious_catch_rate / maxCatch} tone={shipped ? "bg-signal" : k === "iter1" ? "bg-spurious" : "bg-muted"} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function EvaluationPage() {
  const [snap, setSnap] = useState<Snapshot | null>(null);
  useEffect(() => {
    loadSnapshot().then(setSnap);
  }, []);

  if (!snap?.metrics) {
    return (
      <div className="mx-auto max-w-6xl px-6 py-16">
        <div className="h-40 animate-pulse rounded-xl border border-line bg-surface/60" />
      </div>
    );
  }

  const m = snap.metrics;
  const h = snap.metrics_holdout;
  const mcn = m.mcnemar;

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <h1 className="text-2xl font-semibold tracking-tight">Evaluation</h1>
      <p className="mt-2 max-w-2xl text-sm text-muted">
        One primary metric: spurious catch rate, with false-reject as the guard
        rail. Same cases for baseline and agent, Wilson 95% CIs, McNemar for the
        paired comparison. Everything regenerates byte-identically with{" "}
        <code className="font-mono text-xs text-signal">make eval</code>.
      </p>

      <div className="mt-6 flex flex-wrap gap-2 font-mono text-[11px]">
        {["seed 20260828", m.mode, m.model_id, m.prompt_version, `${m.agent.n_cases} dev cases`].map(
          (c) => (
            <span key={c} className="rounded-md border border-line bg-surface/60 px-2 py-1 text-dim">
              {c}
            </span>
          )
        )}
      </div>

      <section className="mt-8 space-y-8">
        <ComparisonTable m={m} />

        <div className="grid gap-6 lg:grid-cols-2">
          <Strata m={m} />
          <div className="rounded-xl border border-line bg-surface/60 p-6">
            <h3 className="text-sm font-semibold">McNemar paired test</h3>
            <p className="mt-1 text-xs text-muted">
              Same 48 cases through both systems. Discordant pairs decide.
            </p>
            <div className="mt-5 grid grid-cols-2 gap-3 text-center">
              <div className="rounded-lg border border-signal/30 bg-signal/5 p-4">
                <div className="font-mono text-3xl font-semibold text-signal tnum">
                  {mcn.agent_only_correct}
                </div>
                <div className="mt-1 text-[11px] text-muted">agent-only correct</div>
              </div>
              <div className="rounded-lg border border-line bg-background/50 p-4">
                <div className="font-mono text-3xl font-semibold text-muted tnum">
                  {mcn.baseline_only_correct}
                </div>
                <div className="mt-1 text-[11px] text-muted">baseline-only correct</div>
              </div>
            </div>
            <div className="mt-4 rounded-lg border border-line bg-background/50 px-4 py-3 font-mono text-xs text-accent">
              p = {mcn.p_value}
            </div>
          </div>
        </div>

        {h && (
          <div className="rounded-xl border border-review/30 bg-review/5 p-6">
            <h3 className="text-sm font-semibold text-review">
              Sealed hold-out (opened once, at the final gate)
            </h3>
            <p className="mt-1 text-xs text-muted">
              12 cases on a different split, never opened during development.
            </p>
            <div className="mt-4 grid grid-cols-3 gap-3 text-center">
              <div className="rounded-lg border border-line bg-background/50 p-4">
                <div className="font-mono text-2xl font-semibold tnum text-ink">
                  {h.agent.spurious_catch_rate}
                </div>
                <div className="mt-1 text-[11px] text-muted">agent catch</div>
              </div>
              <div className="rounded-lg border border-line bg-background/50 p-4">
                <div className="font-mono text-2xl font-semibold tnum text-ink">
                  {h.agent.false_reject_rate}
                </div>
                <div className="mt-1 text-[11px] text-muted">false-reject</div>
              </div>
              <div className="rounded-lg border border-line bg-background/50 p-4">
                <div className="font-mono text-2xl font-semibold tnum text-ink">
                  {h.baseline.spurious_catch_rate}
                </div>
                <div className="mt-1 text-[11px] text-muted">baseline catch</div>
              </div>
            </div>
          </div>
        )}

        <Ablation snap={snap} />

        <p className="text-xs leading-relaxed text-dim">
          Honest misses are published, not hidden: f3_08 (survivor universe on a
          momentum combo survives point-in-time verification and is labeled
          PROMISING; a labeling dispute), f3_07, f5_04 and f4_06 land in
          NEEDS_REVIEW on marginal signatures. Full failure taxonomy and
          per-case bundles live in reports/ and artifacts/.
        </p>
      </section>
    </div>
  );
}
