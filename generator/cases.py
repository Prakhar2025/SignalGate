"""Case catalog: 60 seeded cases across six strata (docs/07 §2).

Split: 48 dev / 12 sealed hold-out. Hold-out ids: f1_09, f1_10, f2_10, f2_11,
f2_12, f3_09, f3_10, f4_09, f4_10, f5_08, s0_09, s0_10.

Each case carries ground truth (family, mechanism, expected verdict) in the
manifest - never inside the spec file itself. Prose is written to read like
real research-team submissions: the flaw is visible to a careful reader, and
the probes make it measurable. `strength` documents injection strength so
marginal cases are a *design property* (and feed the failure taxonomy), not
an accident.
"""
from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class CaseDef:
    case_id: str
    family: str            # F1..F5, S0
    name: str
    description: str
    pseudocode: str
    notes: str = ""
    universe: str = "all"
    horizon: int = 21
    costs_bps: float = 10.0
    rebalance: str = "daily"
    mechanism: str = ""
    strength: str = "strong"   # strong | medium | subtle


def spec_dict(c: CaseDef) -> dict:
    return {
        "name": c.name,
        "description": c.description,
        "pseudocode": c.pseudocode,
        "params": {
            "universe": c.universe,
            "horizon": c.horizon,
            "costs_bps": c.costs_bps,
            "rebalance": c.rebalance,
        },
        "notes": c.notes or None,
    }


# --------------------------------------------------------------------- F1
# Syntactic lookahead: the pseudocode itself references future bars.

F1: list[CaseDef] = [
    CaseDef(
        case_id="f1_01", family="F1", name="Momentum Ignition",
        description=(
            "Classic 12-1 cross-sectional momentum with a fast exit. Long the top-ranked "
            "names, short the bottom, rebalanced daily over the full cross-section. "
            "21-day holding period, costs modeled at 12 bps per side."
        ),
        pseudocode="mom = pct_change(close, 252) - pct_change(close, 21)\n"
                   "score = rank(mom + shift(close, -1) / close - 1)",
        mechanism="momentum blended with next-day close (shift(-1)) - future price inside the score",
    ),
    CaseDef(
        case_id="f1_02", family="F1", name="Breakout Continuation",
        description=(
            "Breakout system: names pushing above their 63-day high with expanding range "
            "keep running. Long tilt expressed as a cross-sectional rank. 10-day holding "
            "period, costs at 10 bps."
        ),
        pseudocode="hi = ts_max(close, 63)\nscore = rank(lead(close, 1) / hi)",
        mechanism="lead(close, 1) - tomorrow's close in the breakout score",
    ),
    CaseDef(
        case_id="f1_03", family="F1", name="Smoothed Reversion Plus",
        description=(
            "Short-horizon reversion smoothed over three days; a three-bar forward "
            "reference on the price series stabilizes the rank. 5-day holding period, "
            "costs at 8 bps."
        ),
        pseudocode="rev = -pct_change(close, 5)\n"
                   "score = rank(ts_mean(rev, 3) + shift(close, -3) / close - 1)",
        mechanism="reversion blended with 3-day-forward close",
    ),
    CaseDef(
        case_id="f1_04", family="F1", name="Volume-Price Momentum",
        description=(
            "Momentum confirmed by volume: price trend times participation. The volume "
            "series is taken one bar ahead to line up with the order file. 10-day "
            "holding period, costs at 10 bps."
        ),
        pseudocode="vm = pct_change(close, 63) * ts_mean(volume, 10)\n"
                   "score = rank(vm + ts_mean(shift(volume, -1), 5) / ts_mean(volume, 5))",
        mechanism="volume shifted one day forward - mild future-participation signal",
        strength="subtle",
    ),
    CaseDef(
        case_id="f1_05", family="F1", name="Range Expansion Roll",
        description=(
            "Range-expansion continuation: recent true range predicts follow-through. We "
            "roll the range reference five bars ahead so the score is ready before the "
            "open. 10-day holding period, costs at 8 bps."
        ),
        pseudocode="rng = (high - low) / close\nscore = rank(shift(rng, -5))",
        mechanism="score computed on the next five bars' high/low range",
    ),
    CaseDef(
        case_id="f1_06", family="F1", name="Delayed-Confirmation Trend",
        description=(
            "Trend score on the 126-day slope with a two-bar confirmation offset, so the "
            "rank lines up with the execution file. 10-day holding period, costs at "
            "10 bps."
        ),
        pseudocode="trend = pct_change(close, 126)\n"
                   "score = rank(delay(close, -2) / close - 1) + 0.5 * rank(trend)",
        mechanism="delay(close, -2) - a negative delay reads the future",
    ),
    CaseDef(
        case_id="f1_07", family="F1", name="Overnight Continuation Edge",
        description=(
            "Overnight-to-open continuation: names up tonight keep going tomorrow. Score "
            "by the next return directly; everything else is standard risk controls. "
            "5-day holding period, costs at 5 bps."
        ),
        pseudocode="score = rank(pct_change(close, -1))",
        mechanism="pct_change with negative lag = next-day return used as the feature",
    ),
    CaseDef(
        case_id="f1_08", family="F1", name="Quality-Weighted Momentum",
        description=(
            "Momentum weighted by a quality proxy (shallow drawdown over the year). The "
            "rank is anchored on the closing print one bar ahead so the book matches the "
            "morning file. 21-day holding period, costs at 12 bps."
        ),
        pseudocode="qual = -ts_max((close - ts_max(close, 252)) / ts_max(close, 252), 252)\n"
                   "score = rank(pct_change(close, 252) - pct_change(close, 21)) + rank(qual) + shift(close, -1) / close - 1",
        mechanism="momentum + quality blended with next-day close",
    ),
    CaseDef(
        case_id="f1_09", family="F1", name="Participation Surge",
        description=(
            "Volume-surge continuation with a two-bar lead on participation so the signal "
            "is available before the open auction. 5-day holding period, costs at 5 bps."
        ),
        pseudocode="surge = volume / ts_mean(volume, 21)\nscore = rank(lead(volume, 2) / ts_mean(volume, 21))",
        mechanism="lead(volume, 2) - future participation in the score",
        strength="subtle",
    ),
    CaseDef(
        case_id="f1_10", family="F1", name="Two-Day Reversion Refresh",
        description=(
            "Two-day reversion refreshed each close against the next print; the refresh "
            "keeps the book aligned with the execution file. 5-day holding period, costs "
            "at 5 bps."
        ),
        pseudocode="rev = -pct_change(close, 2)\nscore = rank(rev + shift(close, -2) / close - 1)",
        mechanism="reversion blended with 2-day-forward close",
    ),
]


