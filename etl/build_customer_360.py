"""
Bloque 4 - BUILD CUSTOMER_360
Calcula todas las métricas de cliente (CLTV en 3 versiones, RFM, Churn Risk)
y las carga en marts.customer_360.

Reproduce en código la lógica del notebook 04_cltv_exploracion.ipynb.
"""
import time
import numpy as np
import pandas as pd
from sqlalchemy import text

from etl.config import SCHEMA_DWH
from etl.db import get_engine_dwh, truncate_table, row_count, read_sql
from etl.logger import get_logger

log = get_logger()

# Parámetros (alineados con las decisiones de Fase 4)
LIFESPAN_YEARS  = 3
CHURN_THRESHOLD = 365


# =============================================================================
# Construcción de métricas
# =============================================================================
def build_customer_metrics() -> pd.DataFrame:
    """
    Construye el DataFrame con todas las métricas por cliente.
    Devuelve un DataFrame listo para insertar en marts.customer_360.
    """
    eng = get_engine_dwh()

    # Snapshot date = último día con datos
    snapshot_date = pd.Timestamp(read_sql(
        "SELECT MAX(sale_timestamp)::date AS d FROM dwh.fact_sales;", eng
    )['d'].iloc[0])
    log.info(f"  Snapshot date: {snapshot_date.date()}")

    # 1) Métricas básicas desde fact_sales
    log.info("  Construyendo métricas base desde fact_sales...")
    df = read_sql("""
        SELECT 
            fs.customer_sk,
            dc.customer_id_nk,
            dc.full_name,
            dc.email,
            dc.cohort_year,
            dc.cohort_month,
            COUNT(DISTINCT fs.sale_id_nk)              AS num_orders,
            COUNT(*)                                   AS num_items,
            SUM(fs.quantity)                           AS total_units,
            ROUND(SUM(fs.gross_revenue)::numeric, 2)   AS gross_revenue,
            ROUND(SUM(fs.discount_amount)::numeric, 2) AS discount_amount,
            ROUND(SUM(fs.net_revenue)::numeric, 2)     AS net_revenue,
            ROUND(SUM(fs.cost_amount)::numeric, 2)     AS cost_amount,
            ROUND(SUM(fs.gross_margin)::numeric, 2)    AS gross_margin,
            MIN(fs.sale_timestamp)::date               AS first_order_date,
            MAX(fs.sale_timestamp)::date               AS last_order_date
        FROM dwh.fact_sales fs
        JOIN dwh.dim_customer dc ON fs.customer_sk = dc.customer_sk
        GROUP BY fs.customer_sk, dc.customer_id_nk, dc.full_name, dc.email, 
                 dc.cohort_year, dc.cohort_month;
    """, eng)
    log.info(f"  Clientes con compras: {len(df)}")

    # 2) Métricas derivadas
    df['avg_order_value'] = (df['net_revenue'] / df['num_orders']).round(2)
    df['customer_lifespan_days'] = (
        pd.to_datetime(df['last_order_date']) - pd.to_datetime(df['first_order_date'])
    ).dt.days
    df['days_since_last_order'] = (
        snapshot_date - pd.to_datetime(df['last_order_date'])
    ).dt.days
    df['purchase_frequency_year'] = (
        df['num_orders'] / df['customer_lifespan_days'].clip(lower=365) * 365
    ).round(4)

    df['is_one_shot']  = df['num_orders'] == 1
    df['is_recurrent'] = df['num_orders'] >= 2
    df['is_active']    = df['days_since_last_order'] <= CHURN_THRESHOLD
    df['is_churned']   = df['days_since_last_order'] > CHURN_THRESHOLD

    # 3) Devoluciones
    log.info("  Añadiendo info de devoluciones...")
    df_ret = read_sql("""
        SELECT 
            customer_sk,
            COUNT(*)                                AS num_returns,
            SUM(quantity_returned)                  AS units_returned,
            ROUND(SUM(refund_amount)::numeric, 2)   AS refund_amount,
            ROUND(SUM(margin_lost)::numeric, 2)     AS margin_lost_returns
        FROM dwh.fact_returns
        GROUP BY customer_sk;
    """, eng)
    df = df.merge(df_ret, on='customer_sk', how='left')
    for col in ['num_returns', 'units_returned', 'refund_amount', 'margin_lost_returns']:
        df[col] = df[col].fillna(0)
    df['num_returns']    = df['num_returns'].astype(int)
    df['units_returned'] = df['units_returned'].astype(int)
    df['return_rate']    = (df['units_returned'] / df['total_units']).fillna(0).round(4)
    df['has_returns']    = df['num_returns'] > 0
    df['net_revenue_after_returns'] = (df['net_revenue']  - df['refund_amount']).round(2)
    df['net_margin_after_returns']  = (df['gross_margin'] - df['margin_lost_returns']).round(2)

    # 4) CLTV (3 versiones)
    log.info("  Calculando CLTV (3 versiones)...")
    df['cltv_historic'] = df['net_margin_after_returns']

    df['cliente_margin_pct'] = (
        df['gross_margin'] / df['net_revenue'].replace(0, np.nan)
    ).fillna(0.40)

    df['cltv_predictive'] = np.where(
        df['is_recurrent'],
        (df['avg_order_value'] * df['cliente_margin_pct'] * 
         df['purchase_frequency_year'] * LIFESPAN_YEARS).round(2),
        0
    )

    df['cltv_formula'] = (
        df['net_revenue'] * df['cliente_margin_pct'] * 
        df['purchase_frequency_year'] * LIFESPAN_YEARS
    ).round(2)

    # 5) RFM Score
    log.info("  Calculando RFM Score...")
    df['rfm_recency'] = pd.qcut(
        df['days_since_last_order'].rank(method='first'),
        5, labels=[5, 4, 3, 2, 1]
    ).astype(int)
    df['rfm_frequency'] = pd.qcut(
        df['num_orders'].rank(method='first'),
        5, labels=[1, 2, 3, 4, 5]
    ).astype(int)
    df['rfm_monetary'] = pd.qcut(
        df['net_revenue_after_returns'].rank(method='first'),
        5, labels=[1, 2, 3, 4, 5]
    ).astype(int)
    df['rfm_score'] = df['rfm_recency'] + df['rfm_frequency'] + df['rfm_monetary']

    def rfm_segment(row):
        r, f, m = row['rfm_recency'], row['rfm_frequency'], row['rfm_monetary']
        if   r >= 4 and f >= 4 and m >= 4:                return 'Champions'
        elif r >= 3 and f >= 3 and m >= 4:                return 'Loyal Customers'
        elif r >= 4 and f <= 2:                           return 'New Customers'
        elif r >= 4 and f >= 2 and m >= 2:                return 'Potential Loyalists'
        elif r <= 2 and f >= 4 and m >= 4:                return 'At Risk'
        elif r <= 2 and f >= 3 and m >= 3:                return 'Cant Lose Them'
        elif r <= 2 and f <= 2 and m <= 2:                return 'Lost'
        elif r <= 2 and f <= 2:                           return 'Hibernating'
        else:                                             return 'Others'

    df['rfm_segment'] = df.apply(rfm_segment, axis=1)

    # 6) Churn Risk
    log.info("  Calculando Churn Risk...")
    recency_norm       = (df['days_since_last_order'] / df['days_since_last_order'].max()).clip(0, 1)
    frequency_norm_inv = 1 - (df['num_orders'] / df['num_orders'].max())
    df['churn_risk_score'] = (0.7 * recency_norm + 0.3 * frequency_norm_inv).round(4)

    df['churn_risk_level'] = df['churn_risk_score'].apply(
        lambda s: 'Low' if s < 0.33 else ('Medium' if s < 0.66 else 'High')
    )

    # Limpieza final: quedarnos solo con columnas del DDL
    cols_destino = [
        'customer_sk', 'customer_id_nk', 'full_name', 'email', 'cohort_year', 'cohort_month',
        'num_orders', 'num_items', 'total_units',
        'gross_revenue', 'discount_amount', 'net_revenue', 'cost_amount', 'gross_margin', 'avg_order_value',
        'num_returns', 'units_returned', 'refund_amount', 'margin_lost_returns', 'return_rate',
        'net_revenue_after_returns', 'net_margin_after_returns',
        'first_order_date', 'last_order_date', 'customer_lifespan_days', 'days_since_last_order',
        'purchase_frequency_year',
        'is_one_shot', 'is_recurrent', 'is_active', 'is_churned', 'has_returns',
        'cltv_historic', 'cltv_predictive', 'cltv_formula',
        'rfm_recency', 'rfm_frequency', 'rfm_monetary', 'rfm_score', 'rfm_segment',
        'churn_risk_score', 'churn_risk_level',
    ]
    return df[cols_destino]


