-- ============================================================================
-- Añadir columnas de clustering a marts.customer_360
-- ============================================================================

ALTER TABLE marts.customer_360 
    ADD COLUMN IF NOT EXISTS cluster_all_id   INTEGER,
    ADD COLUMN IF NOT EXISTS cluster_all_name VARCHAR(50),
    ADD COLUMN IF NOT EXISTS cluster_rec_id   INTEGER,
    ADD COLUMN IF NOT EXISTS cluster_rec_name VARCHAR(50);

CREATE INDEX IF NOT EXISTS idx_c360_cluster_all ON marts.customer_360(cluster_all_id);
CREATE INDEX IF NOT EXISTS idx_c360_cluster_rec ON marts.customer_360(cluster_rec_id);

COMMENT ON COLUMN marts.customer_360.cluster_all_id   IS 'ID cluster K-Means sobre toda la población (K=4)';
COMMENT ON COLUMN marts.customer_360.cluster_all_name IS 'Nombre descriptivo del cluster sobre todos';
COMMENT ON COLUMN marts.customer_360.cluster_rec_id   IS 'ID cluster K-Means sobre recurrentes (K=4). NULL para one-shot.';
COMMENT ON COLUMN marts.customer_360.cluster_rec_name IS 'Nombre descriptivo del cluster sobre recurrentes';