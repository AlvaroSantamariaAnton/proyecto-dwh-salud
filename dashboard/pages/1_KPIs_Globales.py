"""
Página 1 — KPIs Globales
Vista ejecutiva: ingresos, márgenes, evolución temporal, devoluciones.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dashboard.config import COLORS, PLOTLY_LAYOUT
from dashboard.data import load_global_kpis, load_monthly_sales, load_customer_360, load_top_products, load_top_stores
from dashboard.components import kpi_card, section_header, fmt_eur, fmt_int, fmt_pct
from dashboard.components import page_header

# ============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================================
st.set_page_config(page_title="KPIs Globales", layout="wide")

page_header(
    "KPIs Globales",
    "Vista ejecutiva del negocio · Ingresos, márgenes y evolución temporal · Periodo 2020–2025",
    color=COLORS["primary"],
)


# ============================================================================
# CARGA DE DATOS
# ============================================================================
kpis = load_global_kpis()
df_monthly = load_monthly_sales()
df_customers = load_customer_360()


# ============================================================================
# FILA 1: KPIs PRINCIPALES (4 cards)
# ============================================================================
section_header("Resumen del negocio", color=COLORS["primary"])

col1, col2, col3, col4 = st.columns(4)
with col1:
    kpi_card("Ingresos totales", fmt_eur(kpis["total_revenue"]),
             color=COLORS["primary"])
with col2:
    kpi_card("Margen bruto", fmt_eur(kpis["total_margin"]),
             delta=f"{kpis['margin_pct']}% sobre ingresos",
             color=COLORS["success"])
with col3:
    kpi_card("Clientes únicos", fmt_int(kpis["total_clientes"]),
             color=COLORS["secondary"])
with col4:
    kpi_card("Ventas (cabecera)", fmt_int(kpis["total_ventas"]),
             delta=f"{fmt_int(kpis['total_items'])} items",
             color=COLORS["purple"])


# ============================================================================
# FILA 2: SECUNDARIOS
# ============================================================================
col1, col2, col3, col4 = st.columns(4)

# Calcular métricas adicionales
return_rate_global = (df_customers["return_rate"].mean() * 100) if "return_rate" in df_customers.columns else 0
recurrent_pct = (df_customers["is_recurrent"].sum() / len(df_customers) * 100) if "is_recurrent" in df_customers.columns else 0
cltv_avg = df_customers["cltv_historic"].mean() if "cltv_historic" in df_customers.columns else 0
churned_pct = (df_customers["is_churned"].sum() / len(df_customers) * 100) if "is_churned" in df_customers.columns else 0

with col1:
    kpi_card("Devoluciones (margen perdido)", fmt_eur(kpis["margin_lost"]),
             color=COLORS["warning"])
with col2:
    kpi_card("Tasa devolución global", fmt_pct(return_rate_global, 2),
             color=COLORS["accent"])
with col3:
    kpi_card("CLTV medio", fmt_eur(cltv_avg, 0),
             delta=f"{recurrent_pct:.1f}% recurrentes",
             color=COLORS["blue"])
with col4:
    kpi_card("Clientes en churn", fmt_pct(churned_pct, 1),
             delta="(>365 días sin compra)",
             color=COLORS["danger"])


# ============================================================================
# FILA 3: EVOLUCIÓN TEMPORAL
# ============================================================================
section_header("Evolución mensual", "Ingresos y margen agrupados por mes",
               color=COLORS["secondary"])

fig = make_subplots(
    rows=2, cols=1, shared_xaxes=True,
    vertical_spacing=0.08,
    subplot_titles=("Ingresos mensuales", "Margen bruto mensual (€)"),
    row_heights=[0.55, 0.45],
)

fig.add_trace(go.Bar(
    x=df_monthly["year_month"], y=df_monthly["revenue"],
    name="Ingresos",
    marker_color=COLORS["primary"],
    hovertemplate="<b>%{x}</b><br>Ingresos: %{y:,.0f} €<extra></extra>",
), row=1, col=1)

fig.add_trace(go.Scatter(
    x=df_monthly["year_month"], y=df_monthly["margin"],
    name="Margen", mode="lines+markers",
    line=dict(color=COLORS["success"], width=2.5),
    marker=dict(size=6),
    hovertemplate="<b>%{x}</b><br>Margen: %{y:,.0f} €<extra></extra>",
), row=2, col=1)

fig.update_layout(
    **PLOTLY_LAYOUT,
    height=480,
    showlegend=False,
)
fig.update_xaxes(gridcolor="#2D3748", linecolor="#4A5568", color="#A0A6B8")
fig.update_yaxes(gridcolor="#2D3748", linecolor="#4A5568", color="#A0A6B8")
fig.update_yaxes(title_text="€", row=1, col=1)
fig.update_yaxes(title_text="€", row=2, col=1)
fig.update_xaxes(title_text="Mes", row=2, col=1)

st.plotly_chart(fig, use_container_width=True)


# ============================================================================
# FILA 4: DOS GRÁFICOS LADO A LADO
# ============================================================================
col1, col2 = st.columns(2)

with col1:
    section_header("Margen % mensual", color=COLORS["accent"])
    fig_pct = go.Figure()
    fig_pct.add_trace(go.Scatter(
        x=df_monthly["year_month"], y=df_monthly["margin_pct"],
        mode="lines+markers", line=dict(color=COLORS["accent"], width=2.5),
        marker=dict(size=7, color=COLORS["accent"], line=dict(color="white", width=1)),
        fill="tozeroy",
        fillcolor=f"rgba(255,230,109,0.15)",
        hovertemplate="<b>%{x}</b><br>Margen: %{y:.2f} %<extra></extra>",
    ))
    fig_pct.add_hline(y=40, line_dash="dash", line_color=COLORS["text_dim"],
                      annotation_text="Objetivo 40%", annotation_position="bottom right",
                      annotation_font_color=COLORS["text_dim"])
    fig_pct.update_layout(**PLOTLY_LAYOUT, height=350,
                          yaxis_title="% margen", xaxis_title="Mes")
    st.plotly_chart(fig_pct, use_container_width=True)

with col2:
    section_header("Tasa devolución mensual", color=COLORS["warning"])
    fig_ret = go.Figure()
    fig_ret.add_trace(go.Scatter(
        x=df_monthly["year_month"], y=df_monthly["return_rate_pct"],
        mode="lines+markers", line=dict(color=COLORS["warning"], width=2.5),
        marker=dict(size=7, color=COLORS["warning"], line=dict(color="white", width=1)),
        fill="tozeroy",
        fillcolor=f"rgba(255,182,39,0.15)",
        hovertemplate="<b>%{x}</b><br>Devoluciones: %{y:.2f} %<extra></extra>",
    ))
    fig_ret.update_layout(**PLOTLY_LAYOUT, height=350,
                          yaxis_title="% items devueltos", xaxis_title="Mes")
    st.plotly_chart(fig_ret, use_container_width=True)


# ============================================================================
# FILA 5: TABLA RESUMEN ANUAL
# ============================================================================
section_header("Resumen anual", "Agregado por año desde fact_sales",
               color=COLORS["purple"])

df_monthly["year"] = df_monthly["year_month"].astype(str).str[:4]
df_yearly = df_monthly.groupby("year").agg(
    n_ventas=("n_ventas", "sum"),
    revenue=("revenue", "sum"),
    margin=("margin", "sum"),
).reset_index()
df_yearly["margin_pct"] = (df_yearly["margin"] / df_yearly["revenue"] * 100).round(2)

# Formatear para display
df_yearly_display = df_yearly.copy()
df_yearly_display["revenue"] = df_yearly_display["revenue"].apply(lambda x: fmt_eur(x))
df_yearly_display["margin"] = df_yearly_display["margin"].apply(lambda x: fmt_eur(x))
df_yearly_display["margin_pct"] = df_yearly_display["margin_pct"].apply(lambda x: f"{x:.2f} %")
df_yearly_display["n_ventas"] = df_yearly_display["n_ventas"].apply(fmt_int)
df_yearly_display.columns = ["Año", "Nº ventas", "Ingresos", "Margen", "Margen %"]

st.dataframe(df_yearly_display, use_container_width=True, hide_index=True)


# ============================================================================
# FILA 6: RANKING PRODUCTOS Y TIENDAS
# ============================================================================
section_header(
    "Ranking de productos y tiendas",
    "Top 5 por revenue (productos) y por margen (tiendas) · Periodo completo 2020-2025",
    color=COLORS["purple"],
)

df_products = load_top_products(n=5)
df_stores   = load_top_stores(n=5)

col1, col2 = st.columns(2)

with col1:
    st.caption("TOP 5 PRODUCTOS · POR REVENUE")
    if len(df_products) > 0:
        # Mini barras horizontales de revenue
        fig_prod = go.Figure()
        fig_prod.add_trace(go.Bar(
            y=df_products["name"],
            x=df_products["revenue"],
            orientation="h",
            marker=dict(color=COLORS["purple"], line=dict(color="#0E1117", width=1)),
            text=df_products["revenue"].apply(lambda x: fmt_eur(x, 0)),
            textposition="outside",
            textfont=dict(color=COLORS["text"], size=11),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Revenue: %{x:,.0f} €<br>"
                "Ventas: %{customdata[0]:,}<br>"
                "Margen: %{customdata[1]:.1f} %<extra></extra>"
            ),
            customdata=df_products[["n_ventas", "margin_pct"]].values,
        ))
        fig_prod.update_layout(
            **PLOTLY_LAYOUT, height=260, showlegend=False,
        )
        fig_prod.update_layout(
            yaxis=dict(autorange="reversed", gridcolor="#2D3748",
                       linecolor="#4A5568", color="#A0A6B8"),
            xaxis=dict(gridcolor="#2D3748", linecolor="#4A5568", color="#A0A6B8"),
            margin=dict(t=10, b=10, l=10, r=80),
        )
        st.plotly_chart(fig_prod, use_container_width=True)
    else:
        st.info("Regenera los snapshots para ver este gráfico en modo CSV.")

with col2:
    st.caption("TOP 5 TIENDAS · POR MARGEN")
    if len(df_stores) > 0:
        df_stores["label"] = df_stores["name"] + " (" + df_stores["city"] + ")"
        fig_store = go.Figure()
        fig_store.add_trace(go.Bar(
            y=df_stores["label"],
            x=df_stores["margin"],
            orientation="h",
            marker=dict(color=COLORS["success"], line=dict(color="#0E1117", width=1)),
            text=df_stores["revenue"].apply(lambda x: fmt_eur(x, 0)),
            textposition="outside",
            textfont=dict(color=COLORS["text"], size=11),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Margen: %{x:,.0f} €<br>"
                "Revenue: %{customdata[0]:,.0f} €<br>"
                "Margen %: %{customdata[1]:.1f} %<extra></extra>"
            ),
            customdata=df_stores[["revenue", "margin_pct"]].values,
        ))
        fig_store.update_layout(
            **PLOTLY_LAYOUT, height=260, showlegend=False,
        )
        fig_store.update_layout(
            yaxis=dict(autorange="reversed", gridcolor="#2D3748",
                       linecolor="#4A5568", color="#A0A6B8"),
            xaxis=dict(gridcolor="#2D3748", linecolor="#4A5568", color="#A0A6B8"),
            margin=dict(t=10, b=10, l=10, r=80),
        )
        st.plotly_chart(fig_store, use_container_width=True)
    else:
        st.info("Regenera los snapshots para ver este gráfico en modo CSV.")


# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.caption(f"💾 Datos cargados desde `marts.customer_360` y `dwh.fact_sales` · "
           f"Cache TTL: 10 min · Snapshot: 2025-12-30")