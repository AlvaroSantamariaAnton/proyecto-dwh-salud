"""
Configuración centralizada del ETL.
Carga variables de entorno desde .env y define constantes.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env desde la raíz del proyecto
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# -----------------------------------------------------------------
# Conexiones a BD
# -----------------------------------------------------------------
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = os.getenv("DB_PORT", "5432")
DB_USER     = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

DB_ORIGEN   = os.getenv("DB_NAME_ORIGEN", "saleshealth_origen")
DB_DWH      = os.getenv("DB_NAME_DWH", "saleshealth_dwh")


def db_url(db_name: str) -> str:
    """Devuelve la URL SQLAlchemy para la BD indicada."""
    return f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{db_name}"


URL_ORIGEN = db_url(DB_ORIGEN)
URL_DWH    = db_url(DB_DWH)

# -----------------------------------------------------------------
# Esquemas en el DWH
# -----------------------------------------------------------------
SCHEMA_STG   = "stg"
SCHEMA_DWH   = "dwh"
SCHEMA_MARTS = "marts"

# -----------------------------------------------------------------
# Reglas de negocio (decisiones tomadas en Fase 1)
# -----------------------------------------------------------------
HUERFANO_PRODUCT_IDS  = [29]
COST_IMPUTATION_RATIO = 0.60

RECALCULAR_SALE_TOTAL = True

SK_OFFER_NONE = 0

DIM_DATE_START = "2019-01-01"
DIM_DATE_END   = "2026-12-31"

# -----------------------------------------------------------------
# Paths
# -----------------------------------------------------------------
LOG_DIR = PROJECT_ROOT / "etl" / "logs"
LOG_DIR.mkdir(exist_ok=True, parents=True)

# Tablas a extraer del origen
ORIGIN_TABLES = [
    "brand", "category", "central_inventory", "central_product",
    "city_zone", "customer", "inventory", "offer", "product",
    "product_offer", "return_item", "return_reason",
    "sale", "sale_item", "store", "warehouse", "warehouse_location"
]