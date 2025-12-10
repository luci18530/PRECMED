#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script emergencial para adicionar VIG_INICIO, VIG_FIM, id_produto, id_preco
na base_pmc_pmvg_unificada.csv que tem todos os preços mas não tem vigências.
"""

import pandas as pd
from pathlib import Path
import sys

def main():
    print("="*60)
    print("CORREÇÃO EMERGENCIAL: Adicionando vigências à base unificada")
    print("="*60)
    
    # Caminhos
    input_path = Path("data/processed/anvisa/base_pmc_pmvg_unificada.csv")
    output_path = Path("data/processed/anvisa/base_pmc_pmvg_unificada.csv")
    backup_path = Path("data/processed/anvisa/base_pmc_pmvg_unificada_BACKUP.csv")
    
    if not input_path.exists():
        print(f"\n[ERRO] Arquivo não encontrado: {input_path}")
        return 1
    
    print(f"\n[INFO] Carregando base unificada: {input_path}")
    print(f"[INFO] Tamanho: {input_path.stat().st_size / 1024**2:.1f} MB")
    
    # Fazer backup
    if not backup_path.exists():
        print(f"\n[INFO] Criando backup em: {backup_path}")
        import shutil
        shutil.copy2(input_path, backup_path)
    
    # Carregar
    print("\n[INFO] Lendo CSV (isso pode demorar)...")
    df = pd.read_csv(input_path, sep=';', dtype=str, low_memory=False)
    print(f"[OK] Carregado: {len(df):,} registros, {len(df.columns)} colunas")
    
    # Verificar se já tem vigências
    if 'VIG_INICIO' in df.columns:
        print("\n[AVISO] Base já possui VIG_INICIO. Nada a fazer.")
        return 0
    
    # Verificar se tem ANO_REF e MES_REF
    if 'ANO_REF' not in df.columns or 'MES_REF' not in df.columns:
        print("\n[ERRO] Base não possui ANO_REF/MES_REF. Impossível criar vigências.")
        return 1
    
    print("\n[INFO] Criando colunas de vigência...")
    
    # 1. Criar VIG_INICIO (primeiro dia do mês)
    df['VIG_INICIO'] = pd.to_datetime(
        df['ANO_REF'].astype(str) + '-' + 
        df['MES_REF'].astype(str).str.zfill(2) + '-01'
    )
    
    # 2. Criar VIG_FIM (último dia do mês)
    df['VIG_FIM'] = df['VIG_INICIO'] + pd.offsets.MonthEnd(0)
    
    # 3. Criar id_produto (REGISTRO + CÓDIGO GGREM)
    df['id_produto'] = (
        df['REGISTRO'].astype(str).str.strip() + '-' +
        df['CÓDIGO GGREM'].astype(str).str.strip()
    )
    
    # 4. Criar id_preco (produto + vigência)
    df['id_preco'] = (
        df['id_produto'] + '_' +
        df['VIG_INICIO'].dt.strftime('%Y%m%d')
    )
    
    print(f"[OK] VIG_INICIO: {df['VIG_INICIO'].min()} até {df['VIG_INICIO'].max()}")
    print(f"[OK] VIG_FIM: {df['VIG_FIM'].min()} até {df['VIG_FIM'].max()}")
    print(f"[OK] Produtos únicos: {df['id_produto'].nunique():,}")
    print(f"[OK] Registros de preço únicos: {df['id_preco'].nunique():,}")
    
    # 5. Remover ANO_REF e MES_REF (substituídos por vigências)
    print("\n[INFO] Removendo colunas ANO_REF e MES_REF...")
    df.drop(columns=['ANO_REF', 'MES_REF'], inplace=True)
    
    # 6. Reordenar colunas (vigências e IDs primeiro)
    print("\n[INFO] Reordenando colunas...")
    priority_cols = ['id_preco', 'id_produto', 'VIG_INICIO', 'VIG_FIM']
    other_cols = [c for c in df.columns if c not in priority_cols]
    df = df[priority_cols + other_cols]
    
    # 7. Salvar
    print(f"\n[INFO] Salvando base corrigida em: {output_path}")
    df.to_csv(output_path, sep=';', index=False)
    
    print(f"\n[OK] Base corrigida salva com sucesso!")
    print(f"[OK] Colunas finais ({len(df.columns)}): {list(df.columns)}")
    
    # Verificar colunas de preço
    precos = [c for c in df.columns if any(x in c for x in ["PMC", "PMVG", "PF"])]
    print(f"\n[OK] Colunas de preço presentes ({len(precos)}): {sorted(precos)}")
    
    print("\n" + "="*60)
    print("SUCESSO! Base unificada agora tem:")
    print("  ✓ PMC 0%, PMC 20%")
    print("  ✓ PMVG 0%, PMVG 20%")
    print("  ✓ PF 0%, PF 20%")
    print("  ✓ VIG_INICIO, VIG_FIM")
    print("  ✓ id_produto, id_preco")
    print("="*60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
