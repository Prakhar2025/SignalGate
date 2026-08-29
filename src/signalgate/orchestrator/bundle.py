"""Evidence bundle writer - every claim becomes a disk artifact (ground rule 09)."""
from __future__ import annotations

import json
from pathlib import Path

from signalgate.schemas import RunResult


def bundle_dir(artifacts_root: Path, run_id: str) -> Path:
    d = artifacts_root / "runs" / run_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def write_bundle(result: RunResult, artifacts_root: Path) -> Path:
    d = bundle_dir(artifacts_root, result.run_id)
    (d / "bundle.json").write_text(
        result.model_dump_json(indent=2), encoding="utf-8")
    (d / "trajectory.json").write_text(
        json.dumps(result.spans, indent=2), encoding="utf-8")
    (d / "bundle.md").write_text(to_markdown(result), encoding="utf-8")
    return d


def to_markdown(r: RunResult) -> str:
    lines = [
        f"# Verdict - {r.spec.name}",
        "",
        f"**{r.verdict.value}** (confidence {r.confidence.value})"
        + (" · DEGRADED" if r.degraded else ""),
        "",
        "Reason codes: " + (", ".join(c.value for c in r.reason_codes) or "none"),
        "",
        "## What came in",
        r.spec.description,
        "",
        "## What we probed",
    ]
    for p in r.probe_results:
        if p.skipped:
            lines.append(f"- `{p.probe}` - SKIPPED ({p.skip_reason})")
        else:
            metrics = ", ".join(f"{k}={v}" for k, v in p.metrics.items())
            lines.append(f"- `{p.probe}` - {metrics}")
    lines += ["", "## Why this verdict", r.narrative or "(see reason codes)", ""]
    if r.claims:
        lines += ["## Claims extracted"]
        lines += [f"- [{c.kind}] {c.text}" for c in r.claims]
        lines.append("")
    lines += [
        f"## Recommended action: `{r.recommended_action.value}`",
        "",
        f"_mode {r.mode} · model {r.model_id} · prompt {r.prompt_version} · "
        f"seed {r.seed} · cost ${r.cost_usd:.4f} · run {r.run_id}_",
        "",
        "Verdicts are advisory. The researcher decides. SignalGate recommends, never trades.",
    ]
    return "\n".join(lines)
