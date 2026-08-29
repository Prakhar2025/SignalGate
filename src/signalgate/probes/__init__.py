"""Probe tools x4 (docs/03 §8) - sandboxed subprocess execution.

Each probe runs as a separate Python process (`python -m signalgate.probes.worker`)
on synthetic data only, with a hard timeout, no network by construction (the
worker imports no sockets and the DSL namespace exposes no I/O), and POSIX
resource limits where the OS supports them.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from signalgate.schemas import ProbeResult

PROBE_TIMEOUT_S = 10
PROBES = (
    "timestamp_alignment_probe",
    "label_permutation_test",
    "regime_subsample",
    "turnover_and_cost_sanity",
)


def _worker_command() -> list[str]:
    return [sys.executable, "-m", "signalgate.probes.worker"]


def run_probe(probe: str, *, market_path: Path, pseudocode: str,
              horizon: int, costs_bps: float, rebalance: str,
              variants_tried: int, seed: int,
              timeout_s: int = PROBE_TIMEOUT_S) -> ProbeResult:
    """Execute one probe in a capped subprocess; disclose skips honestly."""
    payload = {
        "probe": probe,
        "market_path": str(market_path),
        "pseudocode": pseudocode,
        "horizon": horizon,
        "costs_bps": costs_bps,
        "rebalance": rebalance,
        "variants_tried": variants_tried,
        "seed": seed,
    }
    if probe not in PROBES:
        return ProbeResult(probe=probe, ok=False, skipped=True,
                           skip_reason=f"unknown probe {probe!r} (allowlist)")

    with tempfile.TemporaryDirectory() as td:
        req = Path(td) / "request.json"
        res = Path(td) / "response.json"
        req.write_text(json.dumps(payload), encoding="utf-8")
        cmd = _worker_command() + [str(req), str(res)]
        env = {k: v for k, v in os.environ.items()
               if not k.upper().startswith(("SIGNALGATE_", "AWS_", "OPENAI_"))}
        env.setdefault("PYTHONHASHSEED", "0")
        try:
            proc = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout_s, env=env,
                cwd=str(Path(__file__).resolve().parents[2]),
                preexec_fn=_posix_limits() if os.name == "posix" else None,
            )
        except subprocess.TimeoutExpired:
            return ProbeResult(probe=probe, ok=False, skipped=True,
                               skip_reason=f"timeout after {timeout_s}s (PROBE_SKIPPED)")
        if proc.returncode != 0:
            detail = (proc.stderr or "").strip().splitlines()[-1:] or ["unknown error"]
            return ProbeResult(probe=probe, ok=False, skipped=True,
                               skip_reason=f"worker failed: {detail[0][:200]}")
        data = json.loads(res.read_text(encoding="utf-8"))
        return ProbeResult(probe=probe, ok=True, metrics=data.get("metrics", {}),
                           detail=data.get("detail", {}))


def _posix_limits():
    """CPU (10s) and address-space (1.5 GiB) caps on POSIX; no-op elsewhere."""
    import resource

    def limits() -> None:
        resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
        limit = int(1.5 * 1024**3)
        resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
    return limits
