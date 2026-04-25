"""
Bloque 3.2 - EXTRACT
Copia las 17 tablas de saleshealth_origen.public al esquema stg de saleshealth_dwh.
Estrategia: full refresh (TRUNCATE + INSERT cada vez).
"""
import time
import pandas as pd
from sqlalchemy import text

from etl.config import ORIGIN_TABLES, SCHEMA_STG
from etl.db import get_engine_origen, get_engine_dwh
from etl.logger import get_logger

log = get_logger()


def ensure_stg_schema():
    """Asegura que el esquema stg existe."""
    eng = get_engine_dwh()
    with eng.begin() as conn:
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_STG};"))
    log.info(f"Esquema '{SCHEMA_STG}' verificado/creado.")


def extract_table(table_name: str) -> dict:
    """
    Extrae una tabla de origen y la carga en stg con la misma estructura.
    Devuelve dict con métricas de la operación.
    """
    eng_src = get_engine_origen()
    eng_dst = get_engine_dwh()

    t0 = time.time()

    # 1) Leer tabla completa desde origen
    log.info(f"  [{table_name}] Leyendo de origen...")
    with eng_src.connect() as conn:
        df = pd.read_sql(text(f'SELECT * FROM public."{table_name}";'), conn)
    n_origen = len(df)
    t_read = time.time() - t0

    # 2) Escribir en staging (replace = recrea tabla con misma estructura)
    log.info(f"  [{table_name}] Escribiendo en {SCHEMA_STG} ({n_origen} filas)...")
    t1 = time.time()
    df.to_sql(
        name=table_name,
        con=eng_dst,
        schema=SCHEMA_STG,
        if_exists="replace",
        index=False,
        chunksize=5000,
        method="multi",
    )
    t_write = time.time() - t1

    # 3) Verificar count en destino
    with eng_dst.connect() as conn:
        n_dst = conn.execute(
            text(f"SELECT COUNT(*) FROM {SCHEMA_STG}.{table_name};")
        ).scalar()

    elapsed = time.time() - t0
    status = "OK" if n_origen == n_dst else "MISMATCH"
    log.info(
        f"  [{table_name}] {status} | origen={n_origen} dst={n_dst} | "
        f"read={t_read:.2f}s write={t_write:.2f}s total={elapsed:.2f}s"
    )

    return {
        "table": table_name,
        "rows_origen": n_origen,
        "rows_dst": n_dst,
        "status": status,
        "time_read_s": round(t_read, 2),
        "time_write_s": round(t_write, 2),
        "time_total_s": round(elapsed, 2),
    }


def run_extract() -> pd.DataFrame:
    """Ejecuta la extracción completa de las 17 tablas."""
    log.info("=" * 70)
    log.info("INICIANDO EXTRACT: origen -> stg")
    log.info("=" * 70)

    ensure_stg_schema()

    results = []
    t_global = time.time()

    for tbl in ORIGIN_TABLES:
        try:
            res = extract_table(tbl)
            results.append(res)
        except Exception as e:
            log.error(f"  [{tbl}] ERROR: {e}")
            results.append({
                "table": tbl,
                "rows_origen": None,
                "rows_dst": None,
                "status": "ERROR",
                "error": str(e),
            })

    df_results = pd.DataFrame(results)
    total_time = time.time() - t_global

    # Resumen
    log.info("=" * 70)
    log.info("RESUMEN EXTRACT")
    log.info("=" * 70)
    log.info(f"\n{df_results.to_string(index=False)}")
    ok = (df_results["status"] == "OK").sum()
    log.info(f"\nTotal: {ok}/{len(df_results)} tablas extraídas correctamente")
    log.info(f"Tiempo total: {total_time:.2f}s")

    return df_results


if __name__ == "__main__":
    run_extract()