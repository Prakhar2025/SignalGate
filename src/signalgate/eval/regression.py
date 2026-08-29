"""Regression gate (docs/07 §7): catch-rate floor + false-reject ceiling fail the build."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

GATES = {
    "agent_spurious_catch_rate_min": 0.85,
    "agent_false_reject_rate_max": 0.05,
    "agent_f2_catch_min": 0.75,
}


def check(metrics_path: Path) -> int:
    m = json.loads(metrics_path.read_text(encoding="utf-8"))
    a = m["agent"]
    failures = []
    catch = a["spurious_catch_rate"]
    frr = a["false_reject_rate"]
    if catch is None or catch < GATES["agent_spurious_catch_rate_min"]:
        failures.append(f"catch rate {catch} < {GATES['agent_spurious_catch_rate_min']}")
    if frr is None or frr > GATES["agent_false_reject_rate_max"]:
        failures.append(f"false-reject {frr} > {GATES['agent_false_reject_rate_max']}")
    f2 = a["per_stratum"].get("F2", {}).get("catch", 0)
    if f2 < GATES["agent_f2_catch_min"]:
        failures.append(f"F2 catch {f2} < {GATES['agent_f2_catch_min']}")
    if failures:
        print("REGRESSION GATE FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"regression gate OK - catch {a['spurious_catch_rate']}, "
          f"false-reject {a['false_reject_rate']}, F2 {f2}")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--metrics", default="reports/metrics.json")
    args = ap.parse_args()
    sys.exit(check(Path(args.metrics)))
