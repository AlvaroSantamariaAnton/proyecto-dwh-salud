"""
Bloque 3.5-3.6 - TRANSFORM + LOAD de hechos
stg + dwh.dim_* → dwh.fact_*
Las transformaciones se hacen con SQL puro (pushdown a Postgres).
"""
import time
from sqlalchemy import text

from etl.config import SCHEMA_DWH
from etl.db import get_engine_dwh, truncate_table, row_count
from etl.logger import get_logger

log = get_logger()


# =============================================================================
# FACT_SALES
# =============================================================================
SQL_INSERT_FACT_SALES = """
INSERT INTO dwh.fact_sales (
    sale_id_nk,
    sale_item_id_nk,
    customer_sk,
    product_sk,
    store_sk,
    date_sk,
    offer_sk,
    sale_timestamp,
    quantity,
    unit_price,
    unit_cost,
    gross_revenue,
    discount_amount,
    net_revenue,
    cost_amount,
    gross_margin,
    is_returned,
    is_cost_imputed,
    has_offer
)
SELECT
    si.sale_id                                          AS sale_id_nk,
    si.sale_item_id                                     AS sale_item_id_nk,
    dc.customer_sk                                      AS customer_sk,
    dp.product_sk                                       AS product_sk,
    ds.store_sk                                         AS store_sk,
    dd.date_sk                                          AS date_sk,
    COALESCE(do_off.offer_sk, 0)                        AS offer_sk,  -- 0 = 'Sin oferta'
    s.sale_date                                         AS sale_timestamp,
    si.quantity                                         AS quantity,
    si.unit_price                                       AS unit_price,
    dp.unit_cost                                        AS unit_cost,
    -- Métricas calculadas
    ROUND((si.quantity * si.unit_price)::numeric, 2)    AS gross_revenue,
    ROUND(((si.quantity * si.unit_price) - si.subtotal)::numeric, 2) AS discount_amount,
    si.subtotal                                         AS net_revenue,
    ROUND((si.quantity * dp.unit_cost)::numeric, 2)     AS cost_amount,
    ROUND((si.subtotal - (si.quantity * dp.unit_cost))::numeric, 2) AS gross_margin,
    -- Flags
    CASE WHEN ri.return_id IS NOT NULL THEN TRUE ELSE FALSE END AS is_returned,
    dp.is_cost_imputed                                  AS is_cost_imputed,
    CASE WHEN si.offer_id IS NOT NULL THEN TRUE ELSE FALSE END  AS has_offer
FROM stg.sale_item si
JOIN stg.sale         s     ON si.sale_id      = s.sale_id
JOIN dwh.dim_customer dc    ON s.customer_id   = dc.customer_id_nk
JOIN dwh.dim_product  dp    ON si.product_id   = dp.product_id_nk
JOIN dwh.dim_store    ds    ON s.store_id      = ds.store_id_nk
JOIN dwh.dim_date     dd    ON DATE(s.sale_date) = dd.full_date
LEFT JOIN dwh.dim_offer  do_off ON si.offer_id = do_off.offer_id_nk
LEFT JOIN (
    -- Subquery: una fila por sale_item_id que tenga al menos una devolución
    SELECT DISTINCT sale_item_id, MIN(return_id) AS return_id
    FROM stg.return_item
    GROUP BY sale_item_id
) ri ON si.sale_item_id = ri.sale_item_id;
"""


def load_fact_sales():
    """Carga fact_sales desde stg + dimensiones."""
    eng = get_engine_dwh()
    log.info("[fact_sales] TRUNCATE + INSERT")
    t0 = time.time()

    # 1) Truncate (CASCADE limpia también fact_returns)
    truncate_table(SCHEMA_DWH, "fact_sales", eng)

    # 2) INSERT con SQL pushdown
    log.info("  Ejecutando INSERT...SELECT con pushdown a Postgres...")
    with eng.begin() as conn:
        result = conn.execute(text(SQL_INSERT_FACT_SALES))
        n_inserted = result.rowcount

    elapsed = time.time() - t0
    n = row_count(SCHEMA_DWH, "fact_sales", eng)
    log.info(f"[fact_sales] OK | inserted={n_inserted} count={n} en {elapsed:.2f}s")

    if n != 42555:
        log.warning(f"  ⚠ Esperaban 42555 filas (igual que stg.sale_item), pero hay {n}")

    return n


