"""
Página 2 — Análisis de Cliente
Distribución de CLTV, segmentos RFM, top clientes, churn risk.
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

from dashboard.config import COLORS, PLOTLY_LAYOUT, RFM_COLORS
from dashboard.data import load_customer_360
from dashboard.components import kpi_card, section_header, fmt_eur, fmt_int, fmt_pct
from dashboard.components import page_header

# ============================================================================
# CONFIGURACIÓN
# ============================================================================
st.set_page_config(page_title="Análisis Cliente", layout="wide")

page_header(
    "Análisis de Cliente",
    "CLTV · Segmentación RFM · Churn Risk · Top clientes",
    color=COLORS["secondary"],
)


# ============================================================================
# CARGA DE DATOS
# ============================================================================
df = load_customer_360()


# ============================================================================
# FILTROS LATERALES
# ============================================================================
with st.sidebar:
    st.markdown("---")
    st.markdown(f"### Filtros")
    
    only_recurrent = st.checkbox("Solo clientes recurrentes (≥2 compras)", value=False)
    only_active = st.checkbox("Solo clientes activos (no churn)", value=False)
    
    rfm_segments = sorted(df["rfm_segment"].dropna().unique().tolist())
    selected_segments = st.multiselect(
        "Segmentos RFM",
        options=rfm_segments,
        default=rfm_segments,
    )

# Aplicar filtros
df_f = df.copy()
if only_recurrent:
    df_f = df_f[df_f["is_recurrent"] == True]
if only_active:
    df_f = df_f[df_f["is_churned"] == False]
if selected_segments:
    df_f = df_f[df_f["rfm_segment"].isin(selected_segments)]

n_filtered = len(df_f)
n_total = len(df)


# ============================================================================
# FILA 1: KPIs DE LA POBLACIÓN FILTRADA
# ============================================================================
section_header(
    "Resumen de la población",
    f"{fmt_int(n_filtered)} de {fmt_int(n_total)} clientes ({n_filtered/n_total*100:.1f}%)",
    color=COLORS["secondary"],
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_card("Clientes en filtro", fmt_int(n_filtered),
             color=COLORS["secondary"])
with col2:
    cltv_total = df_f["cltv_historic"].sum()
    kpi_card("CLTV total", fmt_eur(cltv_total),
             color=COLORS["primary"])
with col3:
    cltv_avg = df_f["cltv_historic"].mean() if n_filtered > 0 else 0
    kpi_card("CLTV medio", fmt_eur(cltv_avg, 0),
             color=COLORS["success"])
with col4:
    cltv_median = df_f["cltv_historic"].median() if n_filtered > 0 else 0
    kpi_card("CLTV mediano", fmt_eur(cltv_median, 0),
             color=COLORS["accent"])


# ============================================================================
# FILA 2: DISTRIBUCIÓN CLTV + PARETO
# ============================================================================
col1, col2 = st.columns([1, 1])

with col1:
    section_header("Distribución del CLTV histórico", color=COLORS["primary"])
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Histogram(
        x=df_f["cltv_historic"],
        nbinsx=50,
        marker=dict(
            color=COLORS["primary"],
            line=dict(color=COLORS["text"], width=0.3),
        ),
        hovertemplate="CLTV: %{x:,.0f} €<br>Clientes: %{y}<extra></extra>",
    ))
    if n_filtered > 0:
        median_val = df_f["cltv_historic"].median()
        mean_val = df_f["cltv_historic"].mean()
        fig_hist.add_vline(x=median_val, line_dash="dash", line_color=COLORS["accent"],
                           annotation_text=f"Mediana: {median_val:.0f}€",
                           annotation_position="top right",
                           annotation_font_color=COLORS["accent"])
        fig_hist.add_vline(x=mean_val, line_dash="dot", line_color=COLORS["success"],
                           annotation_text=f"Media: {mean_val:.0f}€",
                           annotation_position="top left",
                           annotation_font_color=COLORS["success"])
    fig_hist.update_layout(**PLOTLY_LAYOUT, height=380,
                           xaxis_title="CLTV histórico (€)", yaxis_title="Nº clientes",
                           bargap=0.05)
    st.plotly_chart(fig_hist, use_container_width=True)

with col2:
    section_header("Curva de Pareto del CLTV", color=COLORS["accent"])
    df_sorted = df_f.sort_values("cltv_historic", ascending=False).reset_index(drop=True)
    df_sorted["cum_clientes_pct"] = (df_sorted.index + 1) / len(df_sorted) * 100
    df_sorted["cum_cltv_pct"] = df_sorted["cltv_historic"].cumsum() / df_sorted["cltv_historic"].sum() * 100
    
    fig_pareto = go.Figure()
    fig_pareto.add_trace(go.Scatter(
        x=df_sorted["cum_clientes_pct"],
        y=df_sorted["cum_cltv_pct"],
        mode="lines",
        line=dict(color=COLORS["accent"], width=3),
        fill="tozeroy",
        fillcolor=f"rgba(255,230,109,0.15)",
        hovertemplate="Top %{x:.1f}% clientes<br>%{y:.1f}% del CLTV<extra></extra>",
        name="CLTV acumulado",
    ))
    # Líneas de referencia
    fig_pareto.add_vline(x=20, line_dash="dash", line_color=COLORS["danger"],
                         annotation_text="Top 20%", annotation_position="top",
                         annotation_font_color=COLORS["danger"])
    fig_pareto.add_hline(y=80, line_dash="dot", line_color=COLORS["text_dim"],
                         annotation_text="80% CLTV", annotation_position="bottom right",
                         annotation_font_color=COLORS["text_dim"])
    fig_pareto.update_layout(**PLOTLY_LAYOUT, height=380,
                             xaxis_title="% acumulado de clientes (ordenados por CLTV desc)",
                             yaxis_title="% CLTV acumulado")
    st.plotly_chart(fig_pareto, use_container_width=True)


# ============================================================================
# FILA 3: SEGMENTOS RFM
# ============================================================================
section_header("Segmentación RFM", "9 segmentos accionables · Cada cliente clasificado por R-F-M",
               color=COLORS["purple"])

df_rfm = df_f.groupby("rfm_segment").agg(
    n_clientes=("customer_sk", "count"),
    cltv_total=("cltv_historic", "sum"),
    cltv_avg=("cltv_historic", "mean"),
).reset_index()
df_rfm = df_rfm.sort_values("cltv_total", ascending=False)
df_rfm["pct_clientes"] = df_rfm["n_clientes"] / df_rfm["n_clientes"].sum() * 100
df_rfm["pct_cltv"] = df_rfm["cltv_total"] / df_rfm["cltv_total"].sum() * 100

col1, col2 = st.columns([1, 1])

with col1:
    # Barras horizontales: nº clientes
    fig_rfm_n = go.Figure()
    fig_rfm_n.add_trace(go.Bar(
        y=df_rfm["rfm_segment"],
        x=df_rfm["n_clientes"],
        orientation="h",
        marker_color=[RFM_COLORS.get(s, COLORS["primary"]) for s in df_rfm["rfm_segment"]],
        text=df_rfm["n_clientes"].apply(lambda x: f"{x:,}".replace(",", ".")),
        textposition="outside",
        textfont=dict(color=COLORS["text"]),
        hovertemplate="<b>%{y}</b><br>Clientes: %{x:,}<br>%{customdata:.1f}% de la base<extra></extra>",
        customdata=df_rfm["pct_clientes"],
    ))
    fig_rfm_n.update_layout(**PLOTLY_LAYOUT, height=400, showlegend=False)
    fig_rfm_n.update_layout(
        title_text="Nº clientes por segmento",
        xaxis_title="Nº clientes",
        yaxis=dict(autorange="reversed", gridcolor="#2D3748",
                   linecolor="#4A5568", color="#A0A6B8"),
    )
    st.plotly_chart(fig_rfm_n, use_container_width=True)

with col2:
    # Barras horizontales: CLTV total
    fig_rfm_cltv = go.Figure()
    fig_rfm_cltv.add_trace(go.Bar(
        y=df_rfm["rfm_segment"],
        x=df_rfm["cltv_total"],
        orientation="h",
        marker_color=[RFM_COLORS.get(s, COLORS["primary"]) for s in df_rfm["rfm_segment"]],
        text=df_rfm["pct_cltv"].apply(lambda x: f"{x:.1f}%"),
        textposition="outside",
        textfont=dict(color=COLORS["text"]),
        hovertemplate="<b>%{y}</b><br>CLTV: %{x:,.0f} €<br>%{customdata:.1f}% del CLTV total<extra></extra>",
        customdata=df_rfm["pct_cltv"],
    ))
    fig_rfm_cltv.update_layout(**PLOTLY_LAYOUT, height=400, showlegend=False)
    fig_rfm_cltv.update_layout(
        title_text="CLTV total por segmento (€)",
        xaxis_title="CLTV total (€)",
        yaxis=dict(autorange="reversed", gridcolor="#2D3748",
                   linecolor="#4A5568", color="#A0A6B8"),
    )
    st.plotly_chart(fig_rfm_cltv, use_container_width=True)


# Tabla detalle RFM
df_rfm_display = df_rfm.copy()
df_rfm_display["n_clientes"] = df_rfm_display["n_clientes"].apply(fmt_int)
df_rfm_display["cltv_total"] = df_rfm_display["cltv_total"].apply(lambda x: fmt_eur(x))
df_rfm_display["cltv_avg"] = df_rfm_display["cltv_avg"].apply(lambda x: fmt_eur(x, 2))
df_rfm_display["pct_clientes"] = df_rfm_display["pct_clientes"].apply(lambda x: f"{x:.1f} %")
df_rfm_display["pct_cltv"] = df_rfm_display["pct_cltv"].apply(lambda x: f"{x:.1f} %")
df_rfm_display.columns = ["Segmento RFM", "Nº", "CLTV total", "CLTV medio", "% base", "% CLTV"]
st.dataframe(df_rfm_display, use_container_width=True, hide_index=True)


# ============================================================================
# TREEMAP · CLTV por segmento RFM (visualización del Pareto)
# ============================================================================
section_header(
    "Concentración del CLTV por segmento",
    "Tamaño del rectángulo proporcional al CLTV total · Visualización del Pareto",
    color=COLORS["primary"],
)

# Preparar dataframe para el treemap (filtrar segmentos con CLTV>0)
df_tree = df_rfm[df_rfm["cltv_total"] > 0].copy()
df_tree["color_hex"] = df_tree["rfm_segment"].map(
    lambda s: RFM_COLORS.get(s, COLORS["primary"])
)
df_tree["label_html"] = df_tree.apply(
    lambda r: f"<b>{r['rfm_segment']}</b><br>"
              f"{int(r['n_clientes']):,} clientes<br>"
              f"{r['pct_cltv']:.1f}% del CLTV".replace(",", "."),
    axis=1,
)

fig_tree = go.Figure(go.Treemap(
    labels=df_tree["label_html"],
    parents=[""] * len(df_tree),  # todos al mismo nivel (sin jerarquía)
    values=df_tree["cltv_total"],
    marker=dict(
        colors=df_tree["color_hex"],
        line=dict(color="#0E1117", width=2),
    ),
    text=df_tree["label_html"],
    textposition="middle center",
    textfont=dict(color="white", family="sans-serif", size=14),
    hovertemplate=(
        "<b>%{customdata[0]}</b><br>"
        "Clientes: %{customdata[1]:,}<br>"
        "CLTV total: %{value:,.0f} €<br>"
        "% del CLTV global: %{customdata[2]:.2f} %<extra></extra>"
    ),
    customdata=df_tree[["rfm_segment", "n_clientes", "pct_cltv"]].values,
))

fig_tree.update_layout(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=COLORS["text"]),
    height=420,
    margin=dict(t=10, b=10, l=10, r=10),
)

st.plotly_chart(fig_tree, use_container_width=True)

# Caja explicativa
st.markdown(f"""
<div style="
    background: {COLORS['card_bg']};
    border-left: 3px solid {COLORS['primary']};
    border-radius: 4px;
    padding: 14px 20px;
    margin-top: 8px;
    font-size: 0.88rem;
    color: {COLORS['text_dim']};
    line-height: 1.5;
