"""
Funciones de carga de datos con cache de Streamlit.
Detecta automáticamente si debe leer de Postgres (local) o de CSV (cloud).
"""
import os
import json
from pathlib import Path

import pandas as pd
import streamlit as st
from sqlalchemy import text

from dashboard.config import get_engine

# ============================================================================
# DETECCIÓN DE MODO: postgres (local) vs csv (cloud)
# ============================================================================
ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_DIR = ROOT / "data" / "snapshots"

# Modo CSV si existe la variable de entorno DATA_MODE=csv
# O si simplemente la BD no es accesible y los snapshots existen
def _detect_mode() -> str:
    """
    Detecta si usar Postgres (local) o CSV (cloud).
    Prioridad:
      1. st.secrets["DATA_MODE"] (Streamlit Cloud)
      2. Variable de entorno DATA_MODE
      3. Auto: si Postgres responde → postgres, sino → csv
    """
    # 1) Streamlit Cloud Secrets
    try:
        if hasattr(st, "secrets") and "DATA_MODE" in st.secrets:
            mode = str(st.secrets["DATA_MODE"]).lower()
            if mode in ("csv", "postgres"):
                return mode
    except Exception:
        pass

    # 2) Variable de entorno
    explicit = os.getenv("DATA_MODE", "").lower()
    if explicit in ("csv", "postgres"):
        return explicit

    # 3) Auto-detección: si los CSVs existen, preferir CSV (más rápido)
    if SNAPSHOT_DIR.exists() and (SNAPSHOT_DIR / "customer_360.csv").exists():
        # Si tampoco hay password de Postgres, va a CSV directo
        if not os.getenv("DB_PASSWORD"):
            return "csv"

    # 4) Intentar Postgres como último recurso
    try:
        eng = get_engine()
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return "postgres"
    except Exception:
        if SNAPSHOT_DIR.exists() and (SNAPSHOT_DIR / "customer_360.csv").exists():
            return "csv"
        raise RuntimeError(
            "No hay conexión a Postgres y no existen los snapshots CSV. "
            "Ejecuta `python -m dashboard.snapshot_to_csv` o configura el .env."
        )

DATA_MODE = _detect_mode()


# ============================================================================
# LOADERS
# ============================================================================
@st.cache_data(ttl=600, show_spinner="Cargando customer_360...")
def load_customer_360() -> pd.DataFrame:
    """Carga la tabla customer_360 completa (5750 filas)."""
    if DATA_MODE == "csv":
        return pd.read_csv(SNAPSHOT_DIR / "customer_360.csv")
    
    eng = get_engine()
    with eng.connect() as conn:
        df = pd.read_sql(text("SELECT * FROM marts.customer_360"), conn)
    return df


@st.cache_data(ttl=600, show_spinner="Cargando ventas mensuales...")
def load_monthly_sales() -> pd.DataFrame:
    """Agregado mensual de ventas e ingresos para la página de KPIs."""
    if DATA_MODE == "csv":
        return pd.read_csv(SNAPSHOT_DIR / "monthly_sales.csv")
    
    eng = get_engine()
    sql = text("""
        SELECT 
            d.year_month                              AS year_month,
            COUNT(DISTINCT s.sale_id_nk)              AS n_ventas,
            COUNT(DISTINCT s.customer_sk)             AS n_clientes,
            SUM(s.net_revenue)::float                 AS revenue,
            SUM(s.gross_margin)::float                AS margin,
            SUM(s.cost_amount)::float                 AS cost,
            COUNT(*) FILTER (WHERE s.is_returned)::int AS items_devueltos,
            COUNT(*)::int                             AS items_total
        FROM dwh.fact_sales s
        JOIN dwh.dim_date d ON s.date_sk = d.date_sk
        GROUP BY d.year_month
        ORDER BY d.year_month
    """)
    with eng.connect() as conn:
        df = pd.read_sql(sql, conn)
    df["margin_pct"] = (df["margin"] / df["revenue"] * 100).round(2)
    df["return_rate_pct"] = (df["items_devueltos"] / df["items_total"] * 100).round(2)
    return df


