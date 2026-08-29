# docs/01-vision.md

| Field | Value |
|---|---|
| Version | 0.1.0 |
| Status | Build-locked for micro1 sprint (Aug 28-31, 2026) |
| Owner | Prakhar Shukla |
| Last updated | 2026-08-28 |

| Version | Change |
|---|---|
| 0.1.0 | Initial lock: doctrine, ladder, disclosure stance |

## 1. Doctrine
Positioning sentence: **research teams don't lack signals, they lack gates. SignalGate sells silence for the research pipeline - spurious signals die with receipts; only signals that deserve a researcher's hour reach a human.**

Three invariants every spurious signal consumes (mirrors Gatehouse doctrine):
1. A definition (code or prose) that smuggles future information or selection bias.
2. A backtest window that hides regime dependence.
3. A cost/turnover assumption that makes miracles look cheap.

SignalGate attacks all three with diagnostic probes, plus a static lint for the cheap syntactic cases.

## 2. Why now
- LLM idea-generators and vendor feeds flood quant pipelines with candidate signals; review committees don't scale.
- The overfitting literature (deflated Sharpe ratio, probability of backtest overfitting) ships as **papers**, not agents. Static linters catch `shift(-1)`; nothing catches lookahead hidden in prose.
- Empty seat: an agentic research-integrity reviewer with a published adversarial benchmark and honest failure taxonomy.

## 3. Definitions of victory
- **Hackathon (this sprint):** agent solution beats static-lint baseline on spurious catch rate at false-reject ≤ 0.05 over a seeded adversarial set; every number regenerates byte-identical from one command; judges run it from a clean environment with zero keys.
- **Company (post-sprint):** expected researcher-hours wasted per spurious signal → near zero for covered flaw families; evidence bundles become the audit artifact prop shops pay for.

## 4. Product ladder
| Release | Scope |
|---|---|
| v0 (this sprint) | CLI + web gate; lint baseline; one investigator agent + 4 probes; eval harness; live demo on Render/Fly |
| v1 | Research-integrity API for prop shops (spec in → evidence bundle out), batch audits |
| v2 | Vendor signal registry + third-party audit reports |
| v3 | Continuous signal-decay monitoring (probes re-run weekly on live P&L proxies) |

The hackathon is P0 validation of a company seed, not a throwaway.

## 5. Lineage and disclosure (rule 02)
Design informed by the builder's prior fraud-defense work (Gatehouse: recommend-never-act, evidence bundles, honest eval discipline). **Zero code imported.** Repo is MIT. Gatehouse proprietary docs never enter this repository.

## 6. Acceptance criteria for this document
Doctrine sentence appears verbatim in README and video cold open. Ladder reviewed at sprint end; v1 scope appended, never silently mutated.
