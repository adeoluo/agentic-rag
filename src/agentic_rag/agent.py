"""The agentic retrieval control loop.

Classic RAG retrieves once and generates. An *agentic* RAG decides, iteratively, what to
retrieve next - it decomposes the question, retrieves for each sub-question, and may issue
follow-up queries when the evidence surfaces a new entity to chase (the "retrieve, reason,
retrieve again" pattern that answers multi-hop questions one hop cannot).

:class:`AgenticRetriever` runs that loop over a :class:`~agentic_rag.core.retrieval.BM25Index`:

1. Decompose the question into sub-questions.
2. For each, retrieve, then optionally issue follow-up queries up to a hop budget.
3. Collect the evidence and synthesize a cited answer with a confidence score.

Every step is recorded in the returned trace, so a run is fully auditable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agentic_rag.core.retrieval import BM25Index, Scored
from agentic_rag.decomposition import Decomposer, RuleDecomposer
from agentic_rag.synthesis import Answer, FollowUpGenerator, synthesize_answer


@dataclass(frozen=True, slots=True)
class RetrievalStep:
    """One retrieval hop in the trace."""

    query: str
    retrieved_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AgenticResult:
    """The outcome of an agentic retrieval run."""

    question: str
    answer: Answer
    sub_questions: tuple[str, ...]
    steps: tuple[RetrievalStep, ...] = field(default_factory=tuple)

    @property
    def num_hops(self) -> int:
        return len(self.steps)


class AgenticRetriever:
    """Drives an index with decomposition and iterative follow-up retrieval."""

    def __init__(
        self,
        index: BM25Index,
        *,
        decomposer: Decomposer | None = None,
        max_hops: int = 2,
        k: int = 3,
    ) -> None:
        """Create an agentic retriever.

        Args:
            index: The retrieval index to drive.
            decomposer: Splits the question into sub-questions (rule-based by default).
            max_hops: Follow-up queries allowed per sub-question.
            k: Passages retrieved per query.
        """
        if max_hops < 1:
            raise ValueError("max_hops must be at least 1")
        if k < 1:
            raise ValueError("k must be at least 1")
        self._index = index
        self._decomposer = decomposer or RuleDecomposer()
        self._follow_up = FollowUpGenerator()
        self._max_hops = max_hops
        self._k = k

    def run(self, question: str) -> AgenticResult:
        """Answer ``question`` by decomposing and iteratively retrieving."""
        sub_questions = list(self._decomposer.decompose(question))
        steps: list[RetrievalStep] = []
        evidence: dict[str, Scored] = {}
        pivoted: set[str] = set()
        seen_queries: set[str] = set()

        for sub_question in sub_questions:
            query = sub_question
            for _ in range(self._max_hops):
                if query in seen_queries:
                    break
                seen_queries.add(query)
                results = self._index.search(query, k=self._k)
                steps.append(RetrievalStep(query=query, retrieved_ids=tuple(r.id for r in results)))
                for scored in results:
                    evidence[scored.id] = scored
                if not results:
                    break
                retrieved_text = " ".join(r.document.text for r in results)
                next_query = self._follow_up.next_query(sub_question, retrieved_text, pivoted)
                if next_query is None:
                    break
                # Record the entity we are pivoting onto so we do not chase it twice.
                pivot = next_query[next_query.rfind("(") + 1 : -1].lower()
                pivoted.add(pivot)
                query = next_query

        ranked = sorted(evidence.values(), key=lambda s: s.score, reverse=True)
        answer = synthesize_answer(question, ranked)
        return AgenticResult(
            question=question,
            answer=answer,
            sub_questions=tuple(sub_questions),
            steps=tuple(steps),
        )
