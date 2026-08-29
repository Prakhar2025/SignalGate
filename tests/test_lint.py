"""Static lint rule suite."""
from __future__ import annotations

from signalgate.lint import baseline_verdict, run_lint
from signalgate.schemas import ReasonCode, SignalSpec


def spec(description="A sufficiently long description of the candidate signal.",
         pseudocode=None, universe="all", costs_bps=10.0, rebalance="daily"):
    return SignalSpec.model_validate({
        "name": "Test Spec", "description": description,
        "pseudocode": pseudocode,
        "params": {"universe": universe, "horizon": 21,
                   "costs_bps": costs_bps, "rebalance": rebalance},
    })


def codes(flags):
    return [f.code for f in flags]


def test_clean_spec_has_no_rejecting_flags():
    flags = run_lint(spec(pseudocode="score = rank(pct_change(close, 252))"))
    assert not [f for f in flags if f.rejecting]


def test_l001_negative_shift():
    flags = run_lint(spec(pseudocode="score = rank(shift(close, -1))"))
    assert ReasonCode.LINT_FUTURE_SHIFT in codes(flags)
    flags = run_lint(spec(pseudocode="score = rank(lead(close, 2))"))
    assert ReasonCode.LINT_FUTURE_SHIFT in codes(flags)


def test_l001_catches_pct_change_negative():
    flags = run_lint(spec(pseudocode="score = rank(pct_change(close, -1))"))
    assert ReasonCode.LINT_FUTURE_SHIFT in codes(flags)


def test_l001_positive_shift_is_clean():
    flags = run_lint(spec(pseudocode="score = rank(delay(close, 5))"))
    assert ReasonCode.LINT_FUTURE_SHIFT not in codes(flags)


def test_l101_survivors_param():
    flags = run_lint(spec(universe="survivors"))
    assert ReasonCode.LINT_SURVIVORSHIP in codes(flags)


def test_l101_survivorship_prose():
    flags = run_lint(spec(
        description="Five-day reversion on the current constituents of the index, "
                    "which is a long description for the schema fence to accept."))
    assert ReasonCode.LINT_SURVIVORSHIP in codes(flags)


def test_l201_selection_with_count():
    flags = run_lint(spec(
        description="We screened a grid of 40 lookback windows and kept the best "
                    "performer; this sentence is long enough for the fence."))
    assert ReasonCode.LINT_SELECTION_BIAS in codes(flags)


def test_l201_word_count_does_not_flag():
    flags = run_lint(spec(
        description="The two lookbacks diversify the trend estimate and halve the "
                    "churn of either alone in this honest blend description."))
    assert ReasonCode.LINT_SELECTION_BIAS not in codes(flags)


def test_l301_regime_language_non_rejecting():
    flags = run_lint(spec(
        description="Designed for bull markets, this description is long enough "
                    "for the schema fence to accept it happily."))
    assert ReasonCode.LINT_REGIME_LANGUAGE in codes(flags)
    assert not [f for f in flags if f.rejecting]


def test_baseline_verdict_rules():
    reject_flags = run_lint(spec(pseudocode="score = rank(shift(close, -1))"))
    verdict, _ = baseline_verdict(reject_flags)
    assert verdict == "REJECT_SPURIOUS"
    clean_flags = run_lint(spec())
    verdict, _ = baseline_verdict(clean_flags)
    assert verdict == "NEEDS_REVIEW"  # lint alone never promises
