# docs/10-reproduction.md

| Field | Value |
|---|---|
| Version | 0.1.0 |
| Status | Build-locked (becomes root REPRODUCTION.md) |
| Owner | Prakhar Shukla |
| Last updated | 2026-08-28 |

Written for a clean machine. No keys required. No data downloads (all synthetic).

## 1. Prerequisites
Python 3.12, git, make, Docker (optional). Versions pinned in `requirements-lock.txt`.

## 2. Setup
```
git clone <repo> && cd signalgate
make install          # uv/pip sync from lock file
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

## 4. Expected output
`make eval` prints the §4 comparison table (catch rate, false-reject, cost, human time) and writes `reports/metrics.json`. `make serve` → paste any spec from `generator/examples/` → verdict card + bundle in < 60 s.

## 5. Runtime and cost
Eval wall-time ≈ 2-4 min on a laptop. Cost: $0 in LOCAL_MOCK; ≈ $0.03-0.05 per case LIVE (reported from measured spend, breaker-capped).

## 6. Versions
Python 3.12.x, fastapi 0.11x, pydantic 2.x, numpy 2.x, pandas 2.x (exact pins in lock). Model IDs + prompt versions embedded in `metrics.json`.

## 7. Troubleshooting
Missing keys → automatic LOCAL_MOCK (banner shown). Probe timeout → `PROBE_SKIPPED` disclosed, run continues. Schema fail → `REJECTED_INVALID` with field reasons.

## 8. Acceptance criteria
A second person completes §2-§4 from a clean environment in < 10 minutes and reaches the main result. Verified once by a fresh clone in CI container before submit.
