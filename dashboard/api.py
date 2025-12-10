"""
API FastAPI para o Dashboard ANVISA

Endpoints otimizados para:
- Listagem paginada de produtos
- Busca por texto
- Filtros por dimensões
- Séries temporais de preços
- Agregações e estatísticas
"""
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import date
import pandas as pd

from data_layer import get_data_manager, get_aggregation_engine
from config import CACHE_DIR

app = FastAPI(
    title="ANVISA Dashboard API",
    description="API para consulta de dados de medicamentos ANVISA",
    version="1.0.0"
)

# CORS para permitir acesso do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instâncias dos managers
dm = get_data_manager()
agg = get_aggregation_engine()


# ============================================================
# MODELOS
# ============================================================

class ProdutoResumo(BaseModel):
    codigo_ggrem: str
    produto: str
    substancia: Optional[str]
    laboratorio: Optional[str]
    classe_terapeutica: Optional[str]
    preco_atual: Optional[float]


class EvolucaoPreco(BaseModel):
    data: str
    preco: Optional[float]


class FiltrosDisponiveis(BaseModel):
    substancias: List[str]
    laboratorios: List[str]
    classes_terapeuticas: List[str]
    tipos_produto: List[str]


# ============================================================
# ENDPOINTS - METADADOS
# ============================================================

