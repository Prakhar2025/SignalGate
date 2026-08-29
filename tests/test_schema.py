"""Spec schema fencing (docs/03 §2 trust boundary)."""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from signalgate.schemas import SignalSpec, SpecParams


def base_spec(**over):
    d = {
        "name": "Valid Spec",
        "description": "A sufficiently long description of the candidate signal.",
        "params": {"universe": "all", "horizon": 21, "costs_bps": 10.0},
    }
    d.update(over)
    return d


def test_valid_spec():
    spec = SignalSpec.model_validate(base_spec())
    assert spec.params.horizon == 21
    assert spec.params.rebalance == "daily"  # default
    assert spec.notes is None


def test_description_too_short_rejected():
    with pytest.raises(ValidationError):
        SignalSpec.model_validate(base_spec(description="too short"))


def test_bad_universe_rejected():
    with pytest.raises(ValidationError):
        SignalSpec.model_validate(base_spec(params={"universe": "everyone"}))


def test_horizon_bounds():
    with pytest.raises(ValidationError):
        SignalSpec.model_validate(base_spec(params={"horizon": 0}))
    with pytest.raises(ValidationError):
        SignalSpec.model_validate(base_spec(params={"horizon": 300}))
    assert SignalSpec.model_validate(
        base_spec(params={"horizon": 252})).params.horizon == 252


def test_costs_bounds():
    with pytest.raises(ValidationError):
        SignalSpec.model_validate(base_spec(params={"costs_bps": -1}))
    with pytest.raises(ValidationError):
        SignalSpec.model_validate(base_spec(params={"costs_bps": 101}))


def test_params_defaults():
    p = SpecParams()
    assert p.universe == "all" and p.rebalance == "daily"
