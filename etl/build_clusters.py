"""
Bloque 5 - BUILD CLUSTERS
Ejecuta PCA + K-Means y persiste las asignaciones de cluster en marts.customer_360.

Reproduce en código la lógica del notebook 05_pca_clustering.ipynb,
con los nombres de cluster ya validados manualmente.
"""
import time
import numpy as np
import pandas as pd
from sqlalchemy import text

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

from etl.db import get_engine_dwh, read_sql
from etl.logger import get_logger

log = get_logger()

# Configuración
RANDOM_STATE = 42
K_ALL = 4
K_REC = 4

FEATURES = [
    'num_orders',
    'total_units',
    'avg_order_value',
    'net_revenue_after_returns',
    'gross_margin',
    'customer_lifespan_days',
    'days_since_last_order',
    'return_rate',
]

# Mapeos de nombres (validados visualmente en el notebook)
NAMES_ALL = {
    0: 'Champions activos',
    1: 'Compradores ocasionales',
    2: 'Champions Premium',
    3: 'Devolvedores compulsivos',
}
NAMES_REC = {
    0: 'Recurrentes Estándar',
    1: 'Recurrentes En Riesgo',
    2: 'Recurrentes Consolidados',
    3: 'Élite VIP',
}


def _label_clusters_by_cltv(km_labels: np.ndarray, cltv: np.ndarray, names_dict: dict) -> tuple:
    """
    Asigna nombres a los clusters de forma determinista basándose en el CLTV medio.
    El cluster con mayor CLTV recibe el nombre asociado al ID más alto del mapping,
    salvo el cluster 'tóxico' que se identifica por return_rate alto (lo gestionamos aparte).
    
    Esto evita que K-Means devuelva los IDs en orden aleatorio entre ejecuciones.
    """
    pass  # No lo usamos en esta versión simple — simplemente nos quedamos con el orden de K-Means


