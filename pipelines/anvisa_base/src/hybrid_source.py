# -*- coding: utf-8 -*-
"""
INTEGRAÇÃO DO SCRAPER DINÂMICO COM PIPELINE EXISTENTE
======================================================

Este módulo integra o novo scraper dinâmico com o pipeline de download existente,
permitindo transição gradual dos snippets estáticos para scraping automático.

Author: Luciano
Date: 2025-11-28
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import pandas as pd

# Importar scraper dinâmico
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

from dynamic_scraper import AnvisaDynamicScraper

logger = logging.getLogger(__name__)


class HybridAnvisaSource:
    """
    Fonte híbrida de links da ANVISA que combina:
    1. Snippets HTML estáticos (legado, para períodos conhecidos)
    2. Scraper dinâmico (para novos períodos e validação)
    
    Estratégia de transição:
    - Usa snippets para períodos até 2024
    - Usa scraper dinâmico para 2025+
    - Valida ambos e detecta inconsistências
    """
    
    def __init__(
        self,
        base_url: str,
        cache_dir: Path,
        snippets_dir: Optional[Path] = None,
        cutoff_year: int = 2025
    ):
        """
        Inicializa fonte híbrida.
        
        Args:
            base_url: URL base do site ANVISA
            cache_dir: Diretório de cache
            snippets_dir: Diretório com snippets HTML (opcional)
            cutoff_year: Ano a partir do qual usa apenas scraper dinâmico
        """
        self.base_url = base_url
        self.cache_dir = Path(cache_dir)
        self.snippets_dir = Path(snippets_dir) if snippets_dir else None
        self.cutoff_year = cutoff_year
        
        # Inicializar scraper dinâmico
        self.scraper = AnvisaDynamicScraper(
            base_url=base_url,
            cache_dir=cache_dir
        )
        
        logger.info(
            f"HybridSource inicializado - "
            f"Snippets até {cutoff_year-1}, Scraper para {cutoff_year}+"
        )
    
    def _load_snippet_html(self, tipo: str, year: int) -> Optional[str]:
        """Carrega snippet HTML para tipo e ano específicos."""
        if not self.snippets_dir:
            return None
        
        snippet_path = self.snippets_dir / tipo.lower() / f"{year}.html"
        
        if snippet_path.exists():
            try:
                with open(snippet_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Erro ao ler snippet {snippet_path}: {e}")
        
        return None
    
    def _parse_snippet_html(
        self,
        html_content: str,
        tipo: str,
        year: int
    ) -> pd.DataFrame:
        """
        Parseia snippet HTML estático (compatível com formato existente).
        
        Args:
            html_content: Conteúdo HTML do snippet
            tipo: Tipo da lista (PMC/PMVG)
            year: Ano do snippet
            
        Returns:
            DataFrame com links extraídos
        """
        from bs4 import BeautifulSoup
        import re
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        meses_map = {
            'janeiro': 1, 'fevereiro': 2, 'março': 3, 'marco': 3,
            'abril': 4, 'maio': 5, 'junho': 6,
            'julho': 7, 'agosto': 8, 'setembro': 9,
            'outubro': 10, 'novembro': 11, 'dezembro': 12
        }
        
        # Padrão: mes/ano
        pattern = re.compile(
            r'\b(' + '|'.join(meses_map.keys()) + r')\s*/\s*(\d{2,4})',
            re.IGNORECASE
        )
        
        dados = []
        
        # Encontrar todos os links
        for link in soup.find_all('a', href=True):
            href = link.get('href', '').strip()
            text = link.get_text(' ', strip=True)
            
            # Pular links de resolução
            if '_reso_' in href.lower() or 'resolucao' in href.lower():
                continue
            
            # Deve ser XLS
            if not ('xls' in text.upper() or '.xls' in href.lower()):
                continue
            
            # Buscar contexto de data - procurar no texto completo do parágrafo
            # que contém o link, não apenas no parent imediato
            current = link
            context = text
            
            # Subir na árvore até encontrar um elemento com texto significativo
            for _ in range(5):  # Subir até 5 níveis
                if current.parent:
                    current = current.parent
                    parent_text = current.get_text(' ', strip=True)
                    if len(parent_text) > len(context):
                        context = parent_text
                    # Se já temos um texto grande o suficiente, continuar subindo
                    # para pegar o máximo de contexto possível
                    if len(context) > 200:
                        break
                else:
                    break
            
            match = pattern.search(context.lower())
            if match:
                mes_nome = match.group(1).replace('ç', 'c')
                mes = meses_map.get(mes_nome)
                ano_str = match.group(2)
                ano = int(ano_str) if len(ano_str) == 4 else 2000 + int(ano_str)
                
                if mes and ano:
                    dados.append({
                        'ano': ano,
                        'mes': mes,
                        'mes_nome': mes_nome,
                        'tipo': tipo,
                        'url': href,
                        'fonte': 'snippet'
                    })
        
        df = pd.DataFrame(dados)
        if not df.empty:
            df = df.drop_duplicates(subset=['ano', 'mes'], keep='first')
            df = df.sort_values(['ano', 'mes']).reset_index(drop=True)
        
        return df
    
    def get_links(
        self,
        tipo_lista: str,
        ano_inicio: int = 2020,
        mes_inicio: int = 1,
        ano_fim: Optional[int] = None,
        mes_fim: Optional[int] = None,
        prefer_dynamic: bool = False
    ) -> pd.DataFrame:
        """
        Obtém links usando estratégia híbrida.
        
        Args:
            tipo_lista: Tipo da lista (PMC, PMVG, etc.)
            ano_inicio: Ano inicial
            mes_inicio: Mês inicial
            ano_fim: Ano final (None = hoje)
            mes_fim: Mês final (None = mês atual)
            prefer_dynamic: Se True, usa apenas scraper dinâmico
            
        Returns:
            DataFrame consolidado de links
        """
        if ano_fim is None:
            hoje = datetime.now()
            ano_fim = hoje.year
            mes_fim = mes_fim or hoje.month
        
        logger.info(
            f"Obtendo links {tipo_lista}: "
            f"{mes_inicio:02d}/{ano_inicio} até {mes_fim:02d}/{ano_fim}"
        )
        
        dfs = []
        
        # Estratégia 1: Usar snippets para anos antigos (se disponíveis)
        if not prefer_dynamic and self.snippets_dir:
            for ano in range(ano_inicio, min(self.cutoff_year, ano_fim + 1)):
                html = self._load_snippet_html(tipo_lista, ano)
                if html:
                    logger.info(f"Snippet carregado: {ano}.html")
                    df_snippet = self._parse_snippet_html(html, tipo_lista, ano)
                    if not df_snippet.empty:
                        dfs.append(df_snippet)
                        logger.info(f"Snippet {tipo_lista}/{ano}: {len(df_snippet)} links extraídos")
                    else:
                        logger.warning(f"Snippet {tipo_lista}/{ano}: NENHUM link extraído!")
                else:
                    logger.warning(f"Snippet {tipo_lista}/{ano}.html NÃO encontrado")
        
        # Estratégia 2: Usar scraper dinâmico
        # (sempre para anos recentes, ou para tudo se prefer_dynamic=True)
        use_scraper_from = ano_inicio if prefer_dynamic else self.cutoff_year
        
        if ano_fim >= use_scraper_from:
            logger.info(f"Usando scraper dinâmico para {use_scraper_from}+")
            df_dynamic = self.scraper.scrape_available_files(tipo_lista=tipo_lista)
            
            if not df_dynamic.empty:
                # Filtrar por período
                df_dynamic = df_dynamic[
                    ((df_dynamic['ano'] > use_scraper_from) |
                     ((df_dynamic['ano'] == use_scraper_from) & (df_dynamic['mes'] >= mes_inicio)))
                    &
                    ((df_dynamic['ano'] < ano_fim) |
                     ((df_dynamic['ano'] == ano_fim) & (df_dynamic['mes'] <= mes_fim)))
                ]
                
                if not df_dynamic.empty:
                    df_dynamic['fonte'] = 'scraper'
                    dfs.append(df_dynamic)
                    logger.debug(f"Scraper {tipo_lista}: {len(df_dynamic)} links")
        
        # Consolidar resultados
        if not dfs:
            logger.warning(f"Nenhum link encontrado para {tipo_lista}")
            return pd.DataFrame()
        
        df_final = pd.concat(dfs, ignore_index=True)
        
        # Remover duplicatas (preferir snippet em caso de conflito, pois é mais estável)
        df_final = df_final.sort_values(['ano', 'mes', 'fonte'], ascending=[True, True, True])
        df_final = df_final.drop_duplicates(subset=['ano', 'mes'], keep='first')
        df_final = df_final.sort_values(['ano', 'mes']).reset_index(drop=True)
        
        logger.info(
            f"Links consolidados para {tipo_lista}: {len(df_final)} "
            f"(snippet: {(df_final['fonte']=='snippet').sum()}, "
            f"scraper: {(df_final['fonte']=='scraper').sum()})"
        )
        
        return df_final
    
    def validate_and_report_gaps(
        self,
        tipo_lista: str,
        ano_inicio: int = 2020,
        mes_inicio: int = 1
    ) -> Dict:
        """
        Valida cobertura e gera relatório de períodos faltantes.
        
        Returns:
            Dicionário com estatísticas e gaps
        """
        df = self.get_links(tipo_lista, ano_inicio, mes_inicio)
        
        # Calcular estatísticas
        hoje = datetime.now()
        inicio = datetime(ano_inicio, mes_inicio, 1)
        
        meses_esperados = 0
        current = inicio
        while current <= hoje:
            meses_esperados += 1
            if current.month == 12:
                current = datetime(current.year + 1, 1, 1)
            else:
                current = datetime(current.year, current.month + 1, 1)
        
        meses_encontrados = len(df)
        cobertura_pct = (meses_encontrados / meses_esperados * 100) if meses_esperados > 0 else 0
        
        # Identificar gaps
        periodos_encontrados = set((row['ano'], row['mes']) for _, row in df.iterrows())
        gaps = []
        
        current = inicio
        while current <= hoje:
            if (current.year, current.month) not in periodos_encontrados:
                gaps.append((current.year, current.month))
            
            if current.month == 12:
                current = datetime(current.year + 1, 1, 1)
            else:
                current = datetime(current.year, current.month + 1, 1)
        
        relatorio = {
            'tipo': tipo_lista,
            'periodo_inicio': f"{mes_inicio:02d}/{ano_inicio}",
            'periodo_fim': f"{hoje.month:02d}/{hoje.year}",
            'meses_esperados': meses_esperados,
            'meses_encontrados': meses_encontrados,
            'cobertura_percentual': round(cobertura_pct, 2),
            'gaps': gaps,
            'fontes': df['fonte'].value_counts().to_dict() if not df.empty else {}
        }
        
        logger.info(
            f"Relatório {tipo_lista}: {meses_encontrados}/{meses_esperados} meses "
            f"({cobertura_pct:.1f}% cobertura), {len(gaps)} gaps"
        )
        
        return relatorio


def migrate_to_dynamic_scraper():
    """
    Script de migração que valida e compara snippets vs scraper dinâmico.
    Útil para validar a transição.
    """
    BASE_URL = "https://www.gov.br/anvisa/pt-br/assuntos/medicamentos/cmed/precos/anos-anteriores/anos-anteriores"
    BASE_DIR = Path(__file__).resolve().parents[1]
    CACHE_DIR = BASE_DIR / "data" / "cache" / "scraper"
    SNIPPETS_DIR = BASE_DIR / "tools" / "snippets"
    
    hybrid = HybridAnvisaSource(
        base_url=BASE_URL,
        cache_dir=CACHE_DIR,
        snippets_dir=SNIPPETS_DIR,
        cutoff_year=2025
    )
    
    print("\n" + "="*80)
    print("VALIDAÇÃO: SNIPPETS vs SCRAPER DINÂMICO")
    print("="*80)
    
    for tipo in ['PMC', 'PMVG']:
        print(f"\n>>> {tipo}")
        
        # Comparar 2024 (deve estar em snippets)
        print("\n--- 2024 (Snippets) ---")
        df_2024_snippet = hybrid.get_links(
            tipo, ano_inicio=2024, mes_inicio=1,
            ano_fim=2024, mes_fim=12, prefer_dynamic=False
        )
        print(f"Encontrados: {len(df_2024_snippet)} meses")
        if not df_2024_snippet.empty:
            print(df_2024_snippet[['ano', 'mes', 'fonte']].to_string(index=False))
        
        # Comparar 2025 (deve usar scraper)
        print("\n--- 2025 (Scraper Dinâmico) ---")
        df_2025_scraper = hybrid.get_links(
            tipo, ano_inicio=2025, mes_inicio=1,
            ano_fim=2025, mes_fim=12, prefer_dynamic=True
        )
        print(f"Encontrados: {len(df_2025_scraper)} meses")
        if not df_2025_scraper.empty:
            print(df_2025_scraper[['ano', 'mes', 'fonte']].to_string(index=False))
        
        # Validar 2024 com scraper (verificar consistência)
        print("\n--- Validação 2024 (Scraper) ---")
        df_2024_scraper = hybrid.get_links(
            tipo, ano_inicio=2024, mes_inicio=1,
            ano_fim=2024, mes_fim=12, prefer_dynamic=True
        )
        
        if len(df_2024_snippet) == len(df_2024_scraper):
            print("✓ Contagem consistente entre snippet e scraper")
        else:
            print(f"⚠ Divergência: Snippet={len(df_2024_snippet)}, Scraper={len(df_2024_scraper)}")
        
        # Relatório de cobertura completa
        print("\n--- Cobertura Completa (2023-2025) ---")
        relatorio = hybrid.validate_and_report_gaps(tipo, ano_inicio=2023, mes_inicio=1)
        print(f"Cobertura: {relatorio['cobertura_percentual']}%")
        print(f"Fontes: {relatorio['fontes']}")
        if relatorio['gaps']:
            print(f"Gaps detectados: {relatorio['gaps'][:10]}{'...' if len(relatorio['gaps']) > 10 else ''}")


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    migrate_to_dynamic_scraper()
