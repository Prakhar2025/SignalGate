"""SignalGate configuration - env-only credentials (ground rule 08)."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _repo_root() -> Path:
    # src/signalgate/config.py -> repo root is three levels up
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    mode: str                    # "mock" | "live" (requested)
    effective_mode: str          # what will actually run (live degrades to mock without creds)
    model: str
    api_base: str
    api_key_set: bool
    api_key: str = ""            # runtime-only; never logged, never persisted
    spend_cap_usd: float = 2.00
    seed: int = 20260828
    data_dir: Path = Path("data")
    artifacts_dir: Path = Path("artifacts")
    reports_dir: Path = Path("reports")

    @property
    def market_path(self) -> Path:
        return self.data_dir / "market.npz"


def load_settings(repo_root: Path | None = None) -> Settings:
    root = repo_root or _repo_root()
    requested = os.getenv("SIGNALGATE_MODE", "mock").strip().lower()
    model = os.getenv("SIGNALGATE_MODEL", "").strip()
    api_base = os.getenv("SIGNALGATE_API_BASE", "").strip()
    api_key = os.getenv("SIGNALGATE_API_KEY", "").strip()
    live_ready = bool(model and api_base and api_key)
    effective = "live" if (requested == "live" and live_ready) else "mock"
    return Settings(
        mode=requested,
        effective_mode=effective,
        model=model or "LOCAL_MOCK",
        api_base=api_base,
        api_key_set=bool(api_key),
        api_key=api_key,
        spend_cap_usd=float(os.getenv("SIGNALGATE_SPEND_CAP_USD", "2.00")),
        seed=int(os.getenv("SIGNALGATE_SEED", "20260828")),
        data_dir=root / "data",
        artifacts_dir=root / "artifacts",
        reports_dir=root / "reports",
    )
