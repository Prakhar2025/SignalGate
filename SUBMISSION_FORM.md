# Submission form copy (paste into the HackerEarth form)

## Title

SignalGate: an agentic research-integrity gate for candidate trading signals

## Description

Quant research teams receive dozens of candidate trading signals a week from LLM idea generators, vendor feeds, and papers. Most are spurious: lookahead hidden in prose, silently screened variants, survivorship-flattered universes, regime-overfit parameters, miracle cost assumptions. A manual review costs 60-90 minutes per signal, review committees do not scale, and static linters catch only syntactic tricks like shift(-1). The scarce resource is researcher hours.

SignalGate screens every submission like a fraud case: a static lint baseline, then an investigator agent that extracts claims and flags contradictions, then four deterministic verification probes run on seeded synthetic data (timestamp alignment via leak-proof re-execution, deflated permutation testing, regime subsampling, turnover/cost sanity), and a verdict composer whose thresholds live in code, never in the model. Every run produces REJECT_SPURIOUS / NEEDS_REVIEW / PROMISING with reason codes and the two strongest numeric receipts, plus a persisted evidence bundle and agent trajectory (instruction, tool response, feedback, checkpoint). Verdicts are advisory: the researcher is the qualified reviewer, and no execution capability exists anywhere.

Measured results (60 seeded adversarial cases, 48 dev + 12 sealed holdout, LOCAL_MOCK, seed 20260828, byte-identically reproducible with one command):

- Spurious catch rate: 0.475 (static lint baseline) -> 0.925 (agent solution), Wilson 95% CI 0.801-0.974, McNemar paired p = 0.00029
- The family linters cannot see, prose-hidden lookahead (F2): 0.0 -> 1.0
- False-reject rate on sound signals: 0.0 (bar: 0.05); sealed holdout catch 0.9 at 0.0 false rejects
- Human time per task: 60-90 min manual -> ~3 min evidence review (-95%)

The improvement changelog was actually run, not written after the fact: a bare-prompt agent without verification tools reached catch 1.0 but falsely rejected 0.875 of the sound book (hallucinated checks); adding the four probes restored false-reject to 0.0 at catch 0.925 - that is the main contribution. A second "regime narrative" agent added +40% tokens for no accuracy gain and was removed. Honest misses are named in the failure taxonomy, not hidden.

Agentic disclosure: the repository was built with coding agents (ZCode CLI, GLM 5.3 Flash), and the product's runtime investigator agent runs in two modes - LOCAL_MOCK (deterministic, zero keys; every published number comes from it so judges reproduce the main result with no credentials) and LIVE (any OpenAI-compatible endpoint via env-only config, spend-breaker capped). Agent instructions are version-stamped in src/signalgate/agent/prompts.py and rendered inside every exported trajectory.

Reproduce from a clean environment in 2-4 minutes, zero keys, no data downloads (all synthetic, seed 20260828): make install && make data && make eval && make serve. 62 tests pass including a byte-identical regeneration check. Frontend: cd frontend && npm install && npm start -- -p 3100.

Repo: https://github.com/Prakhar2025/SignalGate (public, same content as the uploaded zip)

Key artifacts in the zip: README.md (user, bottleneck, value, provenance) - IMPROVEMENT_CHANGELOG.md (stages with evidence, failure mode, hot take) - REPRODUCTION.md (clean-machine guide) - SUBMISSION.md (deliverables and 10 ground rules mapped to evidence) - trajectories/ (runtime agent trajectories plus coding-agent session notes) - reports/ (all measured numbers).
