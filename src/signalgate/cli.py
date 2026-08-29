"""CLI (docs/02 §6 F6): pipeline-native surface over the same orchestrator."""
from __future__ import annotations

from pathlib import Path

import typer
import yaml

from signalgate import __version__

app = typer.Typer(no_args_is_help=True, add_completion=False,
                  help="SignalGate - agentic research-integrity gate.")


@app.command()
def check(spec_path: Path, out: Path = typer.Option(None, help="artifact output dir override"),
          depth: str = typer.Option("agent", help="agent | baseline")):
    """Investigate one signal-spec YAML and print the verdict card."""
    from signalgate.config import load_settings
    from signalgate.orchestrator.bundle import to_markdown
    from signalgate.orchestrator.pipeline import Orchestrator

    settings = load_settings()
    data = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    try:
        from signalgate.schemas import SignalSpec
        spec = SignalSpec.model_validate(data)
    except Exception as exc:
        typer.secho(f"SCHEMA_INVALID: {exc}", fg=typer.colors.RED)
        raise typer.Exit(2) from None
    orch = Orchestrator(settings=settings)
    result = orch.investigate(spec, depth=depth)
    typer.echo(to_markdown(result))
    typer.secho(f"\nverdict: {result.verdict.value} ({result.confidence.value})",
                fg=typer.colors.GREEN if result.verdict.value == "PROMISING"
                else (typer.colors.RED if result.verdict.value == "REJECT_SPURIOUS"
                      else typer.colors.YELLOW))
    raise typer.Exit(0 if result.verdict.value != "REJECTED_INVALID" else 2)


@app.command()
def serve(port: int = typer.Option(8000), host: str = typer.Option("127.0.0.1")):
    """Run the web gate (LOCAL_MOCK by default; LIVE with SIGNALGATE_* env)."""
    import uvicorn

    from signalgate.config import load_settings
    settings = load_settings()
    typer.echo(f"SignalGate {__version__} on http://{host}:{port} "
               f"(mode: {settings.effective_mode})")
    uvicorn.run("signalgate.api.app:app", host=host, port=port)


@app.command()
def digest(src: Path = typer.Option(Path("artifacts/agent")),
           out: Path = typer.Option(Path("reports/digest.md"))):
    """Build the quiet-pipeline digest artifact from eval results."""
    from signalgate.digest import build_digest
    from signalgate.eval.score import load_records
    records_path = src / "agent" / "results.jsonl"
    if not records_path.exists():
        records_path = src / "results.jsonl"
    build_digest(load_records(records_path), out)
    typer.echo(f"digest -> {out}")


@app.command()
def version():
    """Print version + effective mode."""
    from signalgate.config import load_settings
    s = load_settings()
    typer.echo(f"signalgate {__version__} (mode: {s.effective_mode}, seed: {s.seed})")


if __name__ == "__main__":
    app()
