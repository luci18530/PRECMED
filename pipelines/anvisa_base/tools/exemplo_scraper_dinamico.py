#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EXEMPLO PRÁTICO: Uso do Scraper Dinâmico
=========================================

Este script demonstra casos de uso reais do scraper dinâmico.

Executar:
    python -m pipelines.anvisa_base.tools.exemplo_scraper_dinamico

Author: Luciano
Date: 2025-11-28
"""

import logging
import sys
from datetime import datetime
from pathlib import Path

# Configurar paths
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "src"))

from dynamic_scraper import AnvisaDynamicScraper
from hybrid_source import HybridAnvisaSource

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def exemplo_1_descoberta_automatica():
    """
    Exemplo 1: Descoberta Automática de Arquivos
    =============================================
    
    Demonstra como o scraper descobre automaticamente todos os arquivos
    disponíveis no site da ANVISA sem precisar de snippets HTML.
    """
    print("\n" + "="*80)
    print("EXEMPLO 1: Descoberta Automática de Arquivos")
    print("="*80)
    
    BASE_URL = "https://www.gov.br/anvisa/pt-br/assuntos/medicamentos/cmed/precos/anos-anteriores/anos-anteriores"
    CACHE_DIR = BASE_DIR.parent.parent / "data" / "cache" / "scraper"
    
    # Inicializar scraper
    scraper = AnvisaDynamicScraper(base_url=BASE_URL, cache_dir=CACHE_DIR)
    
    # Descobrir todos os arquivos PMC disponíveis
    print("\n📥 Buscando arquivos PMC disponíveis...")
    df_pmc = scraper.scrape_available_files(tipo_lista='PMC')
    
    print(f"\n✅ Encontrados {len(df_pmc)} arquivos PMC")
    print("\nÚltimos 10 arquivos:")
    print(df_pmc.tail(10)[['ano', 'mes', 'mes_nome', 'url']].to_string(index=False))
    
    # Estatísticas
    print(f"\n📊 Estatísticas:")
    print(f"   - Anos cobertos: {df_pmc['ano'].min()} a {df_pmc['ano'].max()}")
    print(f"   - Total de meses: {len(df_pmc)}")
    print(f"   - Último período: {df_pmc.iloc[-1]['mes_nome']}/{df_pmc.iloc[-1]['ano']}")
    
    return df_pmc


def exemplo_2_deteccao_novos_arquivos():
    """
    Exemplo 2: Detecção de Novos Arquivos
    ======================================
    
    Demonstra como detectar automaticamente novos arquivos desde a última
    execução, útil para pipelines incrementais.
    """
    print("\n" + "="*80)
    print("EXEMPLO 2: Detecção de Novos Arquivos (Incremental)")
    print("="*80)
    
    BASE_URL = "https://www.gov.br/anvisa/pt-br/assuntos/medicamentos/cmed/precos/anos-anteriores/anos-anteriores"
    CACHE_DIR = BASE_DIR.parent.parent / "data" / "cache" / "scraper"
    
    scraper = AnvisaDynamicScraper(base_url=BASE_URL, cache_dir=CACHE_DIR)
    
    # Primeira execução: descobre tudo e salva no cache
    print("\n🔍 Primeira execução: construindo cache...")
    df_all = scraper.scrape_available_files(tipo_lista='PMVG')
    print(f"   ✅ {len(df_all)} arquivos no cache")
    
    # Simular nova execução: detectar apenas novos
    print("\n🔍 Segunda execução: detectando novos arquivos...")
    df_novos = scraper.get_new_files_since_last_run('PMVG')
    
    if df_novos.empty:
        print("   ℹ️ Nenhum arquivo novo detectado (esperado se site não atualizou)")
    else:
        print(f"   🆕 {len(df_novos)} novos arquivos detectados!")
        print(df_novos[['ano', 'mes', 'mes_nome']].to_string(index=False))
    
    return df_novos


def exemplo_3_identificacao_gaps():
    """
    Exemplo 3: Identificação de Períodos Faltantes
    ===============================================
    
    Demonstra como identificar automaticamente gaps na cobertura de dados,
    útil para monitoramento de qualidade.
    """
    print("\n" + "="*80)
    print("EXEMPLO 3: Identificação de Gaps (Períodos Faltantes)")
    print("="*80)
    
    BASE_URL = "https://www.gov.br/anvisa/pt-br/assuntos/medicamentos/cmed/precos/anos-anteriores/anos-anteriores"
    CACHE_DIR = BASE_DIR.parent.parent / "data" / "cache" / "scraper"
    
    scraper = AnvisaDynamicScraper(base_url=BASE_URL, cache_dir=CACHE_DIR)
    
    # Verificar gaps desde 2023
    print("\n🔍 Verificando gaps desde janeiro/2023...")
    gaps = scraper.find_missing_periods('PMC', start_year=2023, start_month=1)
    
    if not gaps:
        print("   ✅ Cobertura completa! Nenhum gap detectado.")
    else:
        print(f"   ⚠️ {len(gaps)} períodos faltantes detectados:")
        for ano, mes in gaps[:10]:  # Mostrar primeiros 10
            print(f"      - {mes:02d}/{ano}")
        if len(gaps) > 10:
            print(f"      ... e mais {len(gaps) - 10} períodos")
    
    return gaps


def exemplo_4_fonte_hibrida():
    """
    Exemplo 4: Fonte Híbrida (Transição)
    =====================================
    
    Demonstra como usar a fonte híbrida que combina snippets (períodos antigos)
    com scraper dinâmico (períodos novos).
    """
    print("\n" + "="*80)
    print("EXEMPLO 4: Fonte Híbrida (Snippets + Scraper)")
    print("="*80)
    
    BASE_URL = "https://www.gov.br/anvisa/pt-br/assuntos/medicamentos/cmed/precos/anos-anteriores/anos-anteriores"
    CACHE_DIR = BASE_DIR.parent.parent / "data" / "cache" / "scraper"
    SNIPPETS_DIR = BASE_DIR / "tools" / "snippets"
    
    hybrid = HybridAnvisaSource(
        base_url=BASE_URL,
        cache_dir=CACHE_DIR,
        snippets_dir=SNIPPETS_DIR,
        cutoff_year=2025  # Snippets até 2024, scraper para 2025+
    )
    
    # Obter dados de 2024 (deve usar snippets)
    print("\n📂 Obtendo dados de 2024 (fonte: snippets)...")
    df_2024 = hybrid.get_links(
        tipo_lista='PMC',
        ano_inicio=2024,
        mes_inicio=1,
        ano_fim=2024,
        mes_fim=12
    )
    print(f"   ✅ {len(df_2024)} meses encontrados")
    if not df_2024.empty:
        print(f"   📊 Fonte: {df_2024['fonte'].value_counts().to_dict()}")
    
    # Obter dados de 2025 (deve usar scraper)
    print("\n🌐 Obtendo dados de 2025 (fonte: scraper dinâmico)...")
    df_2025 = hybrid.get_links(
        tipo_lista='PMC',
        ano_inicio=2025,
        mes_inicio=1,
        ano_fim=2025,
        mes_fim=12
    )
    print(f"   ✅ {len(df_2025)} meses encontrados")
    if not df_2025.empty:
        print(f"   📊 Fonte: {df_2025['fonte'].value_counts().to_dict()}")
    
    # Obter período completo (híbrido)
    print("\n🔄 Obtendo período completo 2023-2025 (híbrido)...")
    df_completo = hybrid.get_links(
        tipo_lista='PMC',
        ano_inicio=2023,
        mes_inicio=1
    )
    print(f"   ✅ {len(df_completo)} meses encontrados")
    if not df_completo.empty:
        print(f"   📊 Fontes: {df_completo['fonte'].value_counts().to_dict()}")
    
    return hybrid


def exemplo_5_validacao_qualidade():
    """
    Exemplo 5: Validação de Qualidade
    ==================================
    
    Demonstra como validar a qualidade da cobertura de dados e gerar
    relatórios detalhados.
    """
    print("\n" + "="*80)
    print("EXEMPLO 5: Validação de Qualidade e Relatórios")
    print("="*80)
    
    BASE_URL = "https://www.gov.br/anvisa/pt-br/assuntos/medicamentos/cmed/precos/anos-anteriores/anos-anteriores"
    CACHE_DIR = BASE_DIR.parent.parent / "data" / "cache" / "scraper"
    SNIPPETS_DIR = BASE_DIR / "tools" / "snippets"
    
    hybrid = HybridAnvisaSource(
        base_url=BASE_URL,
        cache_dir=CACHE_DIR,
        snippets_dir=SNIPPETS_DIR
    )
    
    # Gerar relatório para PMC
    print("\n📋 Gerando relatório de cobertura para PMC (desde 2023)...")
    relatorio_pmc = hybrid.validate_and_report_gaps('PMC', ano_inicio=2023)
    
    print(f"\n📊 RELATÓRIO PMC:")
    print(f"   Período: {relatorio_pmc['periodo_inicio']} a {relatorio_pmc['periodo_fim']}")
    print(f"   Meses esperados: {relatorio_pmc['meses_esperados']}")
    print(f"   Meses encontrados: {relatorio_pmc['meses_encontrados']}")
    print(f"   Cobertura: {relatorio_pmc['cobertura_percentual']}%")
    print(f"   Fontes: {relatorio_pmc['fontes']}")
    
    if relatorio_pmc['gaps']:
        print(f"   ⚠️ Gaps: {len(relatorio_pmc['gaps'])} períodos faltantes")
        for ano, mes in relatorio_pmc['gaps'][:5]:
            print(f"      - {mes:02d}/{ano}")
    else:
        print("   ✅ Sem gaps detectados!")
    
    # Gerar relatório para PMVG
    print("\n📋 Gerando relatório de cobertura para PMVG (desde 2023)...")
    relatorio_pmvg = hybrid.validate_and_report_gaps('PMVG', ano_inicio=2023)
    
    print(f"\n📊 RELATÓRIO PMVG:")
    print(f"   Cobertura: {relatorio_pmvg['cobertura_percentual']}%")
    print(f"   Fontes: {relatorio_pmvg['fontes']}")
    
    return relatorio_pmc, relatorio_pmvg


def exemplo_6_exportacao_catalogo():
    """
    Exemplo 6: Exportação de Catálogo
    ==================================
    
    Demonstra como exportar um catálogo completo de todos os arquivos
    disponíveis para análise externa.
    """
    print("\n" + "="*80)
    print("EXEMPLO 6: Exportação de Catálogo Completo")
    print("="*80)
    
    BASE_URL = "https://www.gov.br/anvisa/pt-br/assuntos/medicamentos/cmed/precos/anos-anteriores/anos-anteriores"
    CACHE_DIR = BASE_DIR.parent.parent / "data" / "cache" / "scraper"
    
    scraper = AnvisaDynamicScraper(base_url=BASE_URL, cache_dir=CACHE_DIR)
    
    # Definir caminho de saída
    output_dir = BASE_DIR.parent.parent / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"catalogo_anvisa_{datetime.now():%Y%m%d}.csv"
    
    # Exportar catálogo
    print(f"\n💾 Exportando catálogo para: {output_path}")
    scraper.export_links_catalog(output_path)
    
    print(f"   ✅ Catálogo exportado com sucesso!")
    print(f"   📁 Arquivo: {output_path}")
    print(f"   📏 Tamanho: {output_path.stat().st_size / 1024:.1f} KB")
    
    return output_path


def main():
    """Executa todos os exemplos."""
    print("\n" + "="*80)
    print("DEMONSTRAÇÃO: Scraper Dinâmico ANVISA")
    print("="*80)
    print("\nEste script demonstra os principais casos de uso do scraper dinâmico.")
    print("Cada exemplo é executado sequencialmente.\n")
    
    try:
        # Exemplo 1
        exemplo_1_descoberta_automatica()
        
        # Exemplo 2
        exemplo_2_deteccao_novos_arquivos()
        
        # Exemplo 3
        exemplo_3_identificacao_gaps()
        
        # Exemplo 4
        exemplo_4_fonte_hibrida()
        
        # Exemplo 5
        exemplo_5_validacao_qualidade()
        
        # Exemplo 6
        exemplo_6_exportacao_catalogo()
        
        print("\n" + "="*80)
        print("✅ Todos os exemplos executados com sucesso!")
        print("="*80)
        
    except Exception as e:
        logger.error(f"❌ Erro durante execução: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