@st.cache_data(ttl=600, show_spinner="Cargando KPIs globales...")
def load_global_kpis() -> dict:
    """KPIs globales para mostrar en cards."""
    if DATA_MODE == "csv":
        path = SNAPSHOT_DIR / "global_kpis.json"
        return json.loads(path.read_text(encoding="utf-8"))
    
    eng = get_engine()
    sql = text("""
        SELECT 
            (SELECT COUNT(*) FROM dwh.dim_customer)                       AS total_clientes,
            (SELECT COUNT(*) FROM dwh.fact_sales)                         AS total_items,
            (SELECT COUNT(DISTINCT sale_id_nk) FROM dwh.fact_sales)       AS total_ventas,
            (SELECT SUM(net_revenue) FROM dwh.fact_sales)::float          AS total_revenue,
            (SELECT SUM(gross_margin) FROM dwh.fact_sales)::float         AS total_margin,
            (SELECT SUM(cost_amount) FROM dwh.fact_sales)::float          AS total_cost,
            (SELECT SUM(refund_amount) FROM dwh.fact_returns)::float      AS total_refunds,
            (SELECT SUM(margin_lost) FROM dwh.fact_returns)::float        AS margin_lost
    """)
    with eng.connect() as conn:
        row = conn.execute(sql).fetchone()
    return {
        "total_clientes": int(row.total_clientes),
        "total_items":    int(row.total_items),
        "total_ventas":   int(row.total_ventas),
        "total_revenue":  float(row.total_revenue or 0),
        "total_margin":   float(row.total_margin or 0),
        "total_cost":     float(row.total_cost or 0),
        "total_refunds":  float(row.total_refunds or 0),
        "margin_lost":    float(row.margin_lost or 0),
        "margin_pct":     round((row.total_margin / row.total_revenue * 100), 2),
    }


@st.cache_data(ttl=600)
def load_customer_by_id(customer_id_nk: int) -> pd.DataFrame:
    """Datos de un cliente específico para la página Customer 360."""
    if DATA_MODE == "csv":
        df = load_customer_360()
        return df[df["customer_id_nk"] == customer_id_nk]
    
    eng = get_engine()
    sql = text("""
        SELECT * FROM marts.customer_360 WHERE customer_id_nk = :cid
    """)
    with eng.connect() as conn:
        df = pd.read_sql(sql, conn, params={"cid": customer_id_nk})
    return df


@st.cache_data(ttl=600)
def load_customer_orders(customer_id_nk: int) -> pd.DataFrame:
    """Histórico de compras de un cliente específico."""
    if DATA_MODE == "csv":
        all_orders = _load_all_orders_csv()
        df = all_orders[all_orders["customer_id_nk"] == customer_id_nk].copy()
        return df.drop(columns=["customer_id_nk"]).reset_index(drop=True)
    
    eng = get_engine()
    sql = text("""
        SELECT 
            s.sale_id_nk,
            d.full_date AS fecha,
            COUNT(*)              AS n_items,
            SUM(s.quantity)::int  AS unidades,
            SUM(s.net_revenue)::float    AS importe,
            SUM(s.gross_margin)::float   AS margen,
            BOOL_OR(s.is_returned)       AS tiene_devolucion
        FROM dwh.fact_sales s
        JOIN dwh.dim_customer c ON s.customer_sk = c.customer_sk
        JOIN dwh.dim_date d     ON s.date_sk = d.date_sk
        WHERE c.customer_id_nk = :cid
        GROUP BY s.sale_id_nk, d.full_date
        ORDER BY d.full_date DESC
    """)
    with eng.connect() as conn:
        df = pd.read_sql(sql, conn, params={"cid": customer_id_nk})
    return df


@st.cache_data(ttl=3600)
def _load_all_orders_csv() -> pd.DataFrame:
    """Carga (con cache largo) todos los pedidos cuando estamos en modo CSV."""
    return pd.read_csv(SNAPSHOT_DIR / "customer_orders.csv")