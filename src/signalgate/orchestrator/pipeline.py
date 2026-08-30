"""Orchestrator (docs/03 §4): lint -> agent -> probes -> composer -> bundle.

Orchestrator law: models decide WITHIN stages; code decides BETWEEN stages.
Every run persists an evidence bundle with spans (the trajectory export) and
discloses degradation honestly (docs/03 §7 matrix).
"""
from __future__ import annotations

import hashlib
import time
from datetime import UTC, datetime

from signalgate import PROMPT_VERSION, __version__
from signalgate.agent.adapter import AdapterError, LocalMockAdapter, OpenAICompatAdapter
from signalgate.agent.investigator import Investigator
from signalgate.config import Settings, load_settings
from signalgate.lint import baseline_verdict, run_lint
from signalgate.orchestrator.bundle import write_bundle
from signalgate.orchestrator.composer import ACTION_BY_VERDICT, compose
from signalgate.orchestrator.spend import SpendMeter
from signalgate.schemas import (
    Claim,
    ProbePlan,
    ProbeResult,
    ReasonCode,
    RunResult,
    SignalSpec,
    Verdict,
)


class SpecInvalid(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def _run_id(spec: SignalSpec, mode: str, seed: int) -> str:
    canonical = spec.model_dump_json()
    digest = hashlib.sha256(f"{mode}|{seed}|{canonical}".encode()).hexdigest()[:16]
    return f"{digest}"


class Orchestrator:
    def __init__(self, settings: Settings | None = None,
                 spend: SpendMeter | None = None,
                 probe_timeout_s: int | None = None,
                 chaos: dict | None = None):
        self.settings = settings or load_settings()
        self.spend = spend or SpendMeter(self.settings.spend_cap_usd)
        self.probe_timeout_s = probe_timeout_s
        self.chaos = chaos or {}
        self.mode = self.settings.effective_mode
        if self.mode == "live":
            self.adapter = OpenAICompatAdapter(
                self.settings.model, self.settings.api_base, self._api_key())
        else:
            self.adapter = LocalMockAdapter()

    def _api_key(self) -> str:
        return self.settings.api_key

    def investigate(self, spec: SignalSpec, case_id: str | None = None,
                    depth: str = "agent", persist: bool = True) -> RunResult:
        t0 = time.perf_counter()
        run_id = _run_id(spec, self.mode, self.settings.seed)
        spans: list[dict] = []

        def span(stage: str, event: str, **kw) -> None:
            spans.append({"ts": datetime.now(UTC).isoformat(timespec="seconds"),
                          "stage": stage, "event": event, **kw})

        span("orchestrator", "checkpoint", run_id=run_id, depth=depth,
             mode=self.mode, version=__version__)

        flags = run_lint(spec)
        span("lint", "tool_response", flags=[f.rule_id for f in flags])
        flag_dicts = [{"rule_id": f.rule_id, "code": f.code.value,
                       "message": f.message, "where": f.where,
                       "rejecting": f.rejecting} for f in flags]

        if depth == "baseline":
            verdict_str, codes = baseline_verdict(flags)
            result = RunResult(
                run_id=run_id, case_id=case_id, spec=spec, lint_flags=flag_dicts,
                verdict=Verdict(verdict_str), confidence="MEDIUM",
                reason_codes=[ReasonCode(c) for c in codes],
                recommended_action=ACTION_BY_VERDICT[Verdict(verdict_str)],
                narrative="Static lint only: no probes were run; syntax and "
                          "structured tells only.",
                mode="LINT_ONLY", model_id="none", prompt_version=PROMPT_VERSION,
                seed=self.settings.seed, spans=spans,
                elapsed_ms=int((time.perf_counter() - t0) * 1000))
            if persist:
                write_bundle(result, self.settings.artifacts_dir)
            return result

        # degradation inputs: breaker already tripped, or chaos-injected outage
        degraded = self.spend.exceeded or bool(self.chaos.get("model_down"))
        claims: list[Claim] = []
        probe_results: list[ProbeResult] = []
        interp = None
        investigator = Investigator(
            mode="mock" if degraded else self.mode,
            adapter=None if degraded else self.adapter,
            market_path=self.settings.market_path, seed=self.settings.seed,
            spend_cb=lambda u: self.spend.record(u.cost_usd, u.est_tokens_in + u.est_tokens_out),
            span_cb=lambda s: span(s["stage"], s["event"],
                                   **{k: v for k, v in s.items()
                                      if k not in ("stage", "event")}),
            probe_timeout_s=self.probe_timeout_s)

        if not degraded:
            try:
                claims, plan = investigator.plan(spec, flag_dicts)
            except AdapterError as exc:
                span("agent", "feedback", error=str(exc)[:200])
                degraded = True
        if degraded:
            plan = ProbePlan(probes=[], variants_tried=1)

        if self.spend.exceeded and not degraded:
            # breaker tripped mid-run: drop to the degraded path, disclosed
            degraded = True
            span("orchestrator", "feedback", breaker="tripped mid-run")

        if not degraded:
            chaos_timeout = self.chaos.get("probe_timeout")
            probe_results = investigator.run_probes(
                spec, plan) if not chaos_timeout else [
                ProbeResult(probe=p, ok=False, skipped=True,
                            skip_reason="timeout after 10s (PROBE_SKIPPED)")
                for p in plan.probes]

        verdict, confidence, reasons, _ = compose(probe_results, flag_dicts, degraded)
        span("composer", "checkpoint", verdict=verdict.value, codes=[c.value for c in reasons])

        if degraded:
            reasons = [ReasonCode.DEGRADED_MODEL]
            narrative = ("DEGRADED: verification is incomplete (model unavailable "
                         "or spend breaker tripped). Lint-only run; treat this "
                         "verdict as unverified and resubmit when the model is "
                         "available.")
        else:
            interp = investigator.interpret(spec, verdict, reasons, claims, probe_results)
            narrative = interp.narrative
            # the model may emphasize codes but code owns the verdict
            for c in interp.reason_codes:
                rc = ReasonCode(c)
                if rc not in reasons:
                    reasons.append(rc)

        est_tokens = self.spend.est_tokens
        if est_tokens == 0:
            # mock mode meters the same payload sizes the live adapter would
            import json as _json
            est_tokens = (len(spec.model_dump_json())
                          + len(_json.dumps([c.model_dump() for c in claims]))
                          + len(narrative)) // 4

        result = RunResult(
            run_id=run_id, case_id=case_id, spec=spec, lint_flags=flag_dicts,
            claims=claims, probe_results=probe_results, verdict=verdict,
            confidence=confidence, reason_codes=reasons,
            recommended_action=ACTION_BY_VERDICT[verdict],
            degraded=degraded, narrative=narrative,
            findings=(interp.top_evidence if interp else []),
            cost_usd=round(self.spend.cost_usd, 6),
            est_tokens=est_tokens,
            mode="LOCAL_MOCK" if (degraded or self.mode == "mock") else "LIVE",
            model_id=self.settings.model if self.mode == "live" and not degraded else "LOCAL_MOCK",
            prompt_version=PROMPT_VERSION, seed=self.settings.seed, spans=spans,
            elapsed_ms=int((time.perf_counter() - t0) * 1000))
        if persist:
            write_bundle(result, self.settings.artifacts_dir)
        return result


def investigate_spec_dict(data: dict, settings: Settings | None = None,
                          case_id: str | None = None, **kw) -> RunResult:
    """Schema-fence untrusted input, then investigate (docs/03 §2 trust boundary)."""
    try:
        spec = SignalSpec.model_validate(data)
    except Exception as exc:
        raise SpecInvalid([str(exc)]) from exc
    return Orchestrator(settings=settings, **kw).investigate(spec, case_id=case_id)