# --------------------------------------------------------------------- F2
# Semantic lookahead: the prose sounds disciplined, the vendor field is
# forward-restated (its value at t aggregates the in-progress period).

F2_FLAGSHIP_PROSE = (
    "Score each name by how strongly management sounds about next quarter: we parse the "
    "tone of the quarterly filing and go long the confident names, short the cautious "
    "ones. Positions are priced at quarter-end and rebalanced daily. Universe is the "
    "full cross-section; 21-day holding period; costs modeled at 10 bps."
)

F2: list[CaseDef] = [
    CaseDef(
        case_id="f2_01", family="F2", name="Management Tone Confidence",
        description=F2_FLAGSHIP_PROSE,
        pseudocode="score = rank(mgmt_tone_quarter)",
        mechanism="vendor tone field is forward-restated (value at t reflects the in-progress quarter)",
    ),
    CaseDef(
        case_id="f2_02", family="F2", name="Earnings Surprise Alignment",
        description=(
            "Post-earnings drift with a twist: we score by the surprise of the quarter "
            "being reported, aligned to the decision date. Long positive surprise, short "
            "negative, daily rebalance, 21-day holding period, 10 bps costs."
        ),
        pseudocode="score = rank(earnings_surprise_quarter)",
        mechanism="surprise field keyed to the in-progress quarter (forward-restated)",
    ),
    CaseDef(
        case_id="f2_03", family="F2", name="Next-Day News Momentum",
        description=(
            "News flow leads price: score names by aggregate news sentiment and hold for "
            "a week. The vendor feed stamps sentiment on the session it describes, so "
            "the signal is fresh at the close. 5-day holding period, costs at 8 bps."
        ),
        pseudocode="score = rank(news_sentiment_nextday)",
        mechanism="sentiment stamp refers to the following session (forward-restated)",
    ),
    CaseDef(
        case_id="f2_04", family="F2", name="Tone-Weighted Momentum",
        description=(
            "Momentum where management confidence doubles the weight: strong tone "
            "amplifies the trend score. Priced at quarter-end, 21-day holding period, "
            "12 bps costs."
        ),
        pseudocode="score = rank(pct_change(close, 252) - pct_change(close, 21)) + rank(mgmt_tone_quarter)",
        mechanism="half the score is the forward-restated tone field",
    ),
    CaseDef(
        case_id="f2_05", family="F2", name="Surprise-Volume Combo",
        description=(
            "Combine the earnings surprise of the reporting quarter with a volume-"
            "confirmation overlay. Daily rebalance, 10-day holding period, 10 bps costs."
        ),
        pseudocode="score = rank(earnings_surprise_quarter) + 0.5 * rank(volume / ts_mean(volume, 21))",
        mechanism="forward-restated surprise blended with volume confirmation",
    ),
    CaseDef(
        case_id="f2_06", family="F2", name="News-Confirmed Trend",
        description=(
            "Twelve-month trend confirmed by fresh news sentiment; the feed timestamps "
            "sentiment on the session it covers so nothing is stale. 10-day holding "
            "period, 10 bps costs."
        ),
        pseudocode="score = rank(pct_change(close, 252) - pct_change(close, 21)) + 0.5 * rank(news_sentiment_nextday)",
        mechanism="trend plus half-weight forward-restated sentiment",
        strength="medium",
    ),
    CaseDef(
        case_id="f2_07", family="F2", name="Quarter-Ahead Confidence Screen",
        description=(
            "We rank the cross-section by management tone and dilute to a quarter "
            "position in the extremes; the vendor marks each record with the quarter it "
            "describes, which is the quarter we trade. 21-day holding period, 10 bps."
        ),
        pseudocode="score = 0.5 * rank(mgmt_tone_quarter) + 0.25 * rank(mgmt_tone)",
        mechanism="forward-restated tone at half weight; PIT tone as control",
        strength="medium",
    ),
    CaseDef(
        case_id="f2_08", family="F2", name="Liquid Surprise Drift",
        description=(
            "Earnings-surprise drift restricted to liquid names: surprise of the "
            "reporting quarter times a participation filter. Daily rebalance, 10-day "
            "holding period, 10 bps costs."
        ),
        pseudocode="score = rank(earnings_surprise_quarter) * (rank(volume) > -0.35)",
        mechanism="forward-restated surprise behind a liquidity filter",
    ),
    CaseDef(
        case_id="f2_09", family="F2", name="Weekly Tone Rebalance",
        description=(
            "Weekly rebalanced tone portfolio: long the confident quarter of management "
            "narratives, short the cautious. Weekly turnover keeps costs near 8 bps."
        ),
        pseudocode="score = rank(mgmt_tone_quarter)",
        rebalance="weekly",
        mechanism="forward-restated tone, weekly rebalance",
    ),
    CaseDef(
        case_id="f2_10", family="F2", name="Surprise Momentum Stack",
        description=(
            "Stack the reporting-quarter surprise on twelve-month momentum; daily "
            "rebalance, 21-day holding period, 12 bps costs."
        ),
        pseudocode="score = rank(pct_change(close, 252) - pct_change(close, 21)) + rank(earnings_surprise_quarter)",
        mechanism="momentum plus forward-restated surprise (holdout)",
    ),
    CaseDef(
        case_id="f2_11", family="F2", name="Overnight Sentiment Check",
        description=(
            "Short-horizon sentiment: the vendor stamps tomorrow's news aggregate on "
            "tonight's record, so the score is knowable before the open. 5-day holding "
            "period, 5 bps costs."
        ),
        pseudocode="score = rank(news_sentiment_nextday) * (rank(volume) > -0.35)",
        mechanism="forward-restated next-day sentiment behind a liquidity filter (holdout)",
        strength="medium",
    ),
    CaseDef(
        case_id="f2_12", family="F2", name="Quarter-End Tone Screen",
        description=(
            "The research note is explicit: score by how strongly management sounds "
            "about next quarter, priced at quarter-end. Full cross-section, 21-day "
            "holding period, 10 bps costs."
        ),
        pseudocode="score = rank(mgmt_tone_quarter) + 0.2 * rank(ts_mean(ret, 21))",
        mechanism="forward-restated tone plus a small trend kicker (holdout)",
    ),
]


