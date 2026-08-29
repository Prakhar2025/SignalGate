# docs/02-product-spec.md

| Field | Value |
|---|---|
| Version | 0.1.0 |
| Status | Build-locked |
| Owner | Prakhar Shukla |
| Depends on | 01-vision |
| Last updated | 2026-08-28 |

## 1. Product definition
One sentence: SignalGate screens every candidate trading signal a research team receives, investigates it like a fraud case with statistical probes, and asks a human researcher to look only at what genuinely deserves an hour.

Two surfaces: **Web gate** (server-rendered product UI) and **CLI** (research-pipeline native). Both call the same orchestrator.

## 2. Core concepts
| Concept | Definition |
|---|---|
| Signal spec | Structured input: prose description + optional pseudocode + parameters (universe, horizon, costs) |
| Investigation | One orchestrated run: lint → agent → probes → verdict |
| Probe | Deterministic diagnostic tool executed on synthetic data (see 03 §8) |
| Verdict | `REJECT_SPURIOUS`, `NEEDS_REVIEW`, `PROMISING` - each with confidence + reason codes |
| Evidence bundle | Claims extracted, probe results with numbers, verdict, recommended action, timestamps, cost |
| Stratum | Flaw family: F1 lookahead-syntactic, F2 lookahead-semantic, F3 survivorship, F4 p-hacking, F5 regime-overfit, S0 sound |

## 3. Who has the problem (PDF Q1)
Junior quant researchers and quant PMs at prop shops / hedge funds; risk officers who must audit vendor signals. They are the "family guardian" of the research pipeline.

## 4. Bottleneck (PDF Q2)
- Manual review: 60-90 min per signal (read spec, rebuild backtest, hunt for lookahead).
- Most candidates are spurious; the scarce resource is researcher hours.
- Static linters catch syntax only; prose-hidden bias passes. No one publishes honest precision/recall on adversarial cases.

## 5. User journeys
**J1 - The submit (primary loop, must be flawless).** Researcher pastes a spec in the web gate (or `signalgate check spec.yaml`). Lint runs instantly; investigator agent extracts claims, selects probes, interprets results. Verdict card in < 60 s with the two strongest pieces of evidence. Bundle exportable as markdown/JSON.

**J2 - The quiet pipeline.** Weekly digest artifact: *"14 signals screened. 12 rejected with receipts. 1 needed your hour. 1 promising."* Sells the product better than any feature list.

**J3 - The ambiguous case (trust moment).** A genuine 12-1 momentum spec with costs and proper universe. Probes return: permutation p = 0.011, regime-stable IC, turnover sane. Verdict `PROMISING` **with receipts**. The system does not cry wolf.

**J4 - Degraded honesty.** Model provider down → lint-only mode, verdict `NEEDS_REVIEW` with `DEGRADED` flag shown plainly. Never a silent guess.

## 6. Feature set v1
| ID | Feature |
|---|---|
| F1 | Spec intake + schema validation (prose + pseudocode + params) |
| F2 | Static lint baseline (AST/regex rule suite) |
| F3 | Investigator agent (one LLM) + 4 probe tools, deterministic orchestrator |
| F4 | Evidence bundles + verdict cards (web + CLI) |
| F5 | Eval harness: generator, runner, scorers, reports (doc 04) |
| F6 | Web gate UI + CLI + FastAPI JSON API + swagger |
| F7 | Digest artifact (markdown) |

## 7. Out of scope (explicit)
Real market data feeds, order execution, portfolio construction, auth/multi-tenancy, databases, mobile apps, PDF export, multi-agent swarms.

## 8. UX principles
- Never make the researcher read raw agent output - cards and reason codes only.
- Show receipts: confidence always paired with the two strongest evidence items.
- Quiet by design: batch rejections into digests.
- Recommend, never trade: no execution capability exists anywhere in the tool registry.

## 9. Acceptance criteria (product level)
- A stranger reaches a verdict from clean clone in < 5 minutes using README only.
- Verdict card answers: what came in, what we probed, what we found, why this verdict, what you should do.
- Zero unhandled exceptions in clean-environment runs (CI assertion).
- Digest renders from one command with zero manual steps.
