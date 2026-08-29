# REPRODUCTION

Written for a clean machine. No keys required. No data downloads (all
synthetic). Mirrors [docs/05-reproduction.md](docs/05-reproduction.md) and
carries the measured v0 numbers.

| Field | Value |
|---|---|
| Version | 0.1.0 |
| Status | Verified on this repository (see §8) |
| Owner | Prakhar Shukla |
| Last updated | 2026-08-29 |

## 1. Prerequisites
Python 3.12, git, make, Docker (optional). Versions pinned in
`requirements-lock.txt` (compiled with uv; byte-identical installs).

## 2. Setup
```
git clone <repo> && cd signalgate
make install          # pip sync from lock file
make data             # seeded synthetic market + 60 cases (seed=20260828)
```

## 3. Exact commands
```
make baseline         # static lint over all 60 cases -> artifacts/baseline/
make agent            # agent solution; auto-falls back to LOCAL_MOCK without keys
make eval             # scores both, prints comparison table + CIs -> reports/
make serve            # web gate at http://localhost:8000 (LOCAL_MOCK)
make demo-live        # LIVE mode; requires SIGNALGATE_* env keys (optional)
docker build -t signalgate . && docker run -p 8000:8000 signalgate
```

Windows without make: replace `make X` with the `python -m` equivalents in
the [README](README.md) "Windows note" block (`py -3.12`).

## 4. Expected output

`make eval` prints the comparison table (catch rate with Wilson 95% CIs,
false-reject, F2 catch, cost) and writes `reports/metrics.json` +
`reports/comparison.md`. Measured v0 numbers (LOCAL_MOCK, seed 20260828):

| Metric | Baseline (static lint) | Agent solution |
|---|---|---|
| Spurious catch rate (dev, n=40 flawed) | 0.475 | **0.925** (CI [0.801, 0.974]) |
| False-reject rate (n=8 sound, dev) | 0.0 | **0.0** |
| F2 catch (semantic lookahead) | 0.0 | **1.0** |
| Sealed hold-out (n=10 flawed) | 0.5 | **0.9** |
| McNemar p (dev, paired) | - | **0.00029** |

`make serve` → paste any spec from `generator/examples/` → verdict card +
bundle in < 60 s. `make eval-holdout` opens the sealed split (protocol:
twice total - mid-build sanity, final; logged in
[reports/comparison_holdout.md](reports/comparison_holdout.md)).

## 5. Runtime and cost
Eval wall-time ≈ 2-4 min on a laptop. Cost: $0 in LOCAL_MOCK; ≈ $0.03-0.05
per case LIVE (reported from measured spend, breaker-capped at
`SIGNALGATE_SPEND_CAP_USD`, default $2/run).

## 6. Versions
Python 3.12.x, fastapi 0.141.x, pydantic 2.13.x, numpy 2.5.x, pandas 2.3.x
(exact pins in `requirements-lock.txt`). Package version 0.1.0, prompt
version `prompts@v1.0.0`, generator `generator@v1.0.0` - all embedded in
`reports/metrics.json`.

## 7. Troubleshooting
Missing keys → automatic LOCAL_MOCK (mode shown in `/healthz` and the UI
badge). Probe timeout → `PROBE_SKIPPED` disclosed, run continues. Schema
fail → `REJECTED_INVALID` with field-level reasons. `make data` after
changing generator code - `data/` and `artifacts/` are gitignored and
regenerate deterministically from the locked seed.

## 8. Acceptance criteria - verified
A second person completes §2-§4 from a clean environment in < 10 minutes
and reaches the main result. Byte-identity of `reports/metrics.json` across
identical reruns is asserted by `python -m signalgate.eval.repro`
(`make repro-check`), which passes on this repository (62/62 tests green,
including this slow end-to-end check).
