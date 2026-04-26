-- ============================================================================
-- Evolución mensual de KPIs de venta
-- ============================================================================
SELECT 
    d.year_month,
    COUNT(DISTINCT s.sale_id_nk)                  AS n_ventas,
    COUNT(DISTINCT s.customer_sk)                 AS n_clientes,
    ROUND(SUM(s.net_revenue)::numeric, 2)         AS revenue,
    ROUND(SUM(s.gross_margin)::numeric, 2)        AS margin,
    ROUND(AVG(s.net_revenue)::numeric, 2)         AS ticket_medio_item
FROM dwh.fact_sales s
JOIN dwh.dim_date d ON s.date_sk = d.date_sk
GROUP BY d.year_month
ORDER BY d.year_month;