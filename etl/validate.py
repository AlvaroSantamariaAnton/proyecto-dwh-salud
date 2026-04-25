"""
Bloque 3.7 - VALIDACIONES post-ETL
Comprueba integridad y coherencia del DWH.
"""
import time
import pandas as pd
from sqlalchemy import text

from etl.db import get_engine_dwh
from etl.logger import get_logger

log = get_logger()


# =============================================================================
# Validaciones declarativas — cada una devuelve dict con resultado
# =============================================================================
VALIDATIONS = [
    # --- ROW COUNTS por tabla ---
    {
        "name": "row_count_dim_date",
        "category": "row_count",
        "sql": "SELECT COUNT(*) FROM dwh.dim_date;",
        "expected": 2922,
    },
    {
        "name": "row_count_dim_customer",
        "category": "row_count",
        "sql": "SELECT COUNT(*) FROM dwh.dim_customer;",
        "expected": 5750,
    },
    {
        "name": "row_count_dim_product",
        "category": "row_count",
        "sql": "SELECT COUNT(*) FROM dwh.dim_product;",
        "expected": 50,
    },
    {
        "name": "row_count_dim_store",
        "category": "row_count",
        "sql": "SELECT COUNT(*) FROM dwh.dim_store;",
        "expected": 20,
    },
    {
        "name": "row_count_dim_offer",
        "category": "row_count",
        "sql": "SELECT COUNT(*) FROM dwh.dim_offer;",
        "expected": 2,  # 1 real + 1 'Sin oferta'
    },
    {
        "name": "row_count_dim_return_reason",
        "category": "row_count",
        "sql": "SELECT COUNT(*) FROM dwh.dim_return_reason;",
        "expected": 6,
    },
    {
        "name": "row_count_fact_sales",
        "category": "row_count",
        "sql": "SELECT COUNT(*) FROM dwh.fact_sales;",
        "expected": 42555,
    },
    {
        "name": "row_count_fact_returns",
        "category": "row_count",
        "sql": "SELECT COUNT(*) FROM dwh.fact_returns;",
        "expected": 2330,
    },

    # --- INTEGRIDAD REFERENCIAL (no debería haber huérfanos) ---
    {
        "name": "fk_fact_sales_customer",
        "category": "fk_integrity",
        "sql": """
            SELECT COUNT(*) FROM dwh.fact_sales fs
            LEFT JOIN dwh.dim_customer dc ON fs.customer_sk = dc.customer_sk
            WHERE dc.customer_sk IS NULL;
        """,
        "expected": 0,
    },
    {
        "name": "fk_fact_sales_product",
        "category": "fk_integrity",
        "sql": """
            SELECT COUNT(*) FROM dwh.fact_sales fs
            LEFT JOIN dwh.dim_product dp ON fs.product_sk = dp.product_sk
            WHERE dp.product_sk IS NULL;
        """,
        "expected": 0,
    },
    {
        "name": "fk_fact_sales_store",
        "category": "fk_integrity",
        "sql": """
            SELECT COUNT(*) FROM dwh.fact_sales fs
            LEFT JOIN dwh.dim_store ds ON fs.store_sk = ds.store_sk
            WHERE ds.store_sk IS NULL;
        """,
        "expected": 0,
    },
    {
        "name": "fk_fact_sales_date",
        "category": "fk_integrity",
        "sql": """
            SELECT COUNT(*) FROM dwh.fact_sales fs
            LEFT JOIN dwh.dim_date dd ON fs.date_sk = dd.date_sk
            WHERE dd.date_sk IS NULL;
        """,
        "expected": 0,
    },
    {
        "name": "fk_fact_returns_sale_item",
        "category": "fk_integrity",
        "sql": """
            SELECT COUNT(*) FROM dwh.fact_returns fr
            LEFT JOIN dwh.fact_sales fs ON fr.sale_item_sk = fs.sale_item_sk
            WHERE fs.sale_item_sk IS NULL;
        """,
        "expected": 0,
    },

    # --- COHERENCIA NEGOCIO ---
    {
        "name": "consistency_origen_dwh_revenue",
        "category": "business",
        "sql": """
            SELECT ABS(
                (SELECT SUM(subtotal)    FROM stg.sale_item) -
                (SELECT SUM(net_revenue) FROM dwh.fact_sales)
            )::int;
        """,
        "expected": 0,
    },
    {
        "name": "consistency_origen_dwh_quantity",
        "category": "business",
        "sql": """
            SELECT (
                (SELECT SUM(quantity) FROM stg.sale_item) -
                (SELECT SUM(quantity) FROM dwh.fact_sales)
            );
        """,
        "expected": 0,
    },
    {
        "name": "consistency_returned_flag",
        "category": "business",
        "sql": """
            SELECT ABS(
                (SELECT COUNT(*) FROM dwh.fact_sales WHERE is_returned = TRUE) -
                (SELECT COUNT(DISTINCT sale_item_sk) FROM dwh.fact_returns)
            );
        """,
        "expected": 0,
    },
    {
        "name": "consistency_gross_minus_discount_eq_net",
        "category": "business",
        "sql": """
            SELECT COUNT(*) FROM dwh.fact_sales
            WHERE ABS(gross_revenue - discount_amount - net_revenue) > 0.01;
        """,
        "expected": 0,
    },
    {
        "name": "no_negative_days_to_return",
        "category": "business",
        "sql": "SELECT COUNT(*) FROM dwh.fact_returns WHERE days_to_return < 0;",
        "expected": 0,
    },
    {
        "name": "no_null_business_metrics",
        "category": "business",
        "sql": """
            SELECT COUNT(*) FROM dwh.fact_sales 
            WHERE net_revenue IS NULL OR gross_revenue IS NULL OR cost_amount IS NULL;
        """,
        "expected": 0,
    },

    # --- VALIDACIONES DE DECISIONES DE FASE 1 ---
    {
        "name": "imputed_cost_only_for_orphan",
        "category": "decisions",
        "sql": """
            SELECT COUNT(*) FROM dwh.fact_sales fs
            JOIN dwh.dim_product dp ON fs.product_sk = dp.product_sk
            WHERE fs.is_cost_imputed = TRUE AND dp.product_id_nk != 29;
        """,
        "expected": 0,
    },
    {
        "name": "orphan_product_has_imputed_cost",
        "category": "decisions",
        "sql": """
            SELECT COUNT(*) FROM dwh.fact_sales fs
            JOIN dwh.dim_product dp ON fs.product_sk = dp.product_sk
            WHERE dp.product_id_nk = 29 AND fs.is_cost_imputed = FALSE;
        """,
        "expected": 0,
    },
]


