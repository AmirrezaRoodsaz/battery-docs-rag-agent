"""Tests for citation formatting — the part that makes answers verifiable.

These are pure formatting tests (no model needed), which is exactly why citation logic
lives in its own module: trustworthy citations should be deterministically testable.
"""

from src.index.vectorstore import SearchHit
from src.ingest.chunk import Chunk
from src.rag.cite import build_context, format_sources


def _hit(i: int, source: str, locator: str, text: str, score: float) -> SearchHit:
    return SearchHit(chunk=Chunk(id=i, text=text, source=source, locator=locator), score=score)


def test_build_context_labels_chunks_from_one():
    hits = [
        _hit(0, "soh.md", "Capacity-based SOH", "SOH = Q_now / Q_rated.", 0.81),
        _hit(1, "datasheet.md", "Cycle life", "1000 cycles to 80% SOH.", 0.74),
    ]
    context, citations = build_context(hits)
    assert "[1]" in context and "[2]" in context
    assert "soh.md" in context and "datasheet.md" in context
    assert [c.label for c in citations] == [1, 2]


def test_citation_carries_source_locator_and_score():
    hits = [_hit(0, "soh.md", "Resistance-based SOH", "DCIR doubles at EOL.", 0.66)]
    _, citations = build_context(hits)
    c = citations[0]
    assert c.source == "soh.md"
    assert c.locator == "Resistance-based SOH"
    assert abs(c.score - 0.66) < 1e-9


def test_format_sources_lists_every_label():
    hits = [
        _hit(0, "a.md", "S1", "t1", 0.9),
        _hit(1, "b.md", "S2", "t2", 0.5),
    ]
    _, citations = build_context(hits)
    rendered = format_sources(citations)
    assert "[1] a.md — S1" in rendered
    assert "[2] b.md — S2" in rendered
    assert "0.90" in rendered  # similarity is shown for transparency


def test_format_sources_handles_empty():
    assert "none" in format_sources([]).lower()
