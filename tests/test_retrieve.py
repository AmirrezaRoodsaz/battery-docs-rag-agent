"""Tests for retrieval and grounding.

The retrieval test builds a tiny real index from a few known chunks and asserts that a
known query returns the expected chunk first — the canonical "known query -> expected
chunk" RAG test. It uses the local embedding model (no API key, no network after the model
is cached), so it exercises the real vector path, not a mock.

The grounding test checks the "not found" short-circuit, which must work with NO LLM call.
"""

import numpy as np
import pytest

from src.index.embed import embed_texts
from src.index.vectorstore import VectorStore
from src.ingest.chunk import Chunk
from src.rag.generate import NOT_FOUND, answer_question
from src.rag.retrieve import Retriever

# A tiny corpus with clearly distinct topics so retrieval is unambiguous.
_CHUNKS = [
    "State of Health (SOH) compares present capacity to rated capacity, in percent.",
    "The end-of-life threshold for automotive traction batteries is 80 percent SOH.",
    "Lithium plating happens when charging at low temperature and is a safety hazard.",
    "UN 38.3 defines the transport safety tests a lithium battery must pass to be shipped.",
]


@pytest.fixture(scope="module")
def store() -> VectorStore:
    chunks = [Chunk(id=i, text=t, source="mini.md", locator=f"c{i}") for i, t in enumerate(_CHUNKS)]
    vectors = embed_texts([c.text for c in chunks])
    return VectorStore.build(chunks, vectors, model_name="sentence-transformers/all-MiniLM-L6-v2")


def test_known_query_returns_expected_chunk_first(store):
    retriever = Retriever(store=store)
    hits = retriever.retrieve("What temperature problem causes lithium plating?", k=2)
    assert "plating" in hits[0].chunk.text.lower()


def test_eol_threshold_query_retrieves_the_80_percent_chunk(store):
    retriever = Retriever(store=store)
    hits = retriever.retrieve("What is the end of life SOH threshold?", k=1)
    assert "80" in hits[0].chunk.text


def test_scores_are_cosine_in_range(store):
    retriever = Retriever(store=store)
    hits = retriever.retrieve("battery state of health", k=4)
    assert all(-1.0001 <= h.score <= 1.0001 for h in hits)
    # results come back sorted, most similar first
    scores = [h.score for h in hits]
    assert scores == sorted(scores, reverse=True)


def test_mmr_returns_k_distinct_chunks(store):
    retriever = Retriever(store=store)
    hits = retriever.retrieve("battery safety and health", k=3, use_mmr=True)
    ids = [h.chunk.id for h in hits]
    assert len(ids) == len(set(ids)) == 3


def test_not_found_short_circuits_without_llm(store):
    """An utterly unrelated query must refuse via the retrieval backstop, calling no LLM.

    We pass no provider; if the code tried to call one it would raise (no key configured),
    so reaching the NOT_FOUND answer proves the short-circuit fired."""
    retriever = Retriever(store=store)
    result = answer_question("Who won the 2010 FIFA World Cup?", retriever, k=1)
    assert result.answer == NOT_FOUND
    assert not result.is_grounded
    assert "no LLM call" in result.model


def test_embed_query_matches_index_dim(store):
    from src.index.embed import embed_query

    q = embed_query("anything")
    assert q.shape[1] == np.array(embed_texts(["anything"])).shape[1]
