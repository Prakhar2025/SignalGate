"""Dataset builder: market panel + 60 case specs + manifest + calibration report.

    python -m generator.build --out data

Deterministic under the locked seed (20260828). The only per-case search is
the F4 injection: each p-hack case "researcher" sweeps their own lookback
grid on the noise family and ships the in-sample winner - the builder picks
that winner exactly as the flawed workflow would.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import yaml

from generator import GENERATOR_VERSION
from generator.cases import ALL_CASES, DEV_IDS, EXPECTED, F4, CaseDef, spec_dict
from generator.market import build_market
from signalgate.dsl import compile_program, execute
from signalgate.market_data import REGIME_NAMES, save_market
from signalgate.probes.metrics import (
    circular_permutation_p,
    daily_ic,
    forward_returns,
)

SPLIT_OF = {c.case_id: ("dev" if c.case_id in DEV_IDS else "holdout") for c in ALL_CASES}


def _ic_tstat(score, fwd) -> tuple[float, float, int]:
    ic = daily_ic(score, fwd).dropna()
    if len(ic) < 100 or ic.std(ddof=0) == 0:
        return 0.0, 0.0, len(ic)
    t = float(ic.mean() / ic.std(ddof=0) * np.sqrt(len(ic)))
    return t, float(ic.mean()), len(ic)


def f4_winner(panel, case: CaseDef, seed: int, case_index: int,
              target_p: float = 0.015) -> tuple[str, dict]:
    """Pick the in-sample-best lookback for the F4 noise family.

    Screening uses the IC t-stat (fast); the top candidates get exact
    permutation p-values; the case ships the window whose p sits closest to
    a plausible 'just significant' 0.015 - exactly the flawed workflow.
    """

    rng = np.random.default_rng(seed + 7919 * case_index)
    grid = sorted(rng.choice(np.arange(3, 301), size=60, replace=False).tolist())
    fwd = forward_returns(panel.close, case.horizon, panel.listed)
    fields = panel.as_fields()

    screened: list[tuple[float, int, float]] = []  # |t - t_target|, L, t
    t_target = 2.43  # two-sided normal approx of p = 0.015
    for L in grid:
        prog = compile_program(f"score = rank(ts_sum(volume, {L}))")
        score = execute(prog, fields, pit=False)
        t, _, n = _ic_tstat(score, fwd)
        if n < 100:
            continue
        screened.append((abs(t - t_target), L, t))
    screened.sort()

    best: tuple[float, int, float] | None = None  # |p - target|, L, p
    for _, L, _t in screened[:8]:
        prog = compile_program(f"score = rank(ts_sum(volume, {L}))")
        score = execute(prog, fields, pit=False)
        p, _ = circular_permutation_p(score, fwd, seed=seed + L, n_perm=199)
        if best is None or abs(p - target_p) < best[0]:
            best = (abs(p - target_p), L, p)
    if best is None:  # pragma: no cover - grid is never empty
        raise RuntimeError("F4 selection found no candidates")

    _, L, p = best
    pseudocode = f"score = rank(ts_sum(volume, {int(L)}))"
    info = {"selected_lookback": int(L), "raw_p": round(p, 4), "candidates": len(grid)}
    return pseudocode, info


def build(out_dir: Path, reports_dir: Path, seed: int,
          n_assets: int, n_days: int) -> None:
    print(f"[generator] building market seed={seed} assets={n_assets} days={n_days}")
    panel = build_market(seed, n_assets=n_assets, n_days=n_days)
    save_market(panel, out_dir / "market.npz")

    cases_dir = out_dir / "cases"
    f4_info: dict[str, dict] = {}
    f4_index = {c.case_id: i for i, c in enumerate(F4)}
    manifest_cases: dict[str, dict] = {"dev": {}, "holdout": {}}
    all_spec_bytes: list[str] = []

    for case in ALL_CASES:
        spec = spec_dict(case)
        if case.family == "F4":
            pseudo, info = f4_winner(panel, case, seed, f4_index[case.case_id])
            spec["pseudocode"] = pseudo
            f4_info[case.case_id] = info

        split = SPLIT_OF[case.case_id]
        case_dir = cases_dir / split
        case_dir.mkdir(parents=True, exist_ok=True)
        text = yaml.safe_dump(spec, sort_keys=False, allow_unicode=True,
                              default_flow_style=False, width=100)
        assert "F4_PLACEHOLDER" not in text, f"placeholder leaked into {case.case_id}"
        (case_dir / f"{case.case_id}.yaml").write_text(text, encoding="utf-8")
        all_spec_bytes.append(text)
        manifest_cases[split][case.case_id] = {
            "family": case.family,
            "name": case.name,
            "mechanism": case.mechanism,
            "strength": case.strength,
            "expected_verdict": EXPECTED[case.family],
            "spec_path": f"cases/{split}/{case.case_id}.yaml",
        }

    regime_counts = {REGIME_NAMES[i]: int((panel.regime == i).sum())
                     for i in range(3)}
    manifest = {
        "seed": seed,
        "generator_version": GENERATOR_VERSION,
        "n_assets": n_assets,
        "n_days": n_days,
        "regime_counts": regime_counts,
        "delisted": panel.delisted,
        "field_lags": panel.field_lags,
        "f4_selection": f4_info,
        "cases": manifest_cases,
        "content_sha256": hashlib.sha256(
            "\n".join(all_spec_bytes).encode("utf-8")).hexdigest(),
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    _write_examples(cases_dir)
    _write_dataset_report(reports_dir, panel, manifest, f4_info)
    print(f"[generator] wrote {len(ALL_CASES)} cases -> {cases_dir} "
          f"(dev={len(manifest_cases['dev'])}, holdout={len(manifest_cases['holdout'])})")


def _write_examples(cases_dir: Path) -> None:
    examples = ["s0_01", "f2_01", "f1_01", "f4_01"]
    ex_dir = Path(__file__).resolve().parent / "examples"
    ex_dir.mkdir(exist_ok=True)
    for case_id in examples:
        split = "dev"
        src = cases_dir / split / f"{case_id}.yaml"
        if src.exists():
            (ex_dir / f"{case_id}.yaml").write_text(src.read_text(encoding="utf-8"),
                                                    encoding="utf-8")


def _write_dataset_report(reports_dir: Path, panel, manifest: dict,
                          f4_info: dict[str, dict]) -> None:
    """Calibration report - committed, deterministic (rule 09: every claim -> artifact)."""
    reports_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Dataset report (docs/07 §2)",
        "",
        f"Seed `{manifest['seed']}` · generator `{manifest['generator_version']}` · "
        f"{manifest['n_assets']} assets × {manifest['n_days']} days.",
        "",
        "| Regime | Days |", "|---|---|",
    ]
    for name, count in manifest["regime_counts"].items():
        lines.append(f"| {name} | {count} |")
    lines += ["", f"Distressed/delisted assets: {len(panel.delisted)} "
              f"(day range 600-735).", "", "## F4 p-hack selection",
              "", "| Case | Window shipped | In-sample perm p | Grid size |", "|---|---|---|---|"]
    for case_id, info in sorted(f4_info.items()):
        lines.append(f"| {case_id} | {info['selected_lookback']} | "
                     f"{info['raw_p']:.4f} | {info['candidates']} |")
    (reports_dir / "dataset.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description="Build the SignalGate synthetic dataset")
    ap.add_argument("--out", default="data")
    ap.add_argument("--reports", default="reports")
    ap.add_argument("--seed", type=int, default=20260828)
    ap.add_argument("--n-assets", type=int, default=50)
    ap.add_argument("--n-days", type=int, default=750)
    args = ap.parse_args()
    out = Path(args.out)
    build(out, Path(args.reports), args.seed, args.n_assets, args.n_days)


if __name__ == "__main__":
    main()
