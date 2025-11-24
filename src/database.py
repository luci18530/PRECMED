"""Rotinas auxiliares para persistir os dados processados."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

import duckdb


DEFAULT_DB_PATH = Path("data/processed/precsmed.duckdb")


def ensure_database(db_path: Path | str = DEFAULT_DB_PATH) -> duckdb.DuckDBPyConnection:
    """Abre (ou cria) a base DuckDB padrão para análises."""

    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(path))


def register_csv_table(conn: duckdb.DuckDBPyConnection, csv_path: str | Path, table_name: str) -> None:
    """Cria uma view temporária apontando para um CSV consolidado."""

    conn.execute(
        f"""
        CREATE OR REPLACE VIEW {table_name} AS
        SELECT * FROM read_csv_auto('{Path(csv_path)}', sep=';', header=True)
        """
    )
