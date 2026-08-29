"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

interface DigestRecord {
  case_id: string;
  family: string;
  verdict: string;
  reason_codes: string[];
}

interface Digest {
  n: number;
  rejected: number;
  review: number;
  promising: number;
  records: DigestRecord[];
}

const TONE: Record<string, string> = {
  REJECT_SPURIOUS: "text-spurious",
  NEEDS_REVIEW: "text-review",
  PROMISING: "text-signal",
  REJECTED_INVALID: "text-spurious",
};

export default function DigestPage() {
  const [d, setD] = useState<Digest | null>(null);
  const [offline, setOffline] = useState(false);

  useEffect(() => {
    fetch("/api/digest")
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then(setD)
      .catch(() => setOffline(true));
  }, []);

  return (
    <div className="mx-auto max-w-5xl px-6 py-12">
      <h1 className="text-2xl font-semibold tracking-tight">Digest</h1>
      <p className="mt-2 max-w-2xl text-sm text-muted">
        The quiet-pipeline artifact: what a research desk actually receives every
        week. Volume in, receipts attached, human hours spent only where they
        change a decision.
      </p>

      {offline && (
        <div className="mt-8 rounded-xl border border-line bg-surface/60 p-5 text-sm text-muted">
          The gate API is not running, so there is nothing to summarize yet.
          Generate the data with{" "}
          <code className="font-mono text-xs text-signal">make baseline && make agent</code>{" "}
          then start the API, or read the committed{" "}
          <Link href="https://github.com/Prakhar2025/SignalGate/blob/main/reports/digest.md" className="text-signal underline-offset-4 hover:underline">
            reports/digest.md
          </Link>
          .
        </div>
      )}

      {d && (
        <>
          <div className="mt-8 grid grid-cols-3 gap-3">
            {[
              { k: d.rejected, label: "rejected with receipts", cls: "text-spurious" },
              { k: d.review, label: "needed your hour", cls: "text-review" },
              { k: d.promising, label: "promising", cls: "text-signal" },
            ].map((s) => (
              <div key={s.label} className="rounded-xl border border-line bg-surface/60 p-5 text-center">
                <div className={`font-mono text-3xl font-semibold tnum ${s.cls}`}>{s.k}</div>
                <div className="mt-1 text-[11px] text-muted">{s.label}</div>
              </div>
            ))}
          </div>
          <p className="mt-4 font-mono text-xs text-dim">
            {d.n} signals screened through the dev split.
          </p>

          <div className="mt-8 overflow-x-auto rounded-xl border border-line bg-surface/60">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-line text-left font-mono text-[11px] uppercase tracking-wider text-dim">
                  <th className="px-5 py-3 font-medium">Case</th>
                  <th className="px-5 py-3 font-medium">Family</th>
                  <th className="px-5 py-3 font-medium">Verdict</th>
                  <th className="px-5 py-3 font-medium">Reason codes</th>
                </tr>
              </thead>
              <tbody>
                {d.records.map((r) => (
                  <tr key={r.case_id} className="border-b border-line/60 last:border-0">
                    <td className="px-5 py-2.5 font-mono text-xs text-muted">{r.case_id}</td>
                    <td className="px-5 py-2.5 font-mono text-xs text-muted">{r.family}</td>
                    <td className={`px-5 py-2.5 font-mono text-xs ${TONE[r.verdict]}`}>
                      {r.verdict.replace("_", " ")}
                    </td>
                    <td className="px-5 py-2.5 font-mono text-[11px] text-dim">
                      {r.reason_codes.join(", ") || "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  );
}