# --------------------------------------------------------------------- F3
# Survivorship: the backtest universe is the constituents as of the final day.
# Reversion families are long the crashers, so the point-in-time re-run bites.

F3: list[CaseDef] = [
    CaseDef(
        case_id="f3_01", family="F3", name="Reversion on Current Constituents",
        description=(
            "Five-day reversion on the current constituents of the universe: buy the "
            "dips among names we can still trade today. Daily rebalance, 5-day holding "
            "period, 5 bps costs."
        ),
        pseudocode="score = -rank(pct_change(close, 5))",
        universe="survivors",
        mechanism="backtested only on assets listed on the final day",
    ),
    CaseDef(
        case_id="f3_02", family="F3", name="Dip-Buying on Today's Members",
        description=(
            "Five-day reversion restricted to today's constituents: long the dips among "
            "the names that exist now. Daily rebalance, 5-day holding period, 5 bps."
        ),
        pseudocode="score = -rank(pct_change(close, 5))",
        universe="survivors",
        mechanism="survivor universe on reversion (keyword-visible phrasing)",
    ),
    CaseDef(
        case_id="f3_03", family="F3", name="Liquidity-Filtered Reversion",
        description=(
            "Ten-day reversion on currently listed names with a participation floor. "
            "Daily rebalance, 10-day holding period, 6 bps costs."
        ),
        pseudocode="score = -rank(pct_change(close, 10)) * (rank(volume) > -0.35)",
        universe="survivors",
        mechanism="survivor universe plus liquidity filter",
    ),
    CaseDef(
        case_id="f3_04", family="F3", name="Index-as-it-stands Reversion",
        description=(
            "Five-day reversion where the universe is the index as it stands today - we "
            "only ever trade what exists. Daily rebalance, 5-day holding period, 5 bps."
        ),
        pseudocode="score = -rank(pct_change(close, 5))",
        universe="survivors",
        mechanism="survivor universe; phrasing avoids standard keywords",
        strength="medium",
    ),
    CaseDef(
        case_id="f3_05", family="F3", name="Reconstructed-Universe Reversion",
        description=(
            "Five-day reversion with a point-in-time aware universe selection: membership "
            "is reconstructed as of each decision date from the vendor master."
        ),
        pseudocode="score = -rank(pct_change(close, 5))",
        universe="survivors",
        notes="Vendor master only carries names that are listed as of the pull date.",
        mechanism="prose claims point-in-time discipline; universe is survivors (contradiction)",
        strength="medium",
    ),
    CaseDef(
        case_id="f3_06", family="F3", name="Still-Listed Reversion",
        description=(
            "Ten-day reversion on names still trading at the review date, with a "
            "participation floor. Daily rebalance, 10-day holding period, 6 bps costs."
        ),
        pseudocode="score = -rank(pct_change(close, 10)) * (rank(volume) > -0.35)",
        universe="survivors",
        mechanism="survivor universe; phrasing avoids standard keywords",
        strength="medium",
    ),
    CaseDef(
        case_id="f3_07", family="F3", name="Fast Reversion on Current Names",
        description=(
            "Two-day reversion on current constituents with a participation floor; the "
            "fast book needs the tightest spreads we can actually get. Daily rebalance, "
            "5-day holding period, 5 bps costs."
        ),
        pseudocode="score = -rank(pct_change(close, 2)) * (rank(volume) > -0.30)",
        universe="survivors",
        mechanism="survivor universe, fast reversion",
    ),
    CaseDef(
        case_id="f3_08", family="F3", name="Combination on Standing Members",
        description=(
            "Momentum plus low-vol combo on today's members of the cross-section. "
            "21-day holding period, 12 bps costs."
        ),
        pseudocode="score = rank(pct_change(close, 252) - pct_change(close, 21)) + rank(-ts_std(ret, 63)) * (rank(volume) > -0.30)",
        universe="survivors",
        mechanism="survivor universe on a momentum combo (survivorship may not bite - hard case)",
        strength="subtle",
    ),
    CaseDef(
        case_id="f3_09", family="F3", name="Holdout Reversion on Current Names",
        description=(
            "Five-day reversion on the current constituents with a participation floor; "
            "sealed-split twin of the dev flagship. Daily rebalance, 5-day holding "
            "period, 5 bps costs."
        ),
        pseudocode="score = -rank(pct_change(close, 5)) * (rank(volume) > -0.35)",
        universe="survivors",
        mechanism="survivor universe plus liquidity filter (holdout)",
    ),
    CaseDef(
        case_id="f3_10", family="F3", name="Standing-Index Dip Buyer",
        description=(
            "Ten-day reversion on the standing index membership; long the dips among "
            "names we can still trade. Daily rebalance, 10-day holding period, 6 bps."
        ),
        pseudocode="score = -rank(pct_change(close, 10)) * (rank(volume) > -0.35)",
        universe="survivors",
        mechanism="survivor universe (holdout)",
        strength="medium",
    ),
]


