"""
Página 3 — Clustering K-Means
Visualización de los 4 clusters globales y los 4 sub-clusters de recurrentes,
con scatter 2D (PCA), radar chart de perfiles y comparativa cluster vs RFM.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA

from dashboard.config import COLORS, PLOTLY_LAYOUT, CLUSTER_COLORS, RFM_COLORS
from dashboard.data import load_customer_360
from dashboard.components import kpi_card, section_header, fmt_eur, fmt_int, fmt_pct
from dashboard.components import page_header

# ============================================================================
# CONFIGURACIÓN
# ============================================================================
st.set_page_config(page_title="Clustering", layout="wide")

page_header(
    "Clustering K-Means",
    "Segmentación tras PCA · 4 clusters globales + 4 sub-clusters de recurrentes",
    color=COLORS["purple"],
)


# ============================================================================
# CARGA DE DATOS
# ============================================================================
df = load_customer_360()


# ============================================================================
# SELECTOR: GLOBAL vs RECURRENTES
# ============================================================================
mode = st.radio(
    "Selecciona el modelo de clustering:",
    options=["Global (5.750 clientes, K=4)", "Recurrentes (750 clientes, K=4)"],
    horizontal=True,
)

if mode.startswith("Global"):
    df_view = df.copy()
    cluster_col = "cluster_all_name"
    cluster_id_col = "cluster_all_id"
    title_suffix = "global"
else:
    df_view = df[df["is_recurrent"] == True].copy()
    cluster_col = "cluster_rec_name"
    cluster_id_col = "cluster_rec_id"
    title_suffix = "recurrentes"

df_view = df_view.dropna(subset=[cluster_col])


# ============================================================================
# FILA 1: KPIs por cluster
# ============================================================================
section_header(f"Resumen del modelo {title_suffix}",
               f"{fmt_int(len(df_view))} clientes clusterizados",
               color=COLORS["purple"])

cluster_summary = df_view.groupby(cluster_col).agg(
    n=("customer_sk", "count"),
    cltv_avg=("cltv_historic", "mean"),
    cltv_total=("cltv_historic", "sum"),
    orders_avg=("num_orders", "mean"),
    return_rate_avg=("return_rate", "mean"),
    recency_avg=("days_since_last_order", "mean"),
).reset_index().sort_values("cltv_total", ascending=False)

cols = st.columns(len(cluster_summary))
for i, (_, row) in enumerate(cluster_summary.iterrows()):
    with cols[i]:
        cluster_name = row[cluster_col]
        color = CLUSTER_COLORS.get(cluster_name, COLORS["primary"])
        kpi_card(
            cluster_name,
            fmt_int(row["n"]),
            delta=f"CLTV avg: {fmt_eur(row['cltv_avg'], 0)}",
            color=color,
        )


# ============================================================================
# FILA 2: SCATTER 2D (recalcular PCA on-the-fly para visualización)
# ============================================================================
section_header("Proyección 2D (PCA)", 
               "Cada cliente proyectado en las 2 primeras componentes principales",
               color=COLORS["primary"])

FEATURES = [
    "num_orders", "total_units", "avg_order_value",
    "net_revenue_after_returns", "gross_margin",
    "customer_lifespan_days", "days_since_last_order", "return_rate",
]

X = df_view[FEATURES].fillna(0).values
X_scaled = StandardScaler().fit_transform(X)
pca = PCA(n_components=2, random_state=42)
X_pca = pca.fit_transform(X_scaled)

df_view = df_view.copy()
df_view["pc1"] = X_pca[:, 0]
df_view["pc2"] = X_pca[:, 1]

var_pc1 = pca.explained_variance_ratio_[0] * 100
var_pc2 = pca.explained_variance_ratio_[1] * 100

# Scatter
fig_scatter = go.Figure()
for cname in cluster_summary[cluster_col].tolist():
    sub = df_view[df_view[cluster_col] == cname]
    color = CLUSTER_COLORS.get(cname, COLORS["primary"])
    fig_scatter.add_trace(go.Scatter(
        x=sub["pc1"],
        y=sub["pc2"],
        mode="markers",
        name=f"{cname} (n={len(sub)})",
        marker=dict(
            size=6, color=color,
            opacity=0.7,
            line=dict(width=0.3, color="white"),
        ),
        customdata=sub[["customer_id_nk", "full_name", "cltv_historic", "num_orders"]].values,
        hovertemplate=(
            "<b>%{customdata[1]}</b> (ID: %{customdata[0]})<br>"
            "Cluster: " + cname + "<br>"
            "CLTV: %{customdata[2]:,.0f} €<br>"
            "Pedidos: %{customdata[3]}<br>"
            "PC1: %{x:.2f}, PC2: %{y:.2f}<extra></extra>"
        ),
    ))

fig_scatter.update_layout(**PLOTLY_LAYOUT, height=520)
fig_scatter.update_layout(
    xaxis_title=f"PC1 ({var_pc1:.1f}% varianza)",
    yaxis_title=f"PC2 ({var_pc2:.1f}% varianza)",
    legend=dict(
        orientation="v",
        yanchor="top", y=1, xanchor="left", x=1.02,
        bgcolor="rgba(26,31,46,0.7)",
        bordercolor="#2D3748", borderwidth=1,
    ),
)
st.plotly_chart(fig_scatter, use_container_width=True)


# ============================================================================
# FILA 3: RADAR CHART (perfil de cada cluster)
# ============================================================================
section_header("Perfil de cada cluster",
               "Comparativa normalizada de las 8 features (0=mínimo, 1=máximo en este modelo)",
               color=COLORS["accent"])

# Normalizar features [0, 1] para que sean comparables en radar
scaler_mm = MinMaxScaler()
df_radar = df_view[FEATURES].copy()
df_radar_scaled = pd.DataFrame(
    scaler_mm.fit_transform(df_radar),
    columns=FEATURES,
    index=df_view.index,
)
df_radar_scaled[cluster_col] = df_view[cluster_col]

profile = df_radar_scaled.groupby(cluster_col)[FEATURES].mean()

# Etiquetas más legibles
feat_labels = {
    "num_orders":               "Frecuencia",
    "total_units":              "Volumen",
    "avg_order_value":          "Ticket medio",
    "net_revenue_after_returns":"Ingresos netos",
    "gross_margin":             "Margen",
    "customer_lifespan_days":   "Antigüedad",
    "days_since_last_order":    "Recencia",
    "return_rate":              "Tasa devol.",
}
labels = [feat_labels[f] for f in FEATURES]

fig_radar = go.Figure()
for cname in cluster_summary[cluster_col].tolist():
    if cname not in profile.index:
        continue
    values = profile.loc[cname].values.tolist()
    values += values[:1]  # cerrar el polígono
    color = CLUSTER_COLORS.get(cname, COLORS["primary"])
    fig_radar.add_trace(go.Scatterpolar(
        r=values,
        theta=labels + [labels[0]],
        fill="toself",
        name=cname,
        line=dict(color=color, width=2),
        fillcolor=color,
        opacity=0.35,
    ))

fig_radar.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=COLORS["text"]),
    height=520,
    polar=dict(
        bgcolor="rgba(0,0,0,0)",
        radialaxis=dict(
            visible=True, range=[0, 1],
            gridcolor="#2D3748", linecolor="#4A5568", color=COLORS["text_dim"],
            tickfont=dict(size=9),
        ),
        angularaxis=dict(
            gridcolor="#2D3748", linecolor="#4A5568", color=COLORS["text_dim"],
            tickfont=dict(size=11, color=COLORS["text"]),
        ),
    ),
    legend=dict(
        orientation="h", yanchor="top", y=-0.05,
        bgcolor="rgba(26,31,46,0.7)", bordercolor="#2D3748", borderwidth=1,
    ),
    margin=dict(t=40, b=80, l=60, r=60),
)
st.plotly_chart(fig_radar, use_container_width=True)


# ============================================================================
# FILA 4: COMPARATIVA CLUSTER vs RFM
# ============================================================================
section_header("Cruce Cluster ↔ Segmento RFM",
               "Cuántos clientes de cada cluster pertenecen a cada segmento RFM",
               color=COLORS["secondary"])

ct = pd.crosstab(df_view[cluster_col], df_view["rfm_segment"])

# Heatmap interactivo
fig_heat = go.Figure(data=go.Heatmap(
    z=ct.values,
    x=ct.columns.tolist(),
    y=ct.index.tolist(),
    colorscale=[
        [0.0, "rgba(26,31,46,0.5)"],
        [0.3, COLORS["secondary"]],
        [1.0, COLORS["primary"]],
    ],
    text=ct.values,
    texttemplate="%{text}",
    textfont=dict(color=COLORS["text"], size=12),
    hovertemplate="Cluster: %{y}<br>Segmento RFM: %{x}<br>Clientes: %{z}<extra></extra>",
    colorbar=dict(title="Nº clientes", title_font_color=COLORS["text"],
                  tickfont=dict(color=COLORS["text"])),
))

fig_heat.update_layout(**PLOTLY_LAYOUT, height=420)
fig_heat.update_layout(
    xaxis_title="Segmento RFM",
    yaxis_title="Cluster",
    xaxis=dict(tickangle=-30, gridcolor="#2D3748", linecolor="#4A5568", color="#A0A6B8"),
    yaxis=dict(gridcolor="#2D3748", linecolor="#4A5568", color="#A0A6B8"),
)
st.plotly_chart(fig_heat, use_container_width=True)


# ============================================================================
# FILA 5: TABLA DETALLE DE CLUSTERS
# ============================================================================
section_header("Detalle numérico", color=COLORS["success"])

display = cluster_summary.copy()
display.columns = ["Cluster", "Nº", "CLTV avg", "CLTV total", "Orders avg",
                   "Return rate", "Recencia avg"]
display["CLTV avg"]      = display["CLTV avg"].apply(lambda x: fmt_eur(x, 2))
display["CLTV total"]    = display["CLTV total"].apply(lambda x: fmt_eur(x))
display["Orders avg"]    = display["Orders avg"].apply(lambda x: f"{x:.1f}")
display["Return rate"]   = display["Return rate"].apply(lambda x: f"{x*100:.1f} %")
display["Recencia avg"]  = display["Recencia avg"].apply(lambda x: f"{x:.0f} días")
display["Nº"]            = display["Nº"].apply(fmt_int)

st.dataframe(display, use_container_width=True, hide_index=True)


# ============================================================================
# INSIGHT BOX (solo modo global)
# ============================================================================
if mode.startswith("Global"):
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {COLORS['danger']}25 0%, {COLORS['card_bg']} 100%);
        border-left: 4px solid {COLORS['danger']};
        border-radius: 8px;
        padding: 18px 22px;
        margin-top: 24px;
    ">
        <div style="font-weight:700;color:{COLORS['text']};font-size:1.05rem;">Insight clave</div>
        <div style="color:{COLORS['text_dim']};font-size:0.95rem;margin-top:6px;line-height:1.5;">
            El cluster <b style="color:{COLORS['danger']};">"Devolvedores compulsivos"</b>
            (≈420 clientes, 7,3% de la base) tiene un return rate del 88% y aporta solo ~5.000 € de CLTV
            — un segmento operacionalmente tóxico que el RFM tradicional <i>no detecta</i>.
            Solo el clustering multidimensional lo aísla.
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {COLORS['warning']}25 0%, {COLORS['card_bg']} 100%);
        border-left: 4px solid {COLORS['warning']};
        border-radius: 8px;
        padding: 18px 22px;
        margin-top: 24px;
    ">
        <div style="font-weight:700;color:{COLORS['text']};font-size:1.05rem;">Lista accionable de oro</div>
        <div style="color:{COLORS['text_dim']};font-size:0.95rem;margin-top:6px;line-height:1.5;">
            El cluster <b style="color:{COLORS['warning']};">"Recurrentes En Riesgo"</b>
            (~92 clientes con CLTV >3.000€ pero recencia &gt;300 días) representa Champions desconectándose.
            Una campaña de retención dirigida sobre este grupo protegería ~337.500 € de CLTV potencial.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.caption("💾 Clusters persistidos en `marts.customer_360` · "
           "PCA recalculado on-the-fly para la visualización 2D")