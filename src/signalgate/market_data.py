"""Synthetic market panel I/O - the ONLY data probes ever touch (ground rule 07)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

REGIME_NAMES = ["bull", "bear", "sideways"]


@dataclass(frozen=True)
class MarketPanel:
    dates: pd.DatetimeIndex
    close: pd.DataFrame
    open_: pd.DataFrame
    high: pd.DataFrame
    low: pd.DataFrame
    volume: pd.DataFrame
    mkt: pd.Series
    regime: np.ndarray            # (T,) int8: 0=bull 1=bear 2=sideways
    listed: pd.DataFrame          # (T×N) bool - point-in-time membership
    survivors: np.ndarray         # (N,) bool - constituents as of the final day
    field_lags: dict[str, int]    # PIT disclosure lag per alt-data field
    delisted: dict[str, int]      # asset -> delist day index
    fields: dict[str, pd.DataFrame] = field(default_factory=dict)  # alt-data fields

    def as_fields(self) -> dict[str, pd.DataFrame]:
        """Full DSL namespace: prices + market factor + alt-data fields."""
        ns = {
            "open": self.open_,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "mkt": self.mkt.to_frame("mkt"),
            "ret": self.close.pct_change(fill_method=None),
        }
        ns.update(self.fields)
        return ns


def save_market(panel: MarketPanel, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    field_names = list(panel.fields)
    payload = {
        "dates": panel.dates.asi8,
        "close": panel.close.to_numpy(),
        "open_": panel.open_.to_numpy(),
        "high": panel.high.to_numpy(),
        "low": panel.low.to_numpy(),
        "volume": panel.volume.to_numpy(),
        "mkt": panel.mkt.to_numpy(),
        "regime": panel.regime.astype(np.int8),
        "listed": panel.listed.to_numpy(),
        "survivors": panel.survivors,
        "columns": np.array(panel.close.columns, dtype="U16"),
        "field_lags": np.array(json.dumps(panel.field_lags)),
        "delisted": np.array(json.dumps(panel.delisted)),
        "field_names": np.array(field_names, dtype="U32"),
    }
    for i, name in enumerate(field_names):
        payload[f"field_{i}"] = panel.fields[name].to_numpy()
    np.savez_compressed(path, **payload)


def load_market(path: Path) -> MarketPanel:
    z = np.load(path, allow_pickle=False)
    dates = pd.DatetimeIndex(z["dates"].astype("int64"))
    cols = [str(c) for c in z["columns"]]

    def df(a: np.ndarray) -> pd.DataFrame:
        return pd.DataFrame(a, index=dates, columns=cols)

    fields = {
        str(name): df(z[f"field_{i}"])
        for i, name in enumerate(z["field_names"])
    }
    return MarketPanel(
        dates=dates,
        close=df(z["close"]),
        open_=df(z["open_"]),
        high=df(z["high"]),
        low=df(z["low"]),
        volume=df(z["volume"]),
        mkt=pd.Series(z["mkt"], index=dates, name="mkt"),
        regime=z["regime"].astype(np.int8),
        listed=df(z["listed"]).astype(bool),
        survivors=z["survivors"].astype(bool),
        field_lags=json.loads(str(z["field_lags"])),
        delisted=json.loads(str(z["delisted"])),
        fields=fields,
    )
