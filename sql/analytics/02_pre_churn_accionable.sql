-- ============================================================================
-- Lista accionable: Champions/Recurrentes con riesgo Medium ("pre-churn")
-- 92 clientes con CLTV >3.000€ pero recencia >180 días.
-- Output esperado: lista para campaña de retención dirigida.
-- ============================================================================
SELECT 
    customer_id_nk,
    full_name,
    email,
    ROUND(cltv_historic::numeric, 2)              AS cltv_historic,
    days_since_last_order,
    num_orders,
    rfm_segment,
    cluster_rec_name
FROM marts.customer_360
WHERE NOT is_churned
  AND churn_risk_level = 'Medium'
  AND cltv_historic > 3000
ORDER BY cltv_historic DESC;