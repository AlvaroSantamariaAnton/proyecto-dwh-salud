"""
Helpers de conexión y operaciones comunes con BD.
"""
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from etl.config import URL_ORIGEN, URL_DWH

# Engines reutilizables (singleton-like)
_engine_origen = None
_engine_dwh = None

def get_engine_origen() -> Engine:
    global _engine_origen
    if _engine_origen is None:
        _engine_origen = create_engine(URL_ORIGEN, pool_pre_ping=True)
    return _engine_origen

def get_engine_dwh() -> Engine:
    global _engine_dwh
    if _engine_dwh is None:
        _engine_dwh = create_engine(URL_DWH, pool_pre_ping=True)
    return _engine_dwh

def read_sql(sql: str, engine: Engine, params: dict | None = None) -> pd.DataFrame:
    """Ejecuta un SELECT y devuelve un DataFrame."""
    with engine.connect() as conn:
        return pd.read_sql(text(sql), conn, params=params)

def execute_sql(sql: str, engine: Engine, params: dict | None = None) -> None:
    """Ejecuta una query sin retorno (DDL, DML)."""
    with engine.begin() as conn:
        conn.execute(text(sql), params or {})

def truncate_table(schema: str, table: str, engine: Engine, restart_identity: bool = True) -> None:
    """Vacía una tabla. Si restart_identity=True, resetea las secuencias."""
    cmd = f"TRUNCATE TABLE {schema}.{table}"
    if restart_identity:
        cmd += " RESTART IDENTITY"
    cmd += " CASCADE;"
    execute_sql(cmd, engine)

def row_count(schema: str, table: str, engine: Engine) -> int:
    """Devuelve el número de filas de una tabla."""
    sql = f"SELECT COUNT(*) AS n FROM {schema}.{table};"
    return int(read_sql(sql, engine)["n"].iloc[0])