">
    <b style="color:{COLORS['text']};">Lectura:</b> el rectángulo de
    <b style="color:{RFM_COLORS.get('Champions', COLORS['success'])};">Champions</b>
    ocupa cerca del 90% del área total — esa es la imagen del principio de Pareto:
    un porcentaje pequeño de clientes concentra la mayoría del valor del negocio.
    <b style="color:{COLORS['primary']};">Pasa el ratón</b> sobre cualquier rectángulo
    para ver detalles exactos.
</div>
""", unsafe_allow_html=True)


# ============================================================================
# FILA 4: CHURN RISK + DISTRIBUCIÓN ÓRDENES
# ============================================================================
col1, col2 = st.columns([1, 1])

with col1:
    section_header("Distribución Churn Risk", color=COLORS["danger"])
    
    # Cross-tab is_churned x churn_risk_level
    df_churn = df_f.groupby(["churn_risk_level", "is_churned"]).size().reset_index(name="n")
    df_churn["status"] = df_churn["is_churned"].map({True: "Churned", False: "Active"})
    
    # Asegurar orden de niveles
    level_order = ["Low", "Medium", "High"]
    df_churn["churn_risk_level"] = pd.Categorical(
        df_churn["churn_risk_level"], categories=level_order, ordered=True
    )
    df_churn = df_churn.sort_values("churn_risk_level")
    
    fig_churn = go.Figure()
    for status, color in [("Active", COLORS["success"]), ("Churned", COLORS["danger"])]:
        sub = df_churn[df_churn["status"] == status]
        fig_churn.add_trace(go.Bar(
            x=sub["churn_risk_level"].astype(str),
            y=sub["n"],
            name=status,
            marker_color=color,
            text=sub["n"].apply(lambda x: f"{x:,}".replace(",", ".")),
            textposition="outside",
            textfont=dict(color=COLORS["text"]),
            hovertemplate=f"<b>{status}</b><br>%{{x}}: %{{y:,}}<extra></extra>",
        ))
    fig_churn.update_layout(**PLOTLY_LAYOUT, height=380,
                            barmode="group",
                            xaxis_title="Nivel de Churn Risk",
                            yaxis_title="Nº clientes")
    st.plotly_chart(fig_churn, use_container_width=True)

with col2:
    section_header("Distribución de nº de pedidos", color=COLORS["blue"])
    fig_orders = go.Figure()
    # Limitar visualización a 30 pedidos para que sea legible
    df_orders_clip = df_f.copy()
    df_orders_clip["num_orders_display"] = df_orders_clip["num_orders"].clip(upper=30)
    
    fig_orders.add_trace(go.Histogram(
        x=df_orders_clip["num_orders_display"],
        nbinsx=30,
        marker=dict(color=COLORS["blue"], line=dict(color=COLORS["text"], width=0.3)),
        hovertemplate="Pedidos: %{x}<br>Clientes: %{y}<extra></extra>",
    ))
    fig_orders.update_layout(**PLOTLY_LAYOUT, height=380,
                             xaxis_title="Nº pedidos por cliente (capped a 30)",
                             yaxis_title="Nº clientes",
                             bargap=0.05)
    st.plotly_chart(fig_orders, use_container_width=True)


# ============================================================================
# FILA 5: TOP CLIENTES
# ============================================================================
section_header("Top 20 clientes por CLTV histórico",
               "Ranking de los clientes más valiosos en la población filtrada",
               color=COLORS["success"])

top_n = 20
df_top = df_f.nlargest(top_n, "cltv_historic").copy()

# Construir tabla legible
top_display = df_top[[
    "customer_id_nk", "full_name", "num_orders", "cltv_historic",
    "days_since_last_order", "rfm_segment", "churn_risk_level"
]].copy()
top_display["cltv_historic"] = top_display["cltv_historic"].apply(lambda x: fmt_eur(x, 2))
top_display.columns = ["ID", "Nombre", "Nº pedidos", "CLTV", "Días desde última compra",
                       "Segmento RFM", "Churn Risk"]

st.dataframe(top_display, use_container_width=True, hide_index=True)


# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.caption(f"💾 {n_filtered:,} clientes en el filtro actual · "
           f"Datos desde `marts.customer_360`")