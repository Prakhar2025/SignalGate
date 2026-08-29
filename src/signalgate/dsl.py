"""Fenced DSL for signal pseudocode.

A spec's `pseudocode` is a small assignment program over named panel fields.
The evaluator is the mechanical heart of the timestamp-alignment probe: the
same program runs once **as-written** (fields exactly as the researcher has
them) and once **leak-proof (PIT)** - every field lagged by its disclosure
lag plus the largest negative shift the program itself performs, and the
universe restricted to point-in-time membership.
"""
from __future__ import annotations

import ast
from dataclasses import dataclass

import numpy as np
import pandas as pd

# Methods the DSL may call on panel objects. Anything else (dunder, IO, attrs)
# is rejected before evaluation.
ALLOWED_ATTRS = frozenset(
    {"shift", "rolling", "mean", "std", "sum", "max", "min", "rank", "diff", "abs"}
)
FORBIDDEN_NODES = (ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp, ast.Await,
                   ast.Yield, ast.YieldFrom, ast.Starred)


class DslError(ValueError):
    """Raised for pseudocode that cannot be compiled or safely evaluated."""


@dataclass(frozen=True)
class Program:
    assignments: list[tuple[str, ast.Expression]]   # in source order
    score_name: str                                  # must be `score`
    max_negative_shift: int                          # L: largest peek performed by the program


def _check_node(node: ast.AST) -> None:
    for child in ast.walk(node):
        if isinstance(child, FORBIDDEN_NODES):
            raise DslError(f"forbidden construct: {type(child).__name__}")
        if isinstance(child, ast.Attribute):
            if child.attr.startswith("_") or child.attr not in ALLOWED_ATTRS:
                raise DslError(f"attribute not allowed: .{child.attr}")


def _negative_shift(program_src: str) -> int:
    """Largest peek: shift(x, -k) / x.shift(-k) / lead(x, k) with k > 0."""
    worst = 0
    for line in program_src.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        rhs = line.split("=", 1)[1].strip() if "=" in line else line
        tree = ast.parse(rhs, mode="eval")
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
            if len(call.args) > 1:
                arg = call.args[1]
            else:
                arg = next((kw.value for kw in call.keywords if kw.arg == "n"), None)
            sign = 1
            if isinstance(arg, ast.UnaryOp) and isinstance(arg.op, ast.USub):
                arg = arg.operand
                sign = -1
            arg = arg.value if isinstance(arg, ast.Constant) else None
            if not isinstance(arg, (int, float)) or isinstance(arg, bool):
                continue
            # pct_change(x, -k) is shift(x, -k) in disguise - same peek
            if name == "lead" or (name == "pct_change" and sign * arg < 0):
                worst = max(worst, int(arg))
            elif name in {"shift", "delay", "pct_change"} and sign * arg < 0:
                worst = max(worst, int(-sign * arg))
    return worst


def compile_program(pseudocode: str) -> Program:
    if not pseudocode or not pseudocode.strip():
        raise DslError("pseudocode is empty")
    assignments: list[tuple[str, ast.Expression]] = []
    for raw in pseudocode.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if "=" not in line:
            raise DslError(f"expected `name = expression`, got: {line!r}")
        target, expr = line.split("=", 1)
        target = target.strip()
        if not target.isidentifier():
            raise DslError(f"invalid assignment target: {target!r}")
        tree = ast.parse(expr.strip(), mode="eval")
        _check_node(tree)
        assignments.append((target, tree))
    if not assignments:
        raise DslError("no assignments found")
    names = [t for t, _ in assignments]
    if "score" not in names:
        raise DslError("program must define `score`")
    return Program(
        assignments=assignments,
        score_name="score",
        max_negative_shift=_negative_shift(pseudocode),
    )


# ------------------------------------------------------------------ helpers

def pct_change(x: pd.DataFrame, n: int) -> pd.DataFrame:
    return x / x.shift(int(n)) - 1.0


def ts_mean(x: pd.DataFrame, n: int) -> pd.DataFrame:
    return x.rolling(int(n)).mean()


def ts_std(x: pd.DataFrame, n: int) -> pd.DataFrame:
    return x.rolling(int(n)).std()


def ts_sum(x: pd.DataFrame, n: int) -> pd.DataFrame:
    return x.rolling(int(n)).sum()


def ts_max(x: pd.DataFrame, n: int) -> pd.DataFrame:
    return x.rolling(int(n)).max()


