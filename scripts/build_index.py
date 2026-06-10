"""Build the vector index from the corpus — the single reproducible command.

Pipeline:  load corpus -> chunk -> embed (local model) -> write FAISS index + metadata.

This is deterministic: the same corpus and the same embedding model always produce the
same index. Run it with `make index` (or `python scripts/build_index.py`).

    python scripts/build_index.py --corpus data/corpus --out data/index --chunk-tokens 500
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from src.index.embed import DEFAULT_MODEL, embed_texts
from src.index.vectorstore import VectorStore
from src.ingest.chunk import DEFAULT_CHUNK_TOKENS, DEFAULT_OVERLAP_TOKENS, chunk_corpus
from src.ingest.load import load_corpus


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the FAISS index from the corpus.")
    parser.add_argument("--corpus", type=Path, default=Path("data/corpus"))
    parser.add_argument("--out", type=Path, default=Path("data/index"))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--chunk-tokens", type=int, default=DEFAULT_CHUNK_TOKENS)
    parser.add_argument("--overlap-tokens", type=int, default=DEFAULT_OVERLAP_TOKENS)
    args = parser.parse_args()

    t0 = time.perf_counter()

    print(f"Loading corpus from {args.corpus} ...")
    docs = load_corpus(args.corpus)
    if not docs:
        raise SystemExit(f"No documents found in {args.corpus}. Add .md/.pdf files first.")
    print(f"  {len(docs)} document(s): {', '.join(d.source for d in docs)}")

    print(f"Chunking (target {args.chunk_tokens} tokens, {args.overlap_tokens} overlap) ...")
    chunks = chunk_corpus(docs, args.chunk_tokens, args.overlap_tokens)
    print(f"  {len(chunks)} chunks")

    print(f"Embedding with {args.model} (local) ...")
    vectors = embed_texts([c.text for c in chunks], model_name=args.model)
    print(f"  embedded {vectors.shape[0]} chunks -> dim {vectors.shape[1]}")

    print(f"Building FAISS index and saving to {args.out} ...")
    store = VectorStore.build(chunks, vectors, model_name=args.model)
    store.save(args.out)

    dt = time.perf_counter() - t0
    print(f'Done in {dt:.1f}s. Index has {len(store)} chunks. Query it with `make ask Q="..."`.')


if __name__ == "__main__":
    main()
