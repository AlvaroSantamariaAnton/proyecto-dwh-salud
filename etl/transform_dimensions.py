"""
Bloque 3.3-3.4 - TRANSFORM + LOAD de dimensiones
stg → dwh.dim_*
"""
import time
import pandas as pd
from sqlalchemy import text

from etl.config import (
    DIM_DATE_START, DIM_DATE_END, SCHEMA_DWH,
    HUERFANO_PRODUCT_IDS, COST_IMPUTATION_RATIO, SK_OFFER_NONE,
)
from etl.db import get_engine_dwh, truncate_table, row_count, read_sql
from etl.logger import get_logger

log = get_logger()


# =============================================================================
# DIM_DATE
# =============================================================================
def build_dim_date() -> pd.DataFrame:
    """
    Genera dim_date sintética con todos los días del rango configurado.
    """
    log.info(f"  Generando rango de fechas {DIM_DATE_START} -> {DIM_DATE_END}")

    dates = pd.date_range(start=DIM_DATE_START, end=DIM_DATE_END, freq="D")
    df = pd.DataFrame({"full_date": dates})

    # date_sk en formato YYYYMMDD (entero)
    df["date_sk"] = df["full_date"].dt.strftime("%Y%m%d").astype(int)

    df["year"]          = df["full_date"].dt.year.astype("int16")
    df["quarter"]       = df["full_date"].dt.quarter.astype("int16")
    df["quarter_name"]  = "Q" + df["quarter"].astype(str) + " " + df["year"].astype(str)
    df["month"]         = df["full_date"].dt.month.astype("int16")

    # Nombres en español (los importamos como literales para no depender del locale)
    meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
             "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
    meses_short = ["Ene","Feb","Mar","Abr","May","Jun",
                   "Jul","Ago","Sep","Oct","Nov","Dic"]
    dias = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]

    df["month_name"]    = df["month"].apply(lambda m: meses[m-1])
    df["month_short"]   = df["month"].apply(lambda m: meses_short[m-1])

    df["week_of_year"]  = df["full_date"].dt.isocalendar().week.astype("int16")
    df["day_of_month"]  = df["full_date"].dt.day.astype("int16")
    # Pandas: Lunes=0 ... Domingo=6 → ajustamos a 1..7
    df["day_of_week"]   = (df["full_date"].dt.dayofweek + 1).astype("int16")
    df["day_name"]      = df["day_of_week"].apply(lambda d: dias[d-1])
    df["is_weekend"]    = df["day_of_week"].isin([6, 7])

    df["year_month"]    = df["full_date"].dt.strftime("%Y-%m")
    df["year_quarter"]  = df["year"].astype(str) + "-Q" + df["quarter"].astype(str)

    # Reordenar columnas según DDL (importante)
    cols = [
        "date_sk", "full_date", "year", "quarter", "quarter_name",
        "month", "month_name", "month_short", "week_of_year",
        "day_of_month", "day_of_week", "day_name", "is_weekend",
        "year_month", "year_quarter",
    ]
    return df[cols]


def load_dim_date():
    """Carga dim_date al DWH."""
    eng = get_engine_dwh()
    log.info("[dim_date] TRUNCATE + INSERT")
    t0 = time.time()

    truncate_table(SCHEMA_DWH, "dim_date", eng)

    df = build_dim_date()
    log.info(f"  Filas a cargar: {len(df)}")

    df.to_sql(
        name="dim_date",
        con=eng,
        schema=SCHEMA_DWH,
        if_exists="append",
        index=False,
        chunksize=2000,
        method="multi",
    )

    n = row_count(SCHEMA_DWH, "dim_date", eng)
    log.info(f"[dim_date] OK | {n} filas cargadas en {time.time()-t0:.2f}s")
    return n


# =============================================================================
# DIM_RETURN_REASON
# =============================================================================
def load_dim_return_reason():
    """Copia directa de stg.return_reason."""
    eng = get_engine_dwh()
    log.info("[dim_return_reason] TRUNCATE + INSERT")
    t0 = time.time()

    truncate_table(SCHEMA_DWH, "dim_return_reason", eng)

    df = read_sql("""
        SELECT 
            reason_id    AS reason_id_nk,
            reason       AS reason,
            active       AS is_active
        FROM stg.return_reason
        ORDER BY reason_id;
    """, eng)
    log.info(f"  Filas a cargar: {len(df)}")

    df.to_sql(
        name="dim_return_reason",
        con=eng,
        schema=SCHEMA_DWH,
        if_exists="append",
        index=False,
    )

    n = row_count(SCHEMA_DWH, "dim_return_reason", eng)
    log.info(f"[dim_return_reason] OK | {n} filas en {time.time()-t0:.2f}s")
    return n


