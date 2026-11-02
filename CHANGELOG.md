# Changelog

All notable changes to this project are documented here. The file is generated
from Conventional Commits by [git-cliff](https://git-cliff.org) when a release is cut
with `make cut-release`.

## Unreleased

### Features

- **core:** Add self-contained retrieval and query decomposition
- **agent:** Add the agentic retrieve-reason-retrieve loop
- **cli:** Add multi-hop dataset, evaluation, and the CLI
- Add a deterministic retrieval micro-benchmark
- Add HTTP service, stress benchmark, and operations documentation
- Add production observability (metrics and readiness) and reword footer

### Bug fixes

- Remove polynomial backtracking from query decomposition regexes
- Parse comparison questions with linear string splits
- Valid Prometheus histogram family and zero-overlap abstention (#14)

### Documentation

- Write README, architecture diagram, and responsible-AI cards
- Use plain, factual wording (#13)
- Standard README structure and language framing (#16)
- Reword in-memory index tradeoff in scaling notes (#17)
- Vertical layered architecture diagram
- Horizontal layered architecture diagram
- Compact horizontal architecture diagram
- Recorded demos of more commands, with their vhs tapes (#1)
- Recorded demos of the HTTP service and more commands (#2)

### Build and CI

- Run CodeQL on main and on a weekly schedule only

### Maintenance

- Scaffold agentic-rag from standards template
- Bump continuous integration action versions and dev dependencies
- Remove Dependabot configuration
