"""Enable ``python -m agentic_rag`` to invoke the command-line interface."""

from __future__ import annotations

from agentic_rag.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