# --------------------------------------------------------------------- F4
# P-hacking: best-of-N in-sample selection on a noise family, no correction.
# build.py pins the selected lookback into PLACEHOLDER pseudocode.

F4: list[CaseDef] = [
    CaseDef(
        case_id="f4_01", family="F4", name="Grid-Selected Participation",
        description=(
            "Participation factor: names with elevated cumulative volume keep "
            "outperforming. We screened a grid of 40 lookback windows and kept the best "
            "performer. Daily rebalance, 10-day holding period, 10 bps costs."
        ),
        pseudocode="F4_PLACEHOLDER",
        mechanism="best-of-40 in-sample selection on a noise family; clue in description (lint-visible)",
    ),
    CaseDef(
        case_id="f4_02", family="F4", name="Tuned Volume Trend",
        description=(
            "Volume-trend continuation. Parameters come from our usual tuning pass. "
            "Daily rebalance, 10-day holding period, 10 bps costs."
        ),
        pseudocode="F4_PLACEHOLDER",
        notes="Tuning: 40 lookback windows tried on the same window; the top in-sample IC was shipped uncorrected.",
        mechanism="best-of-40 hidden in notes (agent-visible, lint-blind)",
    ),
    CaseDef(
        case_id="f4_03", family="F4", name="Screened Reversion Variant",
        description=(
            "Volume-carry factor with the lookback chosen from a screen of 24 "
            "candidates; the winner cleared our significance bar in-sample. Daily "
            "rebalance, 10-day holding period, 10 bps costs."
        ),
        pseudocode="F4_PLACEHOLDER",
        mechanism="best-of-24 selection, clue in description",
    ),
    CaseDef(
        case_id="f4_04", family="F4", name="Iterated Turnover Factor",
        description=(
            "Turnover-heavy participation score, costs modeled at 1 bp "
            "(internalization). Search details in notes. Daily rebalance, 10-day "
            "holding period."
        ),
        pseudocode="F4_PLACEHOLDER",
        notes="We iterated 40 lookbacks until the Sharpe peaked; shipped the peak.",
        mechanism="best-of-40 in notes + 1 bp declared costs (turnover evidence in bundle)",
        costs_bps=1.0,
    ),
    CaseDef(
        case_id="f4_05", family="F4", name="Lattice-Searched Participation",
        description=(
            "Participation factor with the window chosen from our parameter lattice. "
            "Daily rebalance, 10-day holding period, 10 bps costs."
        ),
        pseudocode="F4_PLACEHOLDER",
        notes="Lattice: 40 windows scanned in-sample, top performer selected.",
        mechanism="best-of-40 hidden in notes",
    ),
    CaseDef(
        case_id="f4_06", family="F4", name="Standard-Lattice Volume Score",
        description=(
            "Volume-carry score tuned the usual way. Daily rebalance, 10-day holding "
            "period, 10 bps costs."
        ),
        pseudocode="F4_PLACEHOLDER",
        notes="Standard grid search over our usual parameter lattice; ship the winner.",
        mechanism="selection disclosed without a count (expected miss - deflation needs a number)",
        strength="subtle",
    ),
    CaseDef(
        case_id="f4_07", family="F4", name="Forty-Window Participation",
        description=(
            "Participation factor, lookback selected by sweeping 40 windows against the "
            "same tape. Daily rebalance, 10-day holding period, 10 bps costs."
        ),
        pseudocode="F4_PLACEHOLDER",
        mechanism="best-of-40, clue in description (lint-visible)",
    ),
    CaseDef(
        case_id="f4_08", family="F4", name="Quiet-Search Participation",
        description=(
            "Participation-carry score; the tuning notebook has the details. Daily "
            "rebalance, 10-day holding period, 10 bps costs."
        ),
        pseudocode="F4_PLACEHOLDER",
        notes="Notebook 2026-06-12: 40 lookbacks evaluated, best in-sample IC shipped.",
        mechanism="best-of-40 hidden in notes",
    ),
    CaseDef(
        case_id="f4_09", family="F4", name="Sealed-Grid Participation",
        description=(
            "Volume-carry factor with the window from a 40-wide sweep on the same "
            "sample; sealed-split twin of the dev search. Daily rebalance, 10-day "
            "holding period, 10 bps costs."
        ),
        pseudocode="F4_PLACEHOLDER",
        mechanism="best-of-40 (holdout)",
    ),
    CaseDef(
        case_id="f4_10", family="F4", name="Sealed Participation Tune",
        description=(
            "Participation factor tuned by scanning 40 windows in-sample. Daily "
            "rebalance, 10-day holding period, 10 bps costs."
        ),
        pseudocode="F4_PLACEHOLDER",
        mechanism="best-of-40 (holdout)",
        strength="medium",
    ),
]


