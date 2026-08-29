"use client";

import { useEffect, useRef, useState } from "react";
import { loadSnapshot, type MetricsDoc } from "@/lib/metrics";

function CountUp({ value, decimals = 3, duration = 900 }: { value: number; decimals?: number; duration?: number }) {
  const [shown, setShown] = useState(0);
  const start = useRef<number | null>(null);
  useEffect(() => {
    let raf = 0;
    const tick = (ts: number) => {
      if (start.current === null) start.current = ts;
      const p = Math.min(1, (ts - start.current) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      setShown(value * eased);
      if (p < 1) raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [value, duration]);
  return <span className="tnum">{shown.toFixed(decimals)}</span>;
}

function Stat({
  label,
  agent,
  baseline,
  accent,
  decimals = 3,
  note,
}: {
  label: string;
  agent: number | null;
  baseline?: number | null;
  accent: string;
  decimals?: number;
  note: string;
}) {
  return (
    <div className="rounded-xl border border-line bg-surface/80 p-5">
      <div className="text-[11px] font-medium uppercase tracking-[0.14em] text-dim">{label}</div>
      <div className={`mt-2 font-mono text-3xl font-semibold ${accent}`}>
        {agent === null ? "-" : <CountUp value={agent} decimals={decimals} />}
      </div>
      <div className="mt-1 font-mono text-[11px] text-muted">
        {baseline !== undefined && baseline !== null ? `baseline ${baseline.toFixed(decimals)} · ` : ""}
        {note}
      </div>
    </div>
  );
}

export default function NumbersStrip() {
  const [dev, setDev] = useState<MetricsDoc | null>(null);
  const [hold, setHold] = useState<MetricsDoc | null>(null);

  useEffect(() => {
    loadSnapshot().then((s) => {
      setDev(s.metrics ?? null);
      setHold(s.metrics_holdout ?? null);
    });
  }, []);

  if (!dev) {
    return (
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {["catch rate", "false rejects", "semantic catch", "hold-out"].map((l) => (
          <div key={l} className="h-[104px] animate-pulse rounded-xl border border-line bg-surface/60" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <Stat
        label="Spurious catch rate"
        agent={dev.agent.spurious_catch_rate}
        baseline={dev.baseline.spurious_catch_rate}
        accent="text-signal"
        note={`CI ${dev.agent.spurious_catch_ci95[0]}-${dev.agent.spurious_catch_ci95[1]}, n=${dev.agent.n_cases - 8} flawed`}
      />
      <Stat
        label="False-reject rate"
        agent={dev.agent.false_reject_rate}
        accent="text-accent"
        note={`sound signals kept honest, n=${dev.agent.sound_n}`}
      />
      <Stat
        label="Prose-lookahead catch (F2)"
        agent={dev.agent.per_stratum["F2"]?.catch ?? null}
        baseline={dev.baseline.per_stratum["F2"]?.catch ?? 0}
        accent="text-signal"
        note="the family linters cannot see"
      />
      <Stat
        label="Sealed hold-out catch"
        agent={hold?.agent.spurious_catch_rate ?? null}
        accent="text-review"
        decimals={2}
        note={`opened once, n=${hold?.agent.n_cases ?? 0} cases`}
      />
    </div>
  );
}
