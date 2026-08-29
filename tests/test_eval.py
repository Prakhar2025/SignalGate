"""Eval math + reproducibility (docs/04 §5): Wilson CIs, McNemar, byte-identical reruns."""
from __future__ import annotations

import math

import pytest

from signalgate.eval.score import mcnemar, system_metrics, wilson


def test_wilson_known_values():
    lo, hi = wilson(0.5, 10)
    assert lo < 0.5 < hi
    lo, hi = wilson(1.0, 10)
    assert lo > 0.65 and hi == 1.0
    assert wilson(0.0, 0) == (0.0, 0.0)


def test_wilson_no_nan():
    for k in range(0, 11):
        lo, hi = wilson(k / 10, 10)
        assert all(math.isfinite(v) for v in (lo, hi))


def test_mcnemar_significant_and_null():
    assert mcnemar(0, 20) < 0.001
    assert mcnemar(10, 10) > 0.5
    assert mcnemar(0, 0) == 1.0


def _records():
    recs = []
    for i in range(40):
        recs.append({"case_id": f"f_{i}", "family": "F1",
                     "verdict": "REJECT_SPURIOUS" if i < 34 else "NEEDS_REVIEW"})
    for i in range(10):
        recs.append({"case_id": f"s_{i}", "family": "S0",
                     "verdict": "PROMISING" if i < 9 else "REJECT_SPURIOUS"})
    return recs


def test_system_metrics_math():
    m = system_metrics(_records())
    assert m["spurious_catch_rate"] == 0.85
    assert m["false_reject_rate"] == 0.1
    assert m["precision_reject"] == 0.971  # TP=34, FP=1
    assert m["per_stratum"]["F1"]["catch"] == 0.85


@pytest.mark.slow
def test_repro_byte_identical_metrics(market_path, tmp_path):
    """Full eval twice on a subset; metrics.json must be byte-identical."""
    from tests.test_orchestrator import make_settings

    from signalgate.eval.run import run_system
    from signalgate.eval.score import score

    settings = make_settings(tmp_path, market_path)
    cases = [
        ("s0_flagship", {
            "name": "Twelve-One Momentum",
            "description": "Standard 12-1 momentum ranked daily on the liquid "
                           "subset of the point-in-time universe, 21-day holding, "
                           "15 bps costs.",
            "pseudocode": "score = rank(pct_change(close, 252) - pct_change(close, 21)) "
                          "* (rank(volume) > -0.30)",
            "params": {"universe": "all", "horizon": 21, "costs_bps": 15.0,
                       "rebalance": "weekly"},
            "_truth": {"family": "S0", "expected_verdict": "PROMISING"},
        }),
        ("f2_semantic", {
            "name": "Management Tone Confidence",
            "description": "Score by how strongly management sounds about next "
                           "quarter, priced at quarter-end, 21-day holding period, "
                           "10 bps costs. Long enough for the fence.",
            "pseudocode": "score = rank(mgmt_tone_quarter)",
            "params": {"universe": "all", "horizon": 21, "costs_bps": 10.0,
                       "rebalance": "weekly"},
            "_truth": {"family": "F2", "expected_verdict": "REJECT_SPURIOUS"},
        }),
    ]
    metrics_texts = []
    for i in (1, 2):
        out = tmp_path / f"run{i}"
        run_system("agent", settings, [(c, dict(p)) for c, p in cases], out)
        run_system("baseline", settings, [(c, dict(p)) for c, p in cases], out)
        score(out / "baseline", out / "agent", out)
        metrics_texts.append((out / "metrics.json").read_text(encoding="utf-8"))
    assert metrics_texts[0] == metrics_texts[1]
