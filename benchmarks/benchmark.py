"""A micro-benchmark for the agentic retrieval loop.

Measures index-build time, single-hop query throughput, and the agentic loop's
throughput and average hop count over a synthetic corpus, so the README can
quote concrete numbers. Deterministic and offline; run with:

    uv run python benchmarks/benchmark.py
"""

from __future__ import annotations

import random
import time

from agentic_rag import AgenticRetriever, BM25Index, Document

_WORDS = [
    "neural",
    "network",
    "photosynthesis",
    "gravity",
    "retrieval",
    "fusion",
    "ranking",
    "embedding",
    "vector",
    "quantum",
    "revolution",
    "mitochondria",
    "evolution",
    "cell",
    "energy",
    "sunlight",
    "ocean",
    "mountain",
    "pigment",
    "spacetime",
    "glucose",
    "oxygen",
    "capital",
    "river",
    "border",
    "author",
]


def _synthetic_corpus(num_documents: int, *, seed: int = 0) -> list[Document]:
    rng = random.Random(seed)
    documents: list[Document] = []
    for index in range(num_documents):
        words = [rng.choice(_WORDS) for _ in range(40)]
        documents.append(Document(id=f"d{index}", text=" ".join(words)))
    return documents


def main() -> None:
    corpus = _synthetic_corpus(500)
    queries = [" ".join(random.Random(seed).choices(_WORDS, k=4)) for seed in range(200)]

    start = time.perf_counter()
    index = BM25Index()
    index.add(corpus)
    build_ms = (time.perf_counter() - start) * 1000

    print(f"Corpus: {len(corpus)} documents | Queries: {len(queries)}")
    print(f"Index build: {build_ms:.1f} ms\n")
    print(f"{'method':<16}{'queries/sec':>14}{'avg hops':>12}")
    print("-" * 42)

    start = time.perf_counter()
    for query in queries:
        index.search(query, k=3)
    elapsed = time.perf_counter() - start
    print(f"{'single-hop':<16}{len(queries) / elapsed:>14.0f}{1.0:>12.2f}")

    retriever = AgenticRetriever(index, max_hops=2, k=3)
    start = time.perf_counter()
    total_hops = 0
    for query in queries:
        result = retriever.run(query)
        total_hops += result.num_hops
    elapsed = time.perf_counter() - start
    average_hops = total_hops / len(queries)
    print(f"{'agentic':<16}{len(queries) / elapsed:>14.0f}{average_hops:>12.2f}")


if __name__ == "__main__":
    main()
