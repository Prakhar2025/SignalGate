"""Sandboxed probe worker: `python -m signalgate.probes.worker request.json response.json`.

Runs exactly one probe against the synthetic panel and exits. No network
imports, no persistence - the sandbox boundary is this process.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from signalgate.dsl import as_written_and_pit, compile_program
from signalgate.market_data import load_market
from signalgate.probes.metrics import (
    circular_permutation_p,
    forward_returns,
    mean_ic,
    regime_table,
    sidak_deflate,
    turnover_and_net_sharpe,
)


def _universe_written(market, universe: str):
    if universe != "survivors":
        return None
    import numpy as np
    import pandas as pd
    mask = np.tile(market.survivors, (len(market.dates), 1))
    return pd.DataFrame(mask, index=market.dates, columns=market.close.columns)


def main() -> int:
    req_path, res_path = sys.argv[1], sys.argv[2]
    req = json.loads(Path(req_path).read_text(encoding="utf-8"))
    market = load_market(Path(req["market_path"]))
    program = compile_program(req["pseudocode"])
    horizon = int(req["horizon"])
    fwd = forward_returns(market.close, horizon, market.listed)

    out: dict = {"probe": req["probe"], "metrics": {}, "detail": {}}

    if req["probe"] == "timestamp_alignment_probe":
        written, pit = as_written_and_pit(
            program, market.as_fields(), market.field_lags,
            _universe_written(market, "survivors"), market.listed)
        ic_w, ic_p = mean_ic(written, fwd), mean_ic(pit, fwd)
        out["metrics"] = {
            "ic_as_written": round(ic_w, 4),
            "ic_point_in_time": round(ic_p, 4),
            "ic_delta": round(ic_w - ic_p, 4),
            "max_negative_shift": program.max_negative_shift,
        }
        out["detail"] = {"note": "delta = IC(as-written) - IC(leak-proof re-execution)"}

    elif req["probe"] == "label_permutation_test":
        written, _ = as_written_and_pit(
            program, market.as_fields(), market.field_lags,
            _universe_written(market, "survivors"), market.listed)
        p_raw, observed = circular_permutation_p(written, fwd, seed=int(req["seed"]))
        k = max(1, int(req["variants_tried"]))
        out["metrics"] = {
            "p_value": round(p_raw, 4),
            "observed_mean_ic": round(observed, 4),
            "variants_assumed": k,
            "p_deflated": round(sidak_deflate(p_raw, k), 4),
            "n_permutations": 199,
        }

    elif req["probe"] == "regime_subsample":
        _, pit = as_written_and_pit(
            program, market.as_fields(), market.field_lags,
            _universe_written(market, "survivors"), market.listed)
        table = regime_table(pit, fwd, market.regime)
        ics = [v["ic"] for v in table.values()]
        actives = [v["active"] for v in table.values()]
        out["metrics"] = {
            "min_regime_ic": round(min(ics), 4),
            "max_regime_ic": round(max(ics), 4),
            "min_regime_active": round(min(actives), 3),
        }
        out["detail"] = {"regimes": {k: {"ic": round(v["ic"], 4),
                                         "active": v["active"],
                                         "days": v["days"]}
                                      for k, v in table.items()}}

    elif req["probe"] == "turnover_and_cost_sanity":
        written, _ = as_written_and_pit(
            program, market.as_fields(), market.field_lags,
            _universe_written(market, "survivors"), market.listed)
        m = turnover_and_net_sharpe(written, market.close,
                                    costs_bps=float(req["costs_bps"]),
                                    horizon=horizon,
                                    universe_mask=None,
                                    rebalance=req["rebalance"])
        out["metrics"] = {
            "turnover_1s_daily": round(m["turnover_1s_daily"], 4),
            "turnover_annualized": round(m["turnover_annualized"], 2),
            "gross_sharpe": round(m["gross_sharpe"], 3),
            "net_sharpe": round(m["net_sharpe"], 3),
            "daily_cost_drag_bps": round(m["daily_cost_drag_bps"], 3),
            "miracle_flag": bool(m["gross_sharpe"] > 0.8 and m["net_sharpe"] < 0.0),
        }

    Path(res_path).write_text(json.dumps(out), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