# =============================================================================
# DIM_OFFER
# =============================================================================
def load_dim_offer():
    """
    Carga dim_offer.
    Incluye un registro especial offer_sk=0 con offer_id_nk=NULL para 
    representar 'sin oferta' (lo usaremos en fact_sales para items sin oferta).
    """
    eng = get_engine_dwh()
    log.info("[dim_offer] TRUNCATE + INSERT")
    t0 = time.time()

    truncate_table(SCHEMA_DWH, "dim_offer", eng)

    # 1) Insertar el registro especial 'sin oferta' con SK=0 (forzado)
    with eng.begin() as conn:
        conn.execute(text("""
            INSERT INTO dwh.dim_offer 
                (offer_sk, offer_id_nk, name, description, 
                 discount_percent, start_date, end_date, is_active)
            VALUES 
                (0, NULL, 'Sin oferta', 'Registro especial para items sin oferta aplicada', 
                 0.00, NULL, NULL, FALSE);
        """))
        # Reajustar la secuencia para que el siguiente INSERT use SK >= 1
        conn.execute(text(
            "SELECT setval('dwh.dim_offer_offer_sk_seq', 1, false);"
        ))

    # 2) Insertar las ofertas reales desde stg
    df = read_sql("""
        SELECT 
            offer_id          AS offer_id_nk,
            name              AS name,
            description       AS description,
            discount_percent  AS discount_percent,
            start_date        AS start_date,
            end_date          AS end_date,
            CASE 
                WHEN CURRENT_DATE BETWEEN start_date AND end_date THEN TRUE 
                ELSE FALSE 
            END AS is_active
        FROM stg.offer
        ORDER BY offer_id;
    """, eng)
    log.info(f"  Ofertas reales a cargar: {len(df)} (+1 registro 'Sin oferta')")

    df.to_sql(
        name="dim_offer",
        con=eng,
        schema=SCHEMA_DWH,
        if_exists="append",
        index=False,
    )

    n = row_count(SCHEMA_DWH, "dim_offer", eng)
    log.info(f"[dim_offer] OK | {n} filas en {time.time()-t0:.2f}s")
    return n


# =============================================================================
# DIM_STORE (JOIN store + city_zone por postal_code)
# =============================================================================
def load_dim_store():
    """
    Carga dim_store enriquecida con datos geográficos de city_zone.
    Calcula years_open desde opened_date.
    """
    eng = get_engine_dwh()
    log.info("[dim_store] TRUNCATE + INSERT")
    t0 = time.time()

    truncate_table(SCHEMA_DWH, "dim_store", eng)

    df = read_sql("""
        SELECT 
            s.store_id           AS store_id_nk,
            s.name               AS name,
            s.address            AS address,
            s.city               AS city,
            s.postal_code        AS postal_code,
            cz.district          AS district,
            cz.area_type         AS area_type,
            cz.zone_orientation  AS zone_orientation,
            s.latitude           AS latitude,
            s.longitude          AS longitude,
            s.opened_date        AS opened_date,
            EXTRACT(YEAR FROM AGE(CURRENT_DATE, s.opened_date))::int AS years_open
        FROM stg.store s
        LEFT JOIN stg.city_zone cz ON s.postal_code = cz.postal_code
        ORDER BY s.store_id;
    """, eng)

    # Validación: ¿hay tiendas sin enriquecer? (no debería)
    sin_district = df["district"].isna().sum()
    if sin_district > 0:
        log.warning(f"  ⚠ {sin_district} tiendas sin match en city_zone")
    log.info(f"  Filas a cargar: {len(df)}")

    df.to_sql(
        name="dim_store",
        con=eng,
        schema=SCHEMA_DWH,
        if_exists="append",
        index=False,
    )

    n = row_count(SCHEMA_DWH, "dim_store", eng)
    log.info(f"[dim_store] OK | {n} filas en {time.time()-t0:.2f}s")
    return n


