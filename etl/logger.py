"""
Logging unificado para el ETL.
Cada ejecución genera un fichero en etl/logs/etl_YYYYMMDD_HHMMSS.log
"""
import logging
import sys
from datetime import datetime
from etl.config import LOG_DIR

_logger = None

def get_logger(name: str = "etl") -> logging.Logger:
    """Devuelve un logger configurado (singleton)."""
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    # Formato
    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Handler consola
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # Handler fichero
    log_file = LOG_DIR / f"etl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    logger.info(f"Logger inicializado. Fichero: {log_file}")
    _logger = logger
    return logger