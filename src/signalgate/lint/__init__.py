"""Static lint baseline (docs/02 §6 F2) - AST/regex rule suite.

The lint is the *cheap syntactic* pass: it reads the structured spec body
(name, description, pseudocode, params) and flags definite syntax and
keyword patterns. It deliberately does NOT read `notes` (free-text
attachments are the investigator agent's job) and never issues verdicts on
semantics - prose-hidden bias passes a lint by design. That limitation IS
the product's reason to exist.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass

from signalgate.schemas import ReasonCode, SignalSpec


@dataclass(frozen=True)
class LintFlag:
    rule_id: str
    code: ReasonCode
    message: str
    where: str       # description | pseudocode | params
    rejecting: bool  # contributes to a baseline REJECT_SPURIOUS


def _scan_negative_shift(src: str) -> str | None:
    """Return a human-readable mention of the first negative shift / lead."""
    for line in src.splitlines():
        stripped = line.split("#", 1)[0].strip()
        if not stripped:
            continue
        rhs = stripped.split("=", 1)[1].strip() if "=" in stripped else stripped
        try:
            tree = ast.parse(rhs, mode="eval")
        except SyntaxError:
            continue
        for call in ast.walk(tree):
            if not isinstance(call, ast.Call):
                continue
            name = ""
            if isinstance(call.func, ast.Name):
                name = call.func.id
            elif isinstance(call.func, ast.Attribute):
                name = call.func.attr
            if name not in {"shift", "delay", "lead", "pct_change"}:
                continue
            arg = call.args[1] if len(call.args) > 1 else \
                next((kw.value for kw in call.keywords if kw.arg == "n"), None)
            sign = 1
            if isinstance(arg, ast.UnaryOp) and isinstance(arg.op, ast.USub):
                arg, sign = arg.operand, -1
            val = arg.value if isinstance(arg, ast.Constant) else None
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                continue
            if name == "lead" and val > 0:
                return f"lead(..., {int(val)})"
            if sign * val < 0:
                shown = f"{name}(..., {int(sign * val)})"
                return shown
    return None


SURVIVORSHIP_KEYWORDS = [
    "survivors", "survivorship", "current constituents", "today's constituents",
    "current index members", "today's members", "currently listed",
]
# number directly attached to a selection noun, or a selection verb followed
# shortly by a number - "the two lookbacks" (word, not digit) must NOT match
SELECTION_PATTERN = (r"(?:grid of|sweep(?:ing)?|screen(?:ed)?|scan(?:ning)?|tried|"
                     r"tested|iterated|evaluated|lattice)\b[^.]{0,40}?\b(\d{1,4})\b"
                     r"|\b(\d{1,4})\s*-?\s*(?:windows|lookbacks|candidates|variants|"
                     r"parameterizations)\b")
REGIME_KEYWORDS = ["bull market", "bear market"]
PEEK_SUFFIXES = ("_quarter", "_nextday")


def run_lint(spec: SignalSpec) -> list[LintFlag]:
    flags: list[LintFlag] = []

    # L001 - future reference in pseudocode (definite, F1)
    if spec.pseudocode:
        hit = _scan_negative_shift(spec.pseudocode)
        if hit:
            flags.append(LintFlag(
                "L001", ReasonCode.LINT_FUTURE_SHIFT,
                f"pseudocode references a future bar: {hit} - any result built on "
                "this definition is invalid.", "pseudocode", rejecting=True))

    # L101 - survivorship language / structured universe (definite, F3)
    if spec.params.universe == "survivors":
        flags.append(LintFlag(
            "L101", ReasonCode.LINT_SURVIVORSHIP,
            "params.universe = survivors - the backtest only sees assets listed "
            "on the final day (survivor universe).", "params", rejecting=True))
    else:
        low = spec.description.lower()
        for kw in SURVIVORSHIP_KEYWORDS:
            if kw in low:
                flags.append(LintFlag(
                    "L101", ReasonCode.LINT_SURVIVORSHIP,
                    f'description says "{kw}" - backtest universe may exclude '
                    "delisted assets.", "description", rejecting=True))
                break

    # L201 - in-sample selection without correction (definite when a count is given, F4)
    import re
    for where, text in (("description", spec.description),):
        m = re.search(SELECTION_PATTERN, text, re.IGNORECASE)
        if m:
            count = m.group(1) or m.group(2)
            flags.append(LintFlag(
                "L201", ReasonCode.LINT_SELECTION_BIAS,
                f'description discloses in-sample selection ("...{m.group(0)[:60]}...") '
                f"with ~{count} candidates and no multiple-testing correction.",
                where, rejecting=True))
            break

    # L301 - single-regime language (weak signal, F5; does not reject alone)
    low = spec.description.lower()
    for kw in REGIME_KEYWORDS:
        if kw in low:
            flags.append(LintFlag(
                "L301", ReasonCode.LINT_REGIME_LANGUAGE,
                f'description mentions "{kw}" - check regime dependence.',
                "description", rejecting=False))
            break

    # L401 - costs/turnover coherence (informational only)
    if spec.params.costs_bps < 2.0 and spec.params.rebalance == "daily":
        flags.append(LintFlag(
            "L401", ReasonCode.COST_MIRACLE,
            f"declared costs {spec.params.costs_bps:g} bps with daily rebalance - "
            "verify against implied turnover.", "params", rejecting=False))

    return flags


def baseline_verdict(flags: list[LintFlag]) -> tuple[str, list[ReasonCode]]:
    """Lint-only decision rule: reject on definite syntax/structure, never promise."""
    codes = [f.code for f in flags]
    if any(f.rejecting for f in flags):
        return "REJECT_SPURIOUS", codes
    return "NEEDS_REVIEW", codes
