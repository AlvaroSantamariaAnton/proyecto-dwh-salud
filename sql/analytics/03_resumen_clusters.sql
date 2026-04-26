-- ============================================================================
-- Resumen ejecutivo del clustering: KPIs por segmento
-- ============================================================================
SELECT 
    cluster_all_name,
    COUNT(*)                                          AS n_clientes,
    ROUND(AVG(cltv_historic)::numeric, 0)             AS cltv_avg,
    ROUND(SUM(cltv_historic)::numeric, 0)             AS cltv_total,
    ROUND(100.0 * SUM(cltv_historic) / 
        SUM(SUM(cltv_historic)) OVER ()::numeric, 1)  AS pct_cltv,
    ROUND(AVG(num_orders)::numeric, 1)                AS orders_avg,
    ROUND(AVG(return_rate)::numeric, 3)               AS return_rate_avg
FROM marts.customer_360
GROUP BY cluster_all_name
ORDER BY cltv_total DESC;