"""Core types and a self-contained retriever for agentic retrieval.

This project is about the *agentic control* on top of retrieval - decomposing queries,
deciding what to retrieve next, and synthesizing multi-hop answers - so it ships its own
small, self-contained retriever rather than depending on another package.

- :class:`Document` - a passage with an id.
- :class:`Scored` - a document with a relevance score.
- :class:`BM25Index` - a compact Okapi BM25 index, the retrieval primitive the agent drives.

The index is inverted (see :mod:`agentic_rag.core.postings`): each term maps to the documents
containing it with their BM25 term weight precomputed, and a query adds those weights into one
score array in query order. That gives every document the same score, summed in the same order,
as scoring it directly, while touching only documents that share a term with the query.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from agentic_rag.core.postings import Postings, PostingsBuilder, top_k

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
        self._postings: Postings = Postings.empty()
        self._avg_len = 0.0

    def add(self, documents: Sequence[Document]) -> None:
        """Index ``documents`` (replacing any previous contents)."""
        self._docs = list(documents)
        builder = PostingsBuilder()
        lengths: list[int] = []
        for doc, document in enumerate(self._docs):
            tokens = tokenize(document.text)
            lengths.append(len(tokens))
            builder.add_chunk(doc, ((t, float(c)) for t, c in Counter(tokens).items()))
        postings = builder.build()
        self._avg_len = sum(lengths) / len(lengths) if lengths else 0.0
        if not self._docs:
            self._postings = postings
            return
        n = len(self._docs)
        idf = np.array(
            [
                max(0.0, math.log((n - int(df) + 0.5) / (int(df) + 0.5) + 1.0))
                for df in postings.document_frequencies()
            ],
            dtype=np.float64,
        )
        # The length-dependent part of the denominator, fixed per document.
        length_norm = np.array(
            [self._k1 * (1 - self._b + self._b * n_tokens / self._avg_len) for n_tokens in lengths],
            dtype=np.float64,
        )
        tf = postings.values
        postings.values = (
            idf[postings.term_of_entry] * tf * (self._k1 + 1) / (tf + length_norm[postings.ids])
        )
        self._postings = postings

    def search(self, query: str, *, k: int = 5) -> list[Scored]:
        """Return the top-``k`` documents for ``query`` by BM25 score."""
        if not self._docs:
            return []
        scores = np.zeros(len(self._docs), dtype=np.float64)
        for term in tokenize(query):
            posting = self._postings.get(term)
            if posting is not None:
                ids, weights = posting
                scores[ids] += weights
        return [Scored(self._docs[doc], score) for doc, score in top_k(scores, k)]

    def __len__(self) -> int:
        return len(self._docs)
