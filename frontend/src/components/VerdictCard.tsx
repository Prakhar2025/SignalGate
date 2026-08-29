import Link from "next/link";

export interface EvidenceItem {
  probe: string;
  statement: string;
}

export interface InvestigationResult {
  run_id: string;
  verdict: "REJECT_SPURIOUS" | "NEEDS_REVIEW" | "PROMISING" | "REJECTED_INVALID";
  confidence: string;
  reason_codes: string[];
  degraded: boolean;
  findings: EvidenceItem[];
  narrative: string;
  recommended_action: string;
  cost_usd: number;
  elapsed_ms: number;
  bundle?: string;
  error?: string;
}

const TONE: Record<string, { text: string; ring: string; label: string }> = {
  REJECT_SPURIOUS: { text: "text-spurious", ring: "border-spurious/40 bg-spurious/5", label: "REJECT SPURIOUS" },
  NEEDS_REVIEW: { text: "text-review", ring: "border-review/40 bg-review/5", label: "NEEDS REVIEW" },
  PROMISING: { text: "text-signal", ring: "border-signal/40 bg-signal/5", label: "PROMISING" },
  REJECTED_INVALID: { text: "text-spurious", ring: "border-spurious/40 bg-spurious/5", label: "REJECTED INVALID" },
};

export function VerdictCard({ r }: { r: InvestigationResult }) {
  const tone = TONE[r.verdict] ?? TONE.NEEDS_REVIEW;
  return (
    <div className={`overflow-hidden rounded-2xl border bg-surface/80 ${tone.ring}`}>
      {r.degraded && (
        <div className="border-b border-review/20 bg-review/10 px-6 py-2.5 text-sm text-review">
          DEGRADED: verification incomplete (model unavailable or spend breaker).
          Treat this verdict as unverified.
        </div>
      )}
      <div className="p-6 sm:p-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <div className="font-mono text-[11px] uppercase tracking-[0.16em] text-dim">
              verdict card · run {r.run_id}
            </div>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight">
              {r.verdict === "REJECTED_INVALID" ? "Spec rejected by the schema fence" : "Investigation complete"}
            </h2>
          </div>
          <span className={`rounded-lg border px-4 py-2 font-mono text-lg font-bold ${tone.text} ${tone.ring}`}>
            {tone.label}
          </span>
        </div>

        {r.verdict !== "REJECTED_INVALID" && (
          <div className="mt-4 flex flex-wrap gap-2">
            {r.reason_codes.map((c) => (
              <span key={c} className="rounded-md border border-line bg-background/60 px-2 py-1 font-mono text-[11px] text-muted">
                {c}
              </span>
            ))}
            <span className="rounded-md border border-line bg-background/60 px-2 py-1 font-mono text-[11px] text-muted">
              confidence {r.confidence}
            </span>
          </div>
        )}

        {r.error && (
          <p className="mt-4 rounded-lg border border-spurious/30 bg-spurious/5 p-4 font-mono text-xs text-spurious">
            {r.error}
          </p>
        )}

        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          <div>
            <h3 className="text-sm font-semibold text-ink">Findings</h3>
            <ul className="mt-3 space-y-3">
              {r.findings?.map((f) => (
                <li key={f.probe} className="border-l-2 border-line pl-3">
                  <span className="font-mono text-[11px] text-signal">{f.probe}</span>
                  <p className="mt-0.5 text-sm leading-relaxed text-muted">{f.statement}</p>
                </li>
              ))}
              {!r.findings?.length && (
                <li className="text-sm text-dim">No numeric findings. See reason codes.</li>
              )}
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold text-ink">Why this verdict</h3>
            <p className="mt-3 text-sm leading-relaxed text-muted">{r.narrative}</p>
            <div className="mt-5 rounded-lg border border-line bg-background/70 p-4">
              <div className="text-[10px] uppercase tracking-[0.16em] text-dim">Recommended action</div>
              <div className="mt-1 font-mono text-sm font-semibold text-ink">
                {r.recommended_action?.replaceAll("_", " ")}
              </div>
            </div>
            <div className="mt-4 flex flex-wrap gap-4 font-mono text-[11px] text-dim">
              <span>cost ${r.cost_usd?.toFixed(4)}</span>
              <span>{r.elapsed_ms} ms</span>
              {r.bundle && (
                <Link href={r.bundle.replace("/runs/", "/runs/")} className="text-signal underline-offset-4 hover:underline">
                  open bundle →
                </Link>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

