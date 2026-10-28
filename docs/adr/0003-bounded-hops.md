# ADR-0003: A bounded hop budget with pivot tracking

- **Status:** Accepted
- **Date:** 2026-01-01

## Context

Iterative retrieval could loop forever if a follow-up keeps surfacing the same entity or
oscillates between two.

## Decision

Bound follow-up queries per sub-question with `max_hops`, track which entities have been
pivoted onto so none is chased twice, and skip any query already issued.

## Alternatives considered

- **Unbounded iteration until confidence is high.** Risks non-termination on corpora where
  confidence never rises.
- **A single fixed two-hop pass.** Simpler but inflexible; some questions need one hop,
  others two.

## Consequences

- The loop always terminates.
- Worst-case retrieval count is bounded by sub-questions times the hop budget.
- A very deep multi-hop chain beyond the budget is not fully resolved (acceptable and tunable).
