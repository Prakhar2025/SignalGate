"""LOCAL_MOCK reasoner - deterministic canned reasoning keyed by the case seed.

This is the stub model behind the zero-key repro path (docs/03 §9): same
input -> same output, byte-identical evals. It implements the investigator's
job with transparent heuristics (claim extraction, probe selection,
interpretation templates) so the full pipeline - orchestrator, probes,
thresholds, bundles - is exercised without an LLM. It is NOT the product's
intelligence; LIVE mode routes the same prompts to a real model.
"""
from __future__ import annotations

import re

from signalgate.probes import PROBES
from signalgate.schemas import (
    Claim,
    EvidenceItem,
    Interpretation,
    ProbePlan,
    ReasonCode,
    SignalSpec,
    Verdict,
)

SELECTION_RE = re.compile(
    r"(?:grid of|sweep(?:ing)?|screen(?:ed)?|scan(?:ning)?|tried|tested|iterated|"
    r"evaluated|lattice)\b[^.]{0,40}?\b(\d{1,4})\b|\b(\d{1,4})\s*-?\s*"
    r"(?:windows|lookbacks|candidates|variants|parameterizations)\b", re.IGNORECASE)
SELECTION_WORDS_RE = re.compile(
    r"\b(grid|sweep|sweeping|screen|screened|scan|scanning|tried|tested|"
    r"iterated|evaluated|lattice|top performer|best)\b", re.IGNORECASE)
PIT_LANGUAGE = re.compile(
    r"point[- ]in[- ]time|as of each decision date|reconstructed as of", re.IGNORECASE)
STRONG_TAPE = re.compile(r"strong (?:tape|recent tape|bull)|bull window|validated on", re.IGNORECASE)


def extract_claims(spec: SignalSpec) -> list[Claim]:
    claims: list[Claim] = []
    text = " ".join(filter(None, [spec.description, spec.notes or ""]))

    if spec.params.universe == "survivors":
        claims.append(Claim(
            text="Universe is the constituents as of the final day (survivors).",
            kind="universe", evidence_span="params.universe=survivors"))
    elif PIT_LANGUAGE.search(text):
        claims.append(Claim(
            text="Prose claims point-in-time universe construction.",
            kind="universe", evidence_span=PIT_LANGUAGE.search(text).group(0)))
    else:
        claims.append(Claim(
            text="Universe is the full cross-section as of each decision date.",
            kind="universe", evidence_span="params.universe=all"))

    if spec.pseudocode:
        for field in re.findall(r"\b([a-z_]+(?:_quarter|_nextday))\b", spec.pseudocode):
            claims.append(Claim(
                text=f"Uses vendor field '{field}' whose value at row t aggregates "
                     "the in-progress period - timing must be verified.",
                kind="data_source", evidence_span=field))

    if PIT_LANGUAGE.search(text) and spec.params.universe == "survivors":
        claims.append(Claim(
            text="CONTRADICTION: prose claims point-in-time membership while "
                 "params declare a survivor universe.",
            kind="universe", evidence_span="description vs params.universe"))

    m = SELECTION_RE.search(text)
    if m:
        count = m.group(1) or m.group(2)
        claims.append(Claim(
            text=f"In-sample selection disclosed: ~{count} candidates tried, "
                 "no multiple-testing correction stated.",
            kind="selection", evidence_span=m.group(0)[:80]))
    elif SELECTION_WORDS_RE.search(text):
        claims.append(Claim(
            text="Selection language present without a candidate count; "
                 "conservative deflation will be assumed.",
            kind="selection", evidence_span=SELECTION_WORDS_RE.search(text).group(0)))

    if STRONG_TAPE.search(text):
        claims.append(Claim(
            text="Parameters validated on a single strong-tape window; regime "
                 "dependence must be measured.",
            kind="regime", evidence_span=STRONG_TAPE.search(text).group(0)))

    if spec.params.costs_bps < 2.0:
        claims.append(Claim(
            text=f"Declared costs of {spec.params.costs_bps:g} bps are aggressive; "
                 "check implied turnover.",
            kind="cost", evidence_span=f"costs_bps={spec.params.costs_bps}"))
    return claims