@app.get("/api/metadata")
async def get_metadata():
    """Retorna metadados do dataset."""
    import json
    meta_file = CACHE_DIR / "metadata.json"
    
    if meta_file.exists():
        with open(meta_file, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # Gerar metadados básicos
    periodos = dm.get_periodos_disponiveis()
    return {
        "total_periodos": len(periodos),
        "periodo_inicio": f"{periodos[0]['ano']}-{periodos[0]['mes']:02d}" if periodos else None,
        "periodo_fim": f"{periodos[-1]['ano']}-{periodos[-1]['mes']:02d}" if periodos else None,
    }


@app.get("/api/periodos")
async def get_periodos():
    """Lista todos os períodos disponíveis."""
    return dm.get_periodos_disponiveis()


@app.get("/api/filtros")
async def get_filtros_disponiveis():
    """Retorna valores disponíveis para filtros."""
    index_dir = CACHE_DIR / "indices"
    
    filtros = {}
    
    # Carregar lookups pré-computados
    for nome, arquivo in [
        ("substancias", "lookup_substancia.parquet"),
        ("laboratorios", "lookup_laboratorio.parquet"),
        ("classes_terapeuticas", "lookup_classe_terapeutica.parquet"),
    ]:
        path = index_dir / arquivo
        if path.exists():
            df = pd.read_parquet(path)
            filtros[nome] = df.iloc[:, 0].tolist()[:500]  # Limitar para performance
        else:
            filtros[nome] = []
    
    return filtros


# ============================================================
# ENDPOINTS - PRODUTOS
# ============================================================

@app.get("/api/produtos")
async def listar_produtos(
    busca: Optional[str] = Query(None, description="Termo de busca"),
    substancia: Optional[str] = Query(None),
    laboratorio: Optional[str] = Query(None),
    classe: Optional[str] = Query(None),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(50, ge=10, le=200),
):
    """Lista produtos com filtros e paginação."""
    index_path = CACHE_DIR / "indices" / "produtos_index.parquet"
    
    if not index_path.exists():
        raise HTTPException(status_code=503, detail="Índice não disponível. Execute preprocess.py primeiro.")
    
    df = pd.read_parquet(index_path)
    
    # Aplicar filtros
    if busca:
        busca_upper = busca.upper()
        df = df[df["busca"].str.contains(busca_upper, na=False)]
    
    if substancia:
        df = df[df["SUBSTÂNCIA"] == substancia]
    
    if laboratorio:
        df = df[df["LABORATÓRIO"] == laboratorio]
    
    if classe:
        df = df[df["CLASSE TERAPÊUTICA"] == classe]
    
    # Paginação
    total = len(df)
    inicio = (pagina - 1) * por_pagina
    fim = inicio + por_pagina
    
    df_pagina = df.iloc[inicio:fim]
    
    return {
        "total": total,
        "pagina": pagina,
        "por_pagina": por_pagina,
        "total_paginas": (total + por_pagina - 1) // por_pagina,
        "produtos": df_pagina.drop(columns=["busca"], errors="ignore").to_dict(orient="records")
    }


@app.get("/api/produtos/{codigo_ggrem}")
async def detalhe_produto(codigo_ggrem: str):
    """Retorna detalhes de um produto específico."""
    periodos = dm.get_periodos_disponiveis()
    if not periodos:
        raise HTTPException(status_code=404, detail="Nenhum dado disponível")
    
    # Carregar período mais recente
    ultimo = periodos[-1]
    df = dm.carregar_periodo(ultimo["ano"], ultimo["mes"])
    
    if df.empty:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    produto = df[df["CÓDIGO GGREM"] == codigo_ggrem]
    if produto.empty:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    return produto.iloc[0].to_dict()


@app.get("/api/produtos/{codigo_ggrem}/evolucao")
async def evolucao_preco_produto(
    codigo_ggrem: str,
    coluna_preco: str = Query("PF 0%", description="Coluna de preço")
):
    """Retorna evolução temporal do preço de um produto."""
    resultado = agg.evolucao_preco_produto(codigo_ggrem, coluna_preco)
    
    if resultado.empty:
        raise HTTPException(status_code=404, detail="Produto não encontrado ou sem histórico")
    
    return {
        "codigo_ggrem": codigo_ggrem,
        "coluna_preco": coluna_preco,
        "dados": resultado.to_dict(orient="records")
    }


# ============================================================
# ENDPOINTS - AGREGAÇÕES
# ============================================================

@app.get("/api/agregacoes/classe-terapeutica")
async def agregacao_classe_terapeutica(
    ano: int = Query(...),
    mes: int = Query(...)
):
    """Agregação por classe terapêutica em um período."""
    resultado = agg.agregacao_por_dimensao("CLASSE TERAPÊUTICA", ano, mes)
    return resultado.head(20).to_dict(orient="records")


@app.get("/api/agregacoes/laboratorio")
async def agregacao_laboratorio(
    ano: int = Query(...),
    mes: int = Query(...)
):
    """Agregação por laboratório em um período."""
    resultado = agg.agregacao_por_dimensao("LABORATÓRIO", ano, mes)
    return resultado.head(20).to_dict(orient="records")


@app.get("/api/agregacoes/estatisticas-preco")
async def estatisticas_preco_temporais():
    """Retorna estatísticas de preço ao longo do tempo."""
    agg_path = CACHE_DIR / "aggregations" / "estatisticas_preco_temporal.parquet"
    
    if not agg_path.exists():
        raise HTTPException(status_code=503, detail="Agregações não disponíveis. Execute preprocess.py primeiro.")
    
    df = pd.read_parquet(agg_path)
    df["data"] = pd.to_datetime(df["ano"].astype(str) + "-" + df["mes"].astype(str).str.zfill(2) + "-01")
    df = df.sort_values("data")
    
    return df.to_dict(orient="records")


# ============================================================
# ENDPOINTS - COMPARATIVOS
# ============================================================

@app.get("/api/comparativo")
async def comparativo_periodos(
    codigo_ggrem: str,
    ano1: int,
    mes1: int,
    ano2: int,
    mes2: int
):
    """Compara preços de um produto entre dois períodos."""
    resultado = agg.comparativo_periodos(
        codigo_ggrem,
        (ano1, mes1),
        (ano2, mes2)
    )
    return resultado


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
async def health_check():
    """Verifica saúde da API."""
    return {"status": "ok", "periodos_disponiveis": len(dm.get_periodos_disponiveis())}
