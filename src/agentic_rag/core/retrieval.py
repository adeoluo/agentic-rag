"""Core types and a self-contained retriever for agentic retrieval.

This project is about the *agentic control* on top of retrieval - decomposing queries,
deciding what to retrieve next, and synthesizing multi-hop answers - so it ships its own
small, self-contained retriever rather than depending on another package.

- :class:`Document` - a passage with an id.
- :class:`Scored` - a document with a relevance score.
- :class:`BM25Index` - a compact Okapi BM25 index, the retrieval primitive the agent drives.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

_TOKEN = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "of",
        "to",
        "in",
        "on",
        "at",
        "for",
        "is",
        "are",
        "was",
        "were",
        "be",
        "it",
        "its",
        "as",
        "by",
        "with",
        "from",
        "that",
        "this",
        "what",
        "which",
        "who",
        "when",
        "where",
        "how",
        "why",
        "did",
        "do",
        "does",
    }
)


def tokenize(text: str, *, keep_stopwords: bool = False) -> list[str]:
    """Lowercase, split, and optionally drop stopwords."""
    tokens = _TOKEN.findall(text.lower())
    if keep_stopwords:
        return tokens
    return [token for token in tokens if token not in _STOPWORDS]


@dataclass(frozen=True, slots=True)
class Document:
    """A retrievable passage."""

    id: str
    text: str

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Document.id must be non-empty")
        if not self.text:
            raise ValueError("Document.text must be non-empty")


@dataclass(frozen=True, slots=True)
class Scored:
    """A document with a retrieval score."""

    document: Document
    score: float

    @property
    def id(self) -> str:
        return self.document.id


class BM25Index:
    """A compact Okapi BM25 index over documents."""

    def __init__(self, *, k1: float = 1.5, b: float = 0.75) -> None:
        self._k1 = k1
        self._b = b
        self._docs: list[Document] = []
        self._tokens: list[list[str]] = []
        self._freqs: list[Counter[str]] = []
        self._df: Counter[str] = Counter()
        self._avg_len = 0.0

    def add(self, documents: Sequence[Document]) -> None:
        """Index ``documents`` (replacing any previous contents)."""
        self._docs = list(documents)
        self._tokens = [tokenize(doc.text) for doc in self._docs]
        self._freqs = [Counter(tokens) for tokens in self._tokens]
        self._df = Counter()
        for freqs in self._freqs:
            self._df.update(freqs.keys())
        total = sum(len(tokens) for tokens in self._tokens)
        self._avg_len = total / len(self._tokens) if self._tokens else 0.0

    def search(self, query: str, *, k: int = 5) -> list[Scored]:
        """Return the top-``k`` documents for ``query`` by BM25 score."""
        if not self._docs:
            return []
        terms = tokenize(query)
        scored = [Scored(self._docs[i], self._score(terms, i)) for i in range(len(self._docs))]
        scored = [s for s in scored if s.score > 0.0]
        scored.sort(key=lambda s: s.score, reverse=True)
        return scored[:k]

    def __len__(self) -> int:
        return len(self._docs)

    def _score(self, terms: Sequence[str], index: int) -> float:
        freqs = self._freqs[index]
        doc_len = len(self._tokens[index])
        n = len(self._docs)
        score = 0.0
        for term in terms:
            if term not in freqs:
                continue
            idf = max(0.0, math.log((n - self._df[term] + 0.5) / (self._df[term] + 0.5) + 1.0))
            tf = freqs[term]
            denominator = tf + self._k1 * (1 - self._b + self._b * doc_len / self._avg_len)
            score += idf * tf * (self._k1 + 1) / denominator
        return score
