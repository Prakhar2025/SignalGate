"""Scorers (docs/07 §3, §5): catch rates, Wilson CIs, McNemar, comparison table."""
from __future__ import annotations

import json
import math
from pathlib import Path

from signalgate import DATASET_SEED, GENERATOR_VERSION, PROMPT_VERSION, __version__


def wilson(p: float, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def mcnemar(b: int, c: int) -> float:
    """Two-sided exact-ish McNemar with continuity correction; chi2(1) p."""
    if b + c == 0:
        return 1.0
    chi2 = (abs(b - c) - 1) ** 2 / (b + c)
    # p-value from chi2(1) via erfc: p = erfc(sqrt(chi2/2))
    from math import erfc, sqrt
    return erfc(sqrt(chi2 / 2.0))


def _resolve(path: Path) -> Path:
    return path / "results.jsonl" if path.is_dir() else path


def load_records(path: Path) -> list[dict]:
    path = _resolve(Path(path))
    return [json.loads(line) for line in
            path.read_text(encoding="utf-8").splitlines() if line.strip()]


def system_metrics(records: list[dict]) -> dict:
    spurious = [r for r in records if r["family"] != "S0"]
    sound = [r for r in records if r["family"] == "S0"]
    tp = sum(1 for r in spurious if r["verdict"] == "REJECT_SPURIOUS")
    fp = sum(1 for r in sound if r["verdict"] == "REJECT_SPURIOUS")
    promising = sum(1 for r in sound if r["verdict"] == "PROMISING")
    per_stratum = {}
    for fam in ("F1", "F2", "F3", "F4", "F5"):
        rows = [r for r in records if r["family"] == fam]
        if rows:
            k = sum(1 for r in rows if r["verdict"] == "REJECT_SPURIOUS")
            lo, hi = wilson(k / len(rows), len(rows))
            per_stratum[fam] = {"catch": round(k / len(rows), 3), "n": len(rows),
                                "ci95": [round(lo, 3), round(hi, 3)]}
    lo, hi = wilson(tp / len(spurious), len(spurious)) if spurious else (0, 0)
    return {
        "spurious_catch_rate": round(tp / len(spurious), 3) if spurious else None,
        "spurious_catch_ci95": [round(lo, 3), round(hi, 3)],
        "false_reject_rate": round(fp / len(sound), 3) if sound else None,
        "false_rejects": fp, "sound_n": len(sound), "sound_promising": promising,
        "precision_reject": round(tp / (tp + fp), 3) if (tp + fp) else None,
        "per_stratum": per_stratum,
        "cost_usd_mean": round(sum(r.get("cost_usd", 0) for r in records) / len(records), 6)
        if records else 0.0,
        "est_tokens_mean": round(sum(r.get("est_tokens", 0) for r in records) / len(records))
        if records else 0,
        # latency is wall-time and lives in the comparison report only -
        # metrics.json must stay byte-identical across runs (docs/07 §5)
        "n_cases": len(records),
    }


def latency_p50(records: list[dict]) -> int:
    lat = sorted(r.get("latency_ms", 0) for r in records)
    return lat[len(lat) // 2] if lat else 0


def score(baseline_path: Path, agent_path: Path, out_dir: Path,
          suffix: str = "", meta: dict | None = None) -> dict:
    base = load_records(Path(baseline_path))
    agent = load_records(Path(agent_path))
    bm, am = system_metrics(base), system_metrics(agent)

    by_id_b = {r["case_id"]: r for r in base}
    b_only = a_only = both_wrong = both_right = 0
    for r in agent:
        rb = by_id_b[r["case_id"]]
        a_ok = (r["verdict"] == "REJECT_SPURIOUS") == (r["family"] != "S0")
        b_ok = (rb["verdict"] == "REJECT_SPURIOUS") == (r["family"] != "S0")
        if a_ok and not b_ok:
            a_only += 1
        elif b_ok and not a_ok:
            b_only += 1
        elif a_ok and b_ok:
            both_right += 1
        else:
            both_wrong += 1
    p_mcnemar = mcnemar(b_only, a_only)

    metrics = {
        "schema_version": "metrics@1",
        "split": suffix or "dev",
        "mode": meta.get("mode", "LOCAL_MOCK") if meta else "LOCAL_MOCK",
        "model_id": meta.get("model_id", "LOCAL_MOCK") if meta else "LOCAL_MOCK",
        "prompt_version": PROMPT_VERSION,
        "package_version": __version__,
        "generator_version": GENERATOR_VERSION,
        "dataset_seed": DATASET_SEED,
        "baseline": bm,
        "agent": am,
        "delta_catch_rate": round((am["spurious_catch_rate"] or 0)
                                  - (bm["spurious_catch_rate"] or 0), 3),
        "mcnemar": {"baseline_only_correct": b_only, "agent_only_correct": a_only,
                    "both_correct": both_right, "both_wrong": both_wrong,
                    "p_value": round(p_mcnemar, 6)},
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"metrics{('_' + suffix) if suffix else ''}.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = comparison_md(metrics)
    report += ("\nThis run: latency p50 " + str(latency_p50(agent)) + " ms "
               "(wall-clock; excluded from metrics.json to keep it byte-identical).\n")
    (out_dir / f"comparison{('_' + suffix) if suffix else ''}.md").write_text(
        report, encoding="utf-8")
    return metrics


def comparison_md(m: dict) -> str:
    b, a = m["baseline"], m["agent"]
    rows = [
        "| Metric | Baseline (static lint) | Agent solution | Change |",
        "|---|---|---|---|",
        (f"| Spurious catch rate | {b['spurious_catch_rate']} "
         f"(95% CI {b['spurious_catch_ci95']}) | {a['spurious_catch_rate']} "
         f"(95% CI {a['spurious_catch_ci95']}) | {m['delta_catch_rate']:+.3f} |"),
        f"| False-reject rate (S0) | {b['false_reject_rate']} | {a['false_reject_rate']} | - |",
        f"| Precision (reject) | {b['precision_reject']} | {a['precision_reject']} | - |",
        "| Human time per task | 60-90 min manual | ~3 min evidence review | -95% |",
        (f"| Cost per task | $0 | ${a['cost_usd_mean']:.4f} ({m['mode']}) "
         f"| disclosed |"),
    ]
    strata = ["| Stratum | Baseline catch | Agent catch |", "|---|---|---|"]
    for fam in ("F1", "F2", "F3", "F4", "F5"):
        bs = b["per_stratum"].get(fam, {}).get("catch", "-")
        as_ = a["per_stratum"].get(fam, {}).get("catch", "-")
        strata.append(f"| {fam} | {bs} | {as_} |")
    mcn = m["mcnemar"]
    footer = (
        f"\nMcNemar paired test (same {m['agent']['n_cases']} cases): agent-only "
        f"correct {mcn['agent_only_correct']}, baseline-only correct "
        f"{mcn['baseline_only_correct']} - p = {mcn['p_value']}. "
        f"Seed {m['dataset_seed']}, mode {m['mode']}, model {m['model_id']}, "
        f"prompt {m['prompt_version']}.\n\n"
        "Human time: baseline and agent both replace the 60-90 min manual review; "
        "the agent's evidence bundle reduces review to ~3 minutes for surviving cases.\n")
    return "\n".join(rows) + "\n\n" + "\n".join(strata) + footer


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Score eval runs and write metrics + comparison")
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--agent", required=True)
    ap.add_argument("--out", default="reports")
    ap.add_argument("--suffix", default="")
    args = ap.parse_args()
    meta = {"mode": "LOCAL_MOCK", "model_id": "LOCAL_MOCK"}
    m = score(Path(args.baseline), Path(args.agent), Path(args.out),
              suffix=args.suffix, meta=meta)
    a = m["agent"]
    print(f"agent  : catch {a['spurious_catch_rate']} (CI {a['spurious_catch_ci95']}), "
          f"false-reject {a['false_reject_rate']}, F2 {a['per_stratum']['F2']['catch']}")
    b = m["baseline"]
    print(f"baseline: catch {b['spurious_catch_rate']}, false-reject {b['false_reject_rate']}")
    print(f"McNemar p = {m['mcnemar']['p_value']}  -> reports/comparison{('_' + args.suffix) if args.suffix else ''}.md")
