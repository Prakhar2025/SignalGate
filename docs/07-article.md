# Models propose, code decides: building SignalGate, an agent gate for quant signal triage

*Prakhar Shukla · Frontier Engineering Challenge 2026 · August 2026*

Every firm that ingests external trading ideas is about to have the same problem. LLM idea generators, vendor feeds, and paper-mining pipelines now produce candidate signals faster than any review committee can read them, and the failure mode of a bad signal is not a crash. It is a plausible backtest that survives until real money meets real time. This article describes SignalGate, an agent system built in a three-day sprint to sit between that flood and the firm's researchers, and the engineering lessons it produced about making agents reliable when being convincing is not enough.

## The bottleneck, quantified

A typical desk receives around 40 candidate signals a week. A careful manual review, read the spec, rebuild the backtest, hunt for information leakage, costs 60 to 90 minutes. Most candidates are spurious. The math of the review queue is therefore brutal: the firm pays one to two senior hours per rejection, and the rejections are most of the volume.

Static tooling barely helps. A linter catches `shift(-1)`, the syntactic tell of tomorrow's price leaking into today's score. It says nothing about the four failures that actually make backtests lie:

1. **Semantic lookahead.** The formula is clean; the vendor field inside it is not. "Management tone" stamped with the quarter it describes, merged after the fact, is tomorrow's information wearing yesterday's timestamp.
2. **Silent selection.** Forty parameterizations were screened on the same window; the survivor is shipped with no correction. Its in-sample significance is exactly what best-of-40 noise should produce.
3. **Survivorship.** The universe is "today's constituents", so every delisting, which is to say every disaster, is invisible.
4. **Regime overfit and cost amnesia.** Parameters tuned to one bull window, or a strategy whose trading costs exceed its edge, presented at gross.

## The design bet

SignalGate's central decision is a division of labor: **models propose, code decides.** One investigator LLM extracts claims from the submission, surfaces contradictions (a spec whose prose claims point-in-time discipline while its parameters declare a survivor universe), sizes the multiple-testing correction, and later writes the human-readable narrative. It never computes the verdict. The verdict is composed by thresholds in plain Python from the outputs of four deterministic probes, each executed on synthetic data inside a capped subprocess with no network:

- `timestamp_alignment_probe` re-executes the signal leak-proof: every input lagged by its disclosure lag, every forward reference in the program neutralized, the universe restored to point-in-time membership. A real edge survives; a borrowed one collapses. The flagship reject of this benchmark is a prose-lookahead spec whose mean rank-IC falls from +0.475 as written to +0.023 leak-proof.
- `label_permutation_test` builds the honest null by shuffling the score across assets within each day, 199 times, then deflates the p-value for whatever variant count the agent extracted. A best-of-40 winner with raw p 0.015 deflates to 0.45. The hack dies of arithmetic.
- `regime_subsample` reports leak-proof IC per regime with active-day shares, so a signal that only lives above its 200-day mean has to admit it.
- `turnover_and_cost_sanity` prices the positions the signal actually implies at the costs the spec declares, and flags miracles.

The orchestrator law the system inherits from fraud-defense practice holds everywhere: models decide within stages, code decides between stages, and narrative prose is generated last.

## The benchmark, and its guard rail

Evaluating an integrity tool demands cases with known ground truth, which rules out market data; nobody hands a hackathon the labeled set of all traps in CRSP. SignalGate therefore generates its own world: a regime-switching market with exploitable structure deliberately baked in (persistent alpha for momentum, negative autocorrelation for reversion, earnings-drift for surprise signals), ten firms that distress and delist mid-sample, and vendor fields that ship in two variants, the point-in-time series and a forward-restated peek. Sixty cases span five flaw families plus sound templates, 48 for development and 12 held out and opened once.

Self-authored benchmarks are circular by default. The guard is the false-reject rate: ten sound signals with real, regime-stable edge run through the identical pipeline, and rejecting any of them counts against the system as loudly as a miss. Calibration is published beside the results, and the four misses the final system makes are named case by case in the failure taxonomy rather than absorbed into a headline.

## What the numbers say

On the 48-case development split, seed 20260828, everything regenerates byte-identically from one command:

| Metric | Static lint baseline | Agent solution |
|---|---|---|
| Spurious catch rate | 0.475 | **0.925** (95% CI 0.801-0.974) |
| Prose-hidden lookahead (F2) | 0.0 | **1.0** |
| False-reject rate on sound signals | 0.0 | **0.0** |
| Sealed hold-out catch | 0.5 | **0.9** |

McNemar's paired test on the same cases: 20 agent-only correct against 2 baseline-only, p = 0.00029. Human time per task drops from the 60-to-90-minute review to roughly three minutes of evidence reading.

## What the ablation taught

The changelog was executed, not reconstructed. The bare-prompt stage, an agent answering from prose alone with no tools, caught every flawed case and falsely rejected 0.875 of the sound book. It was confident, articulate, and wrong at the exact moment confidence matters. Adding the four probes moved false-rejects to 0.0 at a catch of 0.925. A second narrative agent was measured at +40% token cost for no accuracy gain and removed. The contribution of this system is not the model. It is the verification harness that keeps the model's fluency from being mistaken for an investigation.

## Failure modes, published

The shipped system misses in specific, named ways. A survivor-universe momentum combo passes verification because point-in-time re-execution genuinely does not hurt it; the system calls it PROMISING, which is defensible and disputed, and the dispute is documented. Three marginal cases land in NEEDS_REVIEW instead of REJECT because their signatures sit inside the thresholds. Under a model outage or a tripped spend breaker, the gate drops to lint-only and stamps the verdict DEGRADED rather than improvising. Every degradation path has a test.

## What v1 looks like

The synthetic world is a scaffold, and the scaffold is the point: swap the panel adapter, keep the probes. The v1 roadmap is real panel data with point-in-time vendor fields, factor-crowding and capacity probes, a review-workflow integration where rejected bundles append to the research audit trail, and decay monitoring that re-runs the probes weekly on live paper P&L.

## Takeaways for agent builders

1. Put the verdict in code. A model that scores its own investigation is a model that grades its own homework.
2. Design the honest-failure path first; degraded-and-labeled beats fluent-and-wrong every time.
3. The null hypothesis is a design decision. Get it wrong and every significance number is decoration.
4. Adversarial cases need known ground truth, which means generating them, and the generator needs published calibration.
5. A false-reject guard is what separates a gate from a sieve that happens to be picky.
6. Measure the removed experiments too; the 40% token cost of the deleted agent is part of the system's evidence.
7. Byte-identical regeneration is the cheapest trust you will ever buy.

SignalGate is open source, MIT licensed, reproducible with zero API keys, and its evidence bundles, trajectories, and every number in this article are committed beside the code.

*Repository: github.com/Prakhar2025/SignalGate*
