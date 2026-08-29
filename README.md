# SignalGate

**research teams don't lack signals, they lack gates. SignalGate sells silence for the research pipeline - spurious signals die with receipts; only signals that deserve a researcher's hour reach a human.**

SignalGate is an agentic research-integrity gate: candidate trading signals are investigated like fraud cases - statistical probes as tools, verdicts with receipts, silence unless a signal deserves a researcher's hour.

> Disclosure (micro1 ground rule 02): design informed by the builder's prior fraud-defense work (Gatehouse: recommend-never-act, evidence bundles, honest eval discipline). Zero code imported. Repo is MIT.

---

## What it does

A quant team receives dozens of candidate signals a week - from LLM idea generators, vendors, papers. Most are spurious: lookahead hidden in prose or code, p-hacked variant selection, survivorship-flattered universes, regime-overfit parameters, miracle cost assumptions. Manual review costs 60-90 minutes each; static linters catch only `shift(-1)`.

SignalGate investigates each submission:

1. **Static lint** - AST/regex rules over the structured spec (future shifts, survivor universes, disclosed selection counts).
2. **Investigator agent** (one LLM; LOCAL_MOCK for zero-key repro) - extracts claims, flags contradictions, sizes the multiple-testing correction, selects probes.
3. **Four verification probes** on 100% synthetic seeded data, each in a sandboxed subprocess:
   - `timestamp_alignment_probe` - IC collapse under leak-proof re-execution (fields lagged by their disclosure lag + the program's own forward references; universe restricted to point-in-time membership)
   - `label_permutation_test` - permutation p (199 within-day shuffles), Šidák-deflated for hidden variant selection
   - `regime_subsample` - per-regime leak-proof IC + active-day shares
   - `turnover_and_cost_sanity` - implied turnover vs declared costs; miracle flag
4. **Verdict composer** - thresholds in code, never in the model. `REJECT_SPURIOUS` / `NEEDS_REVIEW` / `PROMISING`, each with confidence, reason codes, and the two strongest numeric receipts.
5. **Evidence bundle** - every run persists `bundle.json` / `bundle.md` / `trajectory.json` (agent spans: instruction → tool response → feedback → checkpoint).

Verdicts are advisory. The researcher decides. No execution capability exists anywhere in the tool registry.

## Measured results (v0, LOCAL_MOCK, seed 20260828)

60 seeded cases across six strata (48 dev / 12 sealed hold-out) - generator in [`generator/`](generator/), design in [docs/07-evaluation.md](docs/07-evaluation.md):

| Metric | Baseline (static lint) | Agent solution | Change |
|---|---|---|---|
| Spurious catch rate (dev, 40 flawed) | 0.475 (95% CI [0.325, 0.630]) | **0.925** (95% CI [0.801, 0.974]) | +0.450 |
| - sealed hold-out (10 flawed) | 0.5 | **0.9** | +0.4 |
| F2 catch (prose-hidden lookahead) | 0.0 | **1.0** | +1.0 |
| False-reject rate (sound signals) | 0.0 | **0.0** (bar: ≤ 0.05) | - |
| Human time per task | 60-90 min manual | ~3 min evidence review | -95% |
| Cost per task | $0 | $0.00 mock / ≤$0.05 live (measured spend, breaker-capped) | disclosed |

McNemar paired test on the dev split: agent-only correct 19, baseline-only correct 0 - p = 0.00029. Every number above regenerates byte-identically from `make data && make baseline && make agent && make eval` (asserted by `python -m signalgate.eval.repro` in CI). Full tables with Wilson CIs: [reports/comparison.md](reports/comparison.md), hold-out in [reports/comparison_holdout.md](reports/comparison_holdout.md), stage-by-stage ablation in [reports/ablation.md](reports/ablation.md).

**Improvement changelog (docs/07 §9, actually run)** - baseline lint catch 0.475 with F2 ≈ 0; a bare-prompt agent without verification tools hit catch 1.0 but **falsely rejected 0.875 of sound specs** (hallucinated checks); adding the four probes restored false-reject to 0.0 at catch 0.925 (the main contribution); a second "regime narrative" agent added +40% tokens for no accuracy gain and was removed. Details and receipts: [IMPROVEMENT_CHANGELOG.md](IMPROVEMENT_CHANGELOG.md).

**Honest misses** (failure taxonomy, docs/07 §8): `f3_08` (survivor universe on a momentum combo - the backtest survives point-in-time verification, labeled `PROMISING`; a labeling dispute), `f3_07`/`f5_04`/`f4_06` (marginal signatures → `NEEDS_REVIEW` instead of reject). They become v1 roadmap items, not shame.

## Quickstart (clean machine, zero keys)

```bash
git clone <repo> && cd signalgate
make install          # pip sync from requirements-lock.txt
make data             # seeded synthetic market + 60 cases (seed=20260828)
make eval             # baseline + agent over dev split, comparison table + CIs
make serve            # web gate at http://localhost:8000
```

Windows without make:

```bash
py -3.12 -m pip install -r requirements-lock.txt && py -3.12 -m pip install -e . --no-deps
py -3.12 -m generator.build --out data
py -3.12 -m signalgate.eval.run --system both --split dev --out artifacts/eval
py -3.12 -m signalgate.eval.score --baseline artifacts/eval/baseline --agent artifacts/eval/agent --out reports
py -3.12 -m uvicorn signalgate.api.app:app --port 8000
```

Then paste a spec from `generator/examples/` into the gate - verdict card in < 60 s. Full script: [REPRODUCTION.md](REPRODUCTION.md).

```bash
signalgate check generator/examples/f2_01.yaml   # CLI: verdict card + bundle
signalgate digest                                 # "48 screened. 37 rejected with receipts…"
```

## Architecture (one paragraph)

FastAPI + Jinja2/Tailwind/HTMX (zero node build) + Typer CLI over one deterministic orchestrator: models decide **within** stages, code decides **between** stages; verdicts come from probe numbers and thresholds in `signalgate/orchestrator/thresholds.py`; narrative prose is generated last. Probes run on synthetic data only, in subprocesses with CPU/memory caps and no network. Degradation is tested, not aspirational: model down or spend breaker tripped → lint-only `NEEDS_REVIEW` with a plain `DEGRADED_MODEL` banner; probe timeout → `PROBE_SKIPPED` disclosed; schema fail → reasoned `REJECTED_INVALID`. Full C4 views, probe contracts, and the ground-rule compliance map: [docs/03-architecture.md](docs/03-architecture.md).

## Repository map

```
docs/                      # locked doc set (01 vision · 02 product · 03 architecture
                           #   · 07 evaluation · 10 reproduction · 12 pitch)
src/signalgate/            # lint/ · agent/ · probes/ · orchestrator/ · api/ · ui/ · eval/
generator/                 # seeded market sim + flaw injector + 60 cases + examples/
scripts/routing_ritual.py  # live model-ID verification (honest SKIP without keys)
tests/                     # 62 tests: units, degradation chaos, API contract, byte-identical repro
Makefile · pyproject.toml · Dockerfile · requirements-lock.txt · LICENSE(MIT) · NOTICE
```

## Ground-rule compliance

Synthetic data only (rule 07) · probes sandboxed, no consequential actions (04) · verdicts advisory, human is the qualified reviewer (05) · env-only credentials, `.env` gitignored, `scripts/secret_scan.py` in CI (08) · every claim → an artifact in `reports/` or `artifacts/` (09) · one-command zero-key repro (10) · MIT + dependency licenses in [NOTICE](NOTICE) (03).

## Documentation index

[01-vision](docs/01-vision.md) · [02-product-spec](docs/02-product-spec.md) · [03-architecture](docs/03-architecture.md) · [07-evaluation](docs/07-evaluation.md) · [10-reproduction](docs/10-reproduction.md) · [12-pitch](docs/12-pitch.md)
