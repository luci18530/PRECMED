#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLI Menu para orquestrar o pipeline PRECMED

Opções:
 - download: Executa downloads da base ANVISA (PMC + PMVG)
 - process: Processa a base unificada (limpeza, padronização, etc.)
 - dashboard: Pré-processa os dados e abre o dashboard (Streamlit)
 - download+process: Executa download seguido do processamento
 - all: Executa tudo (download -> process -> dashboard preprocess)

Uso:
  python cli.py           # menu interativo
  python cli.py --download
  python cli.py --process
  python cli.py --dashboard
  python cli.py --all

"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
import time

PROJECT_ROOT = Path(__file__).resolve().parents[0]

PY = sys.executable or 'python'

# Commands
CMD_DOWNLOAD = [PY, str(PROJECT_ROOT / 'download.py')]
CMD_PROCESS = [PY, str(PROJECT_ROOT / 'pipelines' / 'anvisa_base' / 'scripts' / 'processar_base_anvisa.py')]
CMD_PREPROCESS_DASH = [PY, str(PROJECT_ROOT / 'dashboard' / 'preprocess.py')]
CMD_STREAMLIT = [PY, '-m', 'streamlit', 'run', str(PROJECT_ROOT / 'dashboard' / 'app.py')]


def run_command(cmd, capture=False):
    print(f"\n[CMD] Executando: {' '.join(cmd)}")
    start = time.time()
    try:
        if capture:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(result.stdout)
            print(result.stderr)
        else:
            subprocess.run(cmd, check=True)
        elapsed = time.time() - start
        print(f"[OK] Comando finalizado em {elapsed:.1f}s")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERRO] Comando falhou: {e}")
        if e.stdout:
            print(e.stdout)
        if e.stderr:
            print(e.stderr)
        return False


def do_download():
    print("\n==> Iniciando download (PMC + PMVG)...")
    return run_command(CMD_DOWNLOAD)


def do_process():
    print("\n==> Iniciando processamento (pipeline completo)...")
    return run_command(CMD_PROCESS)


def do_dashboard(preprocess=True, start_streamlit=False):
    print("\n==> Dashboard: preprocesso =", preprocess, "; start_streamlit =", start_streamlit)
    if preprocess:
        ok = run_command(CMD_PREPROCESS_DASH)
        if not ok:
            return False
    if start_streamlit:
        print("\nAbrindo Streamlit (Ctrl+C para parar)...")
        # Running streamlit in the same process will block; run it as subprocess
        return run_command(CMD_STREAMLIT)
    return True


def interactive_menu():
    print("\n== PRECMED - Menu Interativo ==")
    print("Escolha uma opção:")
    print("  1) download (somente)")
    print("  2) process (somente)")
    print("  3) dashboard (preprocess + opcional start streamlit)")
    print("  4) download + process")
    print("  5) all (download -> process -> dashboard preprocess)")
    print("  6) sair")

    while True:
        try:
            choice = int(input("Digite o número da opção e pressione Enter: ").strip())
        except ValueError:
            print("Opção inválida, tente novamente.")
            continue

        if choice == 1:
            do_download()
            break
        elif choice == 2:
            do_process()
            break
        elif choice == 3:
            preprocess = input("Fazer preprocess (conversão para parquet)? [S/n] ") or 'S'
            start_streamlit = input("Abrir streamlit após preprocess? [S/n] ") or 'n'
            do_dashboard(preprocess=(preprocess.lower() != 'n'), start_streamlit=(start_streamlit.lower() == 's'))
            break
        elif choice == 4:
            if do_download():
                do_process()
            break
        elif choice == 5:
            if do_download():
                if do_process():
                    do_dashboard(preprocess=True)
            break
        elif choice == 6:
            print("Saindo.")
            break
        else:
            print("Opção inválida. Informe um número entre 1 e 6.")


def parse_args():
    parser = argparse.ArgumentParser(description="Menu CLI para PRECMED")
    parser.add_argument('--download', action='store_true', help='Executa download PMC + PMVG')
    parser.add_argument('--process', action='store_true', help='Executa processamento da base ANVISA')
    parser.add_argument('--dashboard', nargs='?', const='start', choices=['start', 'preprocess', 'none'], help='Executa dashboard; use "preprocess" para só preprocess; "start" para preprocess + start streamlit')
    parser.add_argument('--all', action='store_true', help='Executa download -> process -> dashboard preprocess')
    parser.add_argument('--no-interactive', action='store_true', help='Não mostrar menu interativo (usado com outras flags)')
    return parser.parse_args()


def main():
    args = parse_args()

    # If no flags and interactive allowed, show menu
    if len(sys.argv) == 1:
        interactive_menu()
        return

    # Non-interactive
    if args.all:
        if not do_download():
            return
        if not do_process():
            return
        do_dashboard(preprocess=True, start_streamlit=False)
        return

    if args.download:
        do_download()

    if args.process:
        do_process()

    if args.dashboard:
        if args.dashboard == 'preprocess':
            do_dashboard(preprocess=True, start_streamlit=False)
        elif args.dashboard == 'start':
            do_dashboard(preprocess=True, start_streamlit=True)
        else:
            do_dashboard(preprocess=False, start_streamlit=False)


if __name__ == '__main__':
    main()
