"""Tests for chunking — the size/overlap behaviour that retrieval quality depends on."""

from src.ingest.chunk import (
    DEFAULT_CHUNK_TOKENS,
    Chunk,
    chunk_block,
    chunk_corpus,
    estimate_tokens,
)
from src.ingest.load import Block, Document


def test_small_block_passes_through_whole():
    block = Block(text="A short sentence about a battery cell.", source="x.md", locator="A")
    chunks = chunk_block(block)
    assert chunks == [block.text]


def test_large_block_is_split_under_budget():
    # Build a block well over the token budget from many distinct paragraphs.
    paras = [
        f"Paragraph number {i} about lithium-ion degradation mechanisms." * 5 for i in range(60)
    ]
    block = Block(text="\n\n".join(paras), source="x.md", locator="A")
    chunks = chunk_block(block, chunk_tokens=200, overlap_tokens=20)
    assert len(chunks) > 1
    # Every chunk should respect the budget (with a small tolerance for the overlap tail).
    for c in chunks:
        assert estimate_tokens(c) <= 200 + 40


def test_overlap_carries_context_between_chunks():
    paras = [f"Sentence {i} word word word word word word word word." for i in range(40)]
    block = Block(text="\n\n".join(paras), source="x.md", locator="A")
    chunks = chunk_block(block, chunk_tokens=80, overlap_tokens=20)
    assert len(chunks) >= 2
    # The tail of chunk[0] should reappear at the head of chunk[1] (that's what overlap means).
    tail_words = set(chunks[0].split()[-3:])
    head_words = set(chunks[1].split()[:15])
    assert tail_words & head_words


def test_chunk_corpus_assigns_unique_sequential_ids():
    doc = Document(
        source="d.md",
        blocks=[
            Block(text="First section text.", source="d.md", locator="One"),
            Block(text="Second section text.", source="d.md", locator="Two"),
        ],
    )
    chunks = chunk_corpus([doc])
    ids = [c.id for c in chunks]
    assert ids == list(range(len(chunks)))  # 0..n-1, unique and sequential


def test_chunk_keeps_source_and_locator():
    block = Block(text="x" * 10, source="soh.md", locator="State of Health")
    doc = Document(source="soh.md", blocks=[block])
    chunks = chunk_corpus([doc])
    assert all(isinstance(c, Chunk) for c in chunks)
    assert chunks[0].source == "soh.md"
    assert chunks[0].locator == "State of Health"


def test_default_budget_is_sane():
    assert 200 <= DEFAULT_CHUNK_TOKENS <= 1200
