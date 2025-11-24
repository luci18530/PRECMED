#!/usr/bin/env python
"""Entrypoint para expor o pipeline via API ou CLI."""

from pipelines.anvisa_base.main import run as run_anvisa_pipeline


def run() -> None:
    """Executa o pipeline de processamento da base ANVISA."""

    run_anvisa_pipeline()


if __name__ == "__main__":
    run()
