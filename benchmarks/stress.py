"""A production-style stress benchmark for the retrieval service.

Unlike ``benchmark.py`` (which times the core primitives), this driver exercises
the full service handler under sustained, concurrent load and reports the
latency distribution operators actually care about: throughput and the p50, p95,
and p99 tail. Deterministic and offline; run with:

    uv run python benchmarks/stress.py
"""

from __future__ import annotations

import random
import statistics
import time
from concurrent.futures import ThreadPoolExecutor

from agentic_rag.core.retrieval import Document
from agentic_rag.service import RetrievalService, handle

_WORDS = [
    "neural",
    "network",
    "gravity",
    "retrieval",
    "fusion",
    "ranking",
    "vector",
    "quantum",
    "evolution",
    "energy",
    "ocean",
    "capital",
    "river",
    "border",
]


def _synthetic_corpus(num_documents: int, *, seed: int = 0) -> list[Document]:
    rng = random.Random(seed)
    return [
        Document(id=f"d{index}", text=" ".join(rng.choice(_WORDS) for _ in range(40)))
        for index in range(num_documents)
    ]


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(fraction * len(ordered)))
    return ordered[index]


def main() -> None:
    service = RetrievalService.from_documents(_synthetic_corpus(1000))
    rng = random.Random(0)
    requests = [{"question": " ".join(rng.choice(_WORDS) for _ in range(4))} for _ in range(2000)]

    def one(body: dict[str, str]) -> float:
        start = time.perf_counter()
        handle("POST", "/retrieve", body, service)
        return (time.perf_counter() - start) * 1000

    for workers in (1, 4, 8):
        start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=workers) as pool:
            latencies = list(pool.map(one, requests))
        wall = time.perf_counter() - start
        throughput = len(requests) / wall
        print(
            f"workers={workers:<2}  "
            f"throughput={throughput:>7.0f} req/s  "
            f"p50={statistics.median(latencies):>6.2f} ms  "
            f"p95={_percentile(latencies, 0.95):>6.2f} ms  "
            f"p99={_percentile(latencies, 0.99):>6.2f} ms"
        )


if __name__ == "__main__":
    main()
