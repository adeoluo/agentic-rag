"""Answer synthesis and a follow-up (self-query) generator.

Between retrieval hops the agent must (a) decide whether it has enough evidence and, if
not, (b) generate the next query. These two transparent, offline components do exactly
that:

- :func:`synthesize_answer` - compose an answer from retrieved passages by extracting the
  sentence(s) most relevant to the question, with citations.
- :class:`FollowUpGenerator` - a self-querying step: given the question and what has been
  retrieved so far, propose the next query by surfacing salient entities not yet covered.

Both are rule-based so the control loop is deterministic; a model-backed synthesizer or
query generator slots in behind the same shapes.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass

from agentic_rag.core.retrieval import Scored, tokenize

_SENTENCE = re.compile(r"[^.!?]+[.!?]?")
_CAPITALIZED = re.compile(r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b")


@dataclass(frozen=True, slots=True)
class Answer:
    """A synthesized answer with the passage ids it draws on."""

    text: str
    citations: tuple[str, ...]
    confidence: float


def _best_sentence(text: str, query_terms: set[str]) -> tuple[str, int]:
    best = ""
    best_hits = -1
    for sentence in _SENTENCE.findall(text):
        sentence = sentence.strip()
        if not sentence:
            continue
        hits = len(query_terms & set(tokenize(sentence)))
        if hits > best_hits:
            best_hits = hits
            best = sentence
    return best, max(0, best_hits)


def synthesize_answer(question: str, passages: Sequence[Scored]) -> Answer:
    """Compose an answer by extracting the most relevant sentence across passages.

    Confidence is the best sentence's query-term coverage, normalized by the question's
    term count - a transparent proxy that is high when a passage clearly addresses the
    question and low when the evidence is thin.
    """
    query_terms = set(tokenize(question))
    if not passages or not query_terms:
        return Answer(text="I could not find an answer.", citations=(), confidence=0.0)

    best_text = ""
    best_hits = -1
    best_id = ""
    for scored in passages:
        sentence, hits = _best_sentence(scored.document.text, query_terms)
        if hits > best_hits:
            best_hits = hits
            best_text = sentence
            best_id = scored.id
    confidence = min(1.0, best_hits / len(query_terms)) if query_terms else 0.0
    citations = (best_id,) if best_id else ()
    text = best_text or "I could not find an answer."
    return Answer(text=text, citations=citations, confidence=confidence)


class FollowUpGenerator:
    """Proposes the next query from salient, not-yet-covered entities."""

    def next_query(self, question: str, retrieved_text: str, covered: set[str]) -> str | None:
        """Return the next query, or ``None`` when nothing new is worth retrieving.

        Surfaces capitalized entities in the retrieved text that are not already covered
        and not already in the question, and pivots the original question onto the most
        salient one.
        """
        question_terms = set(tokenize(question, keep_stopwords=True))
        candidates: list[str] = []
        for match in _CAPITALIZED.findall(retrieved_text):
            entity = match.strip()
            key = entity.lower()
            if key in covered:
                continue
            if all(tok in question_terms for tok in tokenize(entity, keep_stopwords=True)):
                continue
            candidates.append(entity)
        if not candidates:
            return None
        # Pick the entity that appears most often in the retrieved text.
        pivot = max(candidates, key=lambda e: retrieved_text.count(e))
        return f"{question} ({pivot})"
