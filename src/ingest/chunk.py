"""Split documents into retrieval-sized chunks.

Why chunk at all? Embedding a whole document into one vector blurs every topic together,
so retrieval can't tell which part answers a question. Embedding individual sentences
loses the surrounding context. Chunking is the compromise: pieces big enough to be
self-contained, small enough to be specific.

The size/overlap trade-off (say this in an interview):
  - Too SMALL -> context is lost; an answer that spans two chunks gets split and neither
    chunk alone retrieves well.
  - Too BIG  -> retrieval is diluted; one chunk covers several topics, so its vector is an
    average and matches questions only fuzzily.
We target ~500-token chunks with ~60 tokens of overlap. Overlap means a fact sitting on a
chunk boundary still appears whole in at least one chunk.

Strategy: structure-aware. We start from the heading-delimited blocks produced by
`load.py` (so we never merge unrelated sections), then pack each block into chunks on
paragraph boundaries, and only fall back to sentence boundaries if a single paragraph is
itself larger than the budget. This keeps chunks aligned with the document's own
structure, which both improves retrieval and makes citations land on a meaningful unit.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from src.ingest.load import Block, Document

# We estimate tokens without a tokenizer dependency. For English prose, tokens are roughly
# words / 0.75 (i.e. ~1.3 tokens per word). This approximation is good enough to *budget*
# chunk sizes; exact token counts don't change retrieval behaviour materially.
TOKENS_PER_WORD = 1.3

DEFAULT_CHUNK_TOKENS = 500
DEFAULT_OVERLAP_TOKENS = 60


@dataclass
class Chunk:
    """A retrieval unit: text plus enough metadata to embed it and to cite it."""

    id: int  # assigned at index build time; the row position in the FAISS index
    text: str
    source: str
    locator: str

    def as_dict(self) -> dict:
        return asdict(self)


def estimate_tokens(text: str) -> int:
    """Cheap, dependency-free token estimate (~1.3 tokens per whitespace word)."""
    words = len(text.split())
    return int(round(words * TOKENS_PER_WORD))


_SENTENCE = re.compile(r"(?<=[.!?])\s+")


def _split_sentences(text: str) -> list[str]:
    return [s for s in _SENTENCE.split(text.strip()) if s]


def _split_paragraphs(text: str) -> list[str]:
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def _overlap_tail(text: str, overlap_tokens: int) -> str:
    """Return the last ~overlap_tokens worth of words from text, for chunk overlap."""
    if overlap_tokens <= 0:
        return ""
    words = text.split()
    keep = max(1, int(round(overlap_tokens / TOKENS_PER_WORD)))
    return " ".join(words[-keep:])


def _pack_units(units: list[str], chunk_tokens: int, overlap_tokens: int) -> list[str]:
    """Greedily pack text units (paragraphs or sentences) into chunks of <= chunk_tokens,
    carrying an overlap tail from the end of each chunk into the start of the next."""
    chunks: list[str] = []
    current = ""

    for unit in units:
        candidate = f"{current}\n\n{unit}".strip() if current else unit
        if current and estimate_tokens(candidate) > chunk_tokens:
            chunks.append(current)
            tail = _overlap_tail(current, overlap_tokens)
            current = f"{tail}\n\n{unit}".strip() if tail else unit
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


def chunk_block(
    block: Block,
    chunk_tokens: int = DEFAULT_CHUNK_TOKENS,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
) -> list[str]:
    """Chunk a single block. Small blocks pass through whole."""
    if estimate_tokens(block.text) <= chunk_tokens:
        return [block.text]

    paragraphs = _split_paragraphs(block.text)
    # If any single paragraph still busts the budget, split that paragraph into sentences.
    units: list[str] = []
    for para in paragraphs:
        if estimate_tokens(para) > chunk_tokens:
            units.extend(_split_sentences(para))
        else:
            units.append(para)
    return _pack_units(units, chunk_tokens, overlap_tokens)


def chunk_document(
    doc: Document,
    chunk_tokens: int = DEFAULT_CHUNK_TOKENS,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
) -> list[Chunk]:
    """Chunk every block of a document. Chunk ids are assigned later, globally."""
    chunks: list[Chunk] = []
    for block in doc.blocks:
        for text in chunk_block(block, chunk_tokens, overlap_tokens):
            chunks.append(Chunk(id=-1, text=text, source=block.source, locator=block.locator))
    return chunks


def chunk_corpus(
    docs: list[Document],
    chunk_tokens: int = DEFAULT_CHUNK_TOKENS,
    overlap_tokens: int = DEFAULT_OVERLAP_TOKENS,
) -> list[Chunk]:
    """Chunk a whole corpus and assign stable, global ids (the FAISS row positions)."""
    chunks: list[Chunk] = []
    for doc in docs:
        chunks.extend(chunk_document(doc, chunk_tokens, overlap_tokens))
    for i, chunk in enumerate(chunks):
        chunk.id = i
    return chunks
