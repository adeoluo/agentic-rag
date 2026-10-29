"""A dependency-free HTTP service exposing the agentic retriever.

The service is split into two layers so it is fully testable without opening a
socket:

* :func:`handle` is a pure function ``(method, path, body) -> (status, payload)``
  that contains all of the routing and application logic.
* :class:`_Handler` and :func:`serve` bind :func:`handle` to the standard
  library ``http.server`` only when a process is actually started.

Endpoints
---------
``GET  /health``            liveness and index size.
``POST /retrieve``          body ``{"question": str, "max_hops"?: int, "k"?: int}``;
                            returns the answer, citations, confidence, and the hop trace.

The service is stateless per request over an index built once at construction,
which is the shape a production deployment would scale horizontally.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from agentic_rag.agent import AgenticRetriever
from agentic_rag.core.retrieval import BM25Index, Document
from agentic_rag.data import corpus

JsonObject = dict[str, Any]
_MAX_QUESTION_CHARS = 2000
_MAX_HOPS_LIMIT = 8
_MAX_K_LIMIT = 20


@dataclass(frozen=True)
class RetrievalService:
    """Holds the index and answers retrieval requests."""

    index: BM25Index

    @classmethod
    def from_documents(cls, documents: list[Document] | None = None) -> RetrievalService:
        index = BM25Index()
        index.add(documents if documents is not None else corpus())
        return cls(index=index)

    @property
    def index_size(self) -> int:
        return len(self.index)

    def retrieve(self, question: str, *, max_hops: int, k: int) -> JsonObject:
        result = AgenticRetriever(self.index, max_hops=max_hops, k=k).run(question)
        return {
            "question": result.question,
            "answer": result.answer.text,
            "citations": list(result.answer.citations),
            "confidence": round(result.answer.confidence, 4),
            "sub_questions": list(result.sub_questions),
            "hops": [
                {"query": step.query, "retrieved": list(step.retrieved_ids)}
                for step in result.steps
            ],
            "num_hops": result.num_hops,
        }


def _validate_retrieve(body: Mapping[str, Any]) -> tuple[str, int, int]:
    question = body.get("question")
    if not isinstance(question, str) or not question.strip():
        raise ValueError("'question' must be a non-empty string")
    if len(question) > _MAX_QUESTION_CHARS:
        raise ValueError(f"'question' exceeds {_MAX_QUESTION_CHARS} characters")
    max_hops = body.get("max_hops", 2)
    k = body.get("k", 3)
    if not isinstance(max_hops, int) or not 1 <= max_hops <= _MAX_HOPS_LIMIT:
        raise ValueError(f"'max_hops' must be an integer in [1, {_MAX_HOPS_LIMIT}]")
    if not isinstance(k, int) or not 1 <= k <= _MAX_K_LIMIT:
        raise ValueError(f"'k' must be an integer in [1, {_MAX_K_LIMIT}]")
    return question, max_hops, k


def handle(
    method: str, path: str, body: Mapping[str, Any], service: RetrievalService
) -> tuple[int, JsonObject]:
    """Pure request handler: route a request to a status code and payload."""

    if method == "GET" and path == "/health":
        return 200, {"status": "ok", "index_size": service.index_size}
    if method == "POST" and path == "/retrieve":
        try:
            question, max_hops, k = _validate_retrieve(body)
        except ValueError as error:
            return 400, {"error": str(error)}
        return 200, service.retrieve(question, max_hops=max_hops, k=k)
    return 404, {"error": f"no route for {method} {path}"}


class _Handler(BaseHTTPRequestHandler):  # pragma: no cover - exercised over sockets
    service: RetrievalService

    def _respond(self, status: int, payload: JsonObject) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        status, payload = handle("GET", self.path, {}, self.service)
        self._respond(status, payload)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            self._respond(400, {"error": "request body is not valid JSON"})
            return
        status, payload = handle("POST", self.path, body, self.service)
        self._respond(status, payload)

    def log_message(self, *_: Any) -> None:
        return


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:  # pragma: no cover
    """Start the HTTP service (blocking). Used by ``python -m agentic_rag serve``."""

    handler = type("_BoundHandler", (_Handler,), {"service": RetrievalService.from_documents()})
    server = ThreadingHTTPServer((host, port), handler)
    print(f"agentic-rag service listening on http://{host}:{port}")
    server.serve_forever()