# =============================================================================
# Validaciones rápidas post-carga de fact_sales
# =============================================================================
SQL_VALIDATIONS_FACT_SALES = """
SELECT
    'total_filas'                AS metric, COUNT(*)::numeric AS value FROM dwh.fact_sales
UNION ALL
SELECT 'sum_net_revenue',         ROUND(SUM(net_revenue), 2)        FROM dwh.fact_sales
UNION ALL
SELECT 'sum_cost_amount',         ROUND(SUM(cost_amount), 2)        FROM dwh.fact_sales
UNION ALL
SELECT 'sum_gross_margin',        ROUND(SUM(gross_margin), 2)       FROM dwh.fact_sales
UNION ALL
SELECT 'pct_margin_global',       ROUND(100.0*SUM(gross_margin)/NULLIF(SUM(net_revenue),0), 2) FROM dwh.fact_sales
UNION ALL
SELECT 'items_returned',          COUNT(*)::numeric  FROM dwh.fact_sales WHERE is_returned = TRUE
UNION ALL
SELECT 'items_with_offer',        COUNT(*)::numeric  FROM dwh.fact_sales WHERE has_offer = TRUE
UNION ALL
SELECT 'items_cost_imputed',      COUNT(*)::numeric  FROM dwh.fact_sales WHERE is_cost_imputed = TRUE
UNION ALL
SELECT 'distinct_customers',      COUNT(DISTINCT customer_sk)::numeric FROM dwh.fact_sales
UNION ALL
SELECT 'distinct_products',       COUNT(DISTINCT product_sk)::numeric  FROM dwh.fact_sales
UNION ALL
SELECT 'distinct_stores',         COUNT(DISTINCT store_sk)::numeric    FROM dwh.fact_sales
UNION ALL
SELECT 'distinct_dates',          COUNT(DISTINCT date_sk)::numeric     FROM dwh.fact_sales;
"""


def validate_fact_sales():
    """Imprime validaciones de fact_sales."""
    eng = get_engine_dwh()
    log.info("[fact_sales] Validaciones post-carga:")
    with eng.connect() as conn:
        result = conn.execute(text(SQL_VALIDATIONS_FACT_SALES)).fetchall()
    for row in result:
        log.info(f"  {row[0]:.<28} {row[1]}")


# =============================================================================
# FACT_RETURNS
# =============================================================================
SQL_INSERT_FACT_RETURNS = """
INSERT INTO dwh.fact_returns (
    return_id_nk,
    sale_item_id_nk,
    sale_item_sk,
    customer_sk,
    product_sk,
    store_sk,
    date_sk,
    reason_sk,
    return_timestamp,
    sale_timestamp,
    quantity_returned,
    refund_amount,
    cost_recovered,
    margin_lost,
    days_to_return
)
SELECT
    ri.return_id                                              AS return_id_nk,
    ri.sale_item_id                                           AS sale_item_id_nk,
    fs.sale_item_sk                                           AS sale_item_sk,
    fs.customer_sk                                            AS customer_sk,
    fs.product_sk                                             AS product_sk,
    fs.store_sk                                               AS store_sk,
    dd.date_sk                                                AS date_sk,
    drr.reason_sk                                             AS reason_sk,
    ri.return_date                                            AS return_timestamp,
    fs.sale_timestamp                                         AS sale_timestamp,
    ri.quantity                                               AS quantity_returned,
    ROUND((ri.quantity * fs.unit_price)::numeric, 2)          AS refund_amount,
    ROUND((ri.quantity * fs.unit_cost)::numeric, 2)           AS cost_recovered,
    ROUND(((ri.quantity * fs.unit_price) - 
           (ri.quantity * fs.unit_cost))::numeric, 2)         AS margin_lost,
    (DATE(ri.return_date) - DATE(fs.sale_timestamp))::int     AS days_to_return
FROM stg.return_item   ri
JOIN dwh.fact_sales    fs   ON ri.sale_item_id  = fs.sale_item_id_nk
JOIN dwh.dim_date      dd   ON DATE(ri.return_date) = dd.full_date
LEFT JOIN dwh.dim_return_reason drr ON ri.reason_id = drr.reason_id_nk;
"""


