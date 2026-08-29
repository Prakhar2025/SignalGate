"""Seeded synthetic market: regime-switching GBM + baked exploitable structure.

Everything the evaluation needs is manufactured here (ground rule 07 - no
external market data, ever). Baked-in structure so *sound* templates have
genuine, regime-stable edge:

  - persistent per-asset alpha (slow AR)            -> 12-1 momentum family
  - constant AR(1) idio with negative rho           -> short-horizon reversal
  - low-vol / alpha coupling                        -> low-volatility anomaly
  - news_sentiment tracks the forward alpha path    -> news edge (PIT, lag 0)
  - post-earnings-announcement drift (40d decay)    -> earnings_surprise edge

Distress: chosen assets bleed (negative alpha ramp, rising vol, drying
volume) and delist mid-sample - the raw material of survivorship flaws and
of the point-in-time universe the probes enforce.

Alt-data fields ship in two variants:
  - point-in-time series (lag 0) - what a disciplined researcher has;
  - a *peeking* variant (lag > 0) whose value at row t aggregates the
    in-progress period's idio outcome - exactly what a forward-restated
    vendor merge produces. This is the raw material of semantic lookahead.

Disclosed limitation: edge magnitudes in this synthetic world are larger
than real markets. Probe thresholds are calibrated on THIS world and the
calibration is published with the metrics (docs/04 §5).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from signalgate.market_data import REGIME_NAMES, MarketPanel

QUARTER_DAYS = 63
TRANSITIONS = {
    0: (0.986, 0.005, 0.009),   # bull  -> (bull, bear, sideways)
    1: (0.011, 0.977, 0.012),   # bear
    2: (0.010, 0.008, 0.982),   # sideways
}
MU = {"bull": 0.0005, "bear": -0.0005, "sideways": 0.0000}
VOL = {"bull": 0.008, "bear": 0.012, "sideways": 0.006}
RHO_BASE = -0.10        # constant short-horizon reversal (all regimes)
RHO_BULL_EXTRA = -0.60  # bull-only mean reversion (regime-conditional structure)
ALPHA_STD = 0.0009
LOWVOL_COUPLING = 0.0010
PEAD_DRIFT = 0.0008


def build_market(seed: int, n_assets: int = 50, n_days: int = 750,
                 n_distressed: int = 10) -> MarketPanel:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2023-10-02", periods=n_days)
    cols = [f"A{i:03d}" for i in range(n_assets)]

    # ---------------------------------------------------------------- regimes
    regime = np.empty(n_days, dtype=np.int8)
    state = 2
    for t in range(n_days):
        regime[t] = state
        state = rng.choice(3, p=TRANSITIONS[state])

    mkt_ret = np.array([MU[REGIME_NAMES[s]] + VOL[REGIME_NAMES[s]] * rng.standard_normal()
                        for s in regime])

    # ---------------------------------------------------------------- assets
    betas = rng.normal(1.0, 0.12, n_assets).clip(0.5, 1.5)
    idio_vol = rng.uniform(0.014, 0.026, n_assets)
    alpha_level = rng.normal(0.0, ALPHA_STD, n_assets)

    # near-permanent alpha characteristics (half-life >> sample) so that
    # long-window momentum works in every regime; the docstring's "persistent
    # alpha" channel is a level, not a decaying process
    alpha = np.zeros((n_days, n_assets))
    a = alpha_level.copy()
    for t in range(n_days):
        alpha[t] = a
        a = 0.9995 * a + 0.00001 * rng.standard_normal(n_assets)

    # low-vol anomaly: lower-vol assets carry more alpha
    vol_rank = idio_vol.argsort().argsort() / max(1, n_assets - 1)
    alpha += np.broadcast_to((0.5 - vol_rank) * LOWVOL_COUPLING, alpha.shape)

    # distress + delisting (decided before paths so news/peeks see it).
    # Crashers are the names with the highest *current* alpha around day 450 -
    # rising stars that implode - which is what gives survivorship flaws their
    # bite for momentum-family backtests (the slow AR would otherwise have
    # decorrelated the initial alpha from crash time).
    # timeline scales with n_days: distress = final 25%, anchor at 60%
    d_start, d_end = int(n_days * 0.826), int(n_days * 0.98)
    anchor_day = int(n_days * 0.60)
    distress_window = int(n_days * 0.20)
    delist_day = rng.integers(d_start, d_end + 1, size=n_distressed)
    distress_alpha = np.zeros_like(alpha)
    vol_multiplier = np.ones_like(alpha)
    vol_decay = np.ones((n_days, n_assets))
    tiebreak = rng.random(n_assets) * 1e-9
    distressed_ids = np.sort(np.argsort(-(alpha[anchor_day] + tiebreak))[:n_distressed])
    delisted: dict[str, int] = {}
    for k, asset in enumerate(distressed_ids):
        d0 = int(delist_day[k])
        delisted[cols[asset]] = d0
        start = d0 - distress_window
        ramp = np.clip((np.arange(n_days) - start) / float(distress_window), 0.0, 1.0)
        distress_alpha[:, asset] = -0.020 * ramp**1.5
        vol_multiplier[:, asset] = 1.0 + 1.4 * ramp
        # volume dries up early in distress (liquidity floors exclude these names)
        vol_decay[:, asset] = np.clip(1.0 - 2.2 * ramp**0.8, 0.02, 1.0)

    # idio AR(1), regime-dependent rho (bull-only extra mean reversion)
    z_idio = rng.standard_normal((n_days, n_assets))
    e = np.zeros((n_days, n_assets))
    prev = np.zeros(n_assets)
    for t in range(n_days):
        e[t] = prev
        rho = RHO_BASE + (RHO_BULL_EXTRA if regime[t] == 0 else 0.0)
        prev = rho * prev + np.sqrt(1 - rho**2) * z_idio[t]
    idio = e * idio_vol[None, :] * vol_multiplier

    rets = alpha + distress_alpha + betas[None, :] * mkt_ret[:, None] + idio

    # post-earnings-announcement drift from *disclosed* quarterly surprises
    sur = rets - betas[None, :] * mkt_ret[:, None]
    pead = np.zeros_like(rets)
    disclosed_surprise = np.full((n_days, n_assets), np.nan)
    for t in range(QUARTER_DAYS, n_days):
        if t % QUARTER_DAYS == 0:
            q = t // QUARTER_DAYS
            w = sur[(q - 1) * QUARTER_DAYS : q * QUARTER_DAYS]
            surp = (w.mean(axis=0) - w.mean()) / (w.std() + 1e-9)
            disclosed_surprise[t] = surp
            pead[t : min(t + 60, n_days)] += (PEAD_DRIFT * np.sign(surp)
                                              * np.abs(surp) ** 0.5)[None, :]
    rets = rets + pead
    # a disclosed surprise stays "the most recent disclosure" until the next one
    disclosed_surprise = pd.DataFrame(disclosed_surprise, index=dates, columns=cols).ffill()

    prices = 100.0 * np.cumprod(1.0 + rets, axis=0)
    close = pd.DataFrame(prices, index=dates, columns=cols)

    # post-delist ghost rows: flat price (excluded from PIT anyway)
    listed_np = np.ones((n_days, n_assets), dtype=bool)
    for asset, d0 in delisted.items():
        listed_np[d0:, cols.index(asset)] = False
        close.iloc[d0:, cols.index(asset)] = float(close.iloc[d0 - 1, cols.index(asset)])
    listed = pd.DataFrame(listed_np, index=dates, columns=cols)

    noise_px = pd.DataFrame(rng.standard_normal((n_days, n_assets)) * 0.002,
                            index=dates, columns=cols)
    open_ = close.shift(1) * (1 + noise_px)
    open_.iloc[0] = close.iloc[0]
    band = pd.DataFrame(rng.standard_normal((n_days, n_assets)) * 0.008,
                        index=dates, columns=cols).abs()
    high = np.maximum(close, open_) + band
    low = np.minimum(close, open_) - band
    base_vol = rng.lognormal(mean=14.0, sigma=0.35, size=(1, n_assets))
    volume = pd.DataFrame(
        base_vol * vol_decay * (1.0 + 2.0 * pd.DataFrame(
            rng.standard_normal((n_days, n_assets)), index=dates, columns=cols).abs()),
        index=dates, columns=cols,
    )
    volume = volume.where(listed, 0.0)

    # ---------------------------------------------------------------- alt fields
    fields: dict[str, pd.DataFrame] = {}
    field_lags: dict[str, int] = {}

    def cs_z(a: np.ndarray) -> np.ndarray:
        mu = np.nanmean(a, axis=1, keepdims=True)
        sd = np.nanstd(a, axis=1, keepdims=True) + 1e-12
        z = (a - mu) / sd
        return np.where(np.isfinite(z), z, 0.0)

    def panel(a: np.ndarray) -> pd.DataFrame:
        return pd.DataFrame(a, index=dates, columns=cols)

    # news: sentiment published at t tracks the forward alpha path (genuine alpha)
    fwd30 = pd.DataFrame(alpha + distress_alpha).rolling(30).mean().shift(-30)
    news = (cs_z(fwd30.to_numpy()) * 0.0009
            + rng.standard_normal((n_days, n_assets)) * 0.0002)
    fields["news_sentiment"] = panel(news).where(listed)
    field_lags["news_sentiment"] = 0

    # disclosed earnings surprise (lag 0): last completed quarter, announced
    fields["earnings_surprise"] = disclosed_surprise.where(listed)
    field_lags["earnings_surprise"] = 0

    # peeking variants - forward-realized idio aggregates (semantic-lookahead material)
    idio_df = pd.DataFrame(idio, index=dates, columns=cols)
    fwd_q_idio = idio_df.rolling(QUARTER_DAYS).sum().shift(-QUARTER_DAYS + 1)
    tone_peek = cs_z(fwd_q_idio.fillna(0.0).to_numpy()) * 0.85 \
        + rng.standard_normal((n_days, n_assets)) * 0.15
    fields["mgmt_tone_quarter"] = panel(tone_peek).where(listed)
    field_lags["mgmt_tone_quarter"] = QUARTER_DAYS + 2

    surp_peek = cs_z(fwd_q_idio.fillna(0.0).to_numpy()) * 0.80 \
        + rng.standard_normal((n_days, n_assets)) * 0.20
    fields["earnings_surprise_quarter"] = panel(surp_peek).where(listed)
    field_lags["earnings_surprise_quarter"] = QUARTER_DAYS + 2

    nextday_peek = cs_z(np.roll(idio, -1, axis=0)) * 0.80 \
        + rng.standard_normal((n_days, n_assets)) * 0.20
    fields["news_sentiment_nextday"] = panel(nextday_peek).where(listed)
    field_lags["news_sentiment_nextday"] = 1

    # backward (PIT) tone variants - weak, unused by sound templates
    bwd_q_idio = idio_df.rolling(QUARTER_DAYS).sum()
    fields["mgmt_tone"] = panel(cs_z(bwd_q_idio.fillna(0.0).to_numpy()) * 0.30
                                + rng.standard_normal((n_days, n_assets)) * 0.70).where(listed)
    field_lags["mgmt_tone"] = 0

    survivors = listed.iloc[-1].to_numpy()
    mkt = pd.Series(mkt_ret, index=dates, name="mkt")
    return MarketPanel(
        dates=dates, close=close, open_=open_, high=high, low=low, volume=volume,
        mkt=mkt, regime=regime, listed=listed, survivors=survivors,
        field_lags=field_lags, delisted=delisted, fields=fields,
    )
