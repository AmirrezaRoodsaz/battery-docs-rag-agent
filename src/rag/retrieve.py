"""Retrieval: turn a question into the most relevant chunks.

This is the "R" in RAG. Steps:
  1. Embed the question with the SAME local model used to build the index.
  2. Ask the FAISS index for the top-k most similar chunks (cosine similarity).
  3. (Optional) apply MMR to trade a little similarity for diversity, so the k chunks
     don't all repeat the same sentence.

Returning the chunks *with their source metadata* is what makes citation possible — the
generator never sees a chunk without knowing where it came from.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from src.index.embed import embed_query
from src.index.vectorstore import DEFAULT_INDEX_DIR, SearchHit, VectorStore


@dataclass
class Retriever:
    store: VectorStore

    @classmethod
    def from_index(cls, index_dir: Path = DEFAULT_INDEX_DIR) -> Retriever:
        return cls(store=VectorStore.load(index_dir))

    def retrieve(self, query: str, k: int = 4, use_mmr: bool = False) -> list[SearchHit]:
        """Return the top-k chunks for a query, most relevant first."""
        qvec = embed_query(query, model_name=self.store.model_name)
        if not use_mmr:
            return self.store.search(qvec, k=k)
        # MMR needs a wider candidate pool to re-rank within.
        candidates = self.store.search(qvec, k=min(max(k * 4, k), len(self.store)))
        return _mmr(qvec[0], candidates, k=k)


def _mmr(
    query_vec: np.ndarray, candidates: list[SearchHit], k: int, lambda_: float = 0.5
) -> list[SearchHit]:
    """Maximal Marginal Relevance re-ranking.

    Greedily pick chunks that are similar to the query but dissimilar to chunks already
    picked, so the result set covers more of the answer instead of k near-duplicates.
    `lambda_` trades relevance (1.0) against diversity (0.0). We re-embed candidate texts
    to measure chunk-to-chunk similarity.

    Kept simple and exact; for a few candidates the cost is negligible.
    """
    if not candidates:
        return []
    from src.index.embed import embed_texts

    cand_vecs = embed_texts([h.chunk.text for h in candidates])
    query_sim = cand_vecs @ query_vec  # cosine, vectors are normalized

    selected: list[int] = []
    remaining = list(range(len(candidates)))
    while remaining and len(selected) < k:
        if not selected:
            best = int(np.argmax(query_sim[remaining]))
            selected.append(remaining.pop(best))
            continue
        best_idx, best_score = None, -np.inf
        for pos, c in enumerate(remaining):
            diversity = max(float(cand_vecs[c] @ cand_vecs[s]) for s in selected)
            score = lambda_ * float(query_sim[c]) - (1 - lambda_) * diversity
            if score > best_score:
                best_score, best_idx = score, pos
        selected.append(remaining.pop(best_idx))
    return [candidates[i] for i in selected]
