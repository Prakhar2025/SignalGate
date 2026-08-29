"""Byte-identical repro check: score the same subset twice, diff the JSON.

    python -m signalgate.eval.repro        (used by `make repro-check` and CI)
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from signalgate.config import load_settings
from signalgate.eval.run import load_split, run_system
from signalgate.eval.score import score


def main() -> int:
    settings = load_settings()
    cases = load_split(settings, "dev", limit=6)
    if not cases:
        print("dataset missing - run `python -m generator.build --out data` first")
        return 1
    with tempfile.TemporaryDirectory() as td:
        runs = []
        for i in (1, 2):
            out = Path(td) / f"run{i}"
            run_system("agent", settings,
                       [(cid, dict(p)) for cid, p in cases], out)
            run_system("baseline", settings,
                       [(cid, dict(p)) for cid, p in cases], out)
            score(out / "baseline", out / "agent", out)
            runs.append((out / "metrics.json").read_text(encoding="utf-8"))
        if runs[0] == runs[1]:
            print("repro-check OK - metrics.json byte-identical across runs")
            return 0
        print("repro-check FAILED - metrics differ between identical runs")
        a, b = json.loads(runs[0]), json.loads(runs[1])
        for key in a:
            if a[key] != b.get(key):
                print(f"  differs: {key}: {a[key]} != {b.get(key)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