# --------------------------------------------------------------------- F5
# Regime-overfit: the signal only engages above its long mean (params chosen
# on the bull window), so the leak-proof regime table shows a sign collapse.

def f5_spec(ma: int, lookback: int) -> str:
    return (f"gate = close > ts_mean(close, {ma})\n"
            f"score = where(gate, -rank(pct_change(close, {lookback})) * (rank(volume) > -0.30), 0)")


F5: list[CaseDef] = [
    CaseDef(
        case_id="f5_01", family="F5", name="Bull-Gated Reversion",
        description=(
            "Short-horizon reversion that only engages while the name trades above its "
            "200-day mean - designed for bull markets, where reversion pays best. "
            "Daily rebalance, 5-day holding period, 5 bps costs."
        ),
        pseudocode=f5_spec(200, 5),
        horizon=5, costs_bps=5.0,
        mechanism="gate fires only above the long mean; params chosen on the bull window",
    ),
    CaseDef(
        case_id="f5_02", family="F5", name="Uptrend Reversion 150",
        description=(
            "Reversion gated on the 150-day mean; validated on the strong recent tape. "
            "Daily rebalance, 10-day holding period, 5 bps costs."
        ),
        pseudocode=f5_spec(150, 5),
        horizon=10, costs_bps=5.0,
        notes="Validation window: the strong tape of the past year - that is where the book lives.",
        mechanism="gate + params validated on a single regime window",
    ),
    CaseDef(
        case_id="f5_03", family="F5", name="Above-the-Mean Reversion 100",
        description=(
            "Five-day reversion while price holds above its 100-day mean. Daily "
            "rebalance, 10-day holding period, 5 bps costs."
        ),
        pseudocode=f5_spec(100, 5),
        horizon=10, costs_bps=5.0,
        mechanism="regime-gated signal, params fit on bull window",
    ),
    CaseDef(
        case_id="f5_04", family="F5", name="Trend-Day Reversion 200",
        description=(
            "Five-day reversion above the 200-day mean; the gate keeps us out of "
            "downtapes. Daily rebalance, 21-day holding period, 6 bps costs."
        ),
        pseudocode=f5_spec(200, 5),
        horizon=21, costs_bps=6.0,
        mechanism="regime-gated signal",
    ),
    CaseDef(
        case_id="f5_05", family="F5", name="Sealed Bull-Gate Reversion",
        description=(
            "Five-day reversion gated on the 200-day mean, tuned on the bull window of "
            "the sealed split. Daily rebalance, 5-day holding period, 5 bps costs."
        ),
        pseudocode=f5_spec(200, 5),
        horizon=5, costs_bps=5.0,
        mechanism="regime-gated signal (holdout)",
    ),
    CaseDef(
        case_id="f5_06", family="F5", name="Gate-150 Fast Reversion",
        description=(
            "Five-day reversion above the 150-day mean; the gate was sized on the "
            "periods where the book was live. Daily rebalance, 5-day holding period, "
            "5 bps costs."
        ),
        pseudocode=f5_spec(150, 5),
        horizon=5, costs_bps=5.0,
        mechanism="regime-gated signal (holdout)",
        strength="medium",
    ),
    CaseDef(
        case_id="f5_07", family="F5", name="Bull-Window Reversion",
        description=(
            "Five-day reversion above the 200-day mean; parameters fitted to the bull "
            "window only, per the original mandate. Daily rebalance, 10-day holding "
            "period, 5 bps costs."
        ),
        pseudocode=f5_spec(200, 5),
        horizon=10, costs_bps=5.0,
        mechanism="regime-gated signal",
    ),
    CaseDef(
        case_id="f5_08", family="F5", name="Gated-Flow Reversion",
        description=(
            "Reversion above the 200-day mean with a participation floor; the gate was "
            "chosen on the strong tape. Daily rebalance, 10-day holding period, 5 bps."
        ),
        pseudocode="gate = close > ts_mean(close, 200)\n"
                   "score = where(gate, -rank(pct_change(close, 5)) * (rank(volume) > -0.35), 0)",
        horizon=10, costs_bps=5.0,
        mechanism="regime-gated + liquidity-filtered (holdout)",
        strength="medium",
    ),
]


