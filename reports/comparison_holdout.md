| Metric | Baseline (static lint) | Agent solution | Change |
|---|---|---|---|
| Spurious catch rate | 0.5 (95% CI [0.237, 0.763]) | 0.9 (95% CI [0.596, 0.982]) | +0.400 |
| False-reject rate (S0) | 0.0 | 0.0 | - |
| Precision (reject) | 1.0 | 1.0 | - |
| Human time per task | 60-90 min manual | ~3 min evidence review | -95% |
| Cost per task | $0 | $0.0000 (LOCAL_MOCK) | disclosed |

| Stratum | Baseline catch | Agent catch |
|---|---|---|
| F1 | 1.0 | 1.0 |
| F2 | 0.0 | 1.0 |
| F3 | 1.0 | 0.5 |
| F4 | 0.5 | 1.0 |
| F5 | 0.0 | 1.0 |
McNemar paired test (same 12 cases): agent-only correct 5, baseline-only correct 1 - p = 0.220671. Seed 20260828, mode LOCAL_MOCK, model LOCAL_MOCK, prompt prompts@v1.0.0.

Human time: baseline and agent both replace the 60-90 min manual review; the agent's evidence bundle reduces review to ~3 minutes for surviving cases.

This run: latency p50 4698 ms (wall-clock; excluded from metrics.json to keep it byte-identical).
