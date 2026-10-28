"""Entrypoint: `python -m agentic_rag`."""

from __future__ import annotations

from agentic_rag import __version__
from agentic_rag.configuration import settings


def main() -> None:
    header = f"Agentic Rag v{__version__}"
    status = f"environment={settings.environment}, seed={settings.seed}"
    print(f"{header} - {status}")


if __name__ == "__main__":
    main()
