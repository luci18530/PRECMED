"""Interfaces de raspagem e download da CMED/ANVISA.

Durante a fase PMC 2025 usamos o pipeline legado em `pipelines.anvisa_base`
com uma camada fina para expor funções claras ao restante do projeto.
"""
from __future__ import annotations

from typing import Optional

from pipelines.anvisa_base import config_anvisa
from pipelines.anvisa_base.scripts import baixar as pipeline_anvisa


def collect_links(html_override: Optional[str] = None):
    """Retorna um DataFrame com os links das tabelas disponíveis.

    Parameters
    ----------
    html_override: str | None
        Permite injetar o snippet PMC 2025 local para ciclos rápidos.
    """

    return pipeline_anvisa.scrape_anvisa_links(html_override)


def run_full_download() -> None:
    """Executa o pipeline completo de download + limpeza + vigências."""

    pipeline_anvisa.main()


def is_test_mode_enabled() -> bool:
    """Indica se o modo PMC 2025 via HTML local está ativo."""

    return bool(getattr(config_anvisa, "USE_PMC_HTML_SNIPPET", False))


def get_download_window() -> tuple[int, int, int, int]:
    """Retorna o período de coleta configurado (ano/mes início e fim)."""

    return (
        config_anvisa.ANO_INICIO,
        config_anvisa.MES_INICIO,
        config_anvisa.ANO_FIM,
        config_anvisa.MES_FIM,
    )
