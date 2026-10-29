# Operations Guide - Agentic RAG

This document states the operational contract of the retrieval service: how to run
it, what it promises, and where it breaks.

## Running the service

```bash
uv run python -m agentic_rag serve --host 0.0.0.0 --port 8000
```

The service is a standard-library HTTP server with **zero runtime dependencies**. It
builds the index once at startup and then serves stateless requests.

## Endpoints

| Method | Path | Body | Success |
|---|---|---|---|
| GET | `/health` | none | `{"status": "ok", "index_size": N}` (liveness) |
| GET | `/ready` | none | readiness, once the index is loaded |
| GET | `/metrics` | none | per-route request, error, and latency metrics (Prometheus text) |
| POST | `/retrieve` | `{"question", "max_hops"?, "k"?}` | answer, citations, confidence, hop trace |

Every error path returns a JSON `{"error": ...}` with a 4xx status; malformed JSON
yields `400`, unknown routes `404`.

## Service level objectives

Measured by `benchmarks/stress.py` on a developer laptop over a 1000 document index:

| Objective | Target | Observed (single worker) |
|---|---|---|
| Availability | best effort, single process | n/a |
| Read latency p50 | < 5 ms | about 1.8 ms |
| Read latency p99 | < 10 ms at concurrency 1 | about 3.4 ms |
| Throughput | > 400 requests/second/core | about 520 requests/second |

These are illustrative targets for the reference implementation, not a production
guarantee.

## Operational constraints

- **The handler is CPU bound and holds the global interpreter lock.** Throughput does
  not scale with threads in one process; the p99 tail grows with concurrency (see
  `benchmarks/stress.py`: p99 rises from about 3 ms at one worker to over 100 ms at
  eight). Scale with **processes behind a load balancer**, not threads.
- **The index is in memory and immutable after startup.** Memory grows linearly with
  corpus size; updates require a restart or a blue/green swap.
- **Requests are bounded**: questions are capped at 2000 characters, `max_hops` at 8,
  and `k` at 20, so a single request cannot exhaust CPU or memory.
- **No persistence, no authentication.** Put the service behind a gateway that adds
  transport security, authentication, and rate limiting.

## Failure modes and responses

| Symptom | Likely cause | Response |
|---|---|---|
| Rising p99 under load | Concurrency above one worker per core | Add processes/replicas; cap per-replica concurrency |
| `400` on valid-looking input | Request exceeds a documented bound | Inspect the `error` field; split the request |
| Memory growth at startup | Large corpus | Shard the corpus across replicas |

## Capacity planning

Throughput is roughly linear in replicas (shared-nothing). For a target of `R`
requests per second, provision about `ceil(R / 500)` single-core replicas plus
headroom for the tail.
