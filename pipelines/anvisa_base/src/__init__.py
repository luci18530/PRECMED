# -*- coding: utf-8 -*-
"""
Pipeline de Processamento de Dados ANVISA

Módulo principal para processamento de dados de medicamentos da ANVISA.

Inclui scraping dinâmico e sustentável para automação completa.

Exemplo de uso do scraper:
    >>> from pipelines.anvisa_base.src import AnvisaDynamicScraper
    >>> scraper = AnvisaDynamicScraper(
    ...     base_url="https://www.gov.br/anvisa/...",
    ...     cache_dir="data/cache/scraper"
    ... )
    >>> df = scraper.scrape_available_files(tipo_lista='PMC')
"""

__version__ = "2.1.0"  # Incrementado para incluir scraper dinâmico
__author__ = "Data Processing Team"

# Importações de scraper dinâmico (se disponível)
try:
    from .dynamic_scraper import AnvisaDynamicScraper
    from .hybrid_source import HybridAnvisaSource
    _SCRAPER_AVAILABLE = True
except ImportError:
    _SCRAPER_AVAILABLE = False
    AnvisaDynamicScraper = None
    HybridAnvisaSource = None

from .config import configurar_pandas, ARQUIVO_ENTRADA, ARQUIVO_SAIDA

__all__ = ["configurar_pandas", "ARQUIVO_ENTRADA", "ARQUIVO_SAIDA"]
