"""Ground-rule assertions: no secrets in the repo, dataset content integrity."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_secret_scan_passes():
    r = subprocess.run([sys.executable, str(REPO / "scripts" / "secret_scan.py")],
                       capture_output=True, text=True, cwd=str(REPO))
    assert r.returncode == 0, r.stdout + r.stderr


def test_no_env_file_committed():
    assert not (REPO / ".env").exists(), ".env must never be committed (rule 08)"
    assert (REPO / ".env.example").exists()


def test_routing_ritual_runs_offline():
    import os
    env = {k: v for k, v in os.environ.items()
           if not k.upper().startswith("SIGNALGATE_")}
    r = subprocess.run([sys.executable, str(REPO / "scripts" / "routing_ritual.py")],
                       capture_output=True, text=True, cwd=str(REPO), env=env)
    # with no credentials the ritual reports honestly, never fails
    assert "LOCAL_MOCK" in r.stdout, r.stdout + r.stderr
    assert "UNSET" in r.stdout
