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
_COMPARE_LEAD = re.compile(r"^(?:which|who|what) (?:is|was|are|has|had) ", re.IGNORECASE)


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
        comparison = self._split_comparison(normalized.rstrip("?"))
        if comparison is not None:
            attribute, left, right = comparison
            return [
                f"What {attribute} does {left} have?",
                f"What {attribute} does {right} have?",
            ]
        parts = [part.strip(" ?.") for part in _SPLIT.split(normalized) if part.strip(" ?.")]
        if len(parts) <= 1:
            return [normalized]
        return [part if part.endswith("?") else f"{part}?" for part in parts]

    @staticmethod
    def _split_comparison(text: str) -> tuple[str, str, str] | None:
        """Parse "which is <attribute>: <left> or <right>" with linear string splits."""
        lead = _COMPARE_LEAD.match(text)
        if not lead:
            return None
        remainder = text[lead.end() :]
        # The attribute is separated from the choices by the first ':' or ','.
        separator_index = min(
            (index for index in (remainder.find(":"), remainder.find(",")) if index >= 0),
            default=-1,
        )
        if separator_index < 0:
            return None
        attribute = remainder[:separator_index].strip()
        choices = remainder[separator_index + 1 :].strip()
        left, separator, right = choices.partition(" or ")
        if not separator or not attribute or not left.strip() or not right.strip():
            return None
        return attribute, left.strip(), right.strip()
