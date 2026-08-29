# docs/06-pitch.md

| Field | Value |
|---|---|
| Version | 0.1.0 |
| Status | Build-locked |
| Owner | Prakhar Shukla |
| Last updated | 2026-08-28 |

## 1. Strategy
Owner's stated weakness is video; therefore video is engineered: script first, terminal recordings second, TTS voiceover (permitted), hard cuts only, subtitles burned in. Target 4:30 (under 5:00 cap). No face, no camera - rules require neither.

## 2. Master script (beats mapped to PDF's required order)
- **0:00-0:30 Problem + who:** "A quant team receives 40 candidate signals a week. Most are spurious - lookahead hidden in prose, p-hacked variants, regime-overfit params. Each manual review costs an hour. Linters catch syntax; nothing catches semantics."
- **0:30-1:00 Baseline:** show `make baseline`; lint catches `shift(-1)` but passes the prose lookahead case. Catch 0.45, F2 ≈ 0.
- **1:00-2:30 One realistic execution:** web gate live run of the prose-lookahead spec; agent calls `timestamp_alignment_probe` on screen; IC collapses when future info removed; verdict `REJECT_SPURIOUS` with two receipts.
- **2:30-3:10 Final comparison:** the §4 table; McNemar p-value spoken slowly; honest false-reject number.
- **3:10-3:50 Changelog:** baseline → bare-prompt (hallucinated checks) → +probes (the jump) → narrative agent **removed** (cost +40%, no gain). Main contribution = verification tools.
- **3:50-4:20 Hot take:** "An agent without verification tools doesn't investigate - it improvises. Confidence went up while accuracy stayed flat. The tools didn't add evidence; they disciplined the model."
- **4:20-4:30 Close:** "Silence for the research pipeline. SignalGate." + repo URL + live demo URL.

## 3. Shot list
| # | Shot | Source | Dur |
|---|---|---|---|
| S1 | Spec paste + lint miss | terminal (LOCAL_MOCK) | 20 s |
| S2 | Web gate live investigation | browser, timer visible | 60 s |
| S3 | Probe numeric collapse | bundle view | 20 s |
| S4 | Eval table + CIs | terminal | 30 s |
| S5 | Changelog slides | 4 slides | 40 s |
| S6 | Live URL + repo QR | slide | 15 s |

Every shot recorded twice; S2 rehearsed 5 dry runs.

## 4. Submission copy skeleton (README intro)
One-liner: *SignalGate is an agentic research-integrity gate: candidate trading signals are investigated like fraud cases - statistical probes as tools, verdicts with receipts, silence unless a signal deserves a researcher's hour.*
About: who/bottleneck/value (02 §3-4), architecture (03), what is measured (07), links: repo, live demo, reports/.

## 5. Rules compliance register (micro1 ground rules, read in full Aug 28)
| Rule | Our action |
|---|---|
| 01/02 | Known tools; disclosure line: design informed by prior fraud-defense work, zero code imported |
| 03 | MIT + dependency licenses in NOTICE |
| 04 | Probes sandboxed, synthetic-only |
| 05 | Verdicts advisory; researcher = qualified reviewer |
| 06/07 | Synthetic data only; legal use case |
| 08 | Env-only creds; CI secret-scan |
| 09 | Every claim → artifact |
| 10 | One-command repro + live URL through judging |

## 6. Deliverables checklist (the PDF's four)
- [ ] Code + README + IMPROVEMENT_CHANGELOG (07 §9 format, closes with failure mode + hot take)
- [ ] REPRODUCTION.md (= doc 05)
- [ ] Video ≤ 5:00 (script §2)
- [ ] Trajectories: coding-agent traces + runtime agent spans, instruction → tool response → feedback → retry/checkpoint

## 7. Video acceptance criteria
Runtime 4:00-4:40; problem + baseline inside first 60 s; every spoken number identical to README; intelligible on phone speaker; subtitles burned in.
