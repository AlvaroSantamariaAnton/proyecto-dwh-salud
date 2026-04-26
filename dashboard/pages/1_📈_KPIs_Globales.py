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
from dashboard.data import load_global_kpis, load_monthly_sales, load_customer_360
from dashboard.components import kpi_card, section_header, fmt_eur, fmt_int, fmt_pct

# ============================================================================
# CONFIGURACIÓN DE LA PÁGINA
# ============================================================================
st.set_page_config(page_title="KPIs Globales", page_icon="📈", layout="wide")

st.markdown(f"""
<div style="
    background: linear-gradient(90deg, {COLORS['primary']}40 0%, transparent 100%);
    border-left: 5px solid {COLORS['primary']};
    padding: 16px 24px;
    border-radius: 8px;
    margin-bottom: 24px;
">
    <div style="font-size:1.8rem;font-weight:800;color:{COLORS['text']};">
        📈 KPIs Globales
    </div>
    <div style="color:{COLORS['text_dim']};font-size:0.95rem;margin-top:2px;">
        Vista ejecutiva del negocio · Periodo completo (2020-2025)
    </div>
</div>
""", unsafe_allow_html=True)


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
             icon="💰", color=COLORS["primary"])
with col2:
    kpi_card("Margen bruto", fmt_eur(kpis["total_margin"]),
             delta=f"{kpis['margin_pct']}% sobre ingresos",
             icon="📊", color=COLORS["success"])
with col3:
    kpi_card("Clientes únicos", fmt_int(kpis["total_clientes"]),
             icon="👥", color=COLORS["secondary"])
with col4:
    kpi_card("Ventas (cabecera)", fmt_int(kpis["total_ventas"]),
             delta=f"{fmt_int(kpis['total_items'])} items",
             icon="🛒", color=COLORS["purple"])


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
             icon="↩️", color=COLORS["warning"])
with col2:
    kpi_card("Tasa devolución global", fmt_pct(return_rate_global, 2),
             icon="🎯", color=COLORS["accent"])
with col3:
    kpi_card("CLTV medio", fmt_eur(cltv_avg, 0),
             delta=f"{recurrent_pct:.1f}% recurrentes",
             icon="💎", color=COLORS["blue"])
with col4:
    kpi_card("Clientes en churn", fmt_pct(churned_pct, 1),
             delta="(>365 días sin compra)",
             icon="⚠️", color=COLORS["danger"])


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
# FOOTER
# ============================================================================
st.markdown("---")
st.caption(f"💾 Datos cargados desde `marts.customer_360` y `dwh.fact_sales` · "
           f"Cache TTL: 10 min · Snapshot: 2025-12-30")