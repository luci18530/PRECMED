# -*- coding: utf-8 -*-
"""
SCRAPER DINÂMICO E SUSTENTÁVEL PARA ANVISA
==========================================

Este módulo implementa um scraper inteligente que:
1. Detecta automaticamente novos arquivos disponíveis no site da ANVISA
2. Mantém cache de links já processados
3. Identifica períodos faltantes
4. Suporta atualização incremental
5. Não depende de snippets HTML estáticos

Author: Luciano
Date: 2025-11-28
"""

import json
import logging
import re
import time
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Tag

logger = logging.getLogger(__name__)


class AnvisaDynamicScraper:
    """
    Scraper dinâmico e inteligente para o site da ANVISA.
    
    Funcionalidades:
    - Detecção automática de arquivos disponíveis
    - Cache persistente de links conhecidos
    - Identificação de novos períodos
    - Suporte a múltiplos tipos de lista (PMC, PMVG, PF)
    """
    
    # Mapeamento de meses em português para números
    MESES_PT = {
        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'marco': 3,
        'abril': 4, 'maio': 5, 'junho': 6,
        'julho': 7, 'agosto': 8, 'setembro': 9,
        'outubro': 10, 'novembro': 11, 'dezembro': 12
    }
    
    # Padrões de detecção de tipo de lista
    TIPO_PATTERNS = {
        'PMC': [
            'preco maximo ao consumidor',
            'pmc',
            'preço máximo',
            'xls_conformidade_site'
        ],
        'PMVG': [
            'compras publicas',
            'pmvg',
            'governo',
            'xls_conformidade_gov'
        ],
        'PF': [
            'preco fabrica',
            'preço fábrica',
            'pf'
        ]
    }
    
    # Tokens que identificam arquivos de conformidade (não resolução)
    CONFORMIDADE_TOKENS = {
        'xls_conformidade_site',
        'xls_conformidade_gov',
        'xls_conformidade_portal',
        'lista_conformidade'
    }
    
    # Padrões regex para extrair data de URLs
    DATE_PATTERNS = [
        re.compile(r'(\d{4})(\d{2})(\d{2})'),  # YYYYMMDD
        re.compile(r'(\d{4})_(\d{2})_'),        # YYYY_MM_
        re.compile(r'(\d{4})(\d{2})_'),         # YYYYMM_
        re.compile(r'_(\d{4})_(\d{2})'),        # _YYYY_MM
    ]
    
    def __init__(
        self,
        base_url: str,
        cache_dir: Path,
        session: Optional[requests.Session] = None
    ):
        """
        Inicializa o scraper.
        
        Args:
            base_url: URL base do site da ANVISA
            cache_dir: Diretório para armazenar cache de links
            session: Sessão requests personalizada (opcional)
        """
        self.base_url = base_url
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = session or self._create_session()
        
        # Cache em memória
        self._known_links: Dict[str, Set[Tuple[int, int]]] = defaultdict(set)
        self._load_cache()
        
    def _create_session(self) -> requests.Session:
        """Cria uma sessão requests com headers apropriados."""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
        })
        return session
    
    def _load_cache(self) -> None:
        """Carrega cache de links conhecidos do disco."""
        cache_file = self.cache_dir / 'known_links.json'
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for tipo, periodos in data.items():
                        self._known_links[tipo] = {
                            (p['ano'], p['mes']) for p in periodos
                        }
                logger.info(f"Cache carregado: {sum(len(v) for v in self._known_links.values())} links conhecidos")
            except Exception as e:
                logger.warning(f"Erro ao carregar cache: {e}")
    
    def _save_cache(self) -> None:
        """Salva cache de links conhecidos no disco."""
        cache_file = self.cache_dir / 'known_links.json'
        data = {}
        for tipo, periodos in self._known_links.items():
            data[tipo] = [
                {'ano': ano, 'mes': mes}
                for ano, mes in sorted(periodos)
            ]
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Cache salvo em {cache_file}")
        except Exception as e:
            logger.error(f"Erro ao salvar cache: {e}")
    
    def _normalize_text(self, text: str) -> str:
        """Normaliza texto removendo acentos e convertendo para minúsculas."""
        import unicodedata
        nfkd = unicodedata.normalize('NFKD', text)
        return nfkd.encode('ASCII', 'ignore').decode('ASCII').lower()
    
    def _detect_tipo_from_context(self, text: str) -> Optional[str]:
        """
        Detecta o tipo de lista (PMC/PMVG/PF) a partir do contexto textual.
        
        Args:
            text: Texto do contexto (heading, parágrafo, etc.)
            
        Returns:
            Tipo detectado ou None
        """
        normalized = self._normalize_text(text)
        
        for tipo, patterns in self.TIPO_PATTERNS.items():
            if any(pattern in normalized for pattern in patterns):
                return tipo
        
        return None
    
    def _extract_date_from_url(self, url: str) -> Optional[Tuple[int, int]]:
        """
        Extrai ano e mês de uma URL usando padrões regex.
        
        Args:
            url: URL do arquivo
            
        Returns:
            Tupla (ano, mes) ou None se não encontrado
        """
        for pattern in self.DATE_PATTERNS:
            match = pattern.search(url)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    try:
                        ano = int(groups[0])
                        mes = int(groups[1])
                        
                        # Validação básica
                        if 2020 <= ano <= 2030 and 1 <= mes <= 12:
                            return (ano, mes)
                    except (ValueError, IndexError):
                        continue
        
        return None
    
    def _extract_date_from_text(self, text: str) -> Optional[Tuple[int, int]]:
        """
        Extrai ano e mês de texto livre (ex: "abril/23").
        
        Args:
            text: Texto contendo referência a mês/ano
            
        Returns:
            Tupla (ano, mes) ou None se não encontrado
        """
        # Padrão: mes/ano (ex: abril/23, janeiro/2024)
        pattern = re.compile(
            r'\b(' + '|'.join(self.MESES_PT.keys()) + r')\s*/\s*(\d{2,4})\b',
            re.IGNORECASE
        )
        
        match = pattern.search(self._normalize_text(text))
        if match:
            mes_nome = match.group(1)
            ano_str = match.group(2)
            
            mes = self.MESES_PT.get(mes_nome)
            ano = int(ano_str)
            
            # Normalizar ano de 2 dígitos
            if ano < 100:
                ano = 2000 + ano
            
            if mes and 2020 <= ano <= 2030:
                return (ano, mes)
        
        return None
    
    def _is_conformidade_link(self, url: str, link_text: str) -> bool:
        """
        Verifica se um link é de arquivo de conformidade (não resolução).
        
        Args:
            url: URL do link
            link_text: Texto âncora do link
            
        Returns:
            True se for link de conformidade
        """
        url_lower = url.lower()
        text_upper = link_text.upper()
        
        # Ignorar links de resolução
        if '_reso_' in url_lower or 'resolucao' in url_lower:
            return False
        
        # Deve conter XLS no texto
        if 'XLS' not in text_upper and '.xls' not in url_lower:
            return False
        
        # Deve ter algum token de conformidade
        return any(token in url_lower for token in self.CONFORMIDADE_TOKENS)
    
    def scrape_available_files(
        self,
        tipo_lista: Optional[str] = None,
        force_refresh: bool = False
    ) -> pd.DataFrame:
        """
        Raspa o site da ANVISA e retorna todos os arquivos disponíveis.
        
        Args:
            tipo_lista: Filtrar por tipo específico (PMC, PMVG, PF) ou None para todos
            force_refresh: Se True, ignora cache e força nova raspagem
            
        Returns:
            DataFrame com colunas: ano, mes, mes_nome, tipo, url, data_coleta
        """
        logger.info(f"Iniciando raspagem do site ANVISA: {self.base_url}")
        
        try:
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
            html_content = response.content
        except requests.RequestException as e:
            logger.error(f"Erro ao acessar site da ANVISA: {e}")
            raise
        
        soup = BeautifulSoup(html_content, 'html.parser')
        core = soup.find(id='content-core') or soup
        
        dados = []
        ctx_tipo = None
        ctx_date = None
        
        # Percorrer documento identificando contexto e links
        for node in core.descendants:
            # Detectar mudança de contexto (tipo de lista)
            if isinstance(node, Tag) and node.name in {'h2', 'h3', 'h4', 'h5', 'strong'}:
                heading_text = node.get_text(' ', strip=True)
                novo_tipo = self._detect_tipo_from_context(heading_text)
                if novo_tipo:
                    ctx_tipo = novo_tipo
                    logger.debug(f"Contexto detectado: {ctx_tipo}")
            
            # Detectar data em texto livre
            if isinstance(node, NavigableString):
                text = node.strip()
                if text:
                    date = self._extract_date_from_text(text)
                    if date:
                        ctx_date = date
                continue
            
            # Processar links
            if not (isinstance(node, Tag) and node.name == 'a'):
                continue
            
            href = node.get('href', '').strip()
            if not href:
                continue
            
            # Construir URL completa
            url = urljoin(self.base_url, href) if not href.startswith('http') else href
            link_text = node.get_text(' ', strip=True)
            
            # Validar se é link de conformidade
            if not self._is_conformidade_link(url, link_text):
                continue
            
            # Detectar tipo do link (se não tiver contexto)
            link_tipo = ctx_tipo
            if not link_tipo:
                link_tipo = self._detect_tipo_from_context(link_text)
            
            # Filtrar por tipo se especificado
            if tipo_lista and link_tipo and link_tipo != tipo_lista:
                continue
            
            # Extrair data
            date = self._extract_date_from_url(url) or ctx_date
            
            if date:
                ano, mes = date
                mes_nome = list(self.MESES_PT.keys())[mes - 1]
                
                dados.append({
                    'ano': ano,
                    'mes': mes,
                    'mes_nome': mes_nome,
                    'tipo': link_tipo or 'UNKNOWN',
                    'url': url,
                    'data_coleta': datetime.now().isoformat()
                })
        
        # Criar DataFrame e remover duplicatas
        df = pd.DataFrame(dados)
        
        if df.empty:
            logger.warning("Nenhum link encontrado na raspagem")
            return df
        
        # Remover duplicatas (mesmo ano/mes/tipo)
        df = df.drop_duplicates(subset=['ano', 'mes', 'tipo'], keep='first')
        df = df.sort_values(['tipo', 'ano', 'mes']).reset_index(drop=True)
        
        logger.info(f"Raspagem concluída: {len(df)} arquivos encontrados")
        
        # Atualizar cache
        if not force_refresh:
            for _, row in df.iterrows():
                self._known_links[row['tipo']].add((row['ano'], row['mes']))
            self._save_cache()
        
        return df
    
    def find_missing_periods(
        self,
        tipo_lista: str,
        start_year: int = 2020,
        start_month: int = 1
    ) -> List[Tuple[int, int]]:
        """
        Identifica períodos faltantes que deveriam existir mas não foram encontrados.
        
        Args:
            tipo_lista: Tipo da lista (PMC, PMVG, etc.)
            start_year: Ano inicial do período esperado
            start_month: Mês inicial do período esperado
            
        Returns:
            Lista de tuplas (ano, mes) faltantes
        """
        # Raspar para obter períodos disponíveis
        df = self.scrape_available_files(tipo_lista=tipo_lista)
        
        if df.empty:
            logger.warning(f"Nenhum arquivo encontrado para {tipo_lista}")
            return []
        
        # Gerar lista de todos os meses esperados
        hoje = datetime.now()
        inicio = datetime(start_year, start_month, 1)
        
        periodos_esperados = set()
        current = inicio
        while current <= hoje:
            periodos_esperados.add((current.year, current.month))
            # Avançar um mês
            if current.month == 12:
                current = datetime(current.year + 1, 1, 1)
            else:
                current = datetime(current.year, current.month + 1, 1)
        
        # Períodos encontrados
        periodos_encontrados = set(
            (row['ano'], row['mes'])
            for _, row in df[df['tipo'] == tipo_lista].iterrows()
        )
        
        # Calcular diferença
        faltantes = sorted(periodos_esperados - periodos_encontrados)
        
        if faltantes:
            logger.warning(
                f"Encontrados {len(faltantes)} períodos faltantes para {tipo_lista}: "
                f"{faltantes[:5]}{'...' if len(faltantes) > 5 else ''}"
            )
        
        return faltantes
    
    def get_new_files_since_last_run(self, tipo_lista: str) -> pd.DataFrame:
        """
        Retorna apenas arquivos novos desde a última execução (baseado em cache).
        
        Args:
            tipo_lista: Tipo da lista (PMC, PMVG, etc.)
            
        Returns:
            DataFrame com apenas arquivos novos
        """
        # Obter períodos conhecidos do cache
        known_periods = self._known_links.get(tipo_lista, set())
        
        # Raspar site
        df_all = self.scrape_available_files(tipo_lista=tipo_lista)
        
        if df_all.empty:
            return df_all
        
        # Filtrar apenas novos
        df_tipo = df_all[df_all['tipo'] == tipo_lista].copy()
        df_new = df_tipo[
            ~df_tipo.apply(
                lambda row: (row['ano'], row['mes']) in known_periods,
                axis=1
            )
        ]
        
        if not df_new.empty:
            logger.info(f"Encontrados {len(df_new)} novos arquivos para {tipo_lista}")
        else:
            logger.info(f"Nenhum arquivo novo para {tipo_lista}")
        
        return df_new
    
    def export_links_catalog(self, output_path: Path) -> None:
        """
        Exporta catálogo completo de links para arquivo CSV.
        
        Args:
            output_path: Caminho do arquivo de saída
        """
        df = self.scrape_available_files()
        df.to_csv(output_path, sep=';', index=False, encoding='utf-8-sig')
        logger.info(f"Catálogo exportado para {output_path}")


