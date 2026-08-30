"use client";

import { useEffect, useState } from "react";
import { VerdictCard, type InvestigationResult } from "@/components/VerdictCard";
import Link from "next/link";

const EXAMPLES = ["s0_01", "f2_01", "f1_01", "f4_01"];

export default function GatePage() {
  const [yaml, setYaml] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<InvestigationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showLive, setShowLive] = useState(false);
  const [live, setLive] = useState<{ model: string; api_base: string; api_key: string }>(
    () => {
      if (typeof window === "undefined") return { model: "", api_base: "", api_key: "" };
      try {
        return JSON.parse(localStorage.getItem("signalgate_live") ?? "") as { model: string; api_base: string; api_key: string };
      } catch {
        return { model: "", api_base: "", api_key: "" };
      }
    }
  );
  const liveOn = Boolean(live.model && live.api_base && live.api_key);

  useEffect(() => {
    fetch("/api/runs?limit=6")
      .then((r) => (r.ok ? r.json() : []))
      .then((rows) => setRecent(rows))
      .catch(() => setRecent([]));
  }, [result]);

  const [recent, setRecent] = useState<
    { run_id: string; name: string; verdict: string }[]
  >([]);

  async function loadExample(name: string) {
    const text = await fetch(`/examples/${name}/raw`).then((r) => r.text());
    setYaml(text);
    setResult(null);
    setError(null);
  }

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/investigate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ spec_yaml: yaml, ...(liveOn ? { live } : {}) }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.error ?? `investigation failed (${res.status})`);
        setResult(null);
      } else {
        setResult(body);
      }
    } catch (e) {
      setError(
        "could not reach the gate API. Start it with: .venv/Scripts/python -m uvicorn signalgate.api.app:app --port 8000"
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-6xl px-6 py-12">
      <div className="grid gap-8 lg:grid-cols-[1fr_340px]">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">The gate</h1>
          <p className="mt-2 max-w-2xl text-sm text-muted">
            Paste a signal spec in YAML (name, description, optional pseudocode,
            params). The investigator extracts claims, runs four probes on
            synthetic data, and returns a verdict with receipts.
          </p>

          <textarea
            value={yaml}
            onChange={(e) => setYaml(e.target.value)}
            spellCheck={false}
            rows={18}
            placeholder={"name: ...\ndescription: |\n  what the signal claims and how it is built\npseudocode: |\n  score = rank(...)\nparams:\n  universe: all\n  horizon: 21\n  costs_bps: 10\n  rebalance: daily"}
            className="mt-6 w-full rounded-xl border border-line bg-surface/70 p-4 font-mono text-[13px] leading-relaxed text-ink outline-none transition-colors focus:border-signal/50"
          />

          <div className="mt-4 flex items-center gap-3">
            <button
              onClick={submit}
              disabled={busy || !yaml.trim()}
              className="glow-signal rounded-lg bg-signal px-5 py-2.5 text-sm font-semibold text-background transition-colors hover:bg-signal-dim disabled:cursor-not-allowed disabled:opacity-40"
            >
              {busy ? "Investigating..." : "Investigate"}
            </button>
            {busy && (
              <span className="font-mono text-xs text-muted">
                lint → claims → 4 probes → composer (about 5 seconds)
              </span>
            )}
          </div>

          {error && (
            <div className="mt-6 rounded-xl border border-spurious/30 bg-spurious/5 p-4 font-mono text-xs text-spurious">
              {error}
            </div>
          )}

          {result && (
            <div className="mt-8">
              <VerdictCard r={result} />
            </div>
          )}
        </div>

        <aside className="space-y-5">
          <div className="rounded-xl border border-line bg-surface/60 p-5">
            <h2 className="text-sm font-semibold">Load an example</h2>
            <div className="mt-3 grid grid-cols-2 gap-2">
              {EXAMPLES.map((name) => (
                <button
                  key={name}
                  onClick={() => loadExample(name)}
                  className="rounded-lg border border-line bg-background/60 px-3 py-2 text-left font-mono text-xs text-signal transition-colors hover:border-signal/40"
                >
                  {name}.yaml
                </button>
              ))}
            </div>
            <ul className="mt-4 space-y-1.5 text-[11px] text-dim">
              <li>s0_01 · sound 12-1 momentum (should pass)</li>
              <li>f2_01 · lookahead hidden in prose</li>
              <li>f1_01 · syntactic shift(-1)</li>
              <li>f4_01 · best-of-40 p-hack</li>
            </ul>
          </div>

          <div className="rounded-xl border border-line bg-surface/60 p-5">
            <button
              onClick={() => setShowLive(!showLive)}
              className="flex w-full items-center justify-between text-sm font-semibold"
            >
              <span>Bring your own model {liveOn && <span className="ml-2 rounded-full bg-signal/15 px-2 py-0.5 font-mono text-[10px] text-signal">LIVE ON</span>}</span>
              <span className="text-dim">{showLive ? "-" : "+"}</span>
            </button>
            {showLive && (
              <div className="mt-3 space-y-2">
                <p className="text-[11px] leading-relaxed text-dim">
                  Optional. The default LOCAL_MOCK needs no keys and reproduces every
                  published number. Paste any OpenAI-compatible endpoint to run the
                  investigator live; the key stays in this browser and is used for
                  the request only. Live verdicts are clearly badged and the spend
                  breaker still caps the run.
                </p>
                <input value={live.model} onChange={(e) => setLive({ ...live, model: e.target.value })}
                  placeholder="model id, e.g. openai/gpt-4o-mini"
                  className="w-full rounded-md border border-line bg-background/70 px-3 py-2 font-mono text-xs outline-none focus:border-signal/50" />
                <input value={live.api_base} onChange={(e) => setLive({ ...live, api_base: e.target.value })}
                  placeholder="api base, e.g. https://api.openai.com/v1"
                  className="w-full rounded-md border border-line bg-background/70 px-3 py-2 font-mono text-xs outline-none focus:border-signal/50" />
                <input value={live.api_key} onChange={(e) => setLive({ ...live, api_key: e.target.value })}
                  type="password" placeholder="api key (kept in this browser only)"
                  className="w-full rounded-md border border-line bg-background/70 px-3 py-2 font-mono text-xs outline-none focus:border-signal/50" />
                <button
                  onClick={() => {
                    localStorage.setItem("signalgate_live", JSON.stringify(live));
                    if (!liveOn) setShowLive(false);
                  }}
                  className="w-full rounded-md border border-signal/40 bg-signal/10 px-3 py-2 font-mono text-xs text-signal hover:bg-signal/20"
                >
                  {liveOn ? "Save live config" : "Save and enable live mode"}
                </button>
              </div>
            )}
          </div>

          <div className="rounded-xl border border-line bg-surface/60 p-5">
            <h2 className="text-sm font-semibold">Recent runs</h2>
            <ul className="mt-3 space-y-2">
              {recent.map((r) => (
                <li key={r.run_id}>
                  <Link
                    href={`/runs/${r.run_id}`}
                    className="group flex items-center justify-between gap-2 rounded-md px-2 py-1.5 transition-colors hover:bg-background/60"
                  >
                    <span className="font-mono text-[11px] text-muted group-hover:text-ink">
                      {r.run_id.slice(0, 10)}
                    </span>
                    <span className="truncate text-xs text-dim">{r.name}</span>
                    <span
                      className={`font-mono text-[10px] ${
                        r.verdict === "PROMISING"
                          ? "text-signal"
                          : r.verdict === "REJECT_SPURIOUS"
                            ? "text-spurious"
                            : "text-review"
                      }`}
                    >
                      {r.verdict === "REJECT_SPURIOUS" ? "REJECT" : r.verdict === "NEEDS_REVIEW" ? "REVIEW" : r.verdict === "PROMISING" ? "PASS" : "INVALID"}
                    </span>
                  </Link>
                </li>
              ))}
              {!recent.length && (
                <li className="text-xs text-dim">
                  No runs yet. Start the API backend and submit a spec.
                </li>
              )}
            </ul>
          </div>

          <div className="rounded-xl border border-line bg-surface/60 p-5 text-[11px] leading-relaxed text-dim">
            Verdicts are advisory. The researcher is the qualified reviewer.
            SignalGate recommends, never trades, and every rejected signal keeps
            its receipts on disk.
          </div>
        </aside>
      </div>
    </div>
  );
}
