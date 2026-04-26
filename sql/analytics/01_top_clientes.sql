-- ============================================================================
-- Top 50 clientes por CLTV histórico con su segmentación completa
-- ============================================================================
SELECT 
    c.customer_id_nk,
    c.full_name,
    c.num_orders,
    ROUND(c.cltv_historic::numeric, 2)            AS cltv_historic,
    c.rfm_segment,
    c.churn_risk_level,
    c.cluster_all_name,
    c.days_since_last_order
FROM marts.customer_360 c
WHERE NOT c.is_churned
ORDER BY c.cltv_historic DESC
LIMIT 50;