"""Command-line interface for agentic retrieval.

Subcommands:

- ``ask`` - answer a question over the bundled corpus and show the hop-by-hop trace.
- ``evaluate`` - compare agentic (multi-hop) retrieval against the single-hop baseline on
  the bundled labeled questions, the headline result of the project.

The CLI wires the bundled data, the index, the agent, and the evaluator together; it holds
no retrieval logic of its own.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from agentic_rag import __version__
from agentic_rag.agent import AgenticRetriever
from agentic_rag.core.retrieval import BM25Index
from agentic_rag.data import corpus, questions
from agentic_rag.evaluation import evaluate


def _index() -> BM25Index:
    index = BM25Index()
    index.add(corpus())
    return index


def build_parser() -> argparse.ArgumentParser:
    """Construct the argument parser."""
    parser = argparse.ArgumentParser(
        prog="agentic-rag",
        description="Agentic multi-hop retrieval built from scratch.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ask_parser = subparsers.add_parser("ask", help="Answer a question over the corpus.")
    ask_parser.add_argument("question", help="The question to answer.")
    ask_parser.add_argument("--max-hops", type=int, default=2, help="Follow-up hop budget.")
    ask_parser.set_defaults(handler=_handle_ask)

    eval_parser = subparsers.add_parser(
        "evaluate", help="Compare agentic and single-hop retrieval."
    )
    eval_parser.set_defaults(handler=_handle_evaluate)
    return parser


def _handle_ask(args: argparse.Namespace) -> int:
    agent = AgenticRetriever(_index(), max_hops=args.max_hops)
    result = agent.run(args.question)
    print(f"Question: {args.question}")
    if len(result.sub_questions) > 1:
        print("Sub-questions:")
        for sub in result.sub_questions:
            print(f"  - {sub}")
    print("Retrieval hops:")
    for step in result.steps:
        print(f"  {step.query}  ->  {', '.join(step.retrieved_ids) or '(none)'}")
    print(f"\nAnswer: {result.answer.text}")
    print(
        f"Confidence: {result.answer.confidence:.2f}  "
        f"Citations: {', '.join(result.answer.citations) or 'none'}"
    )
    return 0


def _handle_evaluate(_: argparse.Namespace) -> int:
    index = _index()
    labeled = questions()
    baseline = evaluate(index, labeled, agentic=False)
    agentic = evaluate(index, labeled, agentic=True)
    print("Retrieval success (answer passage found):\n")
    print(baseline.format())
    print(agentic.format())
    gain = agentic.multi_hop - baseline.multi_hop
    print(f"\nMulti-hop gain from agentic retrieval: {gain:+.2f}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point; returns a process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    handler = args.handler
    exit_code: int = handler(args)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