def example_usage():
    """Exemplo de uso do scraper dinâmico."""
    
    # Configuração
    BASE_URL = "https://www.gov.br/anvisa/pt-br/assuntos/medicamentos/cmed/precos/anos-anteriores/anos-anteriores"
    CACHE_DIR = Path("data/cache/scraper")
    
    # Inicializar scraper
    scraper = AnvisaDynamicScraper(base_url=BASE_URL, cache_dir=CACHE_DIR)
    
    # Exemplo 1: Obter todos os arquivos disponíveis
    print("\n=== TODOS OS ARQUIVOS ===")
    df_all = scraper.scrape_available_files()
    print(df_all.head(10))
    
    # Exemplo 2: Obter apenas PMC
    print("\n=== APENAS PMC ===")
    df_pmc = scraper.scrape_available_files(tipo_lista='PMC')
    print(df_pmc.head())
    
    # Exemplo 3: Verificar períodos faltantes
    print("\n=== PERÍODOS FALTANTES ===")
    missing = scraper.find_missing_periods('PMC', start_year=2023, start_month=1)
    print(f"Faltantes: {missing}")
    
    # Exemplo 4: Obter apenas novos arquivos
    print("\n=== ARQUIVOS NOVOS ===")
    df_new = scraper.get_new_files_since_last_run('PMVG')
    print(f"Novos: {len(df_new)}")
    
    # Exemplo 5: Exportar catálogo
    scraper.export_links_catalog(Path("data/catalog_links.csv"))


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    example_usage()
