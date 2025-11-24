# -*- coding: utf-8 -*-
"""
CONFIGURAÇÃO DA BASE ANVISA (CMED)
===================================

Arquivo central de configuração para download e processamento da base de preços
de medicamentos da ANVISA.

IMPORTANTE: Edite este arquivo para alterar períodos de coleta e parâmetros.
"""

from datetime import datetime
from pathlib import Path

# Diretório base do módulo (usado em caminhos relativos)
BASE_DIR = Path(__file__).resolve().parent

# ==============================================================================
# PERÍODO DE COLETA DOS DADOS
# ==============================================================================

# Toggle: usar apenas o mês anterior ou coletar histórico completo
USAR_MES_ANTERIOR = False  # True = apenas mês anterior | False = desde ANO/MES_INICIO

# Data INICIAL do período (quando USAR_MES_ANTERIOR = False)
ANO_INICIO = 2023
MES_INICIO = 1

# Tipo de lista alvo padrão (PMC, PMVG, PF etc.)
TIPO_LISTA = "PMC"

# Listas a serem processadas em sequência quando `download.py` for executado
LISTAS_PARA_PROCESSAR = ["PMC", "PMVG"]

# Data FINAL do período (limitada para testes ao ano de 2025)
hoje = datetime.now()
LIMITE_ANO_TESTE = 2025
if hoje.year > LIMITE_ANO_TESTE:
   ANO_FIM = LIMITE_ANO_TESTE
   MES_FIM = 12
else:
   ANO_FIM = hoje.year
   MES_FIM = hoje.month

# ==============================================================================
# CONFIGURAÇÕES DE DOWNLOAD
# ==============================================================================

# URL base do site da ANVISA para download dos arquivos
URL_ANVISA = "https://www.gov.br/anvisa/pt-br/assuntos/medicamentos/cmed/precos/anos-anteriores/anos-anteriores"

# Quando disponível, usar HTML local pré-selecionado (útil para testes controlados)
USE_LOCAL_HTML_SNIPPETS = True
LOCAL_HTML_SNIPPETS = {
   "PMC": BASE_DIR / "tools" / "snippets" / "pmc",
   "PMVG": BASE_DIR / "tools" / "snippets" / "pmvg",
}

# Número máximo de downloads simultâneos
MAX_DOWNLOAD_WORKERS = 6

# Número máximo de threads para limpeza de arquivos
MAX_CLEANING_THREADS = 8

# ==============================================================================
# CAMINHOS DOS ARQUIVOS
# ==============================================================================

# Pasta onde serão salvos os arquivos .zip baixados da ANVISA
PASTA_DOWNLOADS_BRUTOS = "data/raw"

# Pasta onde serão salvos os arquivos processados
PASTA_ARQUIVOS_LIMPOS = "data/processed"

# Arquivo consolidado temporário (durante o processamento)
ARQUIVO_CONSOLIDADO_TEMP = "data/processed/anvisa/anvisa_pmvg_consolidado_temp.csv"

# Arquivo final com vigências processadas
ARQUIVO_FINAL_VIGENCIAS = "data/processed/anvisa/base_anvisa_precos_vigencias.csv"

# Saída combinada PMC + PMVG (chaves ANO_REF; MES_REF; REGISTRO; CÓDIGO GGREM)
CHAVES_FUSAO = ["ANO_REF", "MES_REF", "REGISTRO", "CÓDIGO GGREM"]
ARQUIVO_FUSAO_PMC_PMVG = "data/processed/anvisa/base_pmc_pmvg_unificada.csv"

# ==============================================================================
# NOTAS DE USO
# ==============================================================================
"""
EXEMPLOS DE CONFIGURAÇÃO:

1. Coletar histórico completo desde 2020:
   USAR_MES_ANTERIOR = False
   ANO_INICIO = 2020
   MES_INICIO = 1

2. Coletar apenas últimos 2 anos:
   USAR_MES_ANTERIOR = False
   ANO_INICIO = 2023
   MES_INICIO = 1

3. Atualização incremental (apenas mês anterior):
   USAR_MES_ANTERIOR = True
   (ANO_INICIO e MES_INICIO serão ignorados)

4. Período específico (ex: 2022 até hoje):
   USAR_MES_ANTERIOR = False
   ANO_INICIO = 2022
   MES_INICIO = 1
"""
