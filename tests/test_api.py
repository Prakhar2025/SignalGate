"""API contract (docs/03 §10): healthz, gate UI, investigate, bundles, rate limit."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from signalgate.api.app import _hits, create_app

SPEC_YAML = """
name: Management Tone Confidence
description: |
  Score each name by how strongly management sounds about next quarter: we parse
  the tone of the quarterly filing and go long the confident names, priced at
  quarter-end, 21-day holding period, 10 bps costs.
pseudocode: |
  score = rank(mgmt_tone_quarter)
params:
  universe: all
  horizon: 21
  costs_bps: 10.0
  rebalance: weekly
"""


@pytest.fixture()
def client(tmp_path, market_path):
    from tests.test_orchestrator import make_settings
    settings = make_settings(tmp_path, market_path)
    _hits.clear()  # shared rate-limit table: reset per test
    app = create_app(settings)
    return TestClient(app), settings


@pytest.fixture()
def tight_client(tmp_path, market_path):
    """App with a small rate limit so the 429 path needs no 31 slow requests."""
    from tests.test_orchestrator import make_settings
    settings = make_settings(tmp_path, market_path)
    _hits.clear()
    app = create_app(settings, rate_limit=3, rate_window_s=60.0)
    return TestClient(app)


def test_healthz(client):
    c, _ = client
    r = c.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_gate_ui_renders(client):
    c, _ = client
    r = c.get("/")
    assert r.status_code == 200
    assert "SignalGate" in r.text
    assert "Investigate" in r.text


def test_investigate_json_contract(client):
    c, _ = client
    r = c.post("/investigate", json={"spec_yaml": SPEC_YAML})
    assert r.status_code == 200
    body = r.json()
    assert body["verdict"] == "REJECT_SPURIOUS"
    assert "LOOKAHEAD_COLLAPSE" in body["reason_codes"]
    assert body["findings"]
    assert body["recommended_action"] == "ARCHIVE_WITH_RECEIPTS"


def test_investigate_form_htmx(client):
    c, _ = client
    r = c.post("/investigate", data={"spec": SPEC_YAML},
               headers={"content-type": "application/x-www-form-urlencoded"})
    assert r.status_code == 200
    assert "Verdict card" in r.text or "REJECT" in r.text


def test_invalid_spec_400(client):
    c, _ = client
    r = c.post("/investigate", json={"spec": {"name": "x", "description": "short"}})
    assert r.status_code == 400
    assert "error" in r.json()


def test_bundle_endpoints(client):
    c, _ = client
    run_id = c.post("/investigate", json={"spec_yaml": SPEC_YAML}).json()["run_id"]
    assert c.get(f"/runs/{run_id}").status_code == 200
    assert c.get(f"/runs/{run_id}/bundle.json").json()["verdict"] == "REJECT_SPURIOUS"
    assert "Verdict" in c.get(f"/runs/{run_id}/bundle.md").text


def test_rate_limit_returns_429(tight_client, client):
    codes = []
    for _ in range(5):
        codes.append(
            tight_client.post("/investigate", json={"spec_yaml": SPEC_YAML}).status_code)
    assert codes[:3] == [200, 200, 200]
    assert codes[3] == 429 and codes[4] == 429
