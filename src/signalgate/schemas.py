"""Pydantic schemas - the fence every untrusted spec and every agent output must pass (doc 03 §2)."""
from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class SpecParams(BaseModel):
    universe: Literal["all", "survivors"] = "all"
    horizon: int = Field(default=21, ge=1, le=252)
    costs_bps: float = Field(default=10.0, ge=0.0, le=100.0)
    rebalance: Literal["daily", "weekly"] = "daily"


class SignalSpec(BaseModel):
    """Structured input: prose + optional pseudocode + parameters (doc 02 §2)."""

    name: str = Field(min_length=3, max_length=120)
    description: str = Field(min_length=20, max_length=5000)
    pseudocode: str | None = Field(default=None, max_length=5000)
    params: SpecParams = Field(default_factory=SpecParams)
    notes: str | None = Field(default=None, max_length=5000)


class Verdict(StrEnum):
    REJECT_SPURIOUS = "REJECT_SPURIOUS"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    PROMISING = "PROMISING"
    REJECTED_INVALID = "REJECTED_INVALID"  # schema fail with field-level reasons (03 §7)


class ReasonCode(StrEnum):
    # composer / probe-driven (thresholds live in orchestrator.thresholds - never in the model)
    LOOKAHEAD_COLLAPSE = "LOOKAHEAD_COLLAPSE"
    PIT_ONLY_EDGE = "PIT_ONLY_EDGE"
    NOT_SIGNIFICANT = "NOT_SIGNIFICANT"
    REGIME_FRAGILE = "REGIME_FRAGILE"
    COST_MIRACLE = "COST_MIRACLE"
    # lint-driven
    LINT_FUTURE_SHIFT = "LINT_FUTURE_SHIFT"
    LINT_SURVIVORSHIP = "LINT_SURVIVORSHIP"
    LINT_SELECTION_BIAS = "LINT_SELECTION_BIAS"
    LINT_REGIME_LANGUAGE = "LINT_REGIME_LANGUAGE"
    # disclosure codes
    PROBE_SKIPPED = "PROBE_SKIPPED"
    DEGRADED_MODEL = "DEGRADED_MODEL"
    SCHEMA_INVALID = "SCHEMA_INVALID"


class Confidence(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# ---------------------------------------------------------------- agent outputs

class Claim(BaseModel):
    text: str = Field(min_length=3, max_length=400)
    kind: Literal["universe", "timing", "selection", "regime", "cost", "data_source", "other"]
    evidence_span: str = Field(default="", max_length=400)


class ProbePlan(BaseModel):
    probes: list[str] = Field(min_length=0, max_length=8)
    variants_tried: int = Field(default=1, ge=1, le=10_000)
    watch_fields: list[str] = Field(default_factory=list)


class EvidenceItem(BaseModel):
    probe: str
    statement: str = Field(min_length=3, max_length=500)


class Interpretation(BaseModel):
    reason_codes: list[str] = Field(default_factory=list)
    top_evidence: list[EvidenceItem] = Field(default_factory=list, max_length=4)
    narrative: str = Field(default="", max_length=2000)


class RecommendedAction(StrEnum):
    ARCHIVE_WITH_RECEIPTS = "ARCHIVE_WITH_RECEIPTS"
    ASSIGN_RESEARCHER_HOUR = "ASSIGN_RESEARCHER_HOUR"
    PROMOTE_TO_PAPER_TRADE = "PROMOTE_TO_PAPER_TRADE"
    FIX_SPEC_AND_RESUBMIT = "FIX_SPEC_AND_RESUBMIT"
    RERUN_WITH_FULL_VERIFICATION = "RERUN_WITH_FULL_VERIFICATION"


# ---------------------------------------------------------------- probe results

class ProbeResult(BaseModel):
    probe: str
    ok: bool
    skipped: bool = False
    skip_reason: str = ""
    metrics: dict[str, float | int | str | bool | None] = Field(default_factory=dict)
    detail: dict[str, object] = Field(default_factory=dict)


# ---------------------------------------------------------------- verdict card / bundle

class VerdictCard(BaseModel):
    """Answers: what came in, what we probed, what we found, why this verdict, what to do (02 §9)."""

    run_id: str
    spec_name: str
    verdict: Verdict
    confidence: Confidence
    reason_codes: list[ReasonCode]
    degraded: bool
    what_came_in: str
    what_we_probed: list[str]
    findings: list[EvidenceItem]
    why: str
    recommended_action: RecommendedAction
    cost_usd: float
    est_tokens: int
    elapsed_ms: int


class RunResult(BaseModel):
    """Full orchestrated outcome - persisted as the evidence bundle (02 §2)."""

    schema_version: str = "bundle@1"
    run_id: str
    case_id: str | None = None
    spec: SignalSpec
    lint_flags: list[dict[str, object]] = Field(default_factory=list)
    claims: list[Claim] = Field(default_factory=list)
    probe_results: list[ProbeResult] = Field(default_factory=list)
    verdict: Verdict
    confidence: Confidence = Confidence.LOW
    reason_codes: list[ReasonCode] = Field(default_factory=list)
    recommended_action: RecommendedAction = RecommendedAction.RERUN_WITH_FULL_VERIFICATION
    degraded: bool = False
    narrative: str = ""
    findings: list[EvidenceItem] = Field(default_factory=list)
    cost_usd: float = 0.0
    est_tokens: int = 0
    elapsed_ms: int = 0
    mode: str = "LOCAL_MOCK"
    model_id: str = "LOCAL_MOCK"
    prompt_version: str = ""
    seed: int = 0
    spans: list[dict[str, object]] = Field(default_factory=list)
