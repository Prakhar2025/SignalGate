"""Investigator agent (docs/02 §6 F3): one LLM + 4 probe tools, JSON-gated.

The agent NEVER sees or computes the verdict - it plans probes and writes the
narrative. In LIVE mode each reasoning call is schema-gated with one retry;
on persistent failure the orchestrator degrades to lint-only (J4). In MOCK
mode the deterministic reasoner answers the same contract.
"""
from __future__ import annotations

import json
from collections.abc import Callable

from signalgate.agent import mock_reasoner
from signalgate.agent.adapter import ModelAdapter, Usage
from signalgate.agent.prompts import (
    INTERPRET_SYSTEM,
    INTERPRET_USER_TMPL,
    PLAN_SYSTEM,
    PLAN_USER_TMPL,
    PROMPT_VERSION,
)
from signalgate.probes import PROBES, run_probe
from signalgate.schemas import (
    Claim,
    EvidenceItem,
    Interpretation,
    ProbePlan,
    ProbeResult,
    ReasonCode,
    SignalSpec,
    Verdict,
)

PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {"type": "array", "items": {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "kind": {"type": "string",
                         "enum": ["universe", "timing", "selection", "regime",
                                  "cost", "data_source", "other"]},
                "evidence_span": {"type": "string"},
            },
            "required": ["text", "kind"],
        }},
        "probes": {"type": "array", "items": {"type": "string", "enum": list(PROBES)}},
        "variants_tried": {"type": "integer", "minimum": 1, "maximum": 10000},
        "watch_fields": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["claims", "probes", "variants_tried"],
}

INTERPRET_SCHEMA = {
    "type": "object",
    "properties": {
        "reason_codes": {"type": "array", "items": {"type": "string"}},
        "top_evidence": {"type": "array", "items": {
            "type": "object",
            "properties": {"probe": {"type": "string"}, "statement": {"type": "string"}},
            "required": ["probe", "statement"],
        }},
        "narrative": {"type": "string"},
    },
    "required": ["reason_codes", "top_evidence", "narrative"],
}


class Investigator:
    def __init__(self, mode: str, adapter: ModelAdapter | None = None,
                 market_path=None, seed: int = 20260828,
                 spend_cb: Callable[[Usage], None] | None = None,
                 span_cb: Callable[[dict], None] | None = None,
                 probe_timeout_s: int | None = None):
        self.mode = mode
        self.adapter = adapter
        self.market_path = market_path
        self.seed = seed
        self.spend_cb = spend_cb
        self.span_cb = span_cb
        self.probe_timeout_s = probe_timeout_s

    def _span(self, event: str, **kw) -> None:
        if self.span_cb:
            self.span_cb({"stage": "agent", "event": event, **kw})

    def plan(self, spec: SignalSpec, lint_flags: list[dict]) -> tuple[list[Claim], ProbePlan]:
        if self.mode == "mock":
            claims = mock_reasoner.extract_claims(spec)
            plan = mock_reasoner.plan_probes(spec)
            self._span("instruction", call="mock_plan", claims=len(claims))
            self._span("tool_response", call="mock_plan", plan=plan.model_dump())
            return claims, plan
        assert self.adapter is not None
        user = PLAN_USER_TMPL.format(
            spec_json=json.dumps(spec.model_dump(), indent=2),
            lint_flags="\n".join(f"- {f['rule_id']}: {f['message']}" for f in lint_flags) or "- none",
            probe_list=", ".join(PROBES))
        self._span("instruction", call="plan", model=self.adapter.model_id,
                   prompt_version=PROMPT_VERSION)
        obj, usage = self.adapter.complete(PLAN_SYSTEM, user, PLAN_SCHEMA)
        self._span("tool_response", call="plan", tokens=usage.est_tokens_out,
                   cost_usd=round(usage.cost_usd, 6))
        if self.spend_cb:
            self.spend_cb(usage)
        plan = ProbePlan(
            probes=[p for p in obj.get("probes", PROBES) if p in PROBES],
            variants_tried=max(1, int(obj.get("variants_tried", 1))),
            watch_fields=obj.get("watch_fields", []))
        claims = [Claim(**c) for c in obj.get("claims", [])]
        return claims, plan

    def run_probes(self, spec: SignalSpec, plan: ProbePlan) -> list[ProbeResult]:
        results: list[ProbeResult] = []
        kwargs = dict(market_path=self.market_path, pseudocode=spec.pseudocode or "",
                      horizon=spec.params.horizon, costs_bps=spec.params.costs_bps,
                      rebalance=spec.params.rebalance,
                      variants_tried=plan.variants_tried, seed=self.seed)
        if self.probe_timeout_s:
            kwargs["timeout_s"] = self.probe_timeout_s
        for probe in plan.probes:
            result = run_probe(probe, **kwargs)
            self._span("tool_response", call=probe, ok=result.ok,
                       skipped=result.skipped, skip_reason=result.skip_reason)
            if result.skipped:
                result.metrics = {}
            results.append(result)
        return results

    def interpret(self, spec: SignalSpec, verdict: Verdict, codes: list[ReasonCode],
                  claims: list[Claim], probe_results: list[ProbeResult]) -> Interpretation:
        payload = {r.probe: {**r.metrics,
                             "regimes": r.detail.get("regimes", {})} for r in probe_results}
        code_values = [c.value for c in codes]
        if self.mode == "mock":
            interp = mock_reasoner.interpret(spec, verdict, code_values, payload)
            self._span("checkpoint", call="mock_interpret", verdict=verdict.value)
            return interp
        assert self.adapter is not None
        user = INTERPRET_USER_TMPL.format(
            verdict=verdict.value, reason_codes=", ".join(code_values) or "none",
            claims="\n".join(f"- [{c.kind}] {c.text}" for c in claims) or "- none",
            probe_results=json.dumps(payload, indent=2))
        self._span("instruction", call="interpret", model=self.adapter.model_id)
        obj, usage = self.adapter.complete(INTERPRET_SYSTEM, user, INTERPRET_SCHEMA)
        if self.spend_cb:
            self.spend_cb(usage)
        self._span("checkpoint", call="interpret", verdict=verdict.value,
                   tokens=usage.est_tokens_out)
        return Interpretation(
            reason_codes=[c for c in obj.get("reason_codes", code_values)
                          if c in ReasonCode.__members__],
            top_evidence=[EvidenceItem(probe=str(e.get("probe", "unknown")),
                                       statement=str(e.get("statement", "")))
                          for e in obj.get("top_evidence", [])],
            narrative=str(obj.get("narrative", "")))
