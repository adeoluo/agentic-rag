"""Agentic RAG - iterative multi-hop retrieval driven by an agent.

Public API: the core retrieval primitives and query decomposition. The agentic control
loop and answer synthesis live in their own modules.
"""

from __future__ import annotations

from agentic_rag.agent import AgenticResult, AgenticRetriever, RetrievalStep
from agentic_rag.core import BM25Index, Document, Scored, tokenize
from agentic_rag.decomposition import RuleDecomposer
from agentic_rag.synthesis import Answer, synthesize_answer

__version__ = "0.1.0"

__all__ = [
    "AgenticResult",
    "AgenticRetriever",
    "Answer",
    "BM25Index",
    "Document",
    "RetrievalStep",
    "RuleDecomposer",
    "Scored",
    "__version__",
    "synthesize_answer",
    "tokenize",
]
