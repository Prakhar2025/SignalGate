"""Model adapter (docs/03 §9): LIVE via any OpenAI-compatible endpoint, LOCAL_MOCK stub.

JSON is obtained by prompt + fence-stripping + schema gate - no native
responseFormat is assumed (portability row of the routing table).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Protocol

import httpx
import jsonschema


class AdapterError(RuntimeError):
    """Raised when the model call fails or output cannot be fenced."""


@dataclass
class Usage:
    est_tokens_in: int = 0
    est_tokens_out: int = 0
    cost_usd: float = 0.0


# rough per-1M-token price by model family, for spend metering only
PRICE_TABLE = {
    "default": (0.80, 3.20),
    "nova-pro": (0.80, 3.20),
    "nova-lite": (0.06, 0.24),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
}


def estimate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
    pin, pout = PRICE_TABLE.get("default", (1.0, 4.0))
    for key, prices in PRICE_TABLE.items():
        if key != "default" and key in model.lower():
            pin, pout = prices
            break
    return (tokens_in * pin + tokens_out * pout) / 1e6


class ModelAdapter(Protocol):
    model_id: str

    def complete(self, system: str, user: str, schema: dict, max_tokens: int = 1200) -> tuple[dict, Usage]:
        """Return a schema-validated JSON object plus usage."""


def strip_fence(text: str) -> str:
    """Extract the first JSON object from a possibly-fenced reply."""
    fence = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence:
        return fence.group(1)
    brace = re.search(r"\{.*\}", text, re.DOTALL)
    if brace:
        return brace.group(0)
    raise AdapterError("no JSON object found in model output")


class OpenAICompatAdapter:
    """Minimal chat-completions client, JSON-gated with one bounded retry."""

    def __init__(self, model: str, api_base: str, api_key: str, timeout_s: float = 30.0):
        self.model_id = model
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.timeout_s = timeout_s

    def complete(self, system: str, user: str, schema: dict, max_tokens: int = 1200) -> tuple[dict, Usage]:
        usage = Usage(est_tokens_in=(len(system) + len(user)) // 4)
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        last_err: Exception | None = None
        for _attempt in range(2):
            try:
                resp = httpx.post(
                    f"{self.api_base}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={"model": self.model_id, "messages": messages,
                          "max_tokens": max_tokens, "temperature": 0.0},
                    timeout=self.timeout_s,
                )
                resp.raise_for_status()
                text = resp.json()["choices"][0]["message"]["content"]
            except (httpx.HTTPError, KeyError, IndexError) as exc:
                last_err = exc
                continue
            usage.est_tokens_out = len(text) // 4
            try:
                obj = json.loads(strip_fence(text))
                jsonschema.validate(obj, schema)
            except (AdapterError, json.JSONDecodeError, jsonschema.ValidationError) as exc:
                last_err = exc
                messages.append({"role": "assistant", "content": text})
                messages.append({"role": "user", "content":
                                 "Your reply was not valid against the schema. "
                                 "Reply with ONLY a corrected JSON object."})
                continue
            usage.cost_usd = estimate_cost(self.model_id, usage.est_tokens_in, usage.est_tokens_out)
            return obj, usage
        raise AdapterError(f"model call failed after retries: {last_err}")


class LocalMockAdapter:
    """Zero-key adapter: raises if used - the mock reasoner bypasses text calls."""

    model_id = "LOCAL_MOCK"

    def complete(self, system: str, user: str, schema: dict, max_tokens: int = 1200):
        raise AdapterError("LOCAL_MOCK has no text endpoint")