# =============================================================================
# DIM_CUSTOMER (con cálculo de cohort)
# =============================================================================
def load_dim_customer():
    """
    Carga dim_customer con cálculo de cohort_year y cohort_month
    a partir de created_at.
    """
    eng = get_engine_dwh()
    log.info("[dim_customer] TRUNCATE + INSERT")
    t0 = time.time()

    truncate_table(SCHEMA_DWH, "dim_customer", eng)

    df = read_sql("""
        SELECT 
            customer_id       AS customer_id_nk,
            first_name        AS first_name,
            last_name         AS last_name,
            last_name2        AS last_name2,
            TRIM(CONCAT_WS(' ', first_name, last_name, last_name2)) AS full_name,
            email             AS email,
            phone             AS phone,
            created_at        AS created_at,
            EXTRACT(YEAR FROM created_at)::smallint AS cohort_year,
            TO_CHAR(created_at, 'YYYY-MM')          AS cohort_month
        FROM stg.customer
        ORDER BY customer_id;
    """, eng)
    log.info(f"  Filas a cargar: {len(df)}")

    df.to_sql(
        name="dim_customer",
        con=eng,
        schema=SCHEMA_DWH,
        if_exists="append",
        index=False,
        chunksize=2000,
        method="multi",
    )

    n = row_count(SCHEMA_DWH, "dim_customer", eng)
    log.info(f"[dim_customer] OK | {n} filas en {time.time()-t0:.2f}s")
    return n


# =============================================================================
# DIM_PRODUCT (JOIN product + central_product + category + brand
#              + imputación coste para producto huérfano)
# =============================================================================
def load_dim_product():
    """
    Carga dim_product:
    - JOIN entre product (mundo tienda) y central_product (mundo almacén)
    - Denormaliza category.name y brand.name
    - Imputa unit_cost = price * 0.60 para productos sin record en central_product
      (decisión Fase 1: producto huérfano product_id=29)
    - Marca is_cost_imputed=TRUE en esos casos
    """
    eng = get_engine_dwh()
    log.info("[dim_product] TRUNCATE + INSERT")
    t0 = time.time()

    truncate_table(SCHEMA_DWH, "dim_product", eng)

    df = read_sql(f"""
        SELECT 
            p.product_id                            AS product_id_nk,
            p.name                                  AS name,
            p.category                              AS category,
            cp.category_id                          AS category_id_nk,
            cat.name                                AS category_normalized,
            br.name                                 AS brand_name,
            cp.brand_id                             AS brand_id_nk,
            p.manufacturer                          AS manufacturer,
            cp.sku                                  AS sku,
            cp.barcode                              AS barcode,
            COALESCE(
                cp.unit_cost, 
                ROUND((p.price * {COST_IMPUTATION_RATIO})::numeric, 2)
            )                                       AS unit_cost,
            p.price                                 AS unit_price,
            ROUND(
                (100.0 * (p.price - COALESCE(
                    cp.unit_cost, 
                    p.price * {COST_IMPUTATION_RATIO}
                )) / NULLIF(p.price, 0))::numeric, 2
            )                                       AS profit_margin_pct,
            (cp.product_id IS NULL)                 AS is_cost_imputed,
            (cp.product_id IS NOT NULL)             AS has_central_record,
            p.created_at                            AS created_at
        FROM stg.product p
        LEFT JOIN stg.central_product cp ON p.product_id = cp.product_id
        LEFT JOIN stg.category cat       ON cp.category_id = cat.category_id
        LEFT JOIN stg.brand br           ON cp.brand_id = br.brand_id
        ORDER BY p.product_id;
    """, eng)

    # Validación
    n_imputados = df["is_cost_imputed"].sum()
    log.info(f"  Filas a cargar: {len(df)} (de los cuales {n_imputados} con coste imputado)")
    if n_imputados > 0:
        imputados = df[df["is_cost_imputed"]][["product_id_nk", "name", "unit_price", "unit_cost"]]
        log.info(f"  Productos con coste imputado:\n{imputados.to_string(index=False)}")

    df.to_sql(
        name="dim_product",
        con=eng,
        schema=SCHEMA_DWH,
        if_exists="append",
        index=False,
    )

    n = row_count(SCHEMA_DWH, "dim_product", eng)
    log.info(f"[dim_product] OK | {n} filas en {time.time()-t0:.2f}s")
    return n


# =============================================================================
# Orquestador (provisional, lo iremos extendiendo)
# =============================================================================
def run_transform_dimensions():
    log.info("=" * 70)
    log.info("INICIANDO TRANSFORM + LOAD: dimensiones")
    log.info("=" * 70)

    load_dim_date()
    load_dim_return_reason()
    load_dim_offer()
    load_dim_store()
    load_dim_customer()
    load_dim_product()

    log.info("=" * 70)
    log.info("TRANSFORM + LOAD de dimensiones COMPLETADO")
    log.info("=" * 70)


if __name__ == "__main__":
    run_transform_dimensions()