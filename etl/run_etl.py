"""
Bloque 3.8 - ORQUESTADOR
Ejecuta el pipeline completo: extract → transform_dimensions → transform_facts → validate
Uso:  python -m etl.run_etl
"""
import sys
import time

from etl.extract import run_extract
from etl.transform_dimensions import run_transform_dimensions
from etl.transform_facts import run_transform_facts
from etl.validate import run_validations
from etl.logger import get_logger
from etl.build_customer_360 import load_customer_360
from etl.build_clusters import build_and_persist_clusters

log = get_logger()


def main() -> int:
    """
    Orquesta el ETL end-to-end. Devuelve 0 si todo OK, 1 si alguna fase falla.
    """
    t_global = time.time()
    log.info("#" * 70)
    log.info("# PIPELINE ETL — saleshealth_dwh")
    log.info("# Origen: saleshealth_origen.public")
    log.info("# Destino: saleshealth_dwh.{stg, dwh}")
    log.info("#" * 70)

    try:
        # FASE 1: EXTRACT
        log.info("\n>>> FASE 1/5 — EXTRACT")
        df_extract = run_extract()
        if (df_extract["status"] != "OK").any():
            log.error("❌ EXTRACT con errores. Abortando pipeline.")
            return 1

        # FASE 2: TRANSFORM + LOAD DIMENSIONES
        log.info("\n>>> FASE 2/5 — TRANSFORM + LOAD: DIMENSIONES")
        run_transform_dimensions()

        # FASE 3: TRANSFORM + LOAD HECHOS
        log.info("\n>>> FASE 3/5 — TRANSFORM + LOAD: HECHOS")
        run_transform_facts()

        # FASE 4: VALIDACIONES DEL DWH
        log.info("\n>>> FASE 4/5 — VALIDACIONES DWH")
        df_val = run_validations()
        n_fail = (df_val["status"] != "PASS").sum()
        if n_fail > 0:
            log.error(f"❌ {n_fail} validaciones no han pasado.")
            return 1

        # FASE 5: BUILD CUSTOMER_360
        log.info("\n>>> FASE 5/6 — BUILD MARTS.CUSTOMER_360")
        load_customer_360()

        # FASE 6: BUILD CLUSTERS
        log.info("\n>>> FASE 6/6 — PCA + CLUSTERING")
        build_and_persist_clusters()

    except Exception as e:
        log.exception(f"❌ Error fatal en el pipeline: {e}")
        return 1

    # Resumen final
    elapsed = time.time() - t_global
    log.info("\n" + "#" * 70)
    log.info(f"# ✅ PIPELINE ETL COMPLETADO — tiempo total: {elapsed:.2f}s")
    log.info("#" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())