| Metric | Baseline (static lint) | Agent solution | Change |
|---|---|---|---|
| Spurious catch rate | 0.475 (95% CI [0.329, 0.625]) | 0.925 (95% CI [0.801, 0.974]) | +0.450 |
| False-reject rate (S0) | 0.0 | 0.0 | - |
| Precision (reject) | 1.0 | 1.0 | - |
| Human time per task | 60-90 min manual | ~3 min evidence review | -95% |
| Cost per task | $0 | $0.0000 (LOCAL_MOCK) | disclosed |

| Stratum | Baseline catch | Agent catch |
|---|---|---|
| F1 | 1.0 | 1.0 |
| F2 | 0.0 | 1.0 |
| F3 | 1.0 | 0.75 |
| F4 | 0.375 | 1.0 |
| F5 | 0.0 | 0.857 |
McNemar paired test (same 48 cases): agent-only correct 20, baseline-only correct 2 - p = 0.00029. Seed 20260828, mode LOCAL_MOCK, model LOCAL_MOCK, prompt prompts@v1.0.0.

Human time: baseline and agent both replace the 60-90 min manual review; the agent's evidence bundle reduces review to ~3 minutes for surviving cases.

This run: latency p50 4184 ms (wall-clock; excluded from metrics.json to keep it byte-identical).
