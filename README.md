# Saleshealth · Customer Analytics

**Proyecto Final · Gestión de Datos · UAX 2025/2026 · Álvaro Santamaría Antón**

Construcción end-to-end de un entorno analítico sobre una base de datos operacional
de venta retail de productos de salud. Incluye pipeline ETL automatizado, Data Warehouse
dimensional, cálculo de Customer Lifetime Value (CLTV), segmentación RFM, scoring de
churn y clustering K-Means. Todo orquestado, validado y reproducible en menos de 20
segundos.

---

## Demo en vivo

🔗 **Dashboard interactivo:** [proyecto-dwh-salud-alvaro-santamaria.streamlit.app](https://proyecto-dwh-salud-alvaro-santamaria.streamlit.app/)

🔗 **Repositorio:** [github.com/AlvaroSantamariaAnton/proyecto-dwh-salud](https://github.com/AlvaroSantamariaAnton/proyecto-dwh-salud)

> El dashboard desplegado en Streamlit Cloud usa snapshots CSV versionados en el
> repositorio (`data/snapshots/`). Para datos en vivo desde PostgreSQL, sigue
> [Replicar el entorno en otro PC](#-replicar-el-entorno-en-otro-pc).

---

## Resumen ejecutivo

Pipeline analítico que toma una BD operacional con **17 tablas, 42.555 líneas de venta
y 6 años de histórico (2020-2025)** y la transforma en un Data Warehouse en estrella
con métricas accionables sobre **5.750 clientes únicos**.

### Hallazgos clave

| Insight | Cifra |
|---|---|
| Concentración de valor | El **13% de la base** (Champions Premium + activos) genera el **92,5% del CLTV** histórico (3,45 M€ de 3,76 M€) |
| Detección de toxicidad | El clustering revela **420 clientes con 88% de tasa de devolución** invisibles al RFM tradicional |
| Lista pre-churn accionable | **92 Champions En Riesgo** con CLTV >3.000€ y 349 días sin compra → ~338 K€ de CLTV potencial |
| Tiempo de pipeline | ETL completo end-to-end en **~19 segundos** con **21/21 validaciones automáticas** |

---

## Arquitectura

```
┌────────────────┐    ┌─────────┐    ┌──────────┐    ┌────────────────────┐    ┌──────────────┐
│    ORIGEN      │ ─> │ STAGING │ ─> │   DWH    │ ─> │       MARTS        │ ─> │  DASHBOARD   │
│ saleshealth_   │    │  stg.*  │    │  dwh.*   │    │ marts.customer_360 │    │  Streamlit   │
│   origen       │    │         │    │ 6 dim +  │    │ CLTV · RFM ·       │    │   + Plotly   │
│   (17 tablas)  │    │ Copia   │    │ 2 fact   │    │ Churn · Clustering │    │              │
└────────────────┘    └─────────┘    └──────────┘    └────────────────────┘    └──────────────┘
        │                  │              │                    │
        │                  └────── pipeline ETL automatizado ──┘
        │                          (Python · pandas · SQLAlchemy)
        │
        └─── pg_dump → restore en otra máquina
```

Modelo dimensional **tipo Kimball** con grano `1 línea de venta = 1 sale_item`, claves
subrogadas (SK) en todas las dimensiones, y dos hechos: `fact_sales` (ventas) +
`fact_returns` (devoluciones).

---

## Quick start

### Solo ver el dashboard online

[👉 Abrir el dashboard en vivo](https://proyecto-dwh-salud-alvaro-santamaria.streamlit.app/)

### Reproducir el dashboard en local sin Postgres

```bash
git clone https://github.com/AlvaroSantamariaAnton/proyecto-dwh-salud.git
cd proyecto-dwh-salud

python -m venv venv
# Windows: .\venv\Scripts\Activate.ps1
# Mac/Linux: source venv/bin/activate

pip install -r requirements.txt
streamlit run streamlit_app.py
```

El dashboard detecta automáticamente que no hay Postgres y carga los snapshots CSV
versionados (`data/snapshots/`). Listo en ~30 segundos.

---

## Estructura del proyecto

```
proyecto-dwh-salud/
├── etl/                         # Paquete Python con el pipeline
│   ├── extract.py               # Origen → stg
│   ├── transform_dimensions.py  # Carga las 6 dimensiones
│   ├── transform_facts.py       # Carga los 2 hechos (INSERT...SELECT)
│   ├── validate.py              # 21 validaciones declarativas
│   ├── build_customer_360.py    # CLTV (3 versiones) + RFM + Churn Risk
│   ├── build_clusters.py        # PCA + K-Means clustering
│   ├── run_etl.py               # Orquestador (6 fases secuenciales)
│   ├── config.py                # Conexión BD desde .env
│   ├── db.py                    # Helpers SQLAlchemy
│   └── logger.py                # Logging unificado
├── dashboard/                   # Aplicación Streamlit
│   ├── Inicio.py                # Home + KPIs preview
│   ├── pages/                   # 4 páginas: KPIs, Cliente, Clustering, Customer 360
│   ├── components.py            # Widgets reutilizables (KPI cards, headers)
│   ├── config.py                # Paleta dark + plantilla Plotly
│   ├── data.py                  # Carga con cache (auto-detecta Postgres/CSV)
│   └── snapshot_to_csv.py       # Genera snapshots CSV para deploy
├── sql/
│   ├── ddl/                     # 4 archivos DDL versionados
│   └── analytics/               # Queries SQL listas para ejecutar
├── notebooks/                   # Análisis exploratorio reproducible
├── data/
│   ├── raw/                     # Dump original de la BD origen
│   └── snapshots/               # CSVs versionados para Streamlit Cloud
├── docs/
│   ├── diagramas/               # ER de origen + Modelo dimensional (PNG/PDF/DBML)
│   ├── findings/                # Hallazgos de EDA + decisiones de diseño
│   └── entregables/             # Documento técnico final (.docx, .pdf)
├── reports/figures/             # 18 figuras generadas por los notebooks
├── streamlit_app.py             # Entry point para Streamlit Cloud
├── requirements.txt             # Dependencias mínimas (producción / dashboard)
├── requirements-dev.txt         # Dependencias completas (desarrollo + notebooks)
├── .streamlit/config.toml       # Tema dark forzado
└── .env.example                 # Plantilla de credenciales
```

---

## Replicar el entorno en otro PC

> **Prerrequisitos**: Python 3.11+, PostgreSQL 18 y Git instalados y operativos.

Tiempo estimado: **~10 minutos**.

### 1. Clonar el repositorio

```bash
git clone https://github.com/AlvaroSantamariaAnton/proyecto-dwh-salud.git
cd proyecto-dwh-salud
```

### 2. Crear entorno virtual e instalar dependencias

```bash
python -m venv venv
# Windows: .\venv\Scripts\Activate.ps1
# Mac/Linux: source venv/bin/activate

pip install -r requirements-dev.txt
```

> 💡 Usa `requirements.txt` (sin `-dev`) si solo quieres el dashboard, sin notebooks ni ETL.

### 3. Crear las dos bases de datos

Conecta a tu instancia de PostgreSQL (con `psql`, pgAdmin o tu cliente favorito) y ejecuta:

```sql
-- Rol de lectura para la BD origen
CREATE ROLE uaxuser WITH LOGIN PASSWORD 'uaxuser';

-- BD origen (donde se restaurará el dump)
CREATE DATABASE saleshealth_origen WITH OWNER = uaxuser ENCODING = 'UTF8';

-- BD destino (donde se carga el DWH)
CREATE DATABASE saleshealth_dwh WITH OWNER = postgres ENCODING = 'UTF8';

GRANT CONNECT ON DATABASE saleshealth_origen TO postgres;
```

> 💡 El proyecto usa **dos BDs separadas**: una para datos operacionales y otra para el
> Data Warehouse. Aísla el origen del modelo analítico, igual que en producción real.

### 4. Restaurar el dump de la BD origen

El dump (`saleshealthBackupGD.sql`, ~843 KB) está en `data/raw/`.

```bash
# Mac/Linux
PGPASSWORD=uaxuser pg_restore \
    -h localhost -p 5432 -U uaxuser -d saleshealth_origen \
    --no-owner --no-privileges --verbose \
    data/raw/saleshealthBackupGD.sql
```

```powershell
# Windows
$env:PGPASSWORD = "uaxuser"
pg_restore -h localhost -p 5432 -U uaxuser -d saleshealth_origen `
    --no-owner --no-privileges --verbose `
    "data\raw\saleshealthBackupGD.sql"
```

Verifica que se ha restaurado bien:
```sql
-- Conectado a saleshealth_origen
SELECT COUNT(*) FROM customer;   -- 5750
SELECT COUNT(*) FROM sale_item;  -- 42555
```

### 5. Configurar el archivo `.env`

```bash
cp .env.example .env  # Windows: copy .env.example .env
```

Edita `.env` con tus credenciales reales:

```env
DB_USER=postgres
DB_PASSWORD=tu_password_de_postgres
DB_HOST=localhost
DB_PORT=5432
DB_NAME_ORIGEN=saleshealth_origen
DB_NAME_DWH=saleshealth_dwh
```

> ⚠️ El `.env` está en `.gitignore` y nunca se sube al repo. Cada máquina tiene
> su propio `.env`.

### 6. Ejecutar los 4 DDL sobre `saleshealth_dwh`

```bash
# Mac/Linux
for f in 01_dwh_dimensions 02_dwh_facts 03_marts_customer360 04_marts_customer360_clusters; do
    PGPASSWORD=$DB_PASSWORD psql -h localhost -U postgres -d saleshealth_dwh -f "sql/ddl/$f.sql"
done
```

```powershell
# Windows
$env:PGPASSWORD = "tu_password"
foreach ($f in @("01_dwh_dimensions","02_dwh_facts","03_marts_customer360","04_marts_customer360_clusters")) {
    psql -h localhost -U postgres -d saleshealth_dwh -f "sql\ddl\$f.sql"
}
```

> 💡 También puedes ejecutarlos manualmente con pgAdmin abriendo cada `.sql` y dándole a F5.

### 7. Ejecutar el pipeline ETL

```bash
python -m etl.run_etl
```

Output esperado (~19 segundos):

```
>>> FASE 1/6 — EXTRACT             17/17 tablas · 7.4s
>>> FASE 2/6 — DIMENSIONES         6 dim cargadas
>>> FASE 3/6 — HECHOS              fact_sales: 42.555 · fact_returns: 2.330
>>> FASE 4/6 — VALIDACIONES        ✅ 21/21 PASS
>>> FASE 5/6 — CUSTOMER_360        5.750 filas con CLTV+RFM+Churn
>>> FASE 6/6 — CLUSTERING          4 clusters globales + 4 sub-clusters

✅ PIPELINE ETL COMPLETADO — tiempo total: 19.34s
```

### 8. Lanzar el dashboard

```bash
streamlit run streamlit_app.py
```

Abre `http://localhost:8501`. El dashboard detectará automáticamente que tienes
Postgres corriendo y cargará desde la BD en lugar de los CSVs.

---

### Regenerar los snapshots CSV (opcional)

Si modificas los datos y quieres actualizar el dashboard online:

```bash
python -m dashboard.snapshot_to_csv
git add data/snapshots/
git commit -m "Update snapshots"
git push
```

Streamlit Cloud detectará el push y redeployará automáticamente.

---

## Pipeline ETL: 6 fases

| # | Fase | Qué hace | Tiempo |
|---|---|---|---|
| 1 | EXTRACT | Lee 17 tablas de `saleshealth_origen.public` y las carga en `saleshealth_dwh.stg.*` | ~7,5 s |
| 2 | TRANSFORM + LOAD: DIMENSIONES | Genera 6 dimensiones (date, customer, product, store, offer, return_reason) con SK y NK | ~2 s |
| 3 | TRANSFORM + LOAD: HECHOS | Carga `fact_sales` y `fact_returns` vía `INSERT…SELECT` con pushdown a Postgres | ~2 s |
| 4 | VALIDACIONES | 21 validaciones automáticas: row counts, FK integrity, business rules, decisiones | ~0,1 s |
| 5 | BUILD CUSTOMER_360 | Genera `marts.customer_360` con 3 versiones de CLTV, scoring RFM y Churn Risk | ~3,8 s |
| 6 | BUILD CLUSTERS | PCA + K-Means sobre todos (K=4) + sobre recurrentes (K=4) | ~3,7 s |

**Total end-to-end: ~19 segundos** sobre PostgreSQL local. Idempotente
(`TRUNCATE+INSERT`), por lo que puedes lanzarlo cuantas veces quieras sin
estado residual.

---

## Dashboard

Aplicación Streamlit con 5 vistas:

| Página | Contenido |
|---|---|
| **Inicio** | KPIs ejecutivos · Hallazgo principal · Stack técnico |
| **KPIs Globales** | Ingresos, márgenes, evolución temporal del negocio |
| **Análisis Cliente** | Distribución de CLTV, segmentos RFM, top clientes, churn risk |
| **Clustering** | Visualización 2D (PCA), perfil de cada cluster, cruce con RFM |
| **Customer 360** | Buscador individual con ficha completa por cliente |

**Tema dark forzado**, paleta de colores consistente entre clusters/segmentos,
gráficos interactivos con Plotly y cache de queries (TTL 10 min).

---

## Modelo de datos

### Esquemas

- **`stg.*`** — Staging: copia 1:1 del origen (datos crudos)
- **`dwh.*`** — Data Warehouse dimensional (esquema en estrella)
  - 6 dimensiones: `dim_date`, `dim_customer`, `dim_product`, `dim_store`,
    `dim_offer`, `dim_return_reason`
  - 2 hechos: `fact_sales` (grano: línea de venta), `fact_returns`
- **`marts.*`** — Vistas analíticas pre-calculadas
  - `customer_360`: una fila por cliente con CLTV (3 versiones), RFM, Churn Risk
    y asignación de cluster

### Hallazgos del EDA · decisiones de diseño

- **Producto 29 sin coste** en `central_product` → coste imputado = 0,60 × precio
  (margen 40% como el resto), flag `is_cost_imputed=TRUE` para trazabilidad
- **Tablas huérfanas** (`city_zone`, `return_reason`) → enlace por
  `postal_code` y `reason_id` respectivamente (relación implícita)
- **Anomalía sale_id 13.009** (+3,00€ inexplicable) → recálculo determinista:
  `net_revenue = SUM(item.subtotal)` (los items son fuente de verdad)
- **Devoluciones**: dual storage → `fact_returns` como hecho secundario + flag
  `is_returned` en `fact_sales` (optimización para CLTV neto)

---

## Sobre el proyecto

- **Asignatura**: Gestión de Datos
- **Universidad**: Universidad Alfonso X el Sabio (UAX)
- **Curso**: 2025/2026
- **Autor**: Álvaro Santamaría Antón
- **Documento técnico final**: disponible en `docs/entregables/Proyecto_Final_GD_Santamaria.pdf`

### Referencias

- Business Research Insights (2024). *Health and Wellness Products Market Report — 2026 to 2035.*
- Putler (2024). *14 Customer Retention Metrics & KPIs to Track (With Formulas).*
- ProsperStack (2024). *28 Customer Retention Metric Formulas for Business Success.*
- Kimball, R. & Ross, M. (2013). *The Data Warehouse Toolkit: The Definitive Guide to Dimensional Modeling* (3ª ed.). Wiley.
