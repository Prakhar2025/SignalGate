# IMPROVEMENT_CHANGELOG - SignalGate v0

Format per docs/04 §9. Every stage below was **actually run** over the full
48-case dev split in LOCAL_MOCK mode (seed 20260828); the receipts live in
[reports/ablation.md](reports/ablation.md) and
[reports/ablation_metrics.json](reports/ablation_metrics.json), regenerable
with `make ablation`.

| Version | Change |
|---|---|
| 0.1.0 | Initial build: generator, lint baseline, tool-agent, eval harness, reports |

## Stage table (docs/04 §9)

| Stage | Tried & why | Evidence (measured, dev split) | Decision |
|---|---|---|---|
| Baseline | static lint over the structured spec - the cheap deterministic floor every submission gets for free | catch **0.475**, F2 catch **0.0**, false-reject **0.0**, 0 tokens | starting point; syntax-only reach confirmed |
| Iter 1 | bare-prompt agent, no verification tools - answer from claims alone | catch **1.0**, false-reject **0.875** (35/40 catch + 7/8 sound specs falsely rejected via hallucinated checks: "costs ≤ 10 bps → reject", "weekly rebalance → stale → reject") | **rejected** - confidence without verification is worse than silence |
| Iter 2 | +4 verification probes (timestamp alignment, deflated permutation, regime subsample, turnover sanity); verdict composer thresholds in code | catch **0.925**, false-reject **0.0**, F2 catch **1.0** | **kept - the main contribution**: the tools, not the model, produce the verdicts |
| Iter 3 | second "regime narrative" agent pass on top | catch **0.925** (no gain), est. tokens **+40%** per case | **removed** |
| Final | lint + tool-agent (one LLM, four probe tools) | final table below | main contribution identified: verification tools discipline the model |

## Final measured table (dev split, LOCAL_MOCK, seed 20260828)

| Metric | Baseline (static lint) | Agent solution | Change |
|---|---|---|---|
| Spurious catch rate | 0.475 (CI [0.325, 0.630]) | 0.925 (CI [0.801, 0.974]) | +0.450 |
| Sealed hold-out (12 cases) | 0.5 | 0.9 | +0.4 |
| F2 catch (prose-hidden lookahead) | 0.0 | 1.0 | +1.0 |
| False-reject rate | 0.0 | 0.0 | - |
| Precision (reject) | 1.0 | 1.0 | - |
| Human time per task | 60-90 min manual | ~3 min evidence review | -95% |
| Cost per task | $0 | $0.00 mock / ≤ $0.05 live (breaker-capped) | disclosed |

McNemar paired test (same 48 cases): agent-only correct 20, baseline-only 2 →
p = 0.00029. Wilson 95% CIs on all proportions; per-stratum breakdown in
[reports/comparison.md](reports/comparison.md).

## Failure mode of the final system (required closing)

The shipped system's misses are **marginal-signature cases, not crashes**:
`f3_08` (survivor universe on a momentum combination) is labeled `PROMISING`
because its backtest genuinely survives point-in-time verification - the
universe flaw does not inflate that particular signal (a `labeling_dispute`
in the docs/04 §8 taxonomy); `f3_07`, `f5_04`, `f4_06` land in
`NEEDS_REVIEW` where a reviewer must spend the hour (marginal
`PIT_ONLY_EDGE` deltas, dead bull-only gates, and selection disclosed
without a candidate count, so deflation cannot fire). Counts, per-miss
classification, and receipts: [reports/comparison.md](reports/comparison.md)
and the per-case bundles under `artifacts/`.

The system also degrades honestly under stress (docs/03 §7 chaos tests):
model outage or a tripped spend breaker produces a lint-only `NEEDS_REVIEW`
with a plain `DEGRADED_MODEL` banner; probe timeouts surface as
`PROBE_SKIPPED` in the bundle and can never silently strengthen a verdict.

## Hot take

An agent without verification tools doesn't investigate - it improvises. In
Iter 1 confidence went **up** (catch 1.0!) while the false-reject rate hit
**0.875** - the model invented checks and rejected most of the sound book.
The four probes didn't add evidence; they **disciplined** the model: numbers
over vibes, thresholds in code, silence unless a signal deserves an hour.
The verdict was never the model's to give.

## Protocol note (honest scope)

Iterations 1 and 3 are instantiated in LOCAL_MOCK mode as deterministic
stage simulations of the documented behaviors (claims-only over-rejection;
a duplicated narrative pass metered at +40% tokens), so the pre-planned
protocol could be executed with zero keys and byte-identical receipts. LIVE
mode routes the identical prompt contracts to the configured model
([docs/03 §9](docs/03-architecture.md)); `scripts/routing_ritual.py`
verifies routed model IDs and records honest SKIPs without credentials.
