"""Tests for the bundled data, evaluation, and CLI."""

from __future__ import annotations

import pytest

from agentic_rag.cli import main
from agentic_rag.core.retrieval import BM25Index
from agentic_rag.data import corpus, questions
from agentic_rag.evaluation import evaluate


def _index() -> BM25Index:
    index = BM25Index()
    index.add(corpus())
    return index


# --------------------------------------------------------------------------- #
# Data
# --------------------------------------------------------------------------- #
def test_corpus_and_questions_consistent() -> None:
    ids = {doc.id for doc in corpus()}
    for _question, answer_id, _multi in questions():
        assert answer_id in ids


def test_has_multi_hop_questions() -> None:
    assert any(multi for _, _, multi in questions())


# --------------------------------------------------------------------------- #
# Evaluation
# --------------------------------------------------------------------------- #
def test_agentic_beats_single_hop_on_multi_hop() -> None:
    index = _index()
    labeled = questions()
    baseline = evaluate(index, labeled, agentic=False)
    agentic = evaluate(index, labeled, agentic=True)
    # The whole point: agentic retrieval wins on multi-hop questions.
    assert agentic.multi_hop > baseline.multi_hop


def test_evaluation_reports_fields() -> None:
    report = evaluate(_index(), questions(), agentic=True)
    assert 0.0 <= report.overall <= 1.0
    assert report.num_questions == len(questions())
    assert "agentic" in report.format()


def test_single_hop_matches_on_single_hop_questions() -> None:
    # On single-hop questions both methods should do comparably.
    index = _index()
    labeled = questions()
    baseline = evaluate(index, labeled, agentic=False)
    agentic = evaluate(index, labeled, agentic=True)
    assert agentic.single_hop >= baseline.single_hop - 0.01


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def test_cli_ask(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["ask", "What is the capital of France"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Answer:" in output
    assert "Paris" in output


def test_cli_ask_multi_hop_shows_hops(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["ask", "Where is the Eiffel Tower located"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Retrieval hops:" in output


def test_cli_evaluate(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["evaluate"])
    output = capsys.readouterr().out
    assert exit_code == 0
    assert "single-hop" in output
    assert "agentic" in output
    assert "Multi-hop gain" in output


def test_cli_requires_command() -> None:
    with pytest.raises(SystemExit):
        main([])
