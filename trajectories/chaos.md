# Degradation trajectories (docs chaos matrix)

## model provider down

Verdict: `NEEDS_REVIEW` (LOW), degraded=True, codes: DEGRADED_MODEL

```json
[]
```

## probe timeouts

Verdict: `NEEDS_REVIEW` (MEDIUM), degraded=False, codes: PROBE_SKIPPED

```json
[
  {
    "probe": "timestamp_alignment_probe",
    "ok": false,
    "skipped": true,
    "skip_reason": "timeout after 10s (PROBE_SKIPPED)",
    "metrics": {},
    "detail": {}
  },
  {
    "probe": "label_permutation_test",
    "ok": false,
    "skipped": true,
    "skip_reason": "timeout after 10s (PROBE_SKIPPED)",
    "metrics": {},
    "detail": {}
  },
  {
    "probe": "regime_subsample",
    "ok": false,
    "skipped": true,
    "skip_reason": "timeout after 10s (PROBE_SKIPPED)",
    "metrics": {},
    "detail": {}
  },
  {
    "probe": "turnover_and_cost_sanity",
    "ok": false,
    "skipped": true,
    "skip_reason": "timeout after 10s (PROBE_SKIPPED)",
    "metrics": {},
    "detail": {}
  }
]
```

