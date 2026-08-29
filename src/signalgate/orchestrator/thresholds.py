"""Verdict composer thresholds - CODE, not model (docs/03 §6).

Calibrated on the locked synthetic world; the calibration table is published
in reports/dataset.md and the derived numbers in reports/metrics.json.
"""
from __future__ import annotations

# timestamp_alignment_probe
LOOKAHEAD_DELTA = 0.10          # delta = IC(as-written) - IC(leak-proof)
LOOKAHEAD_PIT_RATIO = 0.5       # and PIT IC below this fraction of as-written

# survivorship / universe collapse
PIT_ONLY_DELTA = 0.035          # written edge that vanishes point-in-time
PIT_ONLY_WRITTEN = 0.005
PIT_ONLY_CAP = 0.01             # PIT IC effectively dead

# label_permutation_test
SIGNIFICANCE_REJECT = 0.10      # deflated p above this -> no claimed edge
SIGNIFICANCE_PROMISE = 0.02     # deflated p at/below this -> strong evidence

# regime_subsample
REGIME_MAX_IC = 0.03            # a real edge somewhere...
REGIME_MIN_ACTIVE = 0.30        # ...and the signal barely exists in some regime

# turnover_and_cost_sanity
COST_MIRACLE_GROSS = 0.8        # gross looks great...
COST_MIRACLE_NET = 0.0          # ...but net of declared costs it loses money

# promising gate
PROMISE_NET_SHARPE = 0.3
PROMISE_MIN_PIT_IC = 0.02
PROMISE_MAX_DELTA = 0.05
