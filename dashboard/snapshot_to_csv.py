"""
Genera un snapshot de los datos del DWH en archivos CSV/JSON.
Se ejecuta UNA VEZ desde local; los archivos generados se versionan en el repo
para que el dashboard pueda funcionar en Streamlit Cloud sin BD.

Uso:
    python -m dashboard.snapshot_to_csv

Genera:
    data/snapshots/customer_360.csv
    data/snapshots/monthly_sales.csv
    data/snapshots/global_kpis.json
    data/snapshots/customer_orders.csv  (todos los pedidos consolidados)
"""
import sys
import json
from pathlib import Path
from datetime import datetime

import pandas as pd
from sqlalchemy import text

# Permitir ejecutar desde la raíz del proyecto
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dashboard.config import get_engine

OUT_DIR = ROOT / "data" / "snapshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def snapshot_customer_360(eng):
    print("📦 Snapshot: customer_360...")
    df = pd.read_sql(text("SELECT * FROM marts.customer_360"), eng)
    out = OUT_DIR / "customer_360.csv"
    df.to_csv(out, index=False)
    print(f"   ✓ {len(df):,} filas → {out.name}")


def snapshot_monthly_sales(eng):
    print("📦 Snapshot: monthly_sales...")
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
    df = pd.read_sql(sql, eng)
    df["margin_pct"] = (df["margin"] / df["revenue"] * 100).round(2)
    df["return_rate_pct"] = (df["items_devueltos"] / df["items_total"] * 100).round(2)
    out = OUT_DIR / "monthly_sales.csv"
    df.to_csv(out, index=False)
    print(f"   ✓ {len(df)} meses → {out.name}")


def snapshot_global_kpis(eng):
    print("📦 Snapshot: global_kpis...")
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
    
    kpis = {
        "total_clientes": int(row.total_clientes),
        "total_items":    int(row.total_items),
        "total_ventas":   int(row.total_ventas),
        "total_revenue":  float(row.total_revenue or 0),
        "total_margin":   float(row.total_margin or 0),
        "total_cost":     float(row.total_cost or 0),
        "total_refunds":  float(row.total_refunds or 0),
        "margin_lost":    float(row.margin_lost or 0),
        "margin_pct":     round((row.total_margin / row.total_revenue * 100), 2),
        "snapshot_date":  datetime.now().isoformat(),
    }
    out = OUT_DIR / "global_kpis.json"
    out.write_text(json.dumps(kpis, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"   ✓ KPIs → {out.name}")


def snapshot_customer_orders(eng):
    """
    Exporta TODOS los pedidos agrupados por cliente.
    Volumen: ~20.000 ventas → CSV ~1-2 MB.
    """
    print("📦 Snapshot: customer_orders (consolidado)...")
    sql = text("""
        SELECT 
            c.customer_id_nk,
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
        GROUP BY c.customer_id_nk, s.sale_id_nk, d.full_date
        ORDER BY c.customer_id_nk, d.full_date DESC
    """)
    df = pd.read_sql(sql, eng)
    out = OUT_DIR / "customer_orders.csv"
    df.to_csv(out, index=False)
    print(f"   ✓ {len(df):,} pedidos → {out.name}")


def snapshot_top_products(eng):
    print("📦 Snapshot: top_products...")
    sql = text("""
        SELECT
            p.name,
            COUNT(DISTINCT s.sale_id_nk)   AS n_ventas,
            SUM(s.quantity)::int            AS unidades,
            SUM(s.net_revenue)::float       AS revenue,
            SUM(s.gross_margin)::float      AS margin,
            ROUND(100.0 * SUM(s.gross_margin)
                / NULLIF(SUM(s.net_revenue), 0)::numeric, 1) AS margin_pct
        FROM dwh.fact_sales s
        JOIN dwh.dim_product p ON s.product_sk = p.product_sk
        GROUP BY p.name
        ORDER BY revenue DESC
    """)
    with eng.connect() as conn:
        df = pd.read_sql(sql, conn)
    out = OUT_DIR / "top_products.csv"
    df.to_csv(out, index=False)
    print(f"   ✓ {len(df)} productos → {out.name}")


def snapshot_top_stores(eng):
    print("📦 Snapshot: top_stores...")
    sql = text("""
        SELECT
            st.name,
            st.city,
            COUNT(DISTINCT s.sale_id_nk)   AS n_ventas,
            SUM(s.net_revenue)::float       AS revenue,
            SUM(s.gross_margin)::float      AS margin,
            ROUND(100.0 * SUM(s.gross_margin)
                / NULLIF(SUM(s.net_revenue), 0)::numeric, 1) AS margin_pct
        FROM dwh.fact_sales s
        JOIN dwh.dim_store st ON s.store_sk = st.store_sk
        GROUP BY st.name, st.city
        ORDER BY margin DESC
    """)
    with eng.connect() as conn:
        df = pd.read_sql(sql, conn)
    out = OUT_DIR / "top_stores.csv"
    df.to_csv(out, index=False)
    print(f"   ✓ {len(df)} tiendas → {out.name}")


def main():
    print("=" * 70)
    print("SNAPSHOT DE DATOS PARA STREAMLIT CLOUD")
    print("=" * 70)
    print(f"Destino: {OUT_DIR}")
    print()

    eng = get_engine()
    
    snapshot_customer_360(eng)
    snapshot_monthly_sales(eng)
    snapshot_global_kpis(eng)
    snapshot_customer_orders(eng)
    snapshot_top_products(eng)
    snapshot_top_stores(eng)
    
    print()
    print("=" * 70)
    total_size = sum(f.stat().st_size for f in OUT_DIR.glob("*"))
    print(f"✅ Snapshot completado · Tamaño total: {total_size/1024/1024:.2f} MB")
    print("=" * 70)


if __name__ == "__main__":
    main()