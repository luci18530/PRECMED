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
    """Une as bases PMC e PMVG por chave temporal."""

    logging.info("[MERGE] Unificando bases PMC + PMVG...")
    pmc_df = pd.read_csv(pmc_path, sep=';', dtype=str)
    pmvg_df = pd.read_csv(pmvg_path, sep=';', dtype=str)

    chaves = cfg.CHAVES_FUSAO
    
    # Selecionar apenas colunas PMC 0% e 20%
    pmc_cols_preferidas = ["PMC 0%", "PMC 20%"]
    
    # Verificar quais colunas existem no DataFrame PMC
    pmc_cols_existentes = [c for c in pmc_cols_preferidas if c in pmc_df.columns]
    
    if not pmc_cols_existentes:
        logging.warning("Colunas PMC 0%/20% não encontradas; fusão seguirá sem valores PMC.")
        pmc_subset = pmc_df[chaves].drop_duplicates(subset=chaves, keep="first")
    else:
        # Manter chaves + colunas filtradas
        cols_to_keep = chaves + pmc_cols_existentes
        pmc_subset = pmc_df[cols_to_keep].drop_duplicates(subset=chaves, keep="first")

    combinado = pmvg_df.merge(pmc_subset, on=chaves, how="left")
    saida = Path(cfg.ARQUIVO_FUSAO_PMC_PMVG)
    saida.parent.mkdir(parents=True, exist_ok=True)
    combinado.to_csv(saida, sep=';', index=False)

    logging.info("[MERGE] Base PMC+PMVG salva em: %s", saida)
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
        pmc_path = resultados["PMC"]["consolidado"]
        pmvg_path = resultados["PMVG"]["consolidado"]
        _merge_universos(pmc_path, pmvg_path)
    else:
        logging.warning("Fusão PMC+PMVG não executada (listas insuficientes).")


if __name__ == "__main__":
    run()
