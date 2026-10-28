"""A bundled multi-hop corpus and labeled questions.

The passages are self-authored and deliberately structured so that several questions
require two hops: the answer to the question lives in a passage reachable only by first
retrieving an intermediate entity. This lets the evaluation show agentic (multi-hop)
retrieval beating single-hop retrieval on exactly the questions it is designed for.
"""

from __future__ import annotations

from agentic_rag.core.retrieval import Document

_DOCUMENTS: tuple[tuple[str, str], ...] = (
    ("eiffel", "The Eiffel Tower is a wrought-iron landmark located in the city of Paris."),
    ("paris", "Paris is the capital of France and sits on the river Seine."),
    ("france", "France is a country in Western Europe known for its cuisine and wine."),
    ("liberty", "The Statue of Liberty is a monument located in the city of New York."),
    ("nyc", "New York is the most populous city in the United States of America."),
    ("usa", "The United States of America is a country in North America."),
    ("colosseum", "The Colosseum is an ancient amphitheatre located in the city of Rome."),
    ("rome", "Rome is the capital of Italy and was the centre of the Roman Empire."),
    ("italy", "Italy is a country in Southern Europe shaped like a boot."),
    ("fuji", "Mount Fuji is the tallest mountain located in the country of Japan."),
    ("japan", "Japan is an island country in East Asia; its capital is Tokyo."),
)

# Each question maps to the id of the passage that actually contains the answer, and a
# flag for whether answering it requires more than one retrieval hop.
_QUESTIONS: tuple[tuple[str, str, bool], ...] = (
    ("What is the capital of France", "paris", False),
    ("Where is the Eiffel Tower located", "paris", True),
    ("In which country is the Colosseum", "italy", True),
    ("What is the capital of Italy", "rome", False),
    ("In which country is Mount Fuji", "japan", False),
    ("Where is the Statue of Liberty", "nyc", True),
    ("What is the capital of Japan", "japan", False),
)


def corpus() -> list[Document]:
    """Return the bundled documents."""
    return [Document(id=doc_id, text=text) for doc_id, text in _DOCUMENTS]


def questions() -> list[tuple[str, str, bool]]:
    """Return the labeled questions as ``(question, answer_passage_id, multi_hop)``."""
    return list(_QUESTIONS)
