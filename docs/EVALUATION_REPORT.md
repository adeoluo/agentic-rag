# Evaluation Report - Agentic RAG

> Reproduce with `python -m agentic_rag evaluate`. Deterministic and offline.

## Setup

- **Corpus:** 11 short passages linked by shared entities (landmark, city, country).
- **Questions:** 7 labeled questions, 3 of them genuinely multi-hop (the answer passage
  shares no words with the question and is reachable only through an intermediate entity).
- **Metric:** retrieval success - whether the labeled answer passage was retrieved - split
  by single- vs multi-hop.
- **Methods:** agentic multi-hop retrieval vs a single-hop BM25 baseline.

## Results

| Method | overall | multi-hop | single-hop |
|---|---:|---:|---:|
| single-hop baseline | 0.43 | 0.00 | 0.75 |
| agentic | 0.71 | 0.67 | 0.75 |

## Interpretation

Single-hop retrieval cannot answer the multi-hop questions at all (0.00): the answer passage
has no lexical overlap with the question. Agentic retrieval follows the intermediate entity
and reaches the answer passage on two of three (0.67), a +0.67 gain, without regressing on
single-hop questions. This is the central claim of agentic RAG, measured directly.

## Reproducibility

Everything is offline and deterministic; the numbers regenerate exactly.
