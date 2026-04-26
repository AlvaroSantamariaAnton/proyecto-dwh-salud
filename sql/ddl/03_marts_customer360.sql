-- ============================================================================
-- DDL MARTS — customer_360
-- Vista analítica completa de cada cliente:
--   - Métricas básicas (compras, ingresos, ticket medio)
--   - Devoluciones y comportamiento postventa
--   - 3 versiones del CLTV (histórico, predictivo, fórmula enunciado)
--   - RFM Score y segmentación
--   - Churn Risk Score
-- ============================================================================

DROP TABLE IF EXISTS marts.customer_360 CASCADE;

CREATE TABLE marts.customer_360 (
    -- ----- Identificación -----
    customer_sk          INTEGER       PRIMARY KEY REFERENCES dwh.dim_customer(customer_sk),
    customer_id_nk       INTEGER       NOT NULL UNIQUE,
    full_name            VARCHAR(310),
    email                VARCHAR(150),
    cohort_year          SMALLINT,
    cohort_month         VARCHAR(7),

    -- ----- Volumen de actividad -----
    num_orders           INTEGER       NOT NULL DEFAULT 0,   -- nº ventas (sale_id distintos)
    num_items            INTEGER       NOT NULL DEFAULT 0,   -- nº líneas de venta
    total_units          INTEGER       NOT NULL DEFAULT 0,   -- suma de quantity

    -- ----- Métricas económicas (sin restar devoluciones) -----
    gross_revenue        NUMERIC(14,2) NOT NULL DEFAULT 0,
    discount_amount      NUMERIC(14,2) NOT NULL DEFAULT 0,
    net_revenue          NUMERIC(14,2) NOT NULL DEFAULT 0,
    cost_amount          NUMERIC(14,2) NOT NULL DEFAULT 0,
    gross_margin         NUMERIC(14,2) NOT NULL DEFAULT 0,
    avg_order_value      NUMERIC(12,2),                       -- ticket medio

    -- ----- Devoluciones -----
    num_returns          INTEGER       NOT NULL DEFAULT 0,
    units_returned       INTEGER       NOT NULL DEFAULT 0,
    refund_amount        NUMERIC(14,2) NOT NULL DEFAULT 0,
    margin_lost_returns  NUMERIC(14,2) NOT NULL DEFAULT 0,
    return_rate          NUMERIC(5,4),                        -- units_returned / total_units

    -- ----- Métricas económicas NETAS (descontando devoluciones) -----
    net_revenue_after_returns   NUMERIC(14,2),                -- net_revenue - refund_amount
    net_margin_after_returns    NUMERIC(14,2),                -- gross_margin - margin_lost_returns

    -- ----- Temporales -----
    first_order_date     DATE,
    last_order_date      DATE,
    customer_lifespan_days INTEGER,                           -- last - first
    days_since_last_order  INTEGER,                           -- hoy - last_order_date
    purchase_frequency_year NUMERIC(8,4),                     -- num_orders / max(lifespan_days/365, 1)

    -- ----- Segmentación / flags -----
    is_one_shot          BOOLEAN       NOT NULL DEFAULT FALSE,
    is_recurrent         BOOLEAN       NOT NULL DEFAULT FALSE,
    is_active            BOOLEAN       NOT NULL DEFAULT FALSE, -- compró en últimos 365 días
    is_churned           BOOLEAN       NOT NULL DEFAULT FALSE, -- >365 días sin comprar
    has_returns          BOOLEAN       NOT NULL DEFAULT FALSE,

    -- ----- CLTV (3 versiones) -----
    cltv_historic        NUMERIC(14,2),  -- margen neto real ya generado
    cltv_predictive      NUMERIC(14,2),  -- proyección a 3 años (solo recurrentes)
    cltv_formula         NUMERIC(14,2),  -- fórmula literal del enunciado

    -- ----- RFM Score -----
    rfm_recency          INTEGER,        -- score 1-5 (5 = más reciente)
    rfm_frequency        INTEGER,        -- score 1-5 (5 = más frecuente)
    rfm_monetary         INTEGER,        -- score 1-5 (5 = más gasta)
    rfm_score            INTEGER,        -- suma R+F+M (3-15)
    rfm_segment          VARCHAR(40),    -- 'Champions', 'Loyal', 'At Risk', 'Lost'...

    -- ----- Churn Risk -----
    churn_risk_score     NUMERIC(5,4),   -- 0..1 (más alto = más riesgo)
    churn_risk_level     VARCHAR(20),    -- 'Low', 'Medium', 'High'

    -- ----- Auditoría -----
    snapshot_date        DATE          NOT NULL DEFAULT CURRENT_DATE,
    etl_loaded_at        TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_c360_cohort      ON marts.customer_360(cohort_year);
CREATE INDEX idx_c360_segment     ON marts.customer_360(rfm_segment);
CREATE INDEX idx_c360_churn       ON marts.customer_360(churn_risk_level);
CREATE INDEX idx_c360_churned     ON marts.customer_360(is_churned);
CREATE INDEX idx_c360_cltv_hist   ON marts.customer_360(cltv_historic DESC);

COMMENT ON TABLE marts.customer_360 IS 
    'Vista analítica 360 por cliente. Generada por etl/build_customer_360.py. Incluye CLTV (3 versiones), RFM y Churn Risk.';