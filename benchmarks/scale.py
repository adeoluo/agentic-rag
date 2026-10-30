"""A large-workload scale benchmark for the BM25 retrieval primitive.

Where ``benchmark.py`` times the primitives on one corpus and ``stress.py`` drives
the service under concurrency, this script answers a different question: how does
the core retrieval operation behave as the corpus grows? It indexes progressively
larger synthetic corpora, then runs a fixed query set against each, reporting
wall-clock time, query throughput, peak memory (via the stdlib ``tracemalloc``),
and planted-needle recall@k so the quality signal is visible alongside the cost.

The data is synthetic and the retriever is a from-scratch, pure-Python Okapi BM25:
it is not meant to be competitive on wall-clock with compiled inverted indexes or
vector databases. The point is to show how this implementation scales, honestly.

Run with:

    uv run python benchmarks/scale.py
"""

from __future__ import annotations

import random
import time
import tracemalloc
from dataclasses import dataclass

from agentic_rag import BM25Index, Document

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

_CORPUS_SIZES: tuple[int, ...] = (500, 1000, 2000, 4000)
_NUM_QUERIES = 100
_K = 5


@dataclass(frozen=True, slots=True)
class Workload:
    """A synthetic corpus plus the labeled queries that probe it."""

    corpus: list[Document]
    queries: list[str]
    relevant_ids: list[str]


def build_workload(num_documents: int, num_queries: int, *, seed: int = 0) -> Workload:
    """Build a corpus with ``num_queries`` planted relevant documents.

    Each query is a bag of common words; its one relevant document repeats those
    words twice so BM25 can find it among the random distractors. The remaining
    documents are pure noise drawn from the same vocabulary, so the true positive
    has to be distinguished by term frequency rather than by a unique token, and
    recall falls as the corpus (and thus the field of distractors) grows.
    """
    rng = random.Random(seed)
    queries: list[str] = []
    relevant_ids: list[str] = []
    corpus: list[Document] = []

    for query_index in range(num_queries):
        terms = rng.sample(_WORDS, k=3)
        queries.append(" ".join(terms))
        relevant_id = f"rel{query_index}"
        relevant_ids.append(relevant_id)
        filler = [rng.choice(_WORDS) for _ in range(34)]
        words = terms * 2 + filler
        rng.shuffle(words)
        corpus.append(Document(id=relevant_id, text=" ".join(words)))

    for distractor_index in range(num_documents - num_queries):
        words = [rng.choice(_WORDS) for _ in range(40)]
        corpus.append(Document(id=f"noise{distractor_index}", text=" ".join(words)))

    rng.shuffle(corpus)
    return Workload(corpus=corpus, queries=queries, relevant_ids=relevant_ids)


def _recall_at_k(index: BM25Index, workload: Workload, k: int) -> float:
    hits = 0
    for query, relevant_id in zip(workload.queries, workload.relevant_ids, strict=True):
        retrieved = {scored.id for scored in index.search(query, k=k)}
        hits += relevant_id in retrieved
    return hits / len(workload.queries) if workload.queries else 0.0


def measure(num_documents: int, *, k: int = _K) -> tuple[float, float, float, float]:
    """Return ``(seconds, queries_per_sec, peak_mib, recall_at_k)`` for one size."""
    workload = build_workload(num_documents, _NUM_QUERIES)

    tracemalloc.start()
    index = BM25Index()
    index.add(workload.corpus)

    start = time.perf_counter()
    for query in workload.queries:
        index.search(query, k=k)
    elapsed = time.perf_counter() - start

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    recall = _recall_at_k(index, workload, k)
    throughput = len(workload.queries) / elapsed if elapsed else 0.0
    return elapsed, throughput, peak / (1024 * 1024), recall


def main() -> None:
    print("Synthetic corpus; from-scratch pure-Python BM25 (not a compiled index or vector DB).")
    print(
        f"Fixed query set: {_NUM_QUERIES} queries, recall@{_K} against one planted relevant doc.\n"
    )
    print(f"{'documents':>10}{'seconds':>10}{'queries/sec':>14}{'peak MiB':>11}{'recall@5':>11}")
    print("-" * 56)
    for num_documents in _CORPUS_SIZES:
        elapsed, throughput, peak_mib, recall = measure(num_documents)
        print(
            f"{num_documents:>10}{elapsed:>10.3f}{throughput:>14.0f}{peak_mib:>11.1f}{recall:>11.2f}"
        )


if __name__ == "__main__":
    main()
