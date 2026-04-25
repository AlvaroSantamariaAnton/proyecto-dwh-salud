-- ============================================================================
-- DDL DIMENSIONES — saleshealth_dwh
-- Proyecto Final GD-UAX
-- ============================================================================

-- ----------------------------------------------------------------------------
-- DIM_DATE
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS dwh.dim_date CASCADE;
CREATE TABLE dwh.dim_date (
    date_sk           INTEGER       PRIMARY KEY,
    full_date         DATE          NOT NULL UNIQUE,
    year              SMALLINT      NOT NULL,
    quarter           SMALLINT      NOT NULL,
    quarter_name      VARCHAR(10)   NOT NULL,
    month             SMALLINT      NOT NULL,
    month_name        VARCHAR(20)   NOT NULL,
    month_short       VARCHAR(3)    NOT NULL,
    week_of_year      SMALLINT      NOT NULL,
    day_of_month      SMALLINT      NOT NULL,
    day_of_week       SMALLINT      NOT NULL,
    day_name          VARCHAR(20)   NOT NULL,
    is_weekend        BOOLEAN       NOT NULL,
    year_month        VARCHAR(7)    NOT NULL,
    year_quarter      VARCHAR(7)    NOT NULL
);
COMMENT ON TABLE dwh.dim_date IS 'Dimensión temporal generada sintéticamente';

-- ----------------------------------------------------------------------------
-- DIM_CUSTOMER
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS dwh.dim_customer CASCADE;
CREATE TABLE dwh.dim_customer (
    customer_sk       SERIAL        PRIMARY KEY,
    customer_id_nk    INTEGER       NOT NULL UNIQUE,
    first_name        VARCHAR(100),
    last_name         VARCHAR(100),
    last_name2        VARCHAR(100),
    full_name         VARCHAR(310),
    email             VARCHAR(150)  UNIQUE,
    phone             VARCHAR(20),
    created_at        TIMESTAMP     NOT NULL,
    cohort_year       SMALLINT,
    cohort_month      VARCHAR(7),
    etl_loaded_at     TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_dim_customer_nk     ON dwh.dim_customer(customer_id_nk);
CREATE INDEX idx_dim_customer_cohort ON dwh.dim_customer(cohort_year, cohort_month);
COMMENT ON TABLE dwh.dim_customer IS 'Dimensión cliente (SCD Type 1)';

-- ----------------------------------------------------------------------------
-- DIM_PRODUCT
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS dwh.dim_product CASCADE;
CREATE TABLE dwh.dim_product (
    product_sk          SERIAL        PRIMARY KEY,
    product_id_nk       INTEGER       NOT NULL UNIQUE,
    name                VARCHAR(200)  NOT NULL,
    category            VARCHAR(100),
    category_id_nk      INTEGER,
    category_normalized VARCHAR(100),
    brand_name          VARCHAR(150),
    brand_id_nk         INTEGER,
    manufacturer        VARCHAR(150),
    sku                 VARCHAR(50),
    barcode             VARCHAR(50),
    unit_cost           NUMERIC(10,2),
    unit_price          NUMERIC(10,2)  NOT NULL,
    profit_margin_pct   NUMERIC(5,2),
    is_cost_imputed     BOOLEAN        NOT NULL DEFAULT FALSE,
    has_central_record  BOOLEAN        NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMP,
    etl_loaded_at       TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_dim_product_nk        ON dwh.dim_product(product_id_nk);
CREATE INDEX idx_dim_product_category  ON dwh.dim_product(category);
CREATE INDEX idx_dim_product_brand     ON dwh.dim_product(brand_name);
COMMENT ON TABLE dwh.dim_product IS 'Dimensión producto (SCD Type 1) — JOIN product+central_product+category+brand';
COMMENT ON COLUMN dwh.dim_product.is_cost_imputed IS 'TRUE si unit_cost fue estimado (60% del precio) por falta de dato en central_product';

-- ----------------------------------------------------------------------------
-- DIM_STORE
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS dwh.dim_store CASCADE;
CREATE TABLE dwh.dim_store (
    store_sk          SERIAL         PRIMARY KEY,
    store_id_nk       INTEGER        NOT NULL UNIQUE,
    name              VARCHAR(100)   NOT NULL,
    address           VARCHAR(200),
    city              VARCHAR(100),
    postal_code       VARCHAR(10),
    district          VARCHAR(100),
    area_type         VARCHAR(20),
    zone_orientation  VARCHAR(20),
    latitude          NUMERIC(9,6),
    longitude         NUMERIC(9,6),
    opened_date       DATE,
    years_open        INTEGER,
    etl_loaded_at     TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_dim_store_nk       ON dwh.dim_store(store_id_nk);
CREATE INDEX idx_dim_store_district ON dwh.dim_store(district);
COMMENT ON TABLE dwh.dim_store IS 'Dimensión tienda (SCD Type 1) — JOIN store+city_zone por postal_code';

-- ----------------------------------------------------------------------------
-- DIM_OFFER
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS dwh.dim_offer CASCADE;
CREATE TABLE dwh.dim_offer (
    offer_sk          SERIAL         PRIMARY KEY,
    offer_id_nk       INTEGER        UNIQUE,
    name              VARCHAR(150),
    description       TEXT,
    discount_percent  NUMERIC(5,2),
    start_date        DATE,
    end_date          DATE,
    is_active         BOOLEAN        DEFAULT FALSE,
    etl_loaded_at     TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE dwh.dim_offer IS 'Dimensión oferta. Incluye un registro especial offer_sk=0 para "sin oferta"';

-- ----------------------------------------------------------------------------
-- DIM_RETURN_REASON
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS dwh.dim_return_reason CASCADE;
CREATE TABLE dwh.dim_return_reason (
    reason_sk         SERIAL         PRIMARY KEY,
    reason_id_nk      INTEGER        NOT NULL UNIQUE,
    reason            VARCHAR(200)   NOT NULL,
    is_active         BOOLEAN        NOT NULL DEFAULT TRUE,
    etl_loaded_at     TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE dwh.dim_return_reason IS 'Dimensión motivo de devolución';