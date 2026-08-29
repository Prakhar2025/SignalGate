#!/usr/bin/env python
"""Secret scan (ground rule 08): fail if credential-like patterns enter the repo."""
from __future__ import annotations

import re
import sys
from pathlib import Path

PATTERNS = [
    (r"AKIA[0-9A-Z]{16}", "AWS access key"),
    (r"-----BEGIN (RSA|EC|OPENSSH|PGP|DSA) PRIVATE KEY-----", "private key block"),
    (r"ghp_[A-Za-z0-9]{36}", "GitHub PAT"),
    (r"sk-[A-Za-z0-9]{20,}", "API key (sk-…)"),
    (r"xox[bap]-[A-Za-z0-9-]{10,}", "Slack token"),
    (r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}", "JWT"),
]
ALLOW = (".venv", ".git", "node_modules", "__pycache__", "artifacts", "data")
# docs mentioning patterns as documentation are still scanned; only this
# scanner's own pattern definitions are exempt
SELF = Path(__file__).name


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    hits = []
    for p in root.rglob("*"):
        if not p.is_file() or p.name == SELF:
            continue
        if any(part in ALLOW for part in p.parts):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        for pattern, label in PATTERNS:
            for m in re.finditer(pattern, text):
                line = text[:m.start()].count("\n") + 1
                hits.append(f"{p.relative_to(root)}:{line} - {label}")
    if hits:
        print("SECRET SCAN FAILED:")
        for h in hits:
            print(f"  {h}")
        return 1
    print("secret scan OK - no credential-like patterns in tracked files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
