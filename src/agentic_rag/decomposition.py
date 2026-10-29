"""Query decomposition: splitting a complex question into answerable sub-questions.

Multi-hop questions ("What is the capital of the country where the Eiffel Tower is?")
cannot be answered by one retrieval; they must be decomposed. This module provides a
transparent, offline decomposer that splits on conjunctions and comparison structure, plus
a protocol so a model-backed decomposer can drop in behind the same interface.

The decomposition is deliberately rule-based here so the agent's behavior is deterministic
and inspectable; the point of the project is the *control loop* that consumes the
sub-questions, not a learned decomposer.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Protocol, runtime_checkable

_WHITESPACE = re.compile(r"\s+")
_SPLIT = re.compile(r" (?:and then|then|and also|and|;) ", re.IGNORECASE)
_COMPARE = re.compile(
    r"^(?:which|who|what) (?:is|was|are|has|had) ([^:,]+)[:,] ?(.+?) or (.+)$",
    re.IGNORECASE,
)


@runtime_checkable
class Decomposer(Protocol):
    """Splits a complex query into sub-questions."""

    def decompose(self, query: str) -> Sequence[str]:
        """Return the sub-questions for ``query`` (``[query]`` if indivisible)."""
        ...


class RuleDecomposer:
    """A rule-based decomposer splitting on conjunctions and comparisons."""

    def decompose(self, query: str) -> list[str]:
        """Return sub-questions, or ``[query]`` when the query is already atomic."""
        # Collapse whitespace first so the patterns below run in linear time on
        # untrusted input (no ambiguous whitespace quantifiers to backtrack over).
        normalized = _WHITESPACE.sub(" ", query).strip()
        comparison = _COMPARE.match(normalized.rstrip("?"))
        if comparison:
            attribute, left, right = comparison.groups()
            return [
                f"What {attribute.strip()} does {left.strip()} have?",
                f"What {attribute.strip()} does {right.strip()} have?",
            ]
        parts = [part.strip(" ?.") for part in _SPLIT.split(normalized) if part.strip(" ?.")]
        if len(parts) <= 1:
            return [normalized]
        return [part if part.endswith("?") else f"{part}?" for part in parts]