def build_and_persist_clusters() -> None:
    """Ejecuta clustering completo y guarda asignaciones en customer_360."""
    eng = get_engine_dwh()
    log.info("=" * 70)
    log.info("BUILD CLUSTERS (PCA + K-Means)")
    log.info("=" * 70)
    t0 = time.time()

    # 1) Cargar datos
    df = read_sql(f"""
        SELECT customer_sk, is_recurrent,
               {', '.join(FEATURES)}
        FROM marts.customer_360
    """, eng)
    log.info(f"  Clientes cargados: {len(df)}")

    # 2) Clustering sobre todos
    log.info(f"  [ALL] PCA + K-Means (K={K_ALL})...")
    X_all = df[FEATURES].values
    X_all_scaled = StandardScaler().fit_transform(X_all)
    pca_all = PCA(random_state=RANDOM_STATE)
    X_all_pca = pca_all.fit_transform(X_all_scaled)
    var_cum_all = np.cumsum(pca_all.explained_variance_ratio_)
    n_pcs_all = int((var_cum_all >= 0.80).argmax() + 1)
    log.info(f"    Componentes para >=80% varianza: {n_pcs_all} (acum {var_cum_all[n_pcs_all-1]*100:.1f}%)")

    km_all = KMeans(n_clusters=K_ALL, random_state=RANDOM_STATE, n_init=10)
    df['cluster_all_id'] = km_all.fit_predict(X_all_pca[:, :n_pcs_all])

    # Cargar cltv_historic desde BD para usarlo como referencia de naming
    cltv_data = read_sql(
        "SELECT customer_sk, cltv_historic FROM marts.customer_360", eng
    )
    df_naming = df[['customer_sk', 'cluster_all_id', 'return_rate']].merge(
        cltv_data, on='customer_sk', how='left'
    )

    # Perfil real por cluster
    cluster_profiles_all = df_naming.groupby('cluster_all_id').agg(
        avg_return=('return_rate', 'mean'),
        avg_cltv=('cltv_historic', 'mean'),
        n_clientes=('customer_sk', 'count')
    ).sort_values('avg_cltv', ascending=False)
    log.info(f"    Perfil real clusters all (ordenado por CLTV):\n{cluster_profiles_all}")

    # Estrategia de naming basada en perfil real:
    # - Cluster con MAYOR CLTV medio + return_rate bajo → 'Champions Premium'
    # - Siguiente CLTV alto + return_rate bajo → 'Champions activos'
    # - Cluster con muchos clientes y CLTV bajo, return_rate ~0 → 'Compradores ocasionales'
    # - Cluster(s) con return_rate alto → 'Devolvedores compulsivos' (todos los tóxicos)

    THRESHOLD_TOXIC = 0.30  # return_rate por encima de 30% se considera tóxico

    name_mapping_all = {}
    toxic_clusters = []
    healthy_clusters = []

    for cid, row in cluster_profiles_all.iterrows():
        if row['avg_return'] >= THRESHOLD_TOXIC:
            toxic_clusters.append(cid)
        else:
            healthy_clusters.append(cid)  # ya están ordenados por CLTV desc

    # Asignar nombres a los healthy en orden de CLTV descendente
    healthy_names = ['Champions Premium', 'Champions activos', 'Compradores ocasionales']
    for i, cid in enumerate(healthy_clusters[:3]):
        name_mapping_all[cid] = healthy_names[i]
    # Si quedan más clusters healthy (raro con K=4) los etiquetamos genérico
    for cid in healthy_clusters[3:]:
        name_mapping_all[cid] = 'Otros'

    # Todos los tóxicos van como 'Devolvedores compulsivos' (no diferenciamos grado)
    for cid in toxic_clusters:
        name_mapping_all[cid] = 'Devolvedores compulsivos'
    df['cluster_all_name'] = df['cluster_all_id'].map(name_mapping_all)

    log.info(f"    Asignación de nombres (all):")
    for cid, cname in name_mapping_all.items():
        n = (df['cluster_all_id'] == cid).sum()
        log.info(f"      Cluster {cid} → '{cname}' ({n} clientes)")

    # 3) Clustering sobre recurrentes
    log.info(f"  [REC] PCA + K-Means (K={K_REC})...")
    df_rec = df[df['is_recurrent']].copy().reset_index(drop=True)
    X_rec = df_rec[FEATURES].values
    X_rec_scaled = StandardScaler().fit_transform(X_rec)
    pca_rec = PCA(random_state=RANDOM_STATE)
    X_rec_pca = pca_rec.fit_transform(X_rec_scaled)
    var_cum_rec = np.cumsum(pca_rec.explained_variance_ratio_)
    n_pcs_rec = int((var_cum_rec >= 0.80).argmax() + 1)
    log.info(f"    Componentes para >=80% varianza: {n_pcs_rec} (acum {var_cum_rec[n_pcs_rec-1]*100:.1f}%)")

    km_rec = KMeans(n_clusters=K_REC, random_state=RANDOM_STATE, n_init=10)
    df_rec['cluster_rec_id'] = km_rec.fit_predict(X_rec_pca[:, :n_pcs_rec])

    # Para recurrentes ordenamos por CLTV medio
    profiles_rec = df_rec.groupby('cluster_rec_id').agg(
        avg_revenue=('net_revenue_after_returns', 'mean'),
        avg_recency=('days_since_last_order', 'mean')
    )
    # El "En riesgo" es el de mayor recencia
    risk_cluster = profiles_rec['avg_recency'].idxmax()
    # Los demás ordenados por revenue
    sorted_by_rev = profiles_rec.drop(risk_cluster).sort_values('avg_revenue', ascending=False).index.tolist()
    name_mapping_rec = {risk_cluster: 'Recurrentes En Riesgo'}
    if len(sorted_by_rev) >= 1:
        name_mapping_rec[sorted_by_rev[0]] = 'Élite VIP'
    if len(sorted_by_rev) >= 2:
        name_mapping_rec[sorted_by_rev[1]] = 'Recurrentes Consolidados'
    if len(sorted_by_rev) >= 3:
        name_mapping_rec[sorted_by_rev[2]] = 'Recurrentes Estándar'
    df_rec['cluster_rec_name'] = df_rec['cluster_rec_id'].map(name_mapping_rec)

    log.info(f"    Asignación de nombres (rec):")
    for cid, cname in name_mapping_rec.items():
        n = (df_rec['cluster_rec_id'] == cid).sum()
        log.info(f"      Cluster {cid} → '{cname}' ({n} clientes)")

    # 4) Merge de vuelta al df principal
    df = df.merge(
        df_rec[['customer_sk', 'cluster_rec_id', 'cluster_rec_name']],
        on='customer_sk', how='left'
    )

    # 5) Update masivo en customer_360
    log.info("  Actualizando marts.customer_360 con asignaciones...")
    update_data = df[['customer_sk', 'cluster_all_id', 'cluster_all_name', 
                       'cluster_rec_id', 'cluster_rec_name']]
    update_data['cluster_rec_id'] = update_data['cluster_rec_id'].astype('Int64')

    with eng.begin() as conn:
        # Limpiamos las columnas primero
        conn.execute(text("""
            UPDATE marts.customer_360 
            SET cluster_all_id=NULL, cluster_all_name=NULL,
                cluster_rec_id=NULL, cluster_rec_name=NULL
        """))
        # Update fila a fila usando una temp table sería más eficiente,
        # pero para 5750 filas usamos UPDATE batch sencillo
        for _, row in update_data.iterrows():
            conn.execute(text("""
                UPDATE marts.customer_360
                SET cluster_all_id   = :cai,
                    cluster_all_name = :can,
                    cluster_rec_id   = :cri,
                    cluster_rec_name = :crn
                WHERE customer_sk = :sk
            """), {
                "sk":  int(row['customer_sk']),
                "cai": int(row['cluster_all_id']) if pd.notna(row['cluster_all_id']) else None,
                "can": row['cluster_all_name'],
                "cri": int(row['cluster_rec_id']) if pd.notna(row['cluster_rec_id']) else None,
                "crn": row['cluster_rec_name'],
            })

    elapsed = time.time() - t0
    log.info(f"OK | clustering aplicado en {elapsed:.2f}s")

    # 6) Resumen final
    summary_all = read_sql("""
        SELECT cluster_all_name, COUNT(*) AS n,
               ROUND(AVG(cltv_historic)::numeric, 0) AS cltv_avg,
               ROUND(SUM(cltv_historic)::numeric, 0) AS cltv_total
        FROM marts.customer_360
        WHERE cluster_all_name IS NOT NULL
        GROUP BY cluster_all_name
        ORDER BY cltv_total DESC;
    """, eng)
    log.info(f"\nResumen clusters (todos):\n{summary_all.to_string(index=False)}")

    summary_rec = read_sql("""
        SELECT cluster_rec_name, COUNT(*) AS n,
               ROUND(AVG(cltv_historic)::numeric, 0) AS cltv_avg,
               ROUND(AVG(days_since_last_order)::numeric, 0) AS recency_avg
        FROM marts.customer_360
        WHERE cluster_rec_name IS NOT NULL
        GROUP BY cluster_rec_name
        ORDER BY cltv_avg DESC;
    """, eng)
    log.info(f"\nResumen clusters (recurrentes):\n{summary_rec.to_string(index=False)}")
    log.info("=" * 70)


if __name__ == "__main__":
    build_and_persist_clusters()