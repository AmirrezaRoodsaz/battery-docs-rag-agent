"""Command-line interface for the RAG system.

    python -m src.rag.cli ask "What is the rated capacity of the AR-2100?"
    python -m src.rag.cli ask "What is SOH?" --k 5 --mmr --show-chunks
    python -m src.rag.cli retrieve "lithium plating"   # retrieval only, no LLM call

`ask` runs the full retrieve -> generate -> cite pipeline. `retrieve` shows just what the
retriever returns, which is handy for debugging grounding without spending an LLM call.
The .env file is loaded automatically so your provider key is picked up.
"""

from __future__ import annotations

import typer
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from src.rag.cite import format_sources
from src.rag.generate import answer_question
from src.rag.retrieve import Retriever

load_dotenv()  # read .env so GOOGLE_API_KEY / LLM_PROVIDER are available
app = typer.Typer(add_completion=False, help="Grounded, cited RAG over battery documents.")
console = Console()


@app.command()
def ask(
    question: str = typer.Argument(..., help="The question to answer."),
    k: int = typer.Option(4, help="Number of chunks to retrieve."),
    mmr: bool = typer.Option(False, help="Use MMR re-ranking for more diverse chunks."),
    show_chunks: bool = typer.Option(False, help="Also print the retrieved chunk text."),
) -> None:
    """Answer a question with inline citations (or 'not found')."""
    retriever = Retriever.from_index()
    result = answer_question(question, retriever, k=k, use_mmr=mmr)

    color = "green" if result.is_grounded else "yellow"
    console.print(Panel(result.answer, title="Answer", border_style=color))
    console.print(format_sources(result.citations))
    console.print(f"[dim]provider: {result.provider} · model: {result.model}[/dim]")

    if show_chunks:
        for c, hit in zip(result.citations, result.hits, strict=False):
            console.print(
                Panel(
                    hit.chunk.text,
                    title=f"[{c.label}] {c.source} — {c.locator} (sim {c.score:.2f})",
                    border_style="dim",
                )
            )


@app.command()
def retrieve(
    query: str = typer.Argument(..., help="The query to retrieve chunks for."),
    k: int = typer.Option(4, help="Number of chunks to retrieve."),
    mmr: bool = typer.Option(False, help="Use MMR re-ranking."),
) -> None:
    """Show retrieved chunks only — no LLM call (useful for debugging grounding)."""
    retriever = Retriever.from_index()
    hits = retriever.retrieve(query, k=k, use_mmr=mmr)
    if not hits:
        console.print("[yellow]No chunks retrieved.[/yellow]")
        raise typer.Exit()
    for i, hit in enumerate(hits, start=1):
        console.print(
            Panel(
                hit.chunk.text,
                title=f"[{i}] {hit.chunk.source} — {hit.chunk.locator} (sim {hit.score:.2f})",
                border_style="cyan",
            )
        )


if __name__ == "__main__":
    app()
