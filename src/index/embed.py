"""Turn text into vectors with a LOCAL embedding model.

An *embedding* is a fixed-length list of numbers that represents a piece of text's
meaning. The model is trained so that texts with similar meaning get vectors that point in
similar directions. That is the whole trick behind retrieval: embed the question, embed
every chunk, and the chunks whose vectors are most aligned with the question's vector are
the ones most likely to answer it.

We use `sentence-transformers/all-MiniLM-L6-v2` by default: small (~80 MB), fast on CPU,
free, and offline after the first download. No API key, which keeps the project
reproducible and cheap — a deliberate choice over a hosted embedding API.

We L2-normalize every vector. With unit vectors, the dot product equals the cosine
similarity, so a FAISS inner-product index gives us cosine ranking for free. Cosine
(angle) is the right metric here because we care about *direction* (meaning), not
magnitude (which for embeddings mostly reflects text length).
"""

from __future__ import annotations

import os
from functools import lru_cache

import numpy as np

DEFAULT_MODEL = os.environ.get("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")


@lru_cache(maxsize=2)
def _load_model(model_name: str):
    """Load (and cache) the sentence-transformer. Imported lazily so importing this module
    is cheap and test collection doesn't pay the model-load cost unless embedding runs."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(model_name)


def embed_texts(
    texts: list[str], model_name: str = DEFAULT_MODEL, batch_size: int = 32
) -> np.ndarray:
    """Embed a list of texts into an (n, d) float32 array of L2-normalized vectors."""
    model = _load_model(model_name)
    vectors = model.encode(
        texts,
        batch_size=batch_size,
        convert_to_numpy=True,
        normalize_embeddings=True,  # unit vectors -> dot product == cosine similarity
        show_progress_bar=False,
    )
    return vectors.astype(np.float32)


def embed_query(query: str, model_name: str = DEFAULT_MODEL) -> np.ndarray:
    """Embed a single query into a (1, d) array. Must use the SAME model as the index —
    a query embedded by a different model lives in a different space and won't match."""
    return embed_texts([query], model_name=model_name)


def embedding_dim(model_name: str = DEFAULT_MODEL) -> int:
    return int(_load_model(model_name).get_sentence_embedding_dimension())
