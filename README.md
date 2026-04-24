# Proyecto Final - Gestión de Datos (DWH y CLTV)

Construcción de un entorno analítico (Data Warehouse) sobre datos de venta de productos de salud y cálculo de métricas de cliente (CLTV, PCA, clustering).

## Setup

### Requisitos
- Python 3.11+
- PostgreSQL 17

### Instalación
1. Clonar el repo
2. Crear venv: \python -m venv venv\
3. Activar: \.\venv\Scripts\Activate.ps1\ (Windows)
4. Instalar dependencias: \pip install -r requirements.txt\
5. Crear BD origen en Postgres: \saleshealth_origen\
6. Restaurar el dump:
   \\\
   pg_restore -U postgres -d saleshealth_origen -v data/raw/saleshealthBackupGD.sql
   \\\
7. Copiar \.env.example\ a \.env\ y rellenar credenciales.

## Estructura
- \data/\ - dumps y datos brutos/procesados
- \sql/\ - scripts DDL del DWH y consultas analíticas
- \etl/\ - pipeline ETL en Python
- \
otebooks/\ - exploración y análisis
- \docs/\ - diagramas y documentación
- \eports/\ - figuras y outputs
