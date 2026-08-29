# SignalGate - Documentation Index

| Field | Value |
|---|---|
| Owner | Prakhar Shukla |
| Status | Build-locked set for micro1 sprint (Aug 28-31, 2026) |
| Companion docs (repo root) | `README.md` · `IMPROVEMENT_CHANGELOG.md` · `REPRODUCTION.md` |

## Reading order (hand-off sequence for the coding agent)

| # | Doc | Role |
|---|---|---|
| 1 | [01-vision.md](01-vision.md) | Doctrine, definitions of victory, product ladder, disclosure stance |
| 2 | [02-product-spec.md](02-product-spec.md) | Product definition, journeys, feature set v1, acceptance criteria |
| 3 | [03-architecture.md](03-architecture.md) | Stack, C4 views, orchestrator law, probe contracts, degradation matrix, compliance map |
| 4 | [07-evaluation.md](07-evaluation.md) | Dataset design, metrics, statistical honesty, regression gates, failure taxonomy, changelog protocol |
| 5 | [10-reproduction.md](10-reproduction.md) | Clean-machine repro script (mirrored at root `REPRODUCTION.md`) |
| 6 | [12-pitch.md](12-pitch.md) | Video script, shot list, rules register, deliverables checklist |

## Repo shape

```
signalgate/
├── docs/                    # this locked set
├── src/signalgate/          # package: lint/, agent/, probes/, orchestrator/, api/, ui/, eval/
├── generator/               # seeded synthetic market + flaw injector
├── scripts/routing_ritual.py
├── tests/
├── Makefile · pyproject.toml · Dockerfile · requirements-lock.txt
├── README.md · IMPROVEMENT_CHANGELOG.md · REPRODUCTION.md
```

## Change protocol
Docs are build-locked. Fixes append to the changelog table in each doc header; v1 scope is appended, never silently mutated (01 §6).