def load_customer_360():
    """Trunca y carga marts.customer_360."""
    eng = get_engine_dwh()
    log.info("=" * 70)
    log.info("BUILD MARTS.CUSTOMER_360")
    log.info("=" * 70)

    t0 = time.time()
    df = build_customer_metrics()

    log.info("  TRUNCATE marts.customer_360 + INSERT...")
    truncate_table("marts", "customer_360", eng)

    df.to_sql(
        name="customer_360",
        con=eng,
        schema="marts",
        if_exists="append",
        index=False,
        chunksize=2000,
        method="multi",
    )

    n = row_count("marts", "customer_360", eng)
    log.info(f"OK | {n} filas en {time.time()-t0:.2f}s")

    # Resumen rápido
    summary = read_sql("""
        SELECT 
            rfm_segment,
            COUNT(*) AS n,
            ROUND(AVG(cltv_historic)::numeric, 2) AS cltv_hist_avg,
            ROUND(SUM(cltv_historic)::numeric, 2) AS cltv_hist_total
        FROM marts.customer_360
        GROUP BY rfm_segment
        ORDER BY cltv_hist_total DESC;
    """, eng)
    log.info(f"\nResumen por segmento RFM:\n{summary.to_string(index=False)}")

    log.info("=" * 70)
    return n


if __name__ == "__main__":
    load_customer_360()