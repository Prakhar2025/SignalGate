"""Eval runner (docs/07 §6): drives the orchestrator over a dataset split.

    python -m signalgate.eval.run --system both --split dev --out artifacts/agent

Writes per-system results.jsonl (one record per case, deterministic in
LOCAL_MOCK mode). LIVE mode requires SIGNALGATE_* env; every run embeds mode,
model id, prompt version and seed so metrics.json can be regenerated
byte-identically.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import yaml

from signalgate.config import load_settings
from signalgate.orchestrator.pipeline import Orchestrator, SpecInvalid
from signalgate.schemas import SignalSpec, Verdict


def load_split(settings, split: str, limit: int | None = None) -> list[tuple[str, dict]]:
    base = settings.data_dir / "cases" / split
    paths = sorted(base.glob("*.yaml"))
    if limit:
        paths = paths[:limit]
    cases = []
    for p in paths:
        truth = json.loads((settings.data_dir / "manifest.json").read_text(encoding="utf-8"))
        meta = truth["cases"][split][p.stem]
        cases.append((p.stem, {**yaml.safe_load(p.read_text(encoding="utf-8")),
                               "_truth": meta}))
    return cases


def run_system(system: str, settings, cases, out_dir: Path,
               chaos: dict | None = None) -> Path:
    from signalgate.orchestrator.spend import SpendMeter
    out_sys = out_dir / system
    out_sys.mkdir(parents=True, exist_ok=True)
    results_path = out_sys / "results.jsonl"
    spend = SpendMeter(settings.spend_cap_usd)
    orch = Orchestrator(settings=settings, spend=spend, chaos=chaos)
    lines = []
    for case_id, payload in cases:
        truth = payload.pop("_truth")
        t0 = time.perf_counter()
        try:
            spec = SignalSpec.model_validate(payload)
            depth = "baseline" if system == "baseline" else "agent"
            result = orch.investigate(spec, case_id=case_id, depth=depth, persist=False)
            record = {
                "case_id": case_id,
                "family": truth["family"],
                "expected": truth["expected_verdict"],
                "verdict": result.verdict.value,
                "confidence": result.confidence.value,
                "reason_codes": [c.value for c in result.reason_codes],
                "degraded": result.degraded,
                "cost_usd": result.cost_usd,
                "est_tokens": result.est_tokens,
                "latency_ms": result.elapsed_ms,
                "run_id": result.run_id,
            }
        except SpecInvalid as exc:
            record = {"case_id": case_id, "family": truth["family"],
                      "expected": truth["expected_verdict"],
                      "verdict": Verdict.REJECTED_INVALID.value,
                      "reason_codes": ["SCHEMA_INVALID"], "error": str(exc)[:200]}
        record["latency_ms"] = record.get("latency_ms") or int((time.perf_counter() - t0) * 1000)
        lines.append(json.dumps(record, sort_keys=True))
        print(f"  [{system}] {case_id} {record['family']:3s} -> {record['verdict']}"
              f"{'  MISS' if record['verdict'] != truth['expected_verdict'] and truth['family'] != 'S0' else ''}"
              f"{'  FALSE-REJECT' if record['family'] == 'S0' and record['verdict'] == 'REJECT_SPURIOUS' else ''}")
    results_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return results_path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--system", choices=["baseline", "agent", "both"], default="both")
    ap.add_argument("--split", choices=["dev", "holdout"], default="dev")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--out", default="artifacts/eval")
    ap.add_argument("--chaos", default="", help="comma list: model_down,probe_timeout")
    args = ap.parse_args()
    settings = load_settings()
    cases = load_split(settings, args.split, args.limit)
    if not cases:
        print("dataset missing - run `python -m generator.build --out data` first")
        return 1
    chaos = {"model_down": "model_down" in args.chaos,
             "probe_timeout": "probe_timeout" in args.chaos}
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    systems = ["baseline", "agent"] if args.system == "both" else [args.system]
    for system in systems:
        print(f"[eval] {system} over {len(cases)} {args.split} cases "
              f"(mode={settings.effective_mode})")
        run_system(system, settings,
                   [(cid, dict(payload)) for cid, payload in cases], out_dir, chaos)
    print(f"[eval] results -> {out_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
