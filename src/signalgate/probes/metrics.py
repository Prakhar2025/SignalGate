"""Shared probe mathematics - deterministic, seeded, vectorized.

Used by the sandboxed probe workers, by the orchestrator's composer inputs,
and by the generator (variant selection for F4/F5 injections).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MIN_ASSETS_PER_DAY = 8


def forward_returns(close: pd.DataFrame, horizon: int,
                    listed: pd.DataFrame | None = None) -> pd.DataFrame:
    """Return from decision close t to close t+h. Signal may only use info ≤ t.

    With a `listed` mask, forward returns whose horizon crosses a delisting are
    NaN - the investment could not have been held to horizon.
    """
    fwd = close.shift(-int(horizon)) / close - 1.0
    if listed is not None:
        still_listed = listed.shift(-int(horizon)).fillna(False)
        fwd = fwd.where(still_listed)
    return fwd


def daily_ic(score: pd.DataFrame, fwd: pd.DataFrame) -> pd.Series:
    """Cross-sectional Spearman IC per day (rank-then-Pearson), NaN-aware."""
    valid = score.notna() & fwd.notna() & np.isfinite(score.to_numpy()) & np.isfinite(fwd.to_numpy())
    n_valid = valid.sum(axis=1)
    mask2 = n_valid >= MIN_ASSETS_PER_DAY
    rs = score.where(valid).rank(axis=1)
    rf = fwd.where(valid).rank(axis=1)
    mu_r = rs.sum(axis=1) / n_valid
    mu_f = rf.sum(axis=1) / n_valid
    cov = (rs * rf).sum(axis=1) - n_valid * mu_r * mu_f
    sd_r = ((rs * rs).sum(axis=1) - n_valid * mu_r**2).clip(lower=1e-12) ** 0.5
    sd_f = ((rf * rf).sum(axis=1) - n_valid * mu_f**2).clip(lower=1e-12) ** 0.5
    ic = cov / (sd_r * sd_f)
    ic[~mask2] = np.nan
    return ic


def mean_ic(score: pd.DataFrame, fwd: pd.DataFrame) -> float:
    ic = daily_ic(score, fwd)
    return float(ic.mean()) if ic.notna().any() else 0.0


def circular_permutation_p(score: pd.DataFrame, fwd: pd.DataFrame, *, seed: int,
                           n_perm: int = 199) -> tuple[float, float]:
    """Empirical p of the observed mean rank-IC under a within-day null.

    Each permutation shuffles the score across assets *within each day*, which
    severs any cross-sectional link while imposing no assumption about the
    score's own time-series structure (a circular time-shift null would be
    degenerate for slow-moving scores). Returns (p_value, observed_ic).
    """
    fwd_np = fwd.to_numpy(dtype=float)
    s_all = score.to_numpy(dtype=float)
    ok = np.isfinite(s_all) & np.isfinite(fwd_np)
    if ok.sum() == 0:
        return 1.0, 0.0

    s = np.where(ok, s_all, np.nan)
    f = np.where(ok, fwd_np, np.nan)
    observed = _mean_ic_np(s, f)

    rng = np.random.default_rng(seed)
    t, n = s.shape
    ge = 0
    for _ in range(n_perm):
        r = rng.random((t, n))
        idx = np.argsort(r, axis=1, kind="stable")            # per-day permutation
        perm = np.take_along_axis(s, idx, axis=1)
        if _mean_ic_np(perm, f) >= observed:
            ge += 1
    return (1.0 + ge) / (1.0 + n_perm), observed


def _mean_ic_np(s: np.ndarray, f: np.ndarray) -> float:
    ok = np.isfinite(s) & np.isfinite(f)
    counts = ok.sum(axis=1)
    with np.errstate(invalid="ignore"):
        rs = _row_rank(np.where(ok, s, np.nan))
        rf = _row_rank(np.where(ok, f, np.nan))
    mu_r = np.nanmean(np.where(ok, rs, np.nan), axis=1)
    mu_f = np.nanmean(np.where(ok, rf, np.nan), axis=1)
    cov = np.nanmean(np.where(ok, rs * rf, np.nan), axis=1) - mu_r * mu_f
    sd_r = np.nanstd(np.where(ok, rs, np.nan), axis=1)
    sd_f = np.nanstd(np.where(ok, rf, np.nan), axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        ic = cov / (sd_r * sd_f)
    ic[(counts < MIN_ASSETS_PER_DAY) | (sd_r <= 0) | (sd_f <= 0)] = np.nan
    return float(np.nanmean(ic)) if np.isfinite(ic).any() else 0.0


def _row_rank(a: np.ndarray) -> np.ndarray:
    """Ordinal ranks per row (NaNs excluded from the count), vectorized."""
    ok = np.isfinite(a)
    big = np.where(ok, a, np.finfo(float).max / 4.0)
    order = big.argsort(axis=1, kind="stable").argsort(axis=1, kind="stable").astype(float) + 1.0
    return np.where(ok, order, np.nan)


def sidak_deflate(p: float, n_variants: int) -> float:
    """Multiple-testing correction for hidden variant selection (F4)."""
    n = max(1, int(n_variants))
    return float(1.0 - (1.0 - min(1.0, max(0.0, p))) ** n)


def positions_from_score(score: pd.DataFrame) -> pd.DataFrame:
    """Dollar-neutral book: daily cross-sectional z-scores of the signal."""
    return zscore_rows(score)


def zscore_rows(x: pd.DataFrame) -> pd.DataFrame:
    mu = x.mean(axis=1)
    sd = x.std(axis=1, ddof=0)
    return x.sub(mu, axis=0).div(sd.replace(0.0, np.nan), axis=0)


def turnover_and_net_sharpe(score: pd.DataFrame, close: pd.DataFrame, *,
                            costs_bps: float, horizon: int,
                            universe_mask: pd.DataFrame | None = None,
                            rebalance: str = "daily") -> dict[str, float]:
    """Implied turnover and gross/net annualized Sharpe of the as-written signal.

    Positions are cross-sectional z-scores, frozen between rebalances
    (`daily` | `weekly`); each unit bought or sold pays `costs_bps`.
    """
    pos = positions_from_score(score)
    if universe_mask is not None:
        pos = pos.where(universe_mask.reindex_like(pos).fillna(False).astype(bool))
    period = 5 if rebalance == "weekly" else 1
    asset_ret = close.pct_change(fill_method=None)

    is_rebalance = pd.Series(False, index=pos.index)
    is_rebalance.iloc[::period] = True
    pos_held = pos.where(is_rebalance, np.nan).ffill()
    # gross exposure of the book per day (z-score positions, GMV = sum |pos| / 2)
    gmv = pos_held.abs().sum(axis=1) / 2.0
    trade = pos_held.diff().abs().sum(axis=1)
    trade[~is_rebalance.to_numpy()] = 0.0

    pos_lag = pos_held.shift(1)                 # frozen positions earn next-day returns
    gross_daily = (pos_lag * asset_ret).sum(axis=1) / gmv.shift(1).clip(lower=1e-9)
    # one-sided traded fraction of GMV on rebalance days, amortized across the period
    turnover_rebal = (trade / 2.0) / gmv.clip(lower=1e-9)
    daily_cost = turnover_rebal * costs_bps / 1e4 / period
    net_daily = gross_daily - daily_cost
    traded_daily = turnover_rebal / period

    def ann_sharpe(x: pd.Series) -> float:
        x = x.dropna()
        if len(x) < 50 or x.std(ddof=0) == 0:
            return 0.0
        return float(x.mean() / x.std(ddof=0) * np.sqrt(252))

    gross, net = ann_sharpe(gross_daily), ann_sharpe(net_daily)
    return {
        "turnover_1s_daily": float(traded_daily.mean()) if traded_daily.notna().any() else 0.0,
        "turnover_annualized": float(traded_daily.mean() * 252) if traded_daily.notna().any() else 0.0,
        "gross_sharpe": gross,
        "net_sharpe": net,
        "daily_cost_drag_bps": float(daily_cost.mean() * 1e4) if daily_cost.notna().any() else 0.0,
        "horizon": int(horizon),
        "rebalance": rebalance,
    }


def regime_table(score: pd.DataFrame, fwd: pd.DataFrame, regime: np.ndarray, *,
                 min_active_days: int = 30) -> dict[str, dict[str, float]]:
    """Per-regime leak-proof IC with active-day shares (bull/bear/sideways).

    `active` is the fraction of the regime's days on which the score actually
    tradable (non-constant, enough names) - a gated signal that sleeps through
    a regime reports a low active share rather than a fake IC.
    """
    ic = daily_ic(score, fwd)
    exists = score.notna().any(axis=1).to_numpy()   # warmup-adjusted denominator
    out: dict[str, dict[str, float]] = {}
    for name, idx in (("bull", 0), ("bear", 1), ("sideways", 2)):
        days = int(((regime == idx) & exists).sum())
        sel = ic[(regime == idx) & ic.notna()]
        mean_ic = float(sel.mean()) if len(sel) >= min_active_days else 0.0
        out[name] = {"ic": mean_ic, "active": round(len(sel) / max(1, days), 3),
                     "days": days}
    return out
