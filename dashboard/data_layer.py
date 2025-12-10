"""
Camada de Dados - Carregamento e Cache otimizado para o Dashboard ANVISA

Fonte: output/anvisa/baseANVISA.csv

Estratégias de otimização:
1. Dados em Parquet (colunar, comprimido)
2. Cache em memória
3. Índices otimizados para filtros comuns
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

from .config import BASE_ANVISA_FILE, CACHE_DIR, COLUNAS_PRECO, COLUNAS_DIMENSOES


class DataManager:
    """Gerenciador de dados com cache e otimizações."""
    
    def __init__(self):
        self.cache_dir = CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._df: Optional[pd.DataFrame] = None
        self._metadata: Optional[Dict] = None
    
    def carregar_base(self, force_reload: bool = False) -> pd.DataFrame:
        """Carrega a base ANVISA completa com cache."""
        cache_parquet = self.cache_dir / "baseANVISA.parquet"
        
        if not force_reload and cache_parquet.exists():
            if cache_parquet.stat().st_mtime > BASE_ANVISA_FILE.stat().st_mtime:
                if self._df is None:
                    print(f"Carregando cache de {cache_parquet}...")
                    self._df = pd.read_parquet(cache_parquet)
                return self._df
        
        print(f"Carregando base ANVISA de {BASE_ANVISA_FILE}...")
        df = pd.read_csv(BASE_ANVISA_FILE, sep="\t", encoding="utf-8", low_memory=False)
        
        df = self._otimizar_tipos(df)
        
        df.to_parquet(cache_parquet, index=False)
        print(f"Cache salvo em {cache_parquet}")
        
        self._df = df
        return df
    
    def get_periodos_disponiveis(self) -> List[Dict[str, Any]]:
        """Retorna lista de períodos disponíveis (ano, mês)."""
        df = self.carregar_base()
        
        if "VIG_INICIO" not in df.columns:
            return []
        
        df_temp = df.copy()
        df_temp["VIG_INICIO"] = pd.to_datetime(df_temp["VIG_INICIO"], errors="coerce")
        periodos = df_temp.groupby([df_temp["VIG_INICIO"].dt.year, df_temp["VIG_INICIO"].dt.month]).size()
        
        resultado = []
        for (ano, mes), count in periodos.items():
            if pd.notna(ano) and pd.notna(mes):
                resultado.append({
                    "ano": int(ano),
                    "mes": int(mes),
                    "registros": int(count)
                })
        
        return sorted(resultado, key=lambda x: (x["ano"], x["mes"]))
    
    def carregar_periodo(self, ano: int, mes: int) -> pd.DataFrame:
        """Carrega dados de um período específico."""
        df = self.carregar_base()
        
        if "VIG_INICIO" not in df.columns:
            return pd.DataFrame()
        
        df_temp = df.copy()
        df_temp["VIG_INICIO"] = pd.to_datetime(df_temp["VIG_INICIO"], errors="coerce")
        mask = (df_temp["VIG_INICIO"].dt.year == ano) & (df_temp["VIG_INICIO"].dt.month == mes)
        
        return df[mask].copy()
    
    def carregar_range(self, ano_inicio: int, mes_inicio: int, 
                       ano_fim: int, mes_fim: int) -> pd.DataFrame:
        """Carrega dados de um range de períodos."""
        df = self.carregar_base()
        
        if "VIG_INICIO" not in df.columns:
            return pd.DataFrame()
        
        df_temp = df.copy()
        df_temp["VIG_INICIO"] = pd.to_datetime(df_temp["VIG_INICIO"], errors="coerce")
        
        data_inicio = pd.Timestamp(ano_inicio, mes_inicio, 1)
        data_fim = pd.Timestamp(ano_fim, mes_fim, 28)
        
        mask = (df_temp["VIG_INICIO"] >= data_inicio) & (df_temp["VIG_INICIO"] <= data_fim)
        
        return df[mask].copy()
    
    def _otimizar_tipos(self, df: pd.DataFrame) -> pd.DataFrame:
        """Otimiza tipos de dados para menor uso de memória."""
        for col in COLUNAS_DIMENSOES:
            if col in df.columns:
                df[col] = df[col].astype("category")
        
        for col in COLUNAS_PRECO:
            if col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].astype(str).str.replace(",", ".").str.strip()
                df[col] = pd.to_numeric(df[col], errors="coerce")
        
        for col in ["VIG_INICIO", "VIG_FIM"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        
        return df
    
    def get_metadata(self) -> Dict[str, Any]:
        """Retorna metadados do dataset."""
        if self._metadata is not None:
            return self._metadata
        
        df = self.carregar_base()
        periodos = self.get_periodos_disponiveis()
        
        self._metadata = {
            "total_registros": len(df),
            "total_produtos_unicos": df["ID_PRODUTO"].nunique() if "ID_PRODUTO" in df.columns else 0,
            "total_periodos": len(periodos),
            "periodo_inicio": f"{periodos[0]['ano']}-{periodos[0]['mes']:02d}" if periodos else None,
            "periodo_fim": f"{periodos[-1]['ano']}-{periodos[-1]['mes']:02d}" if periodos else None,
            "colunas": list(df.columns),
            "atualizado_em": datetime.now().isoformat()
        }
        
        return self._metadata
    
    def limpar_cache(self):
        """Limpa o cache em memória e no disco."""
        self._df = None
        self._metadata = None
        for f in self.cache_dir.glob("*.parquet"):
            f.unlink()


class AggregationEngine:
    """Motor de agregações para queries rápidas."""
    
    def __init__(self, data_manager: DataManager):
        self.dm = data_manager
        self.cache_dir = CACHE_DIR / "aggregations"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def evolucao_preco_produto(self, id_produto: str, 
                                coluna_preco: str = "PF 0%") -> pd.DataFrame:
        """Retorna evolução temporal de preço de um produto."""
        df = self.dm.carregar_base()
        
        if "ID_PRODUTO" not in df.columns:
            return pd.DataFrame()
        
        produto = df[df["ID_PRODUTO"] == id_produto].copy()
        
        if produto.empty:
            return pd.DataFrame()
        
        produto["VIG_INICIO"] = pd.to_datetime(produto["VIG_INICIO"], errors="coerce")
        produto = produto.sort_values("VIG_INICIO")
        
        resultado = produto[["VIG_INICIO", coluna_preco, "PRODUTO"]].copy()
        resultado.columns = ["data", "preco", "produto"]
        
        return resultado
    
    def agregacao_por_dimensao(self, dimensao: str, 
                                ano: Optional[int] = None, 
                                mes: Optional[int] = None,
                                metrica: str = "count") -> pd.DataFrame:
        """Agrega dados por uma dimensão específica."""
        if ano and mes:
            df = self.dm.carregar_periodo(ano, mes)
        else:
            df = self.dm.carregar_base()
        
        if df.empty or dimensao not in df.columns:
            return pd.DataFrame()
        
        if metrica == "count":
            result = df.groupby(dimensao).size().reset_index(name="quantidade")
        elif metrica == "preco_medio":
            result = df.groupby(dimensao)["PF 0%"].mean().reset_index(name="preco_medio")
        else:
            result = df.groupby(dimensao).size().reset_index(name="quantidade")
        
        return result.sort_values(result.columns[-1], ascending=False)
    
    def estatisticas_temporais(self) -> pd.DataFrame:
        """Calcula estatísticas de preço por período."""
        df = self.dm.carregar_base()
        
        if "VIG_INICIO" not in df.columns or "PF 0%" not in df.columns:
            return pd.DataFrame()
        
        df_temp = df.copy()
        df_temp["VIG_INICIO"] = pd.to_datetime(df_temp["VIG_INICIO"], errors="coerce")
        df_temp["ano"] = df_temp["VIG_INICIO"].dt.year
        df_temp["mes"] = df_temp["VIG_INICIO"].dt.month
        
        stats = df_temp.groupby(["ano", "mes"]).agg({
            "PF 0%": ["mean", "median", "min", "max"],
            "ID_PRODUTO": "nunique"
        }).reset_index()
        
        stats.columns = ["ano", "mes", "preco_medio", "preco_mediano", "preco_min", "preco_max", "total_produtos"]
        stats["data"] = pd.to_datetime(stats["ano"].astype(str) + "-" + stats["mes"].astype(str).str.zfill(2) + "-01")
        
        return stats.sort_values("data")
    
    def comparativo_periodos(self, id_produto: str,
                              periodo1: tuple, periodo2: tuple) -> Dict[str, Any]:
        """Compara preços entre dois períodos."""
        df1 = self.dm.carregar_periodo(*periodo1)
        df2 = self.dm.carregar_periodo(*periodo2)
        
        p1 = df1[df1["ID_PRODUTO"] == id_produto] if not df1.empty and "ID_PRODUTO" in df1.columns else pd.DataFrame()
        p2 = df2[df2["ID_PRODUTO"] == id_produto] if not df2.empty and "ID_PRODUTO" in df2.columns else pd.DataFrame()
        
        resultado = {
            "id_produto": id_produto,
            "periodo1": periodo1,
            "periodo2": periodo2,
            "encontrado_p1": not p1.empty,
            "encontrado_p2": not p2.empty,
        }
        
        if not p1.empty and not p2.empty:
            for col in ["PF 0%", "PMVG 0%", "PMC 0%"]:
                if col in p1.columns and col in p2.columns:
                    v1 = p1[col].iloc[0]
                    v2 = p2[col].iloc[0]
                    if pd.notna(v1) and pd.notna(v2) and v1 > 0:
                        resultado[f"{col}_p1"] = float(v1)
                        resultado[f"{col}_p2"] = float(v2)
                        resultado[f"{col}_variacao"] = ((v2 - v1) / v1) * 100
        
        return resultado
    
    def buscar_produtos(self, termo: str, limite: int = 100) -> pd.DataFrame:
        """Busca produtos por termo."""
        df = self.dm.carregar_base()
        
        if df.empty:
            return pd.DataFrame()
        
        termo_upper = termo.upper()
        
        mask = pd.Series([False] * len(df))
        for col in ["PRODUTO", "PRINCIPIO ATIVO", "LABORATORIO"]:
            if col in df.columns:
                mask |= df[col].astype(str).str.upper().str.contains(termo_upper, na=False)
        
        resultado = df[mask].drop_duplicates(subset=["ID_PRODUTO"]).head(limite)
        
        return resultado


# Instância global para reuso
_data_manager: Optional[DataManager] = None
_aggregation_engine: Optional[AggregationEngine] = None


def get_data_manager() -> DataManager:
    """Retorna instância singleton do DataManager."""
    global _data_manager
    if _data_manager is None:
        _data_manager = DataManager()
    return _data_manager


def get_aggregation_engine() -> AggregationEngine:
    """Retorna instância singleton do AggregationEngine."""
    global _aggregation_engine
    if _aggregation_engine is None:
        _aggregation_engine = AggregationEngine(get_data_manager())
    return _aggregation_engine
