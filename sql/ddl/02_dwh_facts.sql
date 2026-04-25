-- ============================================================================
-- DDL HECHOS — saleshealth_dwh
-- ============================================================================

-- ----------------------------------------------------------------------------
-- FACT_SALES (grano: 1 línea de venta = 1 sale_item)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS dwh.fact_sales CASCADE;
CREATE TABLE dwh.fact_sales (
    sale_item_sk        BIGSERIAL      PRIMARY KEY,
    sale_id_nk          INTEGER        NOT NULL,
    sale_item_id_nk     INTEGER        NOT NULL UNIQUE,
    customer_sk         INTEGER        NOT NULL REFERENCES dwh.dim_customer(customer_sk),
    product_sk          INTEGER        NOT NULL REFERENCES dwh.dim_product(product_sk),
    store_sk            INTEGER        NOT NULL REFERENCES dwh.dim_store(store_sk),
    date_sk             INTEGER        NOT NULL REFERENCES dwh.dim_date(date_sk),
    offer_sk            INTEGER        NOT NULL REFERENCES dwh.dim_offer(offer_sk),
    sale_timestamp      TIMESTAMP      NOT NULL,
    quantity            INTEGER        NOT NULL,
    unit_price          NUMERIC(10,2)  NOT NULL,
    unit_cost           NUMERIC(10,2),
    gross_revenue       NUMERIC(12,2)  NOT NULL,
    discount_amount     NUMERIC(12,2)  NOT NULL DEFAULT 0,
    net_revenue         NUMERIC(12,2)  NOT NULL,
    cost_amount         NUMERIC(12,2),
    gross_margin        NUMERIC(12,2),
    is_returned         BOOLEAN        NOT NULL DEFAULT FALSE,
    is_cost_imputed     BOOLEAN        NOT NULL DEFAULT FALSE,
    has_offer           BOOLEAN        NOT NULL DEFAULT FALSE,
    etl_loaded_at       TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_fact_sales_customer ON dwh.fact_sales(customer_sk);
CREATE INDEX idx_fact_sales_product  ON dwh.fact_sales(product_sk);
CREATE INDEX idx_fact_sales_store    ON dwh.fact_sales(store_sk);
CREATE INDEX idx_fact_sales_date     ON dwh.fact_sales(date_sk);
CREATE INDEX idx_fact_sales_returned ON dwh.fact_sales(is_returned) WHERE is_returned = TRUE;
COMMENT ON TABLE dwh.fact_sales IS 'Hecho transaccional de ventas. Grano: 1 línea de venta (sale_item)';

-- ----------------------------------------------------------------------------
-- FACT_RETURNS (grano: 1 devolución = 1 return_item)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS dwh.fact_returns CASCADE;
CREATE TABLE dwh.fact_returns (
    return_sk           BIGSERIAL      PRIMARY KEY,
    return_id_nk        INTEGER        NOT NULL UNIQUE,
    sale_item_id_nk     INTEGER        NOT NULL,
    sale_item_sk        BIGINT         NOT NULL REFERENCES dwh.fact_sales(sale_item_sk),
    customer_sk         INTEGER        NOT NULL REFERENCES dwh.dim_customer(customer_sk),
    product_sk          INTEGER        NOT NULL REFERENCES dwh.dim_product(product_sk),
    store_sk            INTEGER        NOT NULL REFERENCES dwh.dim_store(store_sk),
    date_sk             INTEGER        NOT NULL REFERENCES dwh.dim_date(date_sk),
    reason_sk           INTEGER        REFERENCES dwh.dim_return_reason(reason_sk),
    return_timestamp    TIMESTAMP      NOT NULL,
    sale_timestamp      TIMESTAMP      NOT NULL,
    quantity_returned   INTEGER        NOT NULL,
    refund_amount       NUMERIC(12,2)  NOT NULL,
    cost_recovered      NUMERIC(12,2),
    margin_lost         NUMERIC(12,2),
    days_to_return      INTEGER        NOT NULL,
    etl_loaded_at       TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_fact_returns_customer ON dwh.fact_returns(customer_sk);
CREATE INDEX idx_fact_returns_product  ON dwh.fact_returns(product_sk);
CREATE INDEX idx_fact_returns_date     ON dwh.fact_returns(date_sk);
CREATE INDEX idx_fact_returns_reason   ON dwh.fact_returns(reason_sk);
COMMENT ON TABLE dwh.fact_returns IS 'Hecho transaccional de devoluciones. Grano: 1 línea de devolución';