"""Tests for core retrieval and query decomposition."""

from __future__ import annotations

import pytest

from agentic_rag.core import BM25Index, Document, tokenize
from agentic_rag.decomposition import RuleDecomposer


# --------------------------------------------------------------------------- #
# Tokenization and documents
# --------------------------------------------------------------------------- #
def test_tokenize_removes_stopwords() -> None:
    assert tokenize("What is the capital of France") == ["capital", "france"]


def test_document_validates() -> None:
    with pytest.raises(ValueError, match="id"):
        Document(id="", text="x")
    with pytest.raises(ValueError, match="text"):
        Document(id="d", text="")


# --------------------------------------------------------------------------- #
# BM25 index
# --------------------------------------------------------------------------- #
def _corpus() -> list[Document]:
    return [
        Document("d0", "The Eiffel Tower is a landmark located in Paris, France."),
        Document("d1", "Paris is the capital of France and its largest city."),
        Document("d2", "The Statue of Liberty is located in New York, United States."),
        Document("d3", "Tokyo is the capital of Japan."),
    ]


def test_bm25_retrieves_relevant() -> None:
    index = BM25Index()
    index.add(_corpus())
    results = index.search("where is the Eiffel Tower", k=2)
    assert results[0].id == "d0"
    assert len(index) == 4


def test_bm25_empty_and_no_match() -> None:
    index = BM25Index()
    assert index.search("anything") == []
    index.add(_corpus())
    assert index.search("quantum chromodynamics") == []


def test_bm25_scores_descending() -> None:
    index = BM25Index()
    index.add(_corpus())
    scores = [s.score for s in index.search("capital", k=5)]
    assert scores == sorted(scores, reverse=True)


# --------------------------------------------------------------------------- #
# Decomposition
# --------------------------------------------------------------------------- #
def test_decompose_conjunction() -> None:
    subs = RuleDecomposer().decompose("What is the capital of France and the capital of Japan")
    assert len(subs) == 2


def test_decompose_atomic_query_unchanged() -> None:
    subs = RuleDecomposer().decompose("Where is the Eiffel Tower")
    assert subs == ["Where is the Eiffel Tower"]


def test_decompose_appends_question_marks() -> None:
    subs = RuleDecomposer().decompose("find the population and find the area")
    assert all(s.endswith("?") for s in subs)


def test_decompose_comparison() -> None:
    subs = RuleDecomposer().decompose("Which is larger: France or Japan?")
    assert len(subs) == 2
    assert "France" in subs[0]
    assert "Japan" in subs[1]
