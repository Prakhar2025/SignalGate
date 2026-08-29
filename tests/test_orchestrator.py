"""Orchestrator: verdicts, degradation matrix, spend breaker (docs/03 §7)."""
from __future__ import annotations

import pytest

from signalgate.config import Settings
from signalgate.orchestrator.pipeline import Orchestrator, SpecInvalid
from signalgate.schemas import ReasonCode, SignalSpec, Verdict


def make_settings(tmp_path, market_path):
    return Settings(
        mode="mock", effective_mode="mock", model="LOCAL_MOCK", api_base="",
        api_key_set=False, spend_cap_usd=2.0, seed=20260828,
        data_dir=market_path.parent, artifacts_dir=tmp_path / "artifacts",
        reports_dir=tmp_path / "reports")


SPEC_F2 = {
    "name": "Management Tone Confidence",
    "description": (
        "Score each name by how strongly management sounds about next quarter: we "
        "parse the tone of the quarterly filing and go long the confident names. "
        "Positions are priced at quarter-end and rebalanced daily; 21-day holding "
        "period; costs modeled at 10 bps."),
    "pseudocode": "score = rank(mgmt_tone_quarter)",
    "params": {"universe": "all", "horizon": 21, "costs_bps": 10.0,
               "rebalance": "weekly"},
}

SPEC_S0 = {
    "name": "Twelve-One Momentum (flagship)",
    "description": (
        "Standard 12-1 cross-sectional momentum ranked daily on the liquid subset "
        "of the point-in-time universe (bottom volume quintile excluded each day), "
        "21-day holding period, costs modeled conservatively at 15 bps per side."),
    "pseudocode": "score = rank(pct_change(close, 252) - pct_change(close, 21)) * (rank(volume) > -0.30)",
    "params": {"universe": "all", "horizon": 21, "costs_bps": 15.0,
               "rebalance": "weekly"},
}


@pytest.fixture(scope="module")
def settings(tmp_path_factory, full_market_path):
    return make_settings(tmp_path_factory.mktemp("orch"), full_market_path)


def test_flagship_sound_signal_promising(settings):
    spec = SignalSpec.model_validate(SPEC_S0)
    r = Orchestrator(settings).investigate(spec, persist=True)
    assert r.verdict == Verdict.PROMISING
    assert not r.degraded
    assert not r.reason_codes
    assert any(e.probe == "label_permutation_test" for e in r.findings)


def test_semantic_lookahead_rejected(settings):
    spec = SignalSpec.model_validate(SPEC_F2)
    r = Orchestrator(settings).investigate(spec, persist=True)
    assert r.verdict == Verdict.REJECT_SPURIOUS
    assert ReasonCode.LOOKAHEAD_COLLAPSE in r.reason_codes
    ta = next(p for p in r.probe_results if p.probe == "timestamp_alignment_probe")
    assert ta.metrics["ic_delta"] > 0.10


def test_baseline_depth_lint_only(settings):
    spec = SignalSpec.model_validate(SPEC_F2)
    r = Orchestrator(settings).investigate(spec, depth="baseline", persist=False)
    assert r.mode == "LINT_ONLY"
    assert r.verdict == Verdict.NEEDS_REVIEW  # lint cannot see this flaw family


def test_bundle_persisted(settings):
    import json
    spec = SignalSpec.model_validate(SPEC_F2)
    r = Orchestrator(settings).investigate(spec, persist=True)
    d = settings.artifacts_dir / "runs" / r.run_id
    assert (d / "bundle.json").exists()
    assert (d / "bundle.md").exists()
    assert (d / "trajectory.json").exists()
    spans = json.loads((d / "trajectory.json").read_text(encoding="utf-8"))
    events = {s["event"] for s in spans}
    assert {"instruction", "tool_response", "checkpoint"} <= events


def test_chaos_model_down_degrades(settings):
    spec = SignalSpec.model_validate(SPEC_F2)
    r = Orchestrator(settings, chaos={"model_down": True}).investigate(
        spec, persist=False)
    assert r.degraded
    assert r.verdict == Verdict.NEEDS_REVIEW
    assert ReasonCode.DEGRADED_MODEL in r.reason_codes


def test_chaos_probe_timeout_never_rejects_alone(settings):
    spec = SignalSpec.model_validate(SPEC_F2)
    r = Orchestrator(settings, chaos={"probe_timeout": True}).investigate(
        spec, persist=False)
    assert all(p.skipped for p in r.probe_results)
    assert ReasonCode.PROBE_SKIPPED in r.reason_codes
    assert r.verdict == Verdict.NEEDS_REVIEW  # skipped probes weaken, never reject


def test_spend_breaker_trips_to_degraded(settings, market_path):
    from signalgate.orchestrator.spend import SpendMeter
    spend = SpendMeter(cap_usd=0.0)
    spend.record(cost_usd=5.0, tokens=100)   # breaker has tripped
    spec = SignalSpec.model_validate(SPEC_F2)
    r = Orchestrator(settings, spend=spend).investigate(spec, persist=False)
    assert r.degraded
    assert r.verdict == Verdict.NEEDS_REVIEW


def test_invalid_spec_raises_reasoned(settings):
    bad = {"name": "x", "description": "short", "params": {"horizon": 999}}
    with pytest.raises(SpecInvalid):
        from signalgate.orchestrator.pipeline import investigate_spec_dict
        investigate_spec_dict(bad, settings=settings)
