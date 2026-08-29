"use client";

import dynamic from "next/dynamic";
import Link from "next/link";
import NumbersStrip from "@/components/NumbersStrip";

const SignalField = dynamic(() => import("@/components/SignalField"), {
  ssr: false,
  loading: () => <div className="absolute inset-0 bg-grid" aria-hidden />,
});

const PROBES = [
  {
    name: "timestamp_alignment_probe",
    catches: "Lookahead, syntactic and semantic",
    line: "Re-executes the signal leak-proof: every field lagged by its disclosure lag, the universe restored to point-in-time membership. A real edge survives; a borrowed one collapses.",
    signature: "IC 0.475 → 0.023 under re-execution",
  },
  {
    name: "label_permutation_test",
    catches: "P-hacking, hidden variant selection",
    line: "199 within-day permutations of the score across assets give the honest null. If the submission screened 40 variants and shipped the winner, the p-value is deflated before it counts.",
    signature: "raw p 0.005 → deflated 0.18 at k=40",
  },
  {
    name: "regime_subsample",
    catches: "Regime-overfit parameters",
    line: "Per-regime leak-proof IC with active-day shares. A signal that only lives above its 200-day mean has to say so, and a sign flip across regimes is measured, not guessed.",
    signature: "bull +0.068, bear -0.006, sideways -0.045",
  },
  {
    name: "turnover_and_cost_sanity",
    catches: "Miracle cost assumptions",
    line: "Implied turnover from the positions themselves, priced at the declared costs. A gross Sharpe that dies net of its own trading is reported as the miracle it is.",
    signature: "gross 2.4 → net -1.1 after 5 bps",
  },
];

const VERDICTS = [
  {
    label: "REJECT_SPURIOUS",
    tone: "text-spurious border-spurious/30 bg-spurious/5",
    title: "Management Tone Confidence",
    receipt:
      "Mean rank-IC collapses from +0.475 as-written to +0.023 under leak-proof re-execution (delta +0.452).",
    action: "Archive with receipts. No researcher hour.",
  },
  {
    label: "NEEDS_REVIEW",
    tone: "text-review border-review/30 bg-review/5",
    title: "Quarter-Ahead Confidence Screen",
    receipt:
      "Evidence incomplete: deflated p sits at 0.049 with one probe skipped. This one needs a human hour, honestly spent.",
    action: "Assign a researcher hour, starting from the receipts.",
  },
  {
    label: "PROMISING",
    tone: "text-signal border-signal/30 bg-signal/5",
    title: "Twelve-One Momentum (flagship)",
    receipt:
      "p = 0.005 after deflation, all-regime IC positive, alignment delta 0.000, net Sharpe +1.65. It survives everything we ran.",
    action: "Promote to paper-trade review, receipts attached.",
  },
];

