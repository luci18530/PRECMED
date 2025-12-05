# -*- coding: utf-8 -*-
"""
Módulo para limpeza e padronização de dados da Anvisa.
Responsável por padronizar as colunas GGREM e EAN.
"""
import pandas as pd
import sys
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Adicionar src ao path para importar config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import COLUNAS_EAN


def criar_vigencias_de_ano_mes(df):
    """
    Cria colunas VIG_INICIO e VIG_FIM a partir de ANO_REF e MES_REF.
    Também cria id_produto e id_preco para compatibilidade.
    
    Args:
        df (pandas.DataFrame): DataFrame com colunas ANO_REF e MES_REF
        
    Returns:
        pandas.DataFrame: DataFrame com colunas de vigência adicionadas
    """
    print("\n[INFO] Detectado formato ANO_REF/MES_REF (base unificada PMC+PMVG)")
    print("[INFO] Criando colunas de vigência para compatibilidade...")
    
    df = df.copy()
    
    # Criar VIG_INICIO (primeiro dia do mês)
    df['VIG_INICIO'] = pd.to_datetime(
        df['ANO_REF'].astype(str) + '-' + 
        df['MES_REF'].astype(str).str.zfill(2) + '-01'
    )
    
    # Criar VIG_FIM (último dia do mês)
    df['VIG_FIM'] = df['VIG_INICIO'] + pd.offsets.MonthEnd(0)
    
    # Criar id_produto (CODIGO_GGREM serve como identificador único do produto)
    if 'CÓDIGO GGREM' in df.columns:
        df['id_produto'] = df['CÓDIGO GGREM'].astype(str)
    else:
        # Fallback: usar combinação de colunas
        df['id_produto'] = (
            df['REGISTRO'].astype(str) + '_' + 
            df.get('PRODUTO', '').astype(str)
        )
    
    # Criar id_preco (identificador único da linha - produto + vigência)
    df['id_preco'] = (
        df['id_produto'] + '_' + 
        df['VIG_INICIO'].dt.strftime('%Y%m%d')
    )
    
    # Remover colunas ANO_REF e MES_REF (não são mais necessárias após criar vigências)
    df.drop(columns=['ANO_REF', 'MES_REF'], inplace=True)
    
    print(f"[OK] Criadas colunas: VIG_INICIO, VIG_FIM, id_produto, id_preco")
    print(f"[OK] Removidas colunas: ANO_REF, MES_REF (substituídas por VIG_INICIO/VIG_FIM)")
    print(f"[OK] Período coberto: {df['VIG_INICIO'].min()} até {df['VIG_FIM'].max()}")
    
    return df

def padronizar_codigo_ggrem(df):
    """
    Padroniza a coluna 'CÓDIGO GGREM' removendo caracteres não numéricos.
    
    Args:
        df (pandas.DataFrame): DataFrame com a coluna 'CÓDIGO GGREM'
        
    Returns:
        pandas.DataFrame: DataFrame com a coluna 'CÓDIGO GGREM' padronizada
    """
    print("Padronizando 'CÓDIGO GGREM'...")
    
    if 'CÓDIGO GGREM' in df.columns:
        df['CÓDIGO GGREM'] = (
            df['CÓDIGO GGREM']
            .astype(str)
            .str.strip()
            .replace({'nan': None, 'None': None, '': None})
            .str.replace(r'\.0$', '', regex=True)
            .str.replace(r'[^0-9]', '', regex=True)
        )
        print("[OK] 'CODIGO GGREM' padronizado com sucesso.")
    else:
        print("[AVISO] Coluna 'CODIGO GGREM' nao encontrada.")
    
    return df

def padronizar_colunas_ean(df):
    """
    Padroniza as colunas EAN (EAN 1, EAN 2, EAN 3) removendo caracteres não numéricos.
    
    Args:
        df (pandas.DataFrame): DataFrame com as colunas EAN
        
    Returns:
        pandas.DataFrame: DataFrame com as colunas EAN padronizadas
    """
    print("Padronizando colunas EAN...")
    
    for col in COLUNAS_EAN:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.strip()
                .replace({'nan': '', 'None': '', '<NA>': '', '-': ''})
                .str.replace(r'\.0$', '', regex=True)
                .str.replace(r'[^0-9]', '', regex=True)
            )
        else:
            print(f"[AVISO] Coluna '{col}' nao encontrada.")
    
    print("[OK] Colunas EAN padronizadas com sucesso.")
    return df

def limpar_padronizar_dados(df):
    """
    Executa todas as etapas de limpeza e padronização dos dados.
    
    Args:
        df (pandas.DataFrame): DataFrame original
        
    Returns:
        pandas.DataFrame: DataFrame limpo e padronizado
    """
    print("=" * 80)
    print("INICIANDO LIMPEZA E PADRONIZAÇÃO DOS DADOS")
    print("=" * 80)
    
    # Fazer uma cópia para não modificar o original
    df_limpo = df.copy()
    
    # Se tiver ANO_REF/MES_REF em vez de VIG_INICIO/VIG_FIM, criar as colunas
    if 'ANO_REF' in df_limpo.columns and 'VIG_INICIO' not in df_limpo.columns:
        df_limpo = criar_vigencias_de_ano_mes(df_limpo)
    
    # Padronizar GGREM
    df_limpo = padronizar_codigo_ggrem(df_limpo)
    
    # Padronizar EAN
    df_limpo = padronizar_colunas_ean(df_limpo)
    
    print("\n[OK] Limpeza e padronizacao concluida!")
    print("Amostra das colunas apos a limpeza:")
    
    # Mostrar amostra das colunas limpas
    colunas_para_mostrar = ['CÓDIGO GGREM'] + [col for col in COLUNAS_EAN if col in df_limpo.columns]
    if colunas_para_mostrar:
        print(df_limpo[colunas_para_mostrar].head())
    
    return df_limpo

if __name__ == "__main__":
    # Exemplo de uso (para testes)
    print("Este módulo deve ser importado e usado em conjunto com outros módulos.")
    print("Para executar o pipeline completo, use o arquivo 'processar_dados.py'.")