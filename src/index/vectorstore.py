"""Persist and query the vector index.

This is the storage layer: take the chunk vectors and save them in a FAISS index, save the
chunk text + metadata alongside, and load both back for querying. Keeping the index and its
metadata together (and versioned by the embedding model name) means a query is always
matched against vectors produced by the same model.

We use `IndexFlatIP` — a brute-force inner-product index. For a corpus this size (a few
hundred chunks) brute force is instant and *exact*: no approximate-nearest-neighbour error
to reason about. If the corpus grew to millions of chunks we'd switch to an IVF/HNSW index
and trade a little recall for speed, but for a transparent portfolio repo, exact-and-simple
wins. Because our vectors are L2-normalized (see embed.py), inner product == cosine.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from src.ingest.chunk import Chunk

DEFAULT_INDEX_DIR = Path("data/index")
_INDEX_FILE = "corpus.faiss"
_META_FILE = "corpus_meta.json"


@dataclass
class SearchHit:
    chunk: Chunk
    score: float  # cosine similarity in [-1, 1]; higher is more similar


class VectorStore:
    """A FAISS index plus the chunk metadata needed to return and cite results."""

    def __init__(self, index, chunks: list[Chunk], model_name: str):
        self._index = index
        self._chunks = chunks
        self.model_name = model_name

    # --- build / persist ---------------------------------------------------------------

    @classmethod
    def build(cls, chunks: list[Chunk], vectors: np.ndarray, model_name: str) -> VectorStore:
        """Build an index from chunks and their (n, d) normalized vectors."""
        import faiss

        if len(chunks) != vectors.shape[0]:
            raise ValueError("chunk count and vector count differ")
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        return cls(index, list(chunks), model_name)

    def save(self, index_dir: Path = DEFAULT_INDEX_DIR) -> None:
        import faiss

        index_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(index_dir / _INDEX_FILE))
        meta = {
            "model_name": self.model_name,
            "count": len(self._chunks),
            "chunks": [c.as_dict() for c in self._chunks],
        }
        (index_dir / _META_FILE).write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # --- load / query ------------------------------------------------------------------

    @classmethod
    def load(cls, index_dir: Path = DEFAULT_INDEX_DIR) -> VectorStore:
        import faiss

        index_path = index_dir / _INDEX_FILE
        meta_path = index_dir / _META_FILE
        if not index_path.exists() or not meta_path.exists():
            raise FileNotFoundError(
                f"No index found in {index_dir}. Build it first with `make index`."
            )
        index = faiss.read_index(str(index_path))
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        chunks = [Chunk(**c) for c in meta["chunks"]]
        return cls(index, chunks, meta["model_name"])

    def search(self, query_vector: np.ndarray, k: int = 4) -> list[SearchHit]:
        """Return the top-k chunks for a (1, d) query vector, most similar first."""
        k = min(k, len(self._chunks))
        scores, ids = self._index.search(query_vector, k)
        hits: list[SearchHit] = []
        for score, idx in zip(scores[0], ids[0], strict=False):
            if idx < 0:  # FAISS pads with -1 when fewer than k results exist
                continue
            hits.append(SearchHit(chunk=self._chunks[idx], score=float(score)))
        return hits

    def __len__(self) -> int:
        return len(self._chunks)
