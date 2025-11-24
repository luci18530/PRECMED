"""Utilitários para limpeza e consolidação das planilhas CMED."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from pipelines.anvisa_base.scripts import baixar as pipeline_anvisa


__all__ = [
    "clean_downloads",
    "consolidate_clean",
]


def clean_downloads(source: str | Path, target: str | Path) -> None:
    """Dispara a rotina de limpeza em paralelo do pipeline legado."""

    pipeline_anvisa.clean_downloaded_files(str(source), str(target))


def consolidate_clean(target_folder: str | Path, output_file: str | Path):
    """Concatena os CSVs limpos em um arquivo único."""

    return pipeline_anvisa.consolidate_cleaned_files(str(target_folder), str(output_file))
