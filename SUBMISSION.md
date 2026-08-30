# Submission checklist

Mapped one-to-one to the official deliverables (problem PDF, "Final
deliverables") and the ten ground rules. Every claim links to the artifact
that proves it.

## The four deliverables

### 01 Complete solution code and improvement changelog

- [x] Full solution: `src/signalgate/` (lint, agent, probes, orchestrator,
      API, eval) plus `generator/` (seeded market, flaw injector, 60-case
      adversarial set) and `frontend/` (Next.js 16 product surface).
- [x] Agent instructions that shape each agent: committed at
      [`src/signalgate/agent/prompts.py`](src/signalgate/agent/prompts.py)
      (version-stamped, embedded in every bundle and in metrics.json) and
      mirrored inside each exported trajectory.
- [x] README introduces the intended user, the bottleneck, and why solving
      it matters (top of [README.md](README.md)).
- [x] Improvement changelog with one entry per iteration, each connected to
      measured evidence, closing with the main failure mode and the hot
      take: [IMPROVEMENT_CHANGELOG.md](IMPROVEMENT_CHANGELOG.md).
      Receipts: [reports/ablation.md](reports/ablation.md),
      [reports/metrics.json](reports/metrics.json).

### 02 Reproduction guide

- [x] [REPRODUCTION.md](REPRODUCTION.md), written for a clean environment:
      exact commands for solution, baseline and evaluation; the data is
      generated deterministically from seed 20260828 (no downloads);
      expected output is stated with the measured numbers; versions,
      runtime (2-4 min) and cost ($0 LOCAL_MOCK) are published.
- [x] Zero keys required: judges run LOCAL_MOCK; LIVE mode is optional via
      env-only credentials (rule 08), and `scripts/routing_ritual.py`
      records honest skips without them.

- [x] Long-form article with the 1200x675 article image:
      [docs/07-article.md](docs/07-article.md) and
      [docs/assets/article-image.png](docs/assets/article-image.png)

### 03 Solution video (up to 5 minutes)

- [x] Script, beat sheet and shot list: [docs/06-pitch.md](docs/06-pitch.md)
      (problem + baseline inside the first 60 s, one realistic execution,
      final comparison, changelog summary, the removed experiment, every
      spoken number identical to the README).
- [ ] Recording: owner records from the script; commands in executing order
      are listed at the bottom of this file.

### 04 Agent trajectories

- [x] [`trajectories/README.md`](trajectories/README.md): both agent kinds,
      with failures and retries included.
- [x] Runtime investigator trajectories regenerated deterministically via
      `python -m scripts.export_trajectories`:
      [`trajectories/runs/`](trajectories/runs) (pass, three distinct
      reject mechanisms, the honest middle case) plus
      [`trajectories/chaos.md`](trajectories/chaos.md) (model-down and
      probe-timeout degradation).
- [x] Machine-readable forms: every run persists
      `artifacts/runs/<run_id>/bundle.json` + `trajectory.json`
      (instruction, tool response, feedback, retry, checkpoint spans).

## Ground-rule compliance register

| Rule | Where it is satisfied |
|---|---|
| 01 known tools | Python 3.12, FastAPI, Typer, pandas/numpy, Next.js 16; pinned in requirements-lock.txt |
| 02 what existed before | docs/ were authored and locked first; everything else was built during the sprint; disclosure line in README (prior fraud-defense design lineage, zero code imported) |
| 03 licenses | MIT ([LICENSE](LICENSE)) + dependency licenses ([NOTICE](NOTICE)) |
| 04 sandbox | probes run as capped subprocesses on synthetic data only, no network, allowlisted tool registry, no execution capability anywhere |
| 05 human reviewer | verdicts advisory by design; recommended actions stop at "assign a researcher hour" and "promote to paper-trade review" |
| 06 legal, ethical use | defensive research-integrity tooling; no trading, no personal data |
| 07 data | 100% synthetic, seeded generator; calibration published in [reports/dataset.md](reports/dataset.md) |
| 08 credentials | env-only, `.env` gitignored, `scripts/secret_scan.py` in CI; zero keys needed to run or judge |
| 09 claims to evidence | every number in README/changelog traces to reports/metrics.json, reports/comparison.md, reports/ablation.md, all committed |
| 10 judges can run | `make install && make data && make eval && make serve`; byte-identity asserted by `make repro-check` (62/62 tests green) |

## Recording checklist for the video (owner)

1. Fresh shell. `make serve` (backend, :8000) and
   `cd frontend && npm start -- -p 3100`.
2. Shot S1 (20 s): `make baseline` output in terminal; paste f2_01, show
   lint passing it (the miss).
3. Shot S2 (60 s): browser, /gate, load f2_01, Investigate, timer visible;
   verdict card REJECT with the 0.475 to 0.023 collapse receipt.
4. Shot S3 (20 s): /runs/<id> bundle view, probe numbers, trajectory spans.
5. Shot S4 (30 s): /evaluation page, comparison table + McNemar panel.
6. Shot S5 (40 s): ablation slides (baseline 0.475, bare-prompt 1.0 catch /
   0.875 false-reject, tools 0.925 / 0.0, narrative agent removed +40%
   tokens).
7. Shot S6 (15 s): repo URL + this checklist's claims-to-artifacts table.
8. Voiceover per docs/06-pitch.md script; burn in subtitles; hard cuts.

## Known limitations, stated plainly

- The benchmark world is synthetic and self-generated (rule 07 makes this
  unavoidable); calibration and per-case injection strengths are published,
  misses are named, and the false-reject guard keeps the benchmark honest.
- Docker image build is provided but was not completed in the dev
  environment (bandwidth); the supported judge path is the two-command
  local run above.
- LIVE mode is implemented against any OpenAI-compatible endpoint and is
  breaker-capped, but all published numbers come from LOCAL_MOCK so they
  regenerate byte-identically without keys.