def run_validations() -> pd.DataFrame:
    """Ejecuta todas las validaciones y devuelve un DataFrame con los resultados."""
    log.info("=" * 70)
    log.info("INICIANDO VALIDACIONES POST-ETL")
    log.info("=" * 70)

    eng = get_engine_dwh()
    results = []
    t0 = time.time()

    with eng.connect() as conn:
        for v in VALIDATIONS:
            try:
                value = conn.execute(text(v["sql"])).scalar()
                value = int(value) if value is not None else None
                status = "PASS" if value == v["expected"] else "FAIL"
            except Exception as e:
                value = None
                status = "ERROR"
                log.error(f"  [{v['name']}] {e}")

            results.append({
                "category": v["category"],
                "name":     v["name"],
                "expected": v["expected"],
                "actual":   value,
                "status":   status,
            })

    df = pd.DataFrame(results)

    # Resumen por categoría
    log.info(f"\n{df.to_string(index=False)}")
    log.info("-" * 70)
    summary = df.groupby(["category", "status"]).size().unstack(fill_value=0)
    log.info(f"\nResumen por categoría:\n{summary}")

    n_pass = (df["status"] == "PASS").sum()
    n_fail = (df["status"] == "FAIL").sum()
    n_err  = (df["status"] == "ERROR").sum()
    total  = len(df)

    elapsed = time.time() - t0
    log.info("-" * 70)
    log.info(f"RESULTADO: {n_pass}/{total} PASS | {n_fail} FAIL | {n_err} ERROR")
    log.info(f"Tiempo: {elapsed:.2f}s")

    if n_fail or n_err:
        log.warning("⚠ Hay validaciones que NO han pasado. Revisar arriba.")
    else:
        log.info("✅ TODAS LAS VALIDACIONES HAN PASADO")
    log.info("=" * 70)

    return df


if __name__ == "__main__":
    run_validations()