"""Mock reasoner determinism + JSON-gated contracts (docs/02 §2, 03 §9)."""
from __future__ import annotations

import jsonschema

from signalgate.agent import mock_reasoner
from signalgate.agent.investigator import INTERPRET_SCHEMA, PLAN_SCHEMA
from signalgate.schemas import SignalSpec


def make_spec(**over):
    d = {
        "name": "Management Tone Confidence",
        "description": (
            "Score each name by how strongly management sounds about next quarter: "
            "we parse the tone of the quarterly filing and go long the confident "
            "names, priced at quarter-end, 21-day holding period, 10 bps costs."),
        "pseudocode": "score = rank(mgmt_tone_quarter)",
        "notes": None,
        "params": {"universe": "all", "horizon": 21, "costs_bps": 10.0,
                   "rebalance": "weekly"},
    }
    d.update(over)
    return SignalSpec.model_validate(d)


def test_claims_detect_peek_field():
    claims = mock_reasoner.extract_claims(make_spec())
    assert any("mgmt_tone_quarter" in c.text for c in claims)


def test_claims_detect_contradiction():
    spec = make_spec(
        description="Point-in-time aware universe selection reconstructed as of "
                    "each decision date, a long description for the schema fence.",
        params={"universe": "survivors", "horizon": 21, "costs_bps": 10.0,
                "rebalance": "weekly"})
    claims = mock_reasoner.extract_claims(spec)
    assert any("CONTRADICTION" in c.text for c in claims)


def test_variants_extracted_from_description():
    spec = make_spec(description=(
        "We screened a grid of 40 lookback windows and kept the best performer; "
        "this prose is long enough to satisfy the schema fence requirements."))
    assert mock_reasoner.variants_for(spec) == 40


def test_variants_conservative_without_count():
    spec = make_spec(description=(
        "The parameter grid was tuned in the notebook for this participation "
        "factor specification, which is described at length right here."))
    assert mock_reasoner.variants_for(spec) == 10


def test_variants_default_one():
    spec = make_spec(description=(
        "A plain twelve-one momentum specification with no search language at "
        "all in this description text, long enough for the fence."))
    assert mock_reasoner.variants_for(spec) == 1


def test_plan_is_schema_valid_and_deterministic():
    spec = make_spec()
    plans = [mock_reasoner.plan_probes(spec) for _ in range(3)]
    assert all(p.model_dump() == plans[0].model_dump() for p in plans)
    plan_schema = {**PLAN_SCHEMA, "required": ["probes", "variants_tried"]}
    jsonschema.validate(plans[0].model_dump(), plan_schema)


def test_interpretation_is_schema_valid():
    spec = make_spec()
    interp = mock_reasoner.interpret(
        spec, verdict="REJECT_SPURIOUS", reason_codes=["LOOKAHEAD_COLLAPSE"],
        probe_payload={
            "timestamp_alignment_probe": {"ic_as_written": 0.47, "ic_point_in_time": 0.01,
                                          "ic_delta": 0.46, "max_negative_shift": 0},
            "label_permutation_test": {"p_value": 0.005, "p_deflated": 0.005,
                                       "observed_mean_ic": 0.47, "variants_assumed": 1},
        })
    jsonschema.validate(interp.model_dump(), INTERPRET_SCHEMA)
    assert any("0.470" in e.statement for e in interp.top_evidence)
