"""Citation formatting — the anti-hallucination centerpiece.

A RAG answer is only trustworthy if a reader can check it. So we:
  1. Give each retrieved chunk a small, stable label like [1], [2] before showing it to
     the LLM.
  2. Instruct the LLM to cite those labels inline next to each claim.
  3. Print a "Sources" list mapping every label back to its source file and section.

This module just builds the labelled context block and the sources list. It does no
LLM work — keeping the formatting separate makes it independently testable (see
tests/), and testable citation formatting is part of why this is trustworthy.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.index.vectorstore import SearchHit


@dataclass
class Citation:
    label: int  # the [n] shown to the model and the reader
    source: str  # file name
    locator: str  # heading path or page
    score: float  # retrieval similarity, for transparency


def build_context(hits: list[SearchHit]) -> tuple[str, list[Citation]]:
    """Return (context_block, citations).

    The context block is what the LLM sees: each chunk prefixed with its [n] label and its
    source, so the model can cite by label. The citations list is what we show the reader.
    """
    lines: list[str] = []
    citations: list[Citation] = []
    for i, hit in enumerate(hits, start=1):
        c = hit.chunk
        citations.append(Citation(label=i, source=c.source, locator=c.locator, score=hit.score))
        lines.append(f"[{i}] (source: {c.source} — {c.locator})\n{c.text}")
    return "\n\n".join(lines), citations


def format_sources(citations: list[Citation]) -> str:
    """A human-readable 'Sources' block listing each [n] -> file/section + similarity."""
    if not citations:
        return "Sources: (none retrieved)"
    rows = [
        f"  [{c.label}] {c.source} — {c.locator}  (similarity {c.score:.2f})" for c in citations
    ]
    return "Sources:\n" + "\n".join(rows)
