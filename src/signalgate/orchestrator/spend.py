"""Spend meter + breaker (docs/03 §10): per-run cap, shared session meter."""
from __future__ import annotations

import threading


class SpendMeter:
    def __init__(self, cap_usd: float = 2.00):
        self.cap_usd = cap_usd
        self._lock = threading.Lock()
        self.cost_usd = 0.0
        self.est_tokens = 0
        self.tripped = False

    def record(self, cost_usd: float, tokens: int) -> None:
        with self._lock:
            self.cost_usd += cost_usd
            self.est_tokens += tokens
            if self.cost_usd > self.cap_usd:
                self.tripped = True

    @property
    def exceeded(self) -> bool:
        return self.tripped
