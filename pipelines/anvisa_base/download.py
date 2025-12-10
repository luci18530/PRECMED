#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Orquestrador de downloads PMC + PMVG seguindo o README do projeto."""

import os
import sys
import shutil
import logging
from pathlib import Path

import pandas as pd

# Assegura acesso aos módulos da pipeline (scripts + src auxiliares)
BASE_DIR = os.path.dirname(__file__)
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")
SRC_DIR = os.path.join(BASE_DIR, "src")

for path in (BASE_DIR, SCRIPTS_DIR, SRC_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)

import config_anvisa as cfg
from scripts.baixar import main as _baixar_main


def _snapshot_outputs(lista: str) -> dict:
    """Copia arquivos consolidados para diretório específico da lista."""

    lista_slug = lista.lower()
    destino = Path(cfg.PASTA_ARQUIVOS_LIMPOS) / lista_slug
    destino.mkdir(parents=True, exist_ok=True)

    consolidado_src = Path(cfg.ARQUIVO_CONSOLIDADO_TEMP)
    vigencias_src = Path(cfg.ARQUIVO_FINAL_VIGENCIAS)

    consolidado_dst = destino / "consolidado.csv"
    vigencias_dst = destino / "vigencias.csv"

    shutil.copy2(consolidado_src, consolidado_dst)
    shutil.copy2(vigencias_src, vigencias_dst)

    logging.info("[SNAPSHOT] %s => %s", lista, consolidado_dst)
    return {"consolidado": consolidado_dst, "vigencias": vigencias_dst}


def _merge_universos(pmc_path: Path, pmvg_path: Path) -> Path:
    """Une as bases PMC e PMVG (com vigências) por chave id_produto + VIG_INICIO."""

    logging.info("[MERGE] Unificando bases PMC + PMVG (com vigências)...")
    pmc_df = pd.read_csv(pmc_path, sep=';', dtype=str)
    pmvg_df = pd.read_csv(pmvg_path, sep=';', dtype=str)
    
    # DEBUG: Mostrar colunas disponíveis
    print(f"\n[DEBUG] Colunas PMC ({len(pmc_df.columns)}): {list(pmc_df.columns)[:15]}...")
    print(f"[DEBUG] Colunas PMVG ({len(pmvg_df.columns)}): {list(pmvg_df.columns)[:15]}...")
    print(f"[DEBUG] Linhas PMC: {len(pmc_df):,} | Linhas PMVG: {len(pmvg_df):,}")

    # Verificar se temos VIG_INICIO e id_produto (bases processadas)
    if 'VIG_INICIO' not in pmc_df.columns or 'id_produto' not in pmc_df.columns:
        logging.error("[ERRO] Base PMC não possui VIG_INICIO/id_produto. Use arquivo 'vigencias.csv'.")
        return None
    
    if 'VIG_INICIO' not in pmvg_df.columns or 'id_produto' not in pmvg_df.columns:
        logging.error("[ERRO] Base PMVG não possui VIG_INICIO/id_produto. Use arquivo 'vigencias.csv'.")
        return None

    # Chaves de fusão: id_produto + VIG_INICIO (identifica mesmo produto no mesmo período)
    chaves = ["id_produto", "VIG_INICIO"]
    print(f"[DEBUG] Chaves de fusão: {chaves}")
    
    # Verificar se chaves existem em ambos
    missing_pmc = [c for c in chaves if c not in pmc_df.columns]
    missing_pmvg = [c for c in chaves if c not in pmvg_df.columns]
    if missing_pmc:
        logging.error(f"Chaves faltando no PMC: {missing_pmc}")
        return None
    if missing_pmvg:
        logging.error(f"Chaves faltando no PMVG: {missing_pmvg}")
        return None
    
    # Selecionar apenas colunas PMC 0% e 20% do PMC
    pmc_cols_preferidas = ["PMC 0%", "PMC 20%"]
    pmc_cols_existentes = [c for c in pmc_cols_preferidas if c in pmc_df.columns]
    print(f"[DEBUG] Colunas PMC encontradas: {pmc_cols_existentes}")
    
    if not pmc_cols_existentes:
        logging.warning("Colunas PMC 0%/20% não encontradas; fusão seguirá sem valores PMC.")
        pmc_subset = pmc_df[chaves].drop_duplicates(subset=chaves, keep="first")
    else:
        cols_to_keep = chaves + pmc_cols_existentes
        pmc_subset = pmc_df[cols_to_keep].drop_duplicates(subset=chaves, keep="first")
    
    # Remover colunas PMC existentes do PMVG para evitar duplicação (_x, _y)
    pmvg_cols_pmc = [c for c in pmvg_df.columns if c.startswith("PMC")]
    if pmvg_cols_pmc:
        print(f"[DEBUG] Removendo colunas PMC do PMVG: {pmvg_cols_pmc}")
        pmvg_df = pmvg_df.drop(columns=pmvg_cols_pmc)

    # Merge - PMVG (base) LEFT JOIN PMC (adiciona colunas PMC)
    combinado = pmvg_df.merge(pmc_subset, on=chaves, how="left")
    
    print(f"[DEBUG] Colunas resultado ({len(combinado.columns)}): {list(combinado.columns)}")
    print(f"[DEBUG] Linhas resultado: {len(combinado):,}")
    
    # Verificar colunas finais de preço
    precos_final = [c for c in combinado.columns if any(x in c for x in ["PMC", "PMVG", "PF"])]
    print(f"[DEBUG] Colunas de preço finais: {sorted(precos_final)}")
    
    saida = Path(cfg.ARQUIVO_FUSAO_PMC_PMVG)
    saida.parent.mkdir(parents=True, exist_ok=True)
    combinado.to_csv(saida, sep=';', index=False)

    logging.info("[MERGE] Base PMC+PMVG+VIGENCIAS salva em: %s", saida)
    return saida


def _run_single(lista: str) -> dict:
    lista_upper = lista.strip().upper()
    cfg.TIPO_LISTA = lista_upper
    logging.info("==============================")
    logging.info("Processando lista: %s", lista_upper)
    logging.info("==============================")
    _baixar_main()
    return _snapshot_outputs(lista_upper)


def run() -> None:
    """Executa downloads PMC e PMVG e gera base unificada."""

    listas = cfg.LISTAS_PARA_PROCESSAR or [cfg.TIPO_LISTA]
    resultados = {}

    for lista in listas:
        resultados[lista.upper()] = _run_single(lista)

    if {"PMC", "PMVG"}.issubset(resultados.keys()):
        # Usar arquivo de vigências que tem VIG_INICIO/VIG_FIM/id_produto calculados
        pmc_path = resultados["PMC"]["vigencias"]
        pmvg_path = resultados["PMVG"]["vigencias"]
        _merge_universos(pmc_path, pmvg_path)
    else:
        logging.warning("Fusão PMC+PMVG não executada (listas insuficientes).")


if __name__ == "__main__":
    run()
