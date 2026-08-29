"""Shared fixtures: a small deterministic market for fast tests."""
from __future__ import annotations

import pytest
from generator.market import build_market

from signalgate.market_data import save_market


@pytest.fixture(scope="session")
def market_path(tmp_path_factory):
    panel = build_market(20260828, n_assets=30, n_days=320, n_distressed=4)
    path = tmp_path_factory.mktemp("data") / "market.npz"
    save_market(panel, path)
    return path


@pytest.fixture(scope="session")
def full_market_path(tmp_path_factory):
    """Production-size panel (50 x 750) - composer thresholds are calibrated on it."""
    panel = build_market(20260828, n_assets=50, n_days=750, n_distressed=10)
    path = tmp_path_factory.mktemp("fulldata") / "market.npz"
    save_market(panel, path)
    return path