def ts_min(x: pd.DataFrame, n: int) -> pd.DataFrame:
    return x.rolling(int(n)).min()


def rank(x: pd.DataFrame) -> pd.DataFrame:
    """Cross-sectional percentile rank per day, centered on 0."""
    return x.rank(axis=1, pct=True) - 0.5


def zscore(x: pd.DataFrame) -> pd.DataFrame:
    mu = x.mean(axis=1)
    sd = x.std(axis=1, ddof=0)
    return x.sub(mu, axis=0).div(sd.replace(0.0, np.nan), axis=0)


def delay(x: pd.DataFrame, n: int) -> pd.DataFrame:
    return x.shift(int(n))


def lead(x: pd.DataFrame, n: int) -> pd.DataFrame:
    """Forward reference - the syntactic lookahead the lint exists to flag."""
    return x.shift(-int(n))


def where(cond: pd.DataFrame, a: pd.DataFrame, b: pd.DataFrame) -> pd.DataFrame:
    return a.where(cond.astype(bool), b)


HELPERS: dict[str, object] = {
    "pct_change": pct_change,
    "ts_mean": ts_mean,
    "ts_std": ts_std,
    "ts_sum": ts_sum,
    "ts_max": ts_max,
    "ts_min": ts_min,
    "rank": rank,
    "zscore": zscore,
    "delay": delay,
    "shift": lambda x, n: x.shift(int(n)),
    "lead": lead,
    "where": where,
    "abs": lambda x: x.abs(),
    "sign": lambda x: np.sign(x),
    "log": lambda x: np.log(x.clip(lower=1e-12)),
}


def _align(frame: pd.DataFrame, dates: pd.DatetimeIndex, columns: list[str]) -> pd.DataFrame:
    """Reindex a panel to (dates × assets); a single non-asset column broadcasts."""
    if len(frame.columns) == 1 and not set(frame.columns) & set(columns):
        return pd.DataFrame(
            np.broadcast_to(frame.iloc[:, 0].to_numpy()[:, None], (len(dates), len(columns))),
            index=dates, columns=columns,
        )
    return frame.reindex(index=dates, columns=columns)


def _pit_fields(fields: dict[str, pd.DataFrame], lags: dict[str, int], global_lag: int,
                dates: pd.DatetimeIndex, columns: list[str]) -> dict[str, pd.DataFrame]:
    """Lag every field so row t contains only information knowable at t."""
    out: dict[str, pd.DataFrame] = {}
    for name, frame in fields.items():
        aligned = _align(frame, dates, columns)
        lag = int(lags.get(name, 0)) + global_lag
        out[name] = aligned.shift(lag) if lag else aligned
    return out


def execute(program: Program, fields: dict[str, pd.DataFrame], *, pit: bool = False,
            lags: dict[str, int] | None = None,
            universe_mask: pd.DataFrame | None = None) -> pd.DataFrame:
    """Evaluate the program. `pit=True` runs the leak-proof re-execution.

    universe_mask: optional (T×N) bool - entries kept only where True.
    """
    lags = lags or {}
    base = next(iter(fields.values()))
    dates, columns = base.index, list(base.columns)
    ns: dict[str, object] = dict(HELPERS)
    ns["__builtins__"] = {}
    if pit:
        ns.update(_pit_fields(fields, lags, program.max_negative_shift, dates, columns))
    else:
        ns.update({k: _align(v, dates, columns) for k, v in fields.items()})

    for target, tree in program.assignments:
        ns[target] = eval(compile(ast.Expression(tree.body), "<dsl>", "eval"), ns)  # noqa: S307

    score = ns[program.score_name]
    if not isinstance(score, pd.DataFrame):
        score = pd.DataFrame(np.broadcast_to(np.asarray(score), (len(dates), len(columns))),
                             index=dates, columns=columns)
    score = score.reindex(index=dates, columns=columns)
    if universe_mask is not None:
        score = score.where(universe_mask.reindex_like(score).fillna(False).astype(bool))
    return score


def as_written_and_pit(program: Program, fields: dict[str, pd.DataFrame],
                       lags: dict[str, int],
                       universe_written: pd.DataFrame | None,
                       universe_pit: pd.DataFrame | None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The alignment probe's two executions: as the spec says vs. leak-proof."""
    written = execute(program, fields, pit=False, universe_mask=universe_written)
    pit = execute(program, fields, pit=True, lags=lags, universe_mask=universe_pit)
    return written, pit
