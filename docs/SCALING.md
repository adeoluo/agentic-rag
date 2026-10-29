# Scaling and Design Tradeoffs - Agentic RAG

How the reference design grows from a laptop to a fleet, and the tradeoffs taken along
the way.

## Reference architecture (today)

A single process: an in-memory Okapi BM25 index, the agentic control loop, and a
standard-library HTTP service. Shared-nothing and stateless per request.

## Scaling path

| Stage | Bottleneck | Change |
|---|---|---|
| One process | CPU, global interpreter lock | Run one replica per core |
| One host | Host CPU and memory | Horizontal replicas behind a load balancer |
| Large corpus | Index memory per replica | Shard the corpus; scatter/gather across shards |
| Hot queries | Repeated identical work | Add a read-through cache keyed by (question, max_hops, k) |
| Model-backed stages | Decomposition/synthesis latency | Batch and cache model calls; keep the loop bounded |

Because replicas share nothing, throughput is approximately linear in replica count;
the design target is a flat per-request cost and a shardable index.

## Substantial tradeoffs

- **In-memory index vs external store.** In memory gives millisecond retrieval and zero
  dependencies, at the cost of corpus size per replica and restart-to-update. An
  external vector or inverted-index store would lift the size ceiling but add a network
  hop, a dependency, and an operational surface. The reference chooses simplicity and
  latency; the index is behind an interface so the store can be swapped.
- **Rule-based decomposition vs a model.** Rules are deterministic, free, and auditable
  but brittle on unusual phrasing. A model generalizes but adds latency, cost, and
  nondeterminism. The loop is written so a model drops in behind the same interface.
- **Threads vs processes.** The handler is pure Python and GIL-bound, so threads do not
  add throughput and inflate the tail (measured). Processes are the unit of scaling;
  the service is deliberately stateless to make that trivial.
- **Bounded hops vs exhaustive search.** A hop budget guarantees termination and a
  predictable cost envelope, at the risk of missing an answer that needs more hops. The
  budget is configurable per request so callers trade recall for latency explicitly.

## What would change under real load

Add a cache, shard the index, run process-per-core replicas, and move decomposition and
synthesis behind a batched model service. None of these change the control loop; they
change what sits behind its interfaces, which is the point of the design.
