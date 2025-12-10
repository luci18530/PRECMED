"""
Configurações do Dashboard ANVISA
"""
from pathlib import Path

# Caminhos
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output" / "anvisa"
CACHE_DIR = DATA_DIR / "cache" / "dashboard"

# Arquivo principal da base ANVISA
BASE_ANVISA_FILE = OUTPUT_DIR / "baseANVISA.csv"

# Configurações de cache
CACHE_ENABLED = True
CACHE_TTL_SECONDS = 3600  # 1 hora

# Colunas principais para agregações
COLUNAS_PRECO = [
    "PF 0%", "PF 20%", "PMVG 0%", "PMVG 20%", "PMC 0%", "PMC 20%"
]

COLUNAS_DIMENSOES = [
    "PRINCIPIO ATIVO", "LABORATORIO", "PRODUTO", "CLASSE TERAPEUTICA",
    "GRUPO TERAPEUTICO", "GRUPO ANATOMICO", "STATUS", "REGIME DE PREÇO", "TIPO DE PRODUTO"
]

COLUNAS_IDENTIFICACAO = [
    "CÓDIGO GGREM", "REGISTRO", "EAN 1", "ID_PRODUTO", "ID_PRECO"
]

# Mapeamento de colunas para nomes amigáveis
NOMES_AMIGAVEIS = {
    "PRINCIPIO ATIVO": "Princípio Ativo",
    "LABORATORIO": "Laboratório",
    "PRODUTO": "Produto",
    "CLASSE TERAPEUTICA": "Classe Terapêutica",
    "GRUPO TERAPEUTICO": "Grupo Terapêutico",
    "GRUPO ANATOMICO": "Grupo Anatômico",
    "STATUS": "Status",
    "REGIME DE PREÇO": "Regime",
    "TIPO DE PRODUTO": "Tipo de Produto",
    "PF 0%": "Preço Fábrica (ICMS 0%)",
    "PMVG 0%": "PMVG (ICMS 0%)",
    "PMC 0%": "PMC (ICMS 0%)",
}

# Configurações de exibição
ITENS_POR_PAGINA = 50
MAX_SERIES_GRAFICO = 10
