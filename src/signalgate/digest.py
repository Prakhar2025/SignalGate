"""Quiet-pipeline digest (docs/02 §5 J2): the artifact that sells the product.

    python -m signalgate.digest --from artifacts/agent --out reports/digest.md
"""
from __future__ import annotations

import argparse
from pathlib import Path

from signalgate.config import load_settings
from signalgate.eval.score import load_records


def build_digest(records: list[dict], out_path: Path, title: str = "Weekly signal screen") -> None:
    rejects = [r for r in records if r["verdict"] == "REJECT_SPURIOUS"]
    review = [r for r in records if r["verdict"] == "NEEDS_REVIEW"]
    promising = [r for r in records if r["verdict"] == "PROMISING"]
    invalid = [r for r in records if r["verdict"] == "REJECTED_INVALID"]

    lines = [
        f"# {title}",
        "",
        f"**{len(records)} signals screened. "
        f"{len(rejects)} rejected with receipts. "
        f"{len(review) + len(invalid)} needed your hour. "
        f"{len(promising)} promising.**",
        "",
        "## Rejected (no researcher time required)",
        "",
        "| Case | Family | Reason codes |", "|---|---|---|",
    ]
    for r in rejects:
        lines.append(f"| {r['case_id']} | {r['family']} | "
                     f"{', '.join(r['reason_codes']) or '-'} |")
    lines += ["", "## Needs review (start here)", ""]
    for r in review:
        lines.append(f"- **{r['case_id']}** ({r['family']}): "
                     f"{', '.join(r['reason_codes']) or 'incomplete evidence'}")
    if promising:
        lines += ["", "## Promising (with receipts)", ""]
        for r in promising:
            lines.append(f"- **{r['case_id']}** ({r['family']}) - "
                         "verification held; promote to paper-trade review.")
    lines += [
        "",
        "---",
        "",
        "_Verdicts are advisory; the researcher decides. "
        "Rejected cases keep their evidence bundles under artifacts/runs/._",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", default="artifacts/agent")
    ap.add_argument("--out", default="reports/digest.md")
    ap.add_argument("--title", default="Weekly signal screen")
    args = ap.parse_args()
    src = Path(args.src)
    records_path = src / "agent" / "results.jsonl"
    if not records_path.exists():
        records_path = src / "results.jsonl"
    if not records_path.exists():
        settings = load_settings()
        records_path = settings.artifacts_dir / "agent" / "results.jsonl"
    records = load_records(records_path)
    build_digest(records, Path(args.out), args.title)
    print(f"[digest] {len(records)} cases -> {args.out}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
