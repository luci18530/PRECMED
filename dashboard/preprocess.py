"""
Script de pré-processamento para criar dados agregados otimizados.

Fonte: output/anvisa/baseANVISA.csv

Executar este script antes de iniciar o dashboard para:
1. Converter CSV para Parquet (compressão + velocidade)
2. Criar índices e agregações pré-computadas
3. Gerar metadados e estatísticas
"""
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import json
import sys

# Adicionar pasta pai ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dashboard.config import BASE_ANVISA_FILE, CACHE_DIR, COLUNAS_PRECO, COLUNAS_DIMENSOES


def carregar_base_anvisa() -> pd.DataFrame:
    """Carrega a base ANVISA principal."""
    print(f"Carregando {BASE_ANVISA_FILE}...")
    
    if not BASE_ANVISA_FILE.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {BASE_ANVISA_FILE}")
    
    df = pd.read_csv(BASE_ANVISA_FILE, sep="\t", encoding="utf-8", low_memory=False)
    print(f"  Linhas carregadas: {len(df):,}")
    print(f"  Colunas: {len(df.columns)}")
    
    return df


def converter_para_parquet(df: pd.DataFrame):
    """Converte o DataFrame para Parquet otimizado."""
    cache_dir = CACHE_DIR
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    parquet_path = cache_dir / "baseANVISA.parquet"
    
    print(f"\nOtimizando tipos de dados...")
    
    # Otimizar tipos
    for col in COLUNAS_DIMENSOES:
        if col in df.columns:
            df[col] = df[col].astype("category")
            print(f"  [CAT] {col}")
    
    for col in COLUNAS_PRECO:
        if col in df.columns:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.replace(",", ".").str.strip()
            df[col] = pd.to_numeric(df[col], errors="coerce")
            print(f"  [NUM] {col}")
    
    for col in ["VIG_INICIO", "VIG_FIM"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
            print(f"  [DATE] {col}")
    
    print(f"\nSalvando Parquet...")
    df.to_parquet(parquet_path, index=False, compression="snappy")
    
    tamanho_csv = BASE_ANVISA_FILE.stat().st_size / 1024 / 1024
    tamanho_parquet = parquet_path.stat().st_size / 1024 / 1024
    reducao = (1 - tamanho_parquet / tamanho_csv) * 100
    
    print(f"  {tamanho_csv:.1f}MB -> {tamanho_parquet:.1f}MB ({reducao:.0f}% redução)")
    
    return df


def criar_agregacoes_temporais(df: pd.DataFrame):
    """Cria agregações pré-computadas por período."""
    agg_dir = CACHE_DIR / "aggregations"
    agg_dir.mkdir(parents=True, exist_ok=True)
    
    print("\nCriando agregações temporais...")
    
    # Preparar coluna de data
    df["VIG_INICIO"] = pd.to_datetime(df["VIG_INICIO"], errors="coerce")
    df["ano"] = df["VIG_INICIO"].dt.year
    df["mes"] = df["VIG_INICIO"].dt.month
    
    # Estatísticas de preço por período
    print("  Estatísticas de preço...")
    stats = df.groupby(["ano", "mes"]).agg({
        "PF 0%": ["mean", "median", "min", "max", "count"],
        "ID_PRODUTO": "nunique"
    }).reset_index()
    
    stats.columns = ["ano", "mes", "preco_medio", "preco_mediano", "preco_min", "preco_max", "total_registros", "total_produtos"]
    stats = stats.dropna(subset=["ano", "mes"])
    stats.to_parquet(agg_dir / "estatisticas_preco_temporal.parquet", index=False)
    print(f"    Salvo: estatisticas_preco_temporal.parquet ({len(stats)} períodos)")
    
    # Agregação por classe terapêutica
    if "CLASSE TERAPEUTICA" in df.columns:
        print("  Agregação por classe terapêutica...")
        classe_agg = df.groupby(["ano", "mes", "CLASSE TERAPEUTICA"]).size().reset_index(name="quantidade")
        classe_agg = classe_agg.dropna()
        classe_agg.to_parquet(agg_dir / "classe_terapeutica_temporal.parquet", index=False)
        print(f"    Salvo: classe_terapeutica_temporal.parquet ({len(classe_agg)} registros)")
    
    # Agregação por laboratório
    if "LABORATORIO" in df.columns:
        print("  Agregação por laboratório...")
        lab_agg = df.groupby(["ano", "mes", "LABORATORIO"]).size().reset_index(name="quantidade")
        lab_agg = lab_agg.dropna()
        lab_agg.to_parquet(agg_dir / "laboratorio_temporal.parquet", index=False)
        print(f"    Salvo: laboratorio_temporal.parquet ({len(lab_agg)} registros)")
    
    # Agregação por grupo terapêutico
    if "GRUPO TERAPEUTICO" in df.columns:
        print("  Agregação por grupo terapêutico...")
        grupo_agg = df.groupby(["ano", "mes", "GRUPO TERAPEUTICO"]).size().reset_index(name="quantidade")
        grupo_agg = grupo_agg.dropna()
        grupo_agg.to_parquet(agg_dir / "grupo_terapeutico_temporal.parquet", index=False)
        print(f"    Salvo: grupo_terapeutico_temporal.parquet ({len(grupo_agg)} registros)")


def criar_indice_produtos(df: pd.DataFrame):
    """Cria índice de produtos únicos para busca rápida."""
    index_dir = CACHE_DIR / "indices"
    index_dir.mkdir(parents=True, exist_ok=True)
    
    print("\nCriando índice de produtos...")
    
    # Pegar período mais recente para cada produto
    df["VIG_INICIO"] = pd.to_datetime(df["VIG_INICIO"], errors="coerce")
    df_sorted = df.sort_values("VIG_INICIO", ascending=False)
    
    colunas_indice = ["ID_PRODUTO", "PRODUTO", "PRINCIPIO ATIVO", "LABORATORIO", 
                      "CLASSE TERAPEUTICA", "GRUPO TERAPEUTICO", "STATUS", "TIPO DE PRODUTO"]
    colunas_disponiveis = [c for c in colunas_indice if c in df.columns]
    
    produtos = df_sorted.drop_duplicates(subset=["ID_PRODUTO"])[colunas_disponiveis].copy()
    
    # Converter colunas categóricas para string antes de concatenar
    for col in colunas_disponiveis:
        if col in produtos.columns and produtos[col].dtype.name == 'category':
            produtos[col] = produtos[col].astype(str)
    
    # Criar coluna de busca
    produtos["busca"] = ""
    for col in ["PRODUTO", "PRINCIPIO ATIVO", "LABORATORIO"]:
        if col in produtos.columns:
            produtos["busca"] += " " + produtos[col].fillna("").str.upper()
    
    produtos.to_parquet(index_dir / "produtos_index.parquet", index=False)
    print(f"  Salvo: produtos_index.parquet ({len(produtos)} produtos únicos)")
    
    # Criar lookup tables
    for col in ["PRINCIPIO ATIVO", "LABORATORIO", "CLASSE TERAPEUTICA", "GRUPO TERAPEUTICO", "STATUS"]:
        if col in df.columns:
            valores = sorted(df[col].dropna().unique().tolist())
            lookup = pd.DataFrame({col: valores})
            nome_arquivo = col.lower().replace(" ", "_")
            lookup.to_parquet(index_dir / f"lookup_{nome_arquivo}.parquet", index=False)
            print(f"  Salvo: lookup_{nome_arquivo}.parquet ({len(valores)} valores)")


def gerar_metadados(df: pd.DataFrame):
    """Gera arquivo de metadados do dataset."""
    print("\nGerando metadados...")
    
    df["VIG_INICIO"] = pd.to_datetime(df["VIG_INICIO"], errors="coerce")
    
    # Contar períodos
    periodos = df.groupby([df["VIG_INICIO"].dt.year, df["VIG_INICIO"].dt.month]).size()
    lista_periodos = []
    for (ano, mes), count in periodos.items():
        if pd.notna(ano) and pd.notna(mes):
            lista_periodos.append({
                "ano": int(ano),
                "mes": int(mes),
                "registros": int(count)
            })
    
    lista_periodos = sorted(lista_periodos, key=lambda x: (x["ano"], x["mes"]))
    
    metadados = {
        "gerado_em": datetime.now().isoformat(),
        "arquivo_fonte": str(BASE_ANVISA_FILE),
        "total_registros": len(df),
        "total_produtos_unicos": df["ID_PRODUTO"].nunique() if "ID_PRODUTO" in df.columns else 0,
        "total_periodos": len(lista_periodos),
        "periodo_inicio": f"{lista_periodos[0]['ano']}-{lista_periodos[0]['mes']:02d}" if lista_periodos else None,
        "periodo_fim": f"{lista_periodos[-1]['ano']}-{lista_periodos[-1]['mes']:02d}" if lista_periodos else None,
        "colunas": list(df.columns),
        "periodos": lista_periodos
    }
    
    meta_file = CACHE_DIR / "metadata.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadados, f, ensure_ascii=False, indent=2)
    
    print(f"  Total de registros: {metadados['total_registros']:,}")
    print(f"  Produtos únicos: {metadados['total_produtos_unicos']:,}")
    print(f"  Períodos: {metadados['periodo_inicio']} a {metadados['periodo_fim']}")


def main():
    """Executa todo o pré-processamento."""
    print("=" * 60)
    print("PRÉ-PROCESSAMENTO DO DASHBOARD ANVISA")
    print(f"Fonte: {BASE_ANVISA_FILE}")
    print("=" * 60)
    
    inicio = datetime.now()
    
    # Carregar base
    df = carregar_base_anvisa()
    
    # Converter para Parquet
    df = converter_para_parquet(df)
    
    # Criar agregações
    criar_agregacoes_temporais(df.copy())
    
    # Criar índices
    criar_indice_produtos(df.copy())
    
    # Gerar metadados
    gerar_metadados(df)
    
    duracao = datetime.now() - inicio
    print(f"\n{'=' * 60}")
    print(f"Pré-processamento concluído em {duracao.total_seconds():.1f}s")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
