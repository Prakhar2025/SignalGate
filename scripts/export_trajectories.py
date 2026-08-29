"""Export representative agent trajectories (final deliverable 04).

    python -m scripts.export_trajectories --out trajectories/runs

Regenerates a representative set of investigations in LOCAL_MOCK mode
(deterministic, zero keys), then renders each evidence bundle as a readable
trajectory: agent instructions, turn-by-turn spans, tool calls with numeric
responses, feedback, retries and checkpoints, and the final verdict.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generator.cases import ALL_CASES, spec_dict  # noqa: E402

from signalgate import PROMPT_VERSION, __version__  # noqa: E402
from signalgate.agent.prompts import INTERPRET_SYSTEM, PLAN_SYSTEM, PLAN_USER_TMPL  # noqa: E402
from signalgate.config import load_settings  # noqa: E402
from signalgate.orchestrator.pipeline import Orchestrator  # noqa: E402
from signalgate.orchestrator.spend import SpendMeter  # noqa: E402
from signalgate.schemas import SignalSpec  # noqa: E402

# (case_id, label, chaos) - the representative set the judges should read
SELECTION = [
    ("s0_01", "sound flagship passes verification", {}),
    ("f2_01", "semantic lookahead caught by the alignment probe", {}),
    ("f4_01", "best-of-40 p-hack caught by deflation", {}),
    ("f2_06", "partial contamination: honest NEEDS_REVIEW", {}),
    ("f3_01", "survivorship collapse to a dead point-in-time edge", {}),
]


def case_spec(case_id: str) -> SignalSpec:
    """Prefer the built dataset spec (F4 cases carry their selected window there)."""
    import yaml
    settings = load_settings()
    for split in ("dev", "holdout"):
        p = settings.data_dir / "cases" / split / f"{case_id}.yaml"
        if p.exists():
            return SignalSpec.model_validate(yaml.safe_load(p.read_text(encoding="utf-8")))
    case = next(c for c in ALL_CASES if c.case_id == case_id)
    payload = spec_dict(case)
    return SignalSpec.model_validate(payload)


def render(result, label: str) -> str:
    L: list[str] = []
    spec = result.spec
    L.append(f"# Trajectory: {spec.name}")
    L.append("")
    L.append(f"**Outcome: `{result.verdict.value}`** (confidence {result.confidence.value}) - {label}")
    L.append("")
    L.append(f"Mode `{result.mode}` · model `{result.model_id}` · prompt `{result.prompt_version}` "
             f"· seed {result.seed} · cost ${result.cost_usd:.4f} "
             f"(wall-clock runtime excluded to keep regeneration byte-identical)")
    L.append("")
    L.append("## The input the agent received (untrusted spec)")
    L.append("")
    L.append("```yaml")
    L.append(f"name: {spec.name}")
    L.append("description: |")
    for line in spec.description.splitlines():
        L.append(f"  {line}")
    if spec.pseudocode:
        L.append("pseudocode: |")
        for line in spec.pseudocode.splitlines():
            L.append(f"  {line}")
    L.append(f"params: {spec.params.model_dump()}")
    if spec.notes:
        L.append("notes: |")
        for line in spec.notes.splitlines():
            L.append(f"  {line}")
    L.append("```")
    L.append("")

    L.append("## Agent instructions that shaped this run")
    L.append("")
    L.append("Two reasoning calls are available in LIVE mode (LOCAL_MOCK answers the "
             "same contract deterministically). The agent never computes the verdict; "
             "code does, from probe numbers.")
    L.append("")
    L.append("**Call 1, plan (system prompt):**")
    L.append("")
    L.append("```text")
    L.append(PLAN_SYSTEM)
    L.append("```")
    L.append("")
    user = PLAN_USER_TMPL.format(spec_json="{ ...the spec above, serialized... }",
                                 lint_flags="{ ...lint flags from stage 2... }",
                                 probe_list="timestamp_alignment_probe, label_permutation_test, "
                                            "regime_subsample, turnover_and_cost_sanity")
    L.append("**Call 1, user prompt (template):**")
    L.append("")
    L.append("```text")
    L.append(user[:600] + "\n...")
    L.append("```")
    L.append("")
    L.append("**Call 2, interpret (system prompt):**")
    L.append("")
    L.append("```text")
    L.append(INTERPRET_SYSTEM)
    L.append("```")
    L.append("")

    L.append("## Turn-by-turn: instruction, tool response, feedback, checkpoint")
    L.append("")
    L.append("| # | Stage | Event | Detail |")
    L.append("|---|---|---|---|")
    for i, s in enumerate(result.spans, 1):
        detail = {k: v for k, v in s.items() if k not in ("ts", "stage", "event")}
        text = json.dumps(detail, default=str)[:180]
        L.append(f"| {i} | {s['stage']} | {s['event']} | `{text}` |")
    L.append("")

    L.append("## Tool calls and numeric responses")
    L.append("")
    for p in result.probe_results:
        L.append(f"### `{p.probe}`")
        L.append("")
        if p.skipped:
            L.append(f"SKIPPED: {p.skip_reason}")
        else:
            L.append("```json")
            L.append(json.dumps(p.metrics, indent=2))
            L.append("```")
        L.append("")

    L.append("## What the agent extracted (claims)")
    L.append("")
    for c in result.claims:
        span = f' (evidence: "{c.evidence_span}")' if c.evidence_span else ""
        L.append(f"- **[{c.kind}]** {c.text}{span}")
    if not result.claims:
        L.append("- none")
    L.append("")

    L.append("## Feedback and checkpoints")
    L.append("")
    L.append("- The composer checkpoint is the human-checkpoint equivalent inside the "
             "loop: the verdict is computed from thresholds in code, and the narrative "
             "agent is instructed to present it faithfully, never to decide it.")
    if result.degraded:
        L.append("- DEGRADED run: the model path was unavailable, so the run dropped to "
                 "lint-only and the verdict is disclosed as unverified.")
    for p in result.probe_results:
        if p.skipped:
            L.append(f"- `{p.probe}` was skipped and the bundle discloses it; skipped "
                     "probes weaken evidence and can never strengthen a verdict.")
    L.append("")

    L.append("## Final result")
    L.append("")
    L.append(f"- Verdict: `{result.verdict.value}` ({result.confidence.value})")
    L.append(f"- Reason codes: {', '.join(c.value for c in result.reason_codes) or 'none'}")
    L.append(f"- Recommended action: `{result.recommended_action.value}`")
    L.append("")
    L.append("> Verdicts are advisory. The researcher is the qualified reviewer. "
             "SignalGate recommends, never trades.")
    L.append("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="trajectories/runs")
    args = ap.parse_args()
    settings = load_settings()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    index: list[str] = [
        "# Runtime agent trajectories",
        "",
        f"Generated by `scripts/export_trajectories.py` from deterministic LOCAL_MOCK "
        f"runs (package {__version__}, prompt {PROMPT_VERSION}, seed 20260828). Every "
        f"number here regenerates byte-identically.",
        "",
        "| Trajectory | Case | Outcome | What it shows |",
        "|---|---|---|---|",
    ]
    for case_id, label, chaos in SELECTION:
        orch = Orchestrator(settings, spend=SpendMeter(settings.spend_cap_usd),
                            chaos=chaos)
        result = orch.investigate(case_spec(case_id), case_id=case_id, persist=True)
        fname = f"{case_id}.md"
        (out / fname).write_text(render(result, label), encoding="utf-8")
        index.append(f"| [{fname}]({fname}) | {case_id} | `{result.verdict.value}` | {label} |")
        print(f"  exported {fname}: {result.verdict.value}")

    chaos_out = out.parent / "chaos.md"
    lines = ["# Degradation trajectories (docs chaos matrix)", ""]
    for chaos, title in (({"model_down": True}, "model provider down"),
                         ({"probe_timeout": True}, "probe timeouts")):
        orch = Orchestrator(settings, spend=SpendMeter(settings.spend_cap_usd),
                            chaos=chaos)
        result = orch.investigate(case_spec("f2_01"), case_id="f2_01", persist=True)
        lines.append(f"## {title}")
        lines.append("")
        lines.append(f"Verdict: `{result.verdict.value}` ({result.confidence.value}), "
                     f"degraded={result.degraded}, codes: "
                     f"{', '.join(c.value for c in result.reason_codes)}")
        lines.append("")
        lines.append("```json")
        lines.append(json.dumps([p.model_dump() for p in result.probe_results], indent=2, default=str))
        lines.append("```")
        lines.append("")
    chaos_out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    index.append("| [chaos.md](chaos.md) | f2_01 x2 | DEGRADED | model-down and probe-timeout paths, disclosed |")

    (out / "INDEX.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    print(f"trajectories -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
