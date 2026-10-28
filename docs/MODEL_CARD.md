# System Card - Agentic RAG

## Overview

- **What it is:** an agentic retrieval system - query decomposition, a self-querying
  retriever-agent, and iterative multi-hop retrieval with cited answer synthesis.
- **What it is not:** a generator. It retrieves and extracts; it does not call a language
  model to write free-form answers.
- **Version:** 0.1.0.

## Intended use

- **Primary use cases:** learning and demonstrating agentic, multi-hop retrieval; a
  from-scratch reference for decomposition, self-querying, and the retrieve-reason-retrieve
  loop.
- **Primary users:** engineers and researchers building retrieval systems.

## Out-of-scope / prohibited use

- Not tuned for production-scale corpora; the index is in-memory.
- The bundled corpus is a demonstration, not a benchmark.

## Performance

See the README results. Agentic retrieval reaches multi-hop answer passages (0.67) that the
single-hop baseline never finds (0.00), with no single-hop regression.

## Risks and limitations

- Lexical retrieval cannot bridge paraphrase gaps between hops.
- Rule-based decomposition handles conjunctions and comparisons, not arbitrary reasoning.

## Safety mitigations

- Deterministic, offline, reproducible; bounded hops guarantee termination.

## Environmental / cost footprint

Negligible; all in-memory with no model calls.
