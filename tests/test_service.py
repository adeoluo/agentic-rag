"""Tests for the dependency-free HTTP retrieval service (pure handler layer)."""

from __future__ import annotations

from agentic_rag.service import RetrievalService, handle


def _service() -> RetrievalService:
    return RetrievalService.from_documents()


def test_health() -> None:
    status, payload = handle("GET", "/health", {}, _service())
    assert status == 200
    assert payload["status"] == "ok"
    assert payload["index_size"] > 0


def test_retrieve_returns_answer_and_trace() -> None:
    status, payload = handle(
        "POST", "/retrieve", {"question": "What is the capital of France"}, _service()
    )
    assert status == 200
    assert "answer" in payload
    assert isinstance(payload["citations"], list)
    assert payload["num_hops"] >= 1
    assert isinstance(payload["hops"], list)


def test_retrieve_rejects_missing_question() -> None:
    status, payload = handle("POST", "/retrieve", {}, _service())
    assert status == 400
    assert "question" in payload["error"]


def test_retrieve_rejects_bad_parameters() -> None:
    service = _service()
    status, _ = handle("POST", "/retrieve", {"question": "x", "max_hops": 0}, service)
    assert status == 400
    status, _ = handle("POST", "/retrieve", {"question": "x", "k": 99}, service)
    assert status == 400
    status, _ = handle("POST", "/retrieve", {"question": "   "}, service)
    assert status == 400


def test_retrieve_rejects_overlong_question() -> None:
    status, _ = handle("POST", "/retrieve", {"question": "a" * 5000}, _service())
    assert status == 400


def test_unknown_route() -> None:
    status, payload = handle("GET", "/nope", {}, _service())
    assert status == 404
    assert "error" in payload


def test_ready_endpoint() -> None:
    status, payload = handle("GET", "/ready", {}, _service())
    assert status == 200
    assert payload["status"] == "ready"


def test_metrics_record_requests() -> None:
    service = _service()
    handle("POST", "/retrieve", {"question": "What is the capital of France"}, service)
    handle("POST", "/retrieve", {}, service)  # a 400
    text = service.metrics.render_prometheus()
    assert "service_requests_total" in text
    assert 'route="POST /retrieve"' in text
    assert service.metrics.total_requests == 2
    assert service.metrics.total_errors == 1
    assert "service_request_duration_ms_bucket" in text