def variants_for(spec: SignalSpec) -> int:
    m = SELECTION_RE.search(" ".join(filter(None, [spec.description, spec.notes or ""])))
    if m:
        return int(m.group(1) or m.group(2))
    if SELECTION_WORDS_RE.search(" ".join(filter(None, [spec.description, spec.notes or ""]))):
        return 10  # conservative disclosed assumption
    return 1


def plan_probes(spec: SignalSpec) -> ProbePlan:
    watch = []
    if spec.pseudocode:
        watch = re.findall(r"\b([a-z_]+(?:_quarter|_nextday))\b", spec.pseudocode)
    return ProbePlan(probes=list(PROBES), variants_tried=variants_for(spec),
                     watch_fields=watch)


def interpret(spec: SignalSpec, verdict: Verdict, reason_codes: list[str],
              probe_payload: dict) -> Interpretation:
    """Build the human-readable interpretation from authoritative numbers."""
    evidence: list[EvidenceItem] = []
    ta = probe_payload.get("timestamp_alignment_probe", {})
    if ta:
        delta = ta.get("ic_delta", 0.0)
        if abs(delta) > 0.005 or ta.get("max_negative_shift", 0) > 0:
            evidence.append(EvidenceItem(
                probe="timestamp_alignment_probe",
                statement=(
                    f"Mean rank-IC collapses from {ta.get('ic_as_written', 0):+.3f} "
                    f"as-written to {ta.get('ic_point_in_time', 0):+.3f} under leak-proof "
                    f"re-execution (delta {delta:+.3f}; largest forward shift in the "
                    f"program: {ta.get('max_negative_shift', 0)} bars).")))
    perm = probe_payload.get("label_permutation_test", {})
    if perm:
        evidence.append(EvidenceItem(
            probe="label_permutation_test",
            statement=(
                f"Observed mean IC {perm.get('observed_mean_ic', 0):+.3f} has permutation "
                f"p = {perm.get('p_value', 1):.3f}; deflated for "
                f"{perm.get('variants_assumed', 1)} assumed variants: "
                f"p = {perm.get('p_deflated', 1):.3f}.")))
    reg = probe_payload.get("regime_subsample", {}).get("regimes", {})
    if reg:
        table = ", ".join(f"{k} {v['ic']:+.3f} (active {v['active']:.0%})"
                          for k, v in reg.items())
        evidence.append(EvidenceItem(
            probe="regime_subsample",
            statement=f"Leak-proof per-regime IC: {table}."))
    to = probe_payload.get("turnover_and_cost_sanity", {})
    if to:
        evidence.append(EvidenceItem(
            probe="turnover_and_cost_sanity",
            statement=(
                f"Implied turnover {to.get('turnover_1s_daily', 0):.2f}/day one-sided; "
                f"gross Sharpe {to.get('gross_sharpe', 0):+.2f} vs net "
                f"{to.get('net_sharpe', 0):+.2f} after declared costs "
                f"({to.get('daily_cost_drag_bps', 0):.1f} bps/day drag).")))

    if verdict == Verdict.REJECT_SPURIOUS:
        why = ("Verification failed with receipts: the claimed edge does not survive "
               "leak-proof re-execution and/or deflated significance testing. "
               "No researcher hour is warranted for this spec as submitted.")
    elif verdict == Verdict.PROMISING:
        why = ("Verification held: significant after deflation, stable across "
               "regimes, alignment clean, and costs do not eat the edge. This one "
               "deserves a researcher's hour.")
    else:
        why = ("Evidence is incomplete or contradictory - the spec needs a human "
               "hour rather than an automated accept or reject.")

    codes = [ReasonCode(c) for c in reason_codes if c in ReasonCode.__members__]
    return Interpretation(reason_codes=[c.value for c in codes],
                          top_evidence=evidence[:4], narrative=why)
