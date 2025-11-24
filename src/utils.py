"""Funções utilitárias compartilhadas."""
from __future__ import annotations

from pathlib import Path
from datetime import datetime


def ensure_dir(path: str | Path) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def timestamp() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
