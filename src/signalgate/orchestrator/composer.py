"""Verdict composer - thresholds in code, narrative generated last (docs/03 §6)."""
from __future__ import annotations

from signalgate.orchestrator import thresholds as T
from signalgate.schemas import (
    Confidence,
    EvidenceItem,
    ProbeResult,
    ReasonCode,
    RecommendedAction,
    Verdict,
)

ACTION_BY_VERDICT = {
    Verdict.REJECT_SPURIOUS: RecommendedAction.ARCHIVE_WITH_RECEIPTS,
    Verdict.NEEDS_REVIEW: RecommendedAction.ASSIGN_RESEARCHER_HOUR,
    Verdict.PROMISING: RecommendedAction.PROMOTE_TO_PAPER_TRADE,
    Verdict.REJECTED_INVALID: RecommendedAction.FIX_SPEC_AND_RESUBMIT,
}


def _m(probes: list[ProbeResult], name: str) -> dict:
    for p in probes:
        if p.probe == name and p.ok and not p.skipped:
            return p.metrics
    return {}


def compose(probes: list[ProbeResult], lint_flags: list[dict],
            degraded: bool) -> tuple[Verdict, Confidence, list[ReasonCode], list[EvidenceItem]]:
    """Apply the calibrated thresholds to authoritative probe numbers."""
    reasons: list[ReasonCode] = []
    codes = [f.get("code") for f in lint_flags]
    if ReasonCode.LINT_FUTURE_SHIFT.value in codes:
        reasons.append(ReasonCode.LINT_FUTURE_SHIFT)

    ta = _m(probes, "timestamp_alignment_probe")
    perm = _m(probes, "label_permutation_test")
    reg = _m(probes, "regime_subsample")
    to = _m(probes, "turnover_and_cost_sanity")

    ic_w = float(ta.get("ic_as_written", 0.0) or 0.0)
    ic_p = float(ta.get("ic_point_in_time", 0.0) or 0.0)
    delta = ic_w - ic_p

    if ta and delta > T.LOOKAHEAD_DELTA and ic_p < T.LOOKAHEAD_PIT_RATIO * max(ic_w, 1e-9):
        reasons.append(ReasonCode.LOOKAHEAD_COLLAPSE)
    if ta and delta > T.PIT_ONLY_DELTA and ic_w > T.PIT_ONLY_WRITTEN \
            and ic_p < T.PIT_ONLY_CAP:
        reasons.append(ReasonCode.PIT_ONLY_EDGE)

    p_defl = float(perm.get("p_deflated", 1.0) or 1.0)
    if perm and p_defl > T.SIGNIFICANCE_REJECT:
        reasons.append(ReasonCode.NOT_SIGNIFICANT)

    if reg:
        ics = [float(reg.get("min_regime_ic", 0.0)), float(reg.get("max_regime_ic", 0.0))]
        min_ic, max_ic = min(ics), max(ics)
        min_active = float(reg.get("min_regime_active", 1.0))
        if (min_ic < 0.0 and max_ic > T.REGIME_MAX_IC) or min_active < T.REGIME_MIN_ACTIVE:
            reasons.append(ReasonCode.REGIME_FRAGILE)
    else:
        min_ic, max_ic, min_active = None, None, 1.0

    if to and float(to.get("gross_sharpe", 0.0) or 0.0) > T.COST_MIRACLE_GROSS \
            and float(to.get("net_sharpe", 0.0) or 0.0) < T.COST_MIRACLE_NET:
        reasons.append(ReasonCode.COST_MIRACLE)

    # disclosure codes - weaken evidence, never reject on their own
    skipped = any(p.skipped for p in probes)
    if skipped:
        reasons.append(ReasonCode.PROBE_SKIPPED)
    if degraded:
        reasons.append(ReasonCode.DEGRADED_MODEL)

    # ---- verdict
    if degraded:
        verdict = Verdict.NEEDS_REVIEW
    else:
        reject_reasons = [r for r in reasons
                          if r not in (ReasonCode.PROBE_SKIPPED, ReasonCode.DEGRADED_MODEL)]
        if reject_reasons:
            verdict = Verdict.REJECT_SPURIOUS
        else:
            promise = (
                not skipped
                and perm and p_defl <= T.SIGNIFICANCE_PROMISE
                and ta and abs(delta) <= T.PROMISE_MAX_DELTA
                and ic_p >= T.PROMISE_MIN_PIT_IC
                and min_ic is not None and min_ic > 0.0
                and min_active >= T.REGIME_MIN_ACTIVE
                and to and float(to.get("net_sharpe", 0.0) or 0.0) > T.PROMISE_NET_SHARPE
            )
            verdict = Verdict.PROMISING if promise else Verdict.NEEDS_REVIEW

    hard = sum(1 for r in reasons if r != ReasonCode.PROBE_SKIPPED)
    if verdict == Verdict.REJECT_SPURIOUS:
        confidence = Confidence.HIGH if hard >= 2 else Confidence.MEDIUM
    elif verdict == Verdict.PROMISING:
        confidence = Confidence.HIGH if p_defl <= 0.005 else Confidence.MEDIUM
    else:
        confidence = Confidence.LOW if degraded else Confidence.MEDIUM
    return verdict, confidence, reasons, []
