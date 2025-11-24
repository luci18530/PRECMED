"""Camada de parsing para interpretar HTMLs de publicação de preços."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup


def extract_month_sections(html: str) -> list[str]:
    """Extrai blocos `<p>` contendo referências mensais a partir de um HTML simples."""

    soup = BeautifulSoup(html, "html.parser")
    paragraphs = []
    for node in soup.find_all("p"):
        text = node.get_text(" ", strip=True)
        if text:
            paragraphs.append(text)
    return paragraphs


def load_snippet(snippet_path: str | Path) -> Optional[str]:
    """Carrega o snippet PMC local, caso exista."""

    path = Path(snippet_path)
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")