# --------------------------------------------------------------------- S0

S0: list[CaseDef] = [
    CaseDef(
        case_id="s0_01", family="S0", name="Twelve-One Momentum (flagship)",
        description=(
            "Standard 12-1 cross-sectional momentum: twelve-month price change excluding "
            "the most recent month, ranked daily on the liquid subset of the point-in-"
            "time universe (bottom volume quintile excluded each day), 21-day holding "
            "costs modeled conservatively at 15 bps per side."
        ),
        pseudocode="score = rank(pct_change(close, 252) - pct_change(close, 21)) * (rank(volume) > -0.30)",
        horizon=21, costs_bps=15.0,
        rebalance="weekly",
        mechanism="cost-aware momentum; point-in-time universe; deflated significance",
    ),
    CaseDef(
        case_id="s0_02", family="S0", name="Nine-One Momentum",
        description=(
            "Nine-month variant of classic momentum with a one-month skip, ranked "
            "cross-sectionally on the point-in-time universe. 10-day holding period, "
            "12 bps costs."
        ),
        pseudocode="score = rank(pct_change(close, 189) - pct_change(close, 21)) * (rank(volume) > -0.30)",
        horizon=10, costs_bps=12.0,
        rebalance="weekly",
        mechanism="momentum variant, honest parameters",
    ),
    CaseDef(
        case_id="s0_03", family="S0", name="Low-Volatility Anomaly",
        description=(
            "Long the calm names: sixty-three-day return volatility ranked inversely. "
            "Point-in-time universe, 21-day holding period, 10 bps costs."
        ),
        pseudocode="score = -rank(ts_std(ret, 63))",
        horizon=21, costs_bps=10.0,
        rebalance="weekly",
        mechanism="low-vol anomaly with honest costs",
    ),
    CaseDef(
        case_id="s0_04", family="S0", name="Low-Volatility, Fast",
        description=(
            "Fast low-volatility screen: twenty-one-day return volatility ranked "
            "inversely, the quicker sibling of the classic anomaly. Point-in-time "
            "universe, 21-day holding period, 10 bps costs."
        ),
        pseudocode="score = -rank(ts_std(ret, 21))",
        horizon=21, costs_bps=10.0,
        mechanism="fast low-vol anomaly with honest costs",
    ),
    CaseDef(
        case_id="s0_05", family="S0", name="Double Momentum Blend",
        description=(
            "Equal blend of the 12-1 and 6-1 momentum scores; the two lookbacks "
            "diversify the trend estimate and halve the churn of either alone. "
            "Point-in-time universe, 21-day holding period, 12 bps costs."
        ),
        pseudocode="score = (0.5 * rank(pct_change(close, 252) - pct_change(close, 21)) + 0.5 * rank(pct_change(close, 126) - pct_change(close, 21))) * (rank(volume) > -0.30)",
        horizon=21, costs_bps=12.0,
        mechanism="momentum blend with honest parameters",
    ),
    CaseDef(
        case_id="s0_06", family="S0", name="News-Flow Drift",
        description=(
            "Names with positive published news sentiment drift: rank by the sentiment "
            "of records published up to each decision date. Point-in-time universe, "
            "21-day holding period, 10 bps costs."
        ),
        pseudocode="score = rank(news_sentiment)",
        horizon=21, costs_bps=10.0,
        rebalance="weekly",
        mechanism="PIT news field; drift is genuine alpha in this world",
    ),
    CaseDef(
        case_id="s0_07", family="S0", name="Post-Earnings-Announcement Drift",
        description=(
            "Classic PEAD: rank by the most recently disclosed earnings surprise (known "
            "at the decision date by construction) and hold. Point-in-time universe, "
            "21-day holding period, 10 bps costs."
        ),
        pseudocode="score = rank(earnings_surprise)",
        horizon=21, costs_bps=10.0,
        rebalance="weekly",
        mechanism="disclosed surprise with baked 40-day drift",
    ),
    CaseDef(
        case_id="s0_08", family="S0", name="Momentum-LowVol Combination",
        description=(
            "Equal-weight combination of 12-1 momentum and the low-volatility screen; "
            "the two are nearly uncorrelated and the blend halves turnover. Point-in-"
            "time universe, 21-day holding period, 12 bps costs."
        ),
        pseudocode="score = rank(pct_change(close, 252) - pct_change(close, 21)) + rank(-ts_std(ret, 63)) * (rank(volume) > -0.30)",
        horizon=21, costs_bps=12.0,
        rebalance="weekly",
        mechanism="combination template with honest parameters",
    ),
    CaseDef(
        case_id="s0_09", family="S0", name="Six-One Momentum (holdout)",
        description=(
            "Six-month momentum with a one-month skip on the point-in-time universe. "
            "10-day holding period, 12 bps costs."
        ),
        pseudocode="score = rank(pct_change(close, 126) - pct_change(close, 21)) * (rank(volume) > -0.30)",
        horizon=10, costs_bps=12.0,
        rebalance="weekly",
        mechanism="momentum variant (holdout)",
    ),
    CaseDef(
        case_id="s0_10", family="S0", name="Sealed Nine-Two Momentum",
        description=(
            "Nine-month momentum with a two-month skip on the point-in-time universe; "
            "sealed-split twin of the dev momentum family. 10-day holding period, "
            "12 bps costs."
        ),
        pseudocode="score = rank(pct_change(close, 189) - pct_change(close, 42)) * (rank(volume) > -0.30)",
        horizon=10, costs_bps=12.0,
        mechanism="momentum variant (holdout)",
    ),
]


