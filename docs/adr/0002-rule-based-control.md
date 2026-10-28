# ADR-0002: Rule-based decomposition and self-querying

- **Status:** Accepted
- **Date:** 2026-01-01

## Context

The agentic loop needs to decompose questions and generate follow-up queries. These could
be model-backed or rule-based.

## Decision

Implement both as deterministic, rule-based components behind protocols (`Decomposer` and a
follow-up generator). Decomposition splits on conjunctions and comparison structure;
self-querying surfaces salient capitalized entities not yet chased.

## Alternatives considered

- **Model-backed decomposition/query generation.** More general, but adds a dependency and
  nondeterminism, obscuring the control loop that is the point of the project.
- **No decomposition.** Cannot handle conjunctive or multi-hop questions at all.

## Consequences

- The agent's behavior is deterministic, offline, and fully testable.
- A model-backed decomposer or query generator can replace the rule-based one behind the
  same interface without touching the loop.
- Rule-based steps cannot handle arbitrary open-ended reasoning (documented limitation).
