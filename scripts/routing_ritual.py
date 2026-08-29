#!/usr/bin/env python
"""Routing ritual (docs/03 §9): re-verify every routed model ID live.

One capped invocation per routed ID from the deploy region; results append to
artifacts/ritual/ritual.json and print a ready-to-paste markdown row for
docs/03 §9. With no credentials the ritual reports SKIPPED honestly - it
never fabricates a verification.
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROUTED = [
    ("investigation reasoning", os.getenv("SIGNALGATE_MODEL", ""), "primary (env-routed)"),
    ("repro / judges", "LOCAL_MOCK", "zero-key canned reasoning"),
]

MAX_REPLY_TOKENS = 16


def ritual() -> int:
    out_dir = Path("artifacts/ritual")
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).isoformat(timespec="seconds")
    rows = []

    api_base = os.getenv("SIGNALGATE_API_BASE", "").strip()
    api_key = os.getenv("SIGNALGATE_API_KEY", "").strip()

    for job, model_id, note in ROUTED:
        if not model_id:
            rows.append({"job": job, "model": model_id or "(unset)", "status": "UNSET",
                         "note": note, "ts": stamp})
            continue
        if model_id == "LOCAL_MOCK":
            rows.append({"job": job, "model": model_id, "status": "OK (offline)",
                         "note": note + " - no network needed", "ts": stamp})
            continue
        if not (api_base and api_key):
            rows.append({"job": job, "model": model_id, "status": "SKIPPED",
                         "note": "no SIGNALGATE_API_BASE/API_KEY - ritual does not "
                                 "fabricate verification", "ts": stamp})
            continue
        import httpx
        t0 = time.time()
        try:
            resp = httpx.post(
                f"{api_base.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": model_id, "max_tokens": MAX_REPLY_TOKENS,
                      "messages": [{"role": "user", "content": "Reply with the word: ok"}]},
                timeout=20.0)
            resp.raise_for_status()
            text = resp.json()["choices"][0]["message"]["content"].strip()[:40]
            rows.append({"job": job, "model": model_id,
                         "status": f"OK ({time.time() - t0:.1f}s)",
                         "reply": text, "region_check": api_base, "ts": stamp})
        except Exception as exc:
            rows.append({"job": job, "model": model_id, "status": "FAIL",
                         "error": str(exc)[:160], "ts": stamp})

    payload = {"ritual_ts": stamp, "rows": rows}
    (out_dir / "ritual.json").write_text(json.dumps(payload, indent=2) + "\n",
                                         encoding="utf-8")

    print("| Job | Model | Status | Date |")
    print("|---|---|---|---|")
    for r in rows:
        print(f"| {r['job']} | `{r['model']}` | {r['status']} | {stamp[:10]} |")
    print("\nresults -> artifacts/ritual/ritual.json (paste rows into docs/03 §9)")
    return 0 if all("FAIL" not in r["status"] for r in rows) else 1


if __name__ == "__main__":
    sys.exit(ritual())