def _set_weekly(cases: list[CaseDef]) -> list[CaseDef]:
    """Benchmark cases rebalance weekly (matches their holding periods)."""
    return [replace(c, rebalance="weekly") for c in cases]


F1 = _set_weekly(F1)
F2 = _set_weekly(F2)
F3 = _set_weekly(F3)
F4 = [replace(c, rebalance="weekly") if c.case_id != "f4_04" else c for c in F4]
F5 = _set_weekly(F5)
S0 = _set_weekly(S0)

ALL_CASES: list[CaseDef] = F1 + F2 + F3 + F4 + F5 + S0

DEV_IDS = ({f"f1_{i:02d}" for i in range(1, 9)}
           | {f"f2_{i:02d}" for i in range(1, 10)}
           | {f"f3_{i:02d}" for i in range(1, 9)}
           | {f"f4_{i:02d}" for i in range(1, 9)}
           | {f"f5_{i:02d}" for i in range(1, 8)}
           | {f"s0_{i:02d}" for i in range(1, 9)})
HOLDOUT_IDS = {c.case_id for c in ALL_CASES} - DEV_IDS

FAMILY_COUNTS = {"F1": 10, "F2": 12, "F3": 10, "F4": 10, "F5": 8, "S0": 10}
EXPECTED = {"F1": "REJECT_SPURIOUS", "F2": "REJECT_SPURIOUS", "F3": "REJECT_SPURIOUS",
            "F4": "REJECT_SPURIOUS", "F5": "REJECT_SPURIOUS", "S0": "PROMISING"}
