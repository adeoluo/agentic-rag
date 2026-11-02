# AGENTS.md

Working notes for coding agents and contributors in **Agentic RAG**. The [README](README.md)
explains what the project does and why; this file explains how to change it safely.

## Project

Agentic retrieval built from scratch: query decomposition, a self-querying retriever-agent, and iterative multi-hop retrieve-reason-retrieve.

## Layout

- `benchmarks/`: benchmark scripts and recorded results
- `docker-compose.yml`: local container setup
- `docs/`: documentation, architecture diagram source and render, design records
- `src/`: library and service source
- `tests/`: test suite

Key modules:

- `src/agentic_rag/__init__.py`: Agentic RAG - iterative multi-hop retrieval driven by an agent.
- `src/agentic_rag/agent.py`: The agentic retrieval control loop.
- `src/agentic_rag/cli.py`: Command-line interface for agentic retrieval.
- `src/agentic_rag/core/__init__.py`: Core abstractions for agentic retrieval.
- `src/agentic_rag/core/retrieval.py`: Core types and a self-contained retriever for agentic retrieval.
- `src/agentic_rag/data.py`: A bundled multi-hop corpus and labeled questions.
- `src/agentic_rag/decomposition.py`: Query decomposition: splitting a complex question into answerable sub-questions.
- `src/agentic_rag/evaluation.py`: Evaluating agentic retrieval against a single-hop baseline.
- `src/agentic_rag/observability.py`: In-process request metrics for the HTTP service.
- `src/agentic_rag/service.py`: A standard-library HTTP service exposing the agentic retriever.
- `src/agentic_rag/synthesis.py`: Answer synthesis and a follow-up (self-query) generator.

## Commands

| Command | Purpose |
|---|---|
| `make help` | Show this help |
| `make setup` | Install dependencies and pre-commit hooks |
| `make format` | Format automatically |
| `make lint` | Lint (no fixes) |
| `make type` | Type-check |
| `make test` | Run tests |
| `make coverage` | Tests with coverage gate |
| `make evaluation` | Reproduce the results table |
| `make run` | Run the application entrypoint |
| `make diagram` | Render architecture diagram to SVG |
| `make docker-build` | Build the image |
| `make docker-up` | Run via docker compose |
| `make clean` | Remove caches and artifacts |
| `make all` | Full local gate (mirror of continuous integration) |
| `make changelog` | Regenerate CHANGELOG.md from Conventional Commits (git-cliff) |
| `make cut-release` | Cut a release locally: version bump, changelog, tag, GitHub release (RELEASE_VERSION=vX.Y.Z optional) |

Run the full local gate (`make all`) before committing; CI runs the same checks.

## Conventions

- Commits follow Conventional Commits (`feat:`, `fix:`, `perf:`, `refactor:`, `docs:`, `test:`, `ci:`, `chore:`).
  The changelog and the next version number are derived from them.
- Every number quoted in the README is produced by a command in this repository. When behavior
  changes, rerun that command and update the number in the same commit.
- When a component is added, removed or renamed, update `docs/architecture/architecture.mmd`
  and re-render `architecture.svg` so the diagram matches the code.
- README sections keep their fixed order. Prose avoids em and en dashes and promotional wording.
- Tests accompany behavior changes; a bug fix comes with a test that fails without it.
- Releases are cut with `make cut-release`.

## Python notes

- Python is managed with `uv`; run commands through `uv run` so the locked environment is used.
- Lint and format with `ruff`; type-check with `mypy`; tests use `pytest`.
- Public functions carry type hints and a docstring that states the contract, not the steps.
