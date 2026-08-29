"""Web gate + JSON API (docs/03 §10): one service, zero node build.

Routes: GET / (gate UI), POST /investigate (JSON + HTMX form), GET /runs/{id},
GET /digest, GET /healthz, /docs (swagger). Rate limit 30 req/min/IP.
"""
from __future__ import annotations

import json
import time
from collections import defaultdict, deque
from pathlib import Path

import yaml
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from signalgate import __version__
from signalgate.config import load_settings
from signalgate.orchestrator.bundle import to_markdown
from signalgate.orchestrator.pipeline import SpecInvalid, investigate_spec_dict

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "ui" / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

RATE_LIMIT = 30
RATE_WINDOW_S = 60.0
_hits: dict[str, deque] = defaultdict(lambda: deque(maxlen=RATE_LIMIT))


def _rate_limited(request: Request) -> bool:
    ip = request.client.host if request.client else "?"
    limit = getattr(request.app.state, "rate_limit", RATE_LIMIT)
    window = getattr(request.app.state, "rate_window_s", RATE_WINDOW_S)
    now = time.monotonic()
    hits = _hits[ip]
    while hits and now - hits[0] > window:
        hits.popleft()
    if len(hits) >= limit:
        return True
    hits.append(now)
    return False


def create_app(settings=None, rate_limit: int = RATE_LIMIT,
               rate_window_s: float = RATE_WINDOW_S) -> FastAPI:
    settings = settings or load_settings()
    app = FastAPI(title="SignalGate", version=__version__,
                  description="Agentic research-integrity gate - verdicts with receipts.")
    app.state.rate_limit = rate_limit
    app.state.rate_window_s = rate_window_s

    @app.get("/healthz")
    def healthz() -> dict:
        return {"status": "ok", "version": __version__,
                "mode": settings.effective_mode}

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request):
        examples = sorted((settings.data_dir.parent / "generator" / "examples").glob("*.yaml")) \
            if (settings.data_dir.parent / "generator" / "examples").exists() else []
        recent = _recent_runs(settings)
        return templates.TemplateResponse(request, "index.html", {
            "mode": settings.effective_mode, "examples": [p.stem for p in examples],
            "recent": recent, "example_text": "",
        })

    @app.get("/examples/{name}")
    def example(name: str):
        p = settings.data_dir.parent / "generator" / "examples" / f"{name}.yaml"
        if not p.exists():
            return JSONResponse({"error": "unknown example"}, status_code=404)
        return JSONResponse(yaml.safe_load(p.read_text(encoding="utf-8")))

    @app.get("/examples/{name}/raw", response_class=HTMLResponse)
    def example_raw(name: str):
        p = settings.data_dir.parent / "generator" / "examples" / f"{name}.yaml"
        if not p.exists():
            return HTMLResponse("", status_code=404)
        return HTMLResponse(p.read_text(encoding="utf-8"))

    @app.post("/investigate", response_class=HTMLResponse)
    async def investigate(request: Request):
        if _rate_limited(request):
            return JSONResponse({"error": "rate limit: 30 requests/min/IP"},
                                status_code=429)
        ctype = request.headers.get("content-type", "")
        try:
            if "form" in ctype:
                form = await request.form()
                raw = str(form.get("spec", ""))
                spec_dict = yaml.safe_load(raw)
                htmx = True
            else:
                body = await request.json()
                raw = body.get("spec_yaml", "")
                spec_dict = body.get("spec", None) or yaml.safe_load(raw)
                htmx = False
        except yaml.YAMLError as exc:
            return _invalid(request, f"YAML parse error: {exc}", htmx="form" in ctype)
        try:
            result = investigate_spec_dict(spec_dict, settings=settings)
        except SpecInvalid as exc:
            return _invalid(request, str(exc), htmx=htmx)
        except Exception as exc:  # never leak a 500 with a stack trace to the gate
            return _invalid(request, f"investigation failed: {exc}", htmx=htmx)
        if htmx:
            return templates.TemplateResponse(request, "_card.html", {
                "r": result, "spec_yaml": raw})
        return JSONResponse({
            "run_id": result.run_id, "verdict": result.verdict.value,
            "confidence": result.confidence.value,
            "reason_codes": [c.value for c in result.reason_codes],
            "degraded": result.degraded,
            "findings": [e.model_dump() for e in result.findings],
            "narrative": result.narrative,
            "recommended_action": result.recommended_action.value,
            "cost_usd": result.cost_usd, "elapsed_ms": result.elapsed_ms,
            "bundle": f"/runs/{result.run_id}",
        })

    @app.get("/runs/{run_id}", response_class=HTMLResponse)
    def run_page(request: Request, run_id: str):
        d = settings.artifacts_dir / "runs" / run_id
        f = d / "bundle.json"
        if not f.exists():
            return HTMLResponse("bundle not found", status_code=404)
        from signalgate.schemas import RunResult
        result = RunResult.model_validate_json(f.read_text(encoding="utf-8"))
        return templates.TemplateResponse(request, "run.html", {
            "r": result, "markdown": to_markdown(result)})

    @app.get("/runs/{run_id}/bundle.json")
    def run_bundle(run_id: str):
        f = settings.artifacts_dir / "runs" / run_id / "bundle.json"
        if not f.exists():
            return JSONResponse({"error": "not found"}, status_code=404)
        return JSONResponse(json.loads(f.read_text(encoding="utf-8")))

    @app.get("/runs/{run_id}/bundle.md")
    def run_bundle_md(run_id: str):
        f = settings.artifacts_dir / "runs" / run_id / "bundle.md"
        if not f.exists():
            return JSONResponse({"error": "not found"}, status_code=404)
        return HTMLResponse(f.read_text(encoding="utf-8"))

    @app.get("/digest", response_class=HTMLResponse)
    def digest_page(request: Request):
        records = _recent_records(settings)
        return templates.TemplateResponse(request, "digest.html", {"records": records})

    return app


def _recent_runs(settings, limit: int = 8) -> list[dict]:
    runs = settings.artifacts_dir / "runs"
    if not runs.exists():
        return []
    out = []
    for d in sorted(runs.iterdir(), key=lambda p: p.name)[-limit:]:
        f = d / "bundle.json"
        if f.exists():
            try:
                import json
                b = json.loads(f.read_text(encoding="utf-8"))
                out.append({"run_id": b["run_id"], "name": b["spec"]["name"],
                            "verdict": b["verdict"]})
            except Exception:
                continue
    return out


def _recent_records(settings) -> list[dict]:
    from signalgate.eval.score import load_records
    p = settings.artifacts_dir / "agent" / "results.jsonl"
    return load_records(p) if p.exists() else []


def _invalid(request: Request, message: str, htmx: bool):
    if htmx:
        return templates.TemplateResponse(request, "_card.html",
                                          {"error": message, "spec_yaml": ""})
    return JSONResponse({"error": message}, status_code=400)


app = create_app()
