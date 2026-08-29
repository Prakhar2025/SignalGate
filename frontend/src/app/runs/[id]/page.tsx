"use client";

import { use, useEffect, useState } from "react";
import { VerdictCard, type EvidenceItem } from "@/components/VerdictCard";

interface Bundle {
  run_id: string;
  spec: { name: string; description: string; pseudocode: string | null; params: Record<string, unknown>; notes?: string | null };
  claims: { text: string; kind: string; evidence_span: string }[];
  probe_results: {
    probe: string;
    ok: boolean;
    skipped: boolean;
    skip_reason: string;
    metrics: Record<string, string | number | boolean>;
    detail: Record<string, unknown>;
  }[];
  verdict: string;
  confidence: string;
  reason_codes: string[];
  degraded: boolean;
  narrative: string;
  findings?: EvidenceItem[];
  recommended_action: string;
  cost_usd: number;
  elapsed_ms: number;
  mode: string;
  model_id: string;
  prompt_version: string;
  seed: number;
  spans: { ts: string; stage: string; event: string; [k: string]: unknown }[];
}

export default function RunPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const [b, setB] = useState<Bundle | null>(null);
  const [err, setErr] = useState(false);

  useEffect(() => {
    fetch(`/runs/${id}/bundle.json`)
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setB)
      .catch(() => setErr(true));
  }, [id]);

  if (err) {
    return (
      <div className="mx-auto max-w-4xl px-6 py-20 text-center text-muted">
        Bundle <code className="font-mono text-signal">{id}</code> not found. It
        lives on the machine that ran the investigation.
      </div>
    );
  }
  if (!b) {
    return <div className="mx-auto max-w-4xl px-6 py-20 text-muted">Loading bundle...</div>;
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-12">
      <div className="flex items-center justify-between">
        <h1 className="font-mono text-sm text-muted">
          evidence bundle · <span className="text-ink">{b.run_id}</span>
        </h1>
        <a
          href={`/runs/${b.run_id}/bundle.md`}
          className="font-mono text-xs text-signal underline-offset-4 hover:underline"
        >
          bundle.md →
        </a>
      </div>

      <div className="mt-6">
        <VerdictCard
          r={{
            run_id: b.run_id,
            verdict: b.verdict as never,
            confidence: b.confidence,
            reason_codes: b.reason_codes,
            degraded: b.degraded,
            findings: b.findings ?? [],
            narrative: b.narrative,
            recommended_action: b.recommended_action,
            cost_usd: b.cost_usd,
            elapsed_ms: b.elapsed_ms,
          }}
        />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <section className="rounded-xl border border-line bg-surface/60 p-6">
          <h2 className="text-sm font-semibold">What came in</h2>
          <p className="mt-2 text-sm leading-relaxed text-muted">{b.spec.description}</p>
          {b.spec.pseudocode && (
            <pre className="mt-3 overflow-x-auto rounded-lg border border-line bg-background/70 p-3 font-mono text-[11px] text-accent">
              {b.spec.pseudocode}
            </pre>
          )}
          {b.spec.notes && (
            <p className="mt-3 rounded-lg border border-line bg-background/50 p-3 text-xs text-muted">
              notes: {b.spec.notes}
            </p>
          )}
          <h2 className="mt-6 text-sm font-semibold">Claims extracted</h2>
          <ul className="mt-2 space-y-2">
            {b.claims.map((c, i) => (
              <li key={i} className="text-xs text-muted">
                <span className="font-mono text-[10px] text-dim">[{c.kind}]</span> {c.text}
              </li>
            ))}
            {!b.claims.length && <li className="text-xs text-dim">none</li>}
          </ul>
        </section>

        <section className="rounded-xl border border-line bg-surface/60 p-6">
          <h2 className="text-sm font-semibold">Probe numbers</h2>
          <div className="mt-3 space-y-3">
            {b.probe_results.map((p) => (
              <div key={p.probe} className="rounded-lg border border-line bg-background/50 p-3">
                <div className="font-mono text-xs text-signal">{p.probe}</div>
                {p.skipped ? (
                  <div className="mt-1 font-mono text-[11px] text-review">
                    SKIPPED: {p.skip_reason}
                  </div>
                ) : (
                  <dl className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 font-mono text-[11px] text-muted">
                    {Object.entries(p.metrics).map(([k, v]) => (
                      <div key={k} className="flex justify-between gap-2">
                        <dt className="truncate text-dim">{k}</dt>
                        <dd className="text-ink">{String(v)}</dd>
                      </div>
                    ))}
                  </dl>
                )}
              </div>
            ))}
          </div>
        </section>
      </div>

      <section className="mt-6 rounded-xl border border-line bg-surface/60 p-6">
        <h2 className="text-sm font-semibold">Trajectory</h2>
        <p className="mt-1 text-xs text-muted">
          {b.spans.length} spans: instruction to tool response to feedback to
          checkpoint. Mode {b.mode}, model {b.model_id}, prompt {b.prompt_version},
          seed {b.seed}.
        </p>
        <div className="mt-3 max-h-72 space-y-1 overflow-auto rounded-lg border border-line bg-background/60 p-3 font-mono text-[11px]">
          {b.spans.map((s, i) => (
            <div key={i} className="flex gap-3">
              <span className="text-dim">{String(s.ts).slice(11, 19)}</span>
              <span className="w-24 shrink-0 text-signal">{String(s.stage)}</span>
              <span className="w-28 shrink-0 text-accent">{String(s.event)}</span>
              <span className="truncate text-muted">
                {Object.entries(s)
                  .filter(([k]) => !["ts", "stage", "event"].includes(k))
                  .slice(0, 2)
                  .map(([k, v]) => `${k}=${String(v).slice(0, 60)}`)
                  .join(" ")}
              </span>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
