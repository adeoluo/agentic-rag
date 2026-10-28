"""Evaluating agentic retrieval against a single-hop baseline.

The thesis of agentic RAG is that iterative, multi-hop retrieval answers questions a single
retrieval cannot. :func:`evaluate` measures that directly: for each labeled question it
checks whether the answer passage was retrieved, comparing the agentic retriever to a
single-hop baseline. The payoff shows up on the questions flagged as multi-hop.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from agentic_rag.agent import AgenticRetriever
from agentic_rag.core.retrieval import BM25Index


@dataclass(frozen=True, slots=True)
class EvalReport:
    """Aggregated retrieval success for a method."""

    method: str
    overall: float
    multi_hop: float
    single_hop: float
    num_questions: int

    def format(self) -> str:
        return (
            f"{self.method:<12} overall={self.overall:.2f}  "
            f"multi-hop={self.multi_hop:.2f}  single-hop={self.single_hop:.2f}  "
            f"(N={self.num_questions})"
        )


def _retrieved_ids_single_hop(index: BM25Index, question: str, k: int) -> set[str]:
    return {scored.id for scored in index.search(question, k=k)}


def _retrieved_ids_agentic(agent: AgenticRetriever, question: str) -> set[str]:
    result = agent.run(question)
    ids: set[str] = set()
    for step in result.steps:
        ids.update(step.retrieved_ids)
    return ids


def evaluate(
    index: BM25Index,
    questions: Sequence[tuple[str, str, bool]],
    *,
    agentic: bool,
    k: int = 3,
    max_hops: int = 2,
) -> EvalReport:
    """Evaluate retrieval success on labeled questions.

    Args:
        index: The indexed corpus.
        questions: ``(question, answer_passage_id, multi_hop)`` triples.
        agentic: Whether to use the agentic retriever or the single-hop baseline.
        k: Passages per retrieval.
        max_hops: Hop budget for the agentic retriever.
    """
    agent = AgenticRetriever(index, k=k, max_hops=max_hops) if agentic else None

    overall_hits = 0
    multi_total = multi_hits = 0
    single_total = single_hits = 0
    for question, answer_id, multi_hop in questions:
        if agent is not None:
            retrieved = _retrieved_ids_agentic(agent, question)
        else:
            retrieved = _retrieved_ids_single_hop(index, question, k)
        hit = answer_id in retrieved
        overall_hits += hit
        if multi_hop:
            multi_total += 1
            multi_hits += hit
        else:
            single_total += 1
            single_hits += hit

    n = len(questions)
    return EvalReport(
        method="agentic" if agentic else "single-hop",
        overall=overall_hits / n if n else 0.0,
        multi_hop=multi_hits / multi_total if multi_total else 0.0,
        single_hop=single_hits / single_total if single_total else 0.0,
        num_questions=n,
    )
