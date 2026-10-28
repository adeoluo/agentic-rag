# Data Card - Agentic RAG

The project bundles one small, synthetic corpus and a labeled question set for the
evaluation; there is no training data and nothing is downloaded.

## bundled corpus (`src/agentic_rag/data.py`)

- **Provenance:** hand-authored for this project. Eleven short encyclopedia-style passages
  linked by shared entities (landmark -> city -> country), deliberately structured so some
  questions require two retrieval hops.
- **Labeled questions:** seven natural-language questions, each mapped to the answer
  passage id and a multi-hop flag.
- **Licensing:** authored by this repository; MIT.
- **Known gaps:** tiny, English, general-knowledge; a demonstration set, not a competitive
  multi-hop benchmark.

## Ethical considerations

The corpus is synthetic and contains no personal, sensitive, or copyrighted content.
