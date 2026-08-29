"""Probe worker end-to-end (subprocess sandbox) on the small fixture market."""
from __future__ import annotations

from signalgate.probes import run_probe


def test_alignment_probe_collapses_on_lookahead(market_path):
    r = run_probe("timestamp_alignment_probe", market_path=market_path,
                  pseudocode="score = rank(shift(close, -1))",
                  horizon=5, costs_bps=5.0, rebalance="weekly",
                  variants_tried=1, seed=7)
    assert r.ok and not r.skipped
    assert r.metrics["max_negative_shift"] == 1
    assert r.metrics["ic_delta"] > 0.03  # positive on the small fixture


def test_alignment_probe_clean_on_sound_signal(market_path):
    r = run_probe("timestamp_alignment_probe", market_path=market_path,
                  pseudocode="score = rank(pct_change(close, 126))",
                  horizon=21, costs_bps=15.0, rebalance="weekly",
                  variants_tried=1, seed=7)
    assert r.ok
    assert abs(r.metrics["ic_delta"]) < 0.05


def test_permutation_probe_deflates(market_path):
    args = dict(market_path=market_path,
                pseudocode="score = rank(ts_sum(volume, 40))",
                horizon=10, costs_bps=10.0, rebalance="weekly", seed=7)
    r1 = run_probe("label_permutation_test", variants_tried=1, **args)
    r40 = run_probe("label_permutation_test", variants_tried=40, **args)
    assert r40.metrics["p_deflated"] >= r1.metrics["p_deflated"]
    assert r40.metrics["variants_assumed"] == 40
    assert r40.metrics["n_permutations"] == 199


def test_regime_probe_reports_all_regimes(market_path):
    r = run_probe("regime_subsample", market_path=market_path,
                  pseudocode="score = rank(pct_change(close, 126))",
                  horizon=21, costs_bps=15.0, rebalance="weekly",
                  variants_tried=1, seed=7)
    assert r.ok
    assert set(r.detail["regimes"]) == {"bull", "bear", "sideways"}
    assert "min_regime_active" in r.metrics


def test_turnover_probe_miracle_flag(market_path):
    r = run_probe("turnover_and_cost_sanity", market_path=market_path,
                  pseudocode="score = rank(pct_change(close, 126))",
                  horizon=21, costs_bps=500.0, rebalance="daily",
                  variants_tried=1, seed=7)
    assert r.ok
    assert "miracle_flag" in r.metrics


def test_unknown_probe_rejected_by_allowlist(market_path):
    r = run_probe("delete_everything", market_path=market_path,
                  pseudocode="score = rank(close)", horizon=5,
                  costs_bps=5.0, rebalance="daily", variants_tried=1, seed=7)
    assert r.skipped and "allowlist" in r.skip_reason


def test_worker_timeout_disclosed(market_path):
    r = run_probe("timestamp_alignment_probe", market_path=market_path,
                  pseudocode="score = rank(close)", horizon=5,
                  costs_bps=5.0, rebalance="daily", variants_tried=1,
                  seed=7, timeout_s=0)
    assert r.skipped and "timeout" in r.skip_reason.lower()
