"""CLI for the agentic test-report mode.

    python -m src.agent.cli data/test_reports/report_02_degraded.md
    python -m src.agent.cli data/test_reports/report_01_healthy.md --show-steps

Runs the bounded, observable agent loop on a battery test report and prints the structured
diagnostic summary (Markdown) plus the machine-readable JSON. Needs an LLM key (.env).
"""

from __future__ import annotations

from pathlib import Path

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from src.agent.agent_loop import diagnose_report

load_dotenv()
app = typer.Typer(add_completion=False, help="Agentic battery test-report diagnostics.")
console = Console()


@app.command()
def main(
    report: Path = typer.Argument(..., help="Path to a test-report .md/.pdf file."),
    show_steps: bool = typer.Option(False, help="Print the agent's tool-call trace."),
) -> None:
    if not report.exists():
        console.print(f"[red]File not found: {report}[/red]")
        raise typer.Exit(code=1)

    result = diagnose_report(report)

    if show_steps:
        for s in result.steps:
            line = f"[{s.n}] {s.action}"
            if s.tool:
                line += f" → {s.tool}({s.args})"
            console.print(f"[dim]{line}[/dim]")
            if s.observation:
                console.print(f"[dim]    obs: {s.observation}[/dim]")

    color = (
        "red"
        if "END-OF-LIFE" in result.verdict
        else ("yellow" if "DEGRADED" in result.verdict else "green")
    )
    console.print(
        Panel(
            result.summary_markdown, title=f"Diagnostic — {result.report_name}", border_style=color
        )
    )
    console.print(Panel(result.to_json(), title="Structured JSON", border_style="cyan"))


if __name__ == "__main__":
    app()