def load_fact_returns():
    """Carga fact_returns desde stg + fact_sales + dim_*."""
    eng = get_engine_dwh()
    log.info("[fact_returns] TRUNCATE + INSERT")
    t0 = time.time()

    truncate_table(SCHEMA_DWH, "fact_returns", eng)

    log.info("  Ejecutando INSERT...SELECT con pushdown a Postgres...")
    with eng.begin() as conn:
        result = conn.execute(text(SQL_INSERT_FACT_RETURNS))
        n_inserted = result.rowcount

    elapsed = time.time() - t0
    n = row_count(SCHEMA_DWH, "fact_returns", eng)
    log.info(f"[fact_returns] OK | inserted={n_inserted} count={n} en {elapsed:.2f}s")

    if n != 2330:
        log.warning(f"  ⚠ Esperaban 2330 filas (igual que stg.return_item), pero hay {n}")

    return n


# =============================================================================
# Validaciones rápidas post-carga de fact_returns
# =============================================================================
SQL_VALIDATIONS_FACT_RETURNS = """
SELECT 'total_filas'             AS metric, COUNT(*)::numeric AS value FROM dwh.fact_returns
UNION ALL
SELECT 'sum_refund_amount',      ROUND(SUM(refund_amount), 2)   FROM dwh.fact_returns
UNION ALL
SELECT 'sum_cost_recovered',     ROUND(SUM(cost_recovered), 2)  FROM dwh.fact_returns
UNION ALL
SELECT 'sum_margin_lost',        ROUND(SUM(margin_lost), 2)     FROM dwh.fact_returns
UNION ALL
SELECT 'avg_days_to_return',     ROUND(AVG(days_to_return)::numeric, 1) FROM dwh.fact_returns
UNION ALL
SELECT 'min_days_to_return',     MIN(days_to_return)::numeric   FROM dwh.fact_returns
UNION ALL
SELECT 'max_days_to_return',     MAX(days_to_return)::numeric   FROM dwh.fact_returns
UNION ALL
SELECT 'distinct_customers_ret', COUNT(DISTINCT customer_sk)::numeric FROM dwh.fact_returns
UNION ALL
SELECT 'distinct_products_ret',  COUNT(DISTINCT product_sk)::numeric  FROM dwh.fact_returns
UNION ALL
SELECT 'returns_no_reason',      COUNT(*)::numeric FROM dwh.fact_returns WHERE reason_sk IS NULL;
"""


def validate_fact_returns():
    """Imprime validaciones de fact_returns."""
    eng = get_engine_dwh()
    log.info("[fact_returns] Validaciones post-carga:")
    with eng.connect() as conn:
        result = conn.execute(text(SQL_VALIDATIONS_FACT_RETURNS)).fetchall()
    for row in result:
        log.info(f"  {row[0]:.<28} {row[1]}")


# =============================================================================
# Orquestador (lo extenderemos con fact_returns en bloque 3.6)
# =============================================================================
def run_transform_facts():
    log.info("=" * 70)
    log.info("INICIANDO TRANSFORM + LOAD: hechos")
    log.info("=" * 70)

    load_fact_sales()
    validate_fact_sales()

    load_fact_returns()
    validate_fact_returns()

    log.info("=" * 70)
    log.info("TRANSFORM + LOAD de hechos COMPLETADO")
    log.info("=" * 70)


if __name__ == "__main__":
    run_transform_facts()