export default function Home() {
  return (
    <div>
      {/* ---------------------------------------------------------- hero */}
      <section className="relative overflow-hidden">
        <SignalField />
        <div className="relative mx-auto max-w-6xl px-6 pb-24 pt-24 sm:pt-32">
          <div className="max-w-2xl">
            <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-line bg-surface/70 px-3 py-1 font-mono text-[11px] text-muted backdrop-blur">
              <span className="pulse-dot inline-block h-1.5 w-1.5 rounded-full bg-signal" />
              agentic research-integrity gate · measured, reproducible, zero keys
            </div>
            <h1 className="text-balance text-4xl font-semibold leading-[1.08] tracking-tight sm:text-6xl">
              Research teams don&apos;t lack signals.
              <span className="block text-signal text-glow">They lack gates.</span>
            </h1>
            <p className="mt-6 max-w-xl text-pretty text-base leading-relaxed text-muted sm:text-lg">
              LLM idea generators and vendors flood quant pipelines with candidate
              signals. Most are spurious: lookahead hidden in prose, p-hacked
              variants, survivorship-flattered universes. SignalGate investigates
              every submission like a fraud case and returns a verdict with
              receipts, so a researcher&apos;s hour goes only to signals that
              deserve it.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <Link
                href="/gate"
                className="glow-signal rounded-lg bg-signal px-5 py-2.5 text-sm font-semibold text-background transition-colors hover:bg-signal-dim"
              >
                Screen a signal
              </Link>
              <Link
                href="/evaluation"
                className="rounded-lg border border-line bg-surface/70 px-5 py-2.5 text-sm font-medium text-ink backdrop-blur transition-colors hover:border-muted"
              >
                See the measured evidence
              </Link>
            </div>
          </div>

          {/* the numbers, exactly as published in reports/metrics.json */}
          <div className="relative mt-16">
            <div className="mb-3 flex items-center justify-between font-mono text-[11px] text-dim">
              <span>measured results · dev split, 48 cases, seed 20260828, LOCAL_MOCK</span>
              <Link href="/evaluation" className="underline decoration-line underline-offset-4 hover:text-muted">
                full tables →
              </Link>
            </div>
            <NumbersStrip />
          </div>
        </div>
      </section>

      {/* ----------------------------------------------------- bottleneck */}
      <section className="mx-auto max-w-6xl px-6 py-20">
        <h2 className="font-mono text-xs uppercase tracking-[0.2em] text-dim">the bottleneck</h2>
        <div className="mt-6 grid gap-4 md:grid-cols-3">
          {[
            {
              k: "40 / week",
              t: "candidate signals arrive",
              d: "From LLM idea generators, vendor feeds, and papers. Review committees do not scale to that volume.",
            },
            {
              k: "60-90 min",
              t: "to review one signal",
              d: "Read the spec, rebuild the backtest, hunt for lookahead. Most reviews end in rejection, and the hour is gone either way.",
            },
            {
              k: "syntax only",
              t: "what linters catch",
              d: "shift(-1) is easy. Lookahead hidden in prose, a universe of survivors, forty screened variants: nothing off the shelf catches those.",
            },
          ].map((c) => (
            <div key={c.t} className="rounded-xl border border-line bg-surface/60 p-6">
              <div className="font-mono text-2xl font-semibold text-signal">{c.k}</div>
              <div className="mt-1 font-medium">{c.t}</div>
              <p className="mt-3 text-sm leading-relaxed text-muted">{c.d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* -------------------------------------------------------- pipeline */}
      <section className="border-y border-line bg-surface/40">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <h2 className="font-mono text-xs uppercase tracking-[0.2em] text-dim">
            one investigation, start to finish
          </h2>
          <p className="mt-4 max-w-2xl text-muted">
            Models decide within stages. Code decides between stages. The verdict
            comes from probe numbers and thresholds written in Python, and the
            narrative is generated last.
          </p>
          <div className="mt-10 grid gap-3 md:grid-cols-5">
            {[
              { n: "01", t: "Schema fence", d: "Untrusted spec enters through validation or dies with field-level reasons." },
              { n: "02", t: "Static lint", d: "AST and regex rules: future shifts, survivor universes, disclosed selection counts." },
              { n: "03", t: "Investigator", d: "One agent extracts claims, flags contradictions, sizes the multiple-testing correction." },
              { n: "04", t: "Four probes", d: "Sandboxed subprocesses on synthetic data: alignment, permutation, regimes, costs." },
              { n: "05", t: "Composer", d: "Thresholds in code produce the verdict. Two strongest receipts. Bundle on disk." },
            ].map((s) => (
              <div key={s.n} className="scan-line relative overflow-hidden rounded-xl border border-line bg-background/60 p-5">
                <div className="font-mono text-xs text-signal">{s.n}</div>
                <div className="mt-2 font-medium">{s.t}</div>
                <p className="mt-2 text-xs leading-relaxed text-muted">{s.d}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------- probes */}
      <section className="mx-auto max-w-6xl px-6 py-20">
        <h2 className="font-mono text-xs uppercase tracking-[0.2em] text-dim">the four probes</h2>
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {PROBES.map((p) => (
            <div key={p.name} className="rounded-xl border border-line bg-surface/60 p-6 transition-colors hover:border-muted">
              <div className="flex items-baseline justify-between gap-3">
                <code className="font-mono text-sm text-signal">{p.name}</code>
                <span className="text-[10px] uppercase tracking-wider text-dim">sandboxed · synthetic only</span>
              </div>
              <div className="mt-2 text-sm font-medium">{p.catches}</div>
              <p className="mt-2 text-sm leading-relaxed text-muted">{p.line}</p>
              <div className="mt-4 rounded-md border border-line bg-background/70 px-3 py-2 font-mono text-[11px] text-accent">
                {p.signature}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ------------------------------------------------------- verdicts */}
      <section className="border-y border-line bg-surface/40">
        <div className="mx-auto max-w-6xl px-6 py-20">
          <h2 className="font-mono text-xs uppercase tracking-[0.2em] text-dim">
            three verdicts, each with receipts
          </h2>
          <div className="mt-6 grid gap-4 md:grid-cols-3">
            {VERDICTS.map((v) => (
              <div key={v.label} className={`rounded-xl border p-6 ${v.tone}`}>
                <div className="font-mono text-xs font-semibold tracking-wide">{v.label}</div>
                <div className="mt-3 font-medium text-ink">{v.title}</div>
                <p className="mt-2 border-l-2 border-current/30 pl-3 text-sm leading-relaxed text-muted">
                  {v.receipt}
                </p>
                <p className="mt-3 text-xs text-dim">{v.action}</p>
              </div>
            ))}
          </div>
          <p className="mt-6 max-w-2xl text-sm text-muted">
            The system does not cry wolf. A genuine signal passes with receipts
            attached, and a rejected one keeps its evidence bundle forever.
            Verdicts are advisory: the researcher is the qualified reviewer.
          </p>
        </div>
      </section>

      {/* ------------------------------------------------------------- cta */}
      <section className="mx-auto max-w-6xl px-6 py-24 text-center">
        <h2 className="text-balance text-3xl font-semibold tracking-tight">
          Silence for the research pipeline.
        </h2>
        <p className="mx-auto mt-4 max-w-xl text-muted">
          Spurious signals die with receipts. Only signals that deserve a
          researcher&apos;s hour reach a human.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Link
            href="/gate"
            className="glow-signal rounded-lg bg-signal px-6 py-3 text-sm font-semibold text-background transition-colors hover:bg-signal-dim"
          >
            Run the gate
          </Link>
          <Link
            href="/evaluation"
            className="rounded-lg border border-line px-6 py-3 text-sm font-medium text-ink transition-colors hover:border-muted"
          >
            Read the evidence
          </Link>
        </div>
      </section>
    </div>
  );
}
