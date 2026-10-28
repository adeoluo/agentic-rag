"""Tests for synthesis and the agentic retrieval loop."""

from __future__ import annotations

import pytest

from agentic_rag.agent import AgenticRetriever
from agentic_rag.core import BM25Index, Document, Scored
from agentic_rag.synthesis import FollowUpGenerator, synthesize_answer


def _corpus() -> list[Document]:
    return [
        Document("d0", "The Eiffel Tower is a landmark located in the city of Paris."),
        Document("d1", "Paris is the capital of France and its most populous city."),
        Document("d2", "France is a country in Western Europe with a large population."),
        Document("d3", "Tokyo is the capital of Japan, an island country in East Asia."),
        Document("d4", "The Statue of Liberty stands in New York in the United States."),
    ]


def _index() -> BM25Index:
    index = BM25Index()
    index.add(_corpus())
    return index


# --------------------------------------------------------------------------- #
# Synthesis
# --------------------------------------------------------------------------- #
def test_synthesize_picks_relevant_sentence() -> None:
    index = _index()
    passages = index.search("capital of France", k=3)
    answer = synthesize_answer("What is the capital of France", passages)
    assert "Paris" in answer.text
    assert answer.confidence > 0.0
    assert answer.citations


def test_synthesize_no_passages() -> None:
    answer = synthesize_answer("anything", [])
    assert answer.confidence == 0.0
    assert answer.citations == ()


def test_followup_surfaces_new_entity() -> None:
    generator = FollowUpGenerator()
    nxt = generator.next_query(
        "Where is the Eiffel Tower", "The Eiffel Tower is located in Paris.", set()
    )
    assert nxt is not None
    assert "Paris" in nxt


def test_followup_none_when_nothing_new() -> None:
    generator = FollowUpGenerator()
    nxt = generator.next_query("Where is Paris", "generic lowercase text only", set())
    assert nxt is None


# --------------------------------------------------------------------------- #
# Agentic retriever
# --------------------------------------------------------------------------- #
def test_agent_answers_single_hop() -> None:
    agent = AgenticRetriever(_index())
    result = agent.run("What is the capital of France")
    assert "Paris" in result.answer.text
    assert result.num_hops >= 1


def test_agent_multi_hop_follows_entity() -> None:
    # "Where is the Eiffel Tower" -> Paris -> retrieve about Paris (capital of France).
    agent = AgenticRetriever(_index(), max_hops=2)
    result = agent.run("Where is the Eiffel Tower located")
    queries = [step.query for step in result.steps]
    # A follow-up query pivoting on an entity should appear.
    assert any("(" in q for q in queries)


def test_agent_decomposes_conjunction() -> None:
    agent = AgenticRetriever(_index())
    result = agent.run("What is the capital of France and the capital of Japan")
    assert len(result.sub_questions) == 2


def test_agent_validates_params() -> None:
    with pytest.raises(ValueError, match="max_hops"):
        AgenticRetriever(_index(), max_hops=0)
    with pytest.raises(ValueError, match="k must"):
        AgenticRetriever(_index(), k=0)


def test_agent_records_trace() -> None:
    agent = AgenticRetriever(_index())
    result = agent.run("capital of Japan")
    assert result.steps
    assert all(isinstance(step.retrieved_ids, tuple) for step in result.steps)


def test_agent_handles_no_results() -> None:
    agent = AgenticRetriever(_index())
    result = agent.run("xylophone quasar nonexistent")
    assert result.answer.confidence == 0.0


def test_scored_id_property() -> None:
    scored = Scored(Document("x", "text"), 1.0)
    assert scored.id == "x"
