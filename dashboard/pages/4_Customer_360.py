"""
Página 4 — Customer 360 Lookup
Buscador individual con ficha completa por cliente.
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

from dashboard.config import COLORS, PLOTLY_LAYOUT, CLUSTER_COLORS, RFM_COLORS
from dashboard.data import load_customer_360, load_customer_orders
from dashboard.components import kpi_card, section_header, fmt_eur, fmt_int, fmt_pct
from dashboard.components import page_header

# ============================================================================
# CONFIGURACIÓN
# ============================================================================
st.set_page_config(page_title="Customer 360", layout="wide")

page_header(
    "Customer 360",
    "Ficha completa por cliente · Métricas, histórico de compras y comparativa",
    color=COLORS["success"],
)


# ============================================================================
# CARGA DE DATOS
# ============================================================================
df = load_customer_360()


# ============================================================================
# BUSCADOR
# ============================================================================
st.markdown(f"### Selecciona un cliente")

# Construir lista de opciones: "ID - Nombre"
df["display"] = df["customer_id_nk"].astype(str) + " — " + df["full_name"].fillna("(sin nombre)")

# Por defecto: ofrecer los Top 5 por CLTV
top_clientes = df.nlargest(5, "cltv_historic")
default_options = top_clientes["display"].tolist()

# Modo de búsqueda
col_mode, col_search = st.columns([1, 3])
with col_mode:
    search_mode = st.radio(
        "Modo:",
        options=["Top CLTV", "Buscar por ID / nombre"],
        label_visibility="collapsed",
    )

with col_search:
    if search_mode == "Top CLTV":
        selected = st.selectbox(
            "Cliente:",
            options=df.nlargest(50, "cltv_historic")["display"].tolist(),
            label_visibility="collapsed",
        )
    else:
        selected = st.selectbox(
            "Cliente:",
            options=df["display"].tolist(),
            placeholder="Escribe un ID o nombre…",
            label_visibility="collapsed",
        )

# Extraer customer_id_nk
customer_id_nk = int(selected.split(" — ")[0])
cliente = df[df["customer_id_nk"] == customer_id_nk].iloc[0]


# ============================================================================
# CABECERA DEL CLIENTE
# ============================================================================
cluster_color = CLUSTER_COLORS.get(cliente.get("cluster_all_name"), COLORS["primary"])
rfm_color = RFM_COLORS.get(cliente.get("rfm_segment"), COLORS["secondary"])

st.markdown(f"""
<div style="
    background: linear-gradient(135deg, {cluster_color}25 0%, {COLORS['card_bg']} 60%, {rfm_color}25 100%);
    border-radius: 14px;
    padding: 26px 32px;
    margin: 20px 0;
    box-shadow: 0 6px 18px rgba(0,0,0,0.3);
    border: 1px solid #2D3748;
">
    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;">
        <div>
            <div style="color:{COLORS['text_dim']};font-size:0.85rem;text-transform:uppercase;letter-spacing:1px;">
                Cliente #{cliente['customer_id_nk']}
            </div>
            <div style="color:{COLORS['text']};font-size:1.9rem;font-weight:800;line-height:1.1;margin-top:4px;">
                {cliente.get('full_name', '—')}
            </div>
            <div style="color:{COLORS['text_dim']};font-size:0.95rem;margin-top:8px;">
                Email: {cliente.get('email', '—')} &nbsp;·&nbsp; Tel: {cliente.get('phone', '—')}
            </div>
        </div>
        <div style="text-align:right;">
            <div style="
                display:inline-block;background:{cluster_color};color:#000;padding:6px 14px;
                border-radius:20px;font-weight:700;font-size:0.85rem;margin-bottom:6px;
            "> {cliente.get('cluster_all_name', '—')}</div><br>
            <div style="
                display:inline-block;background:{rfm_color};color:#000;padding:6px 14px;
                border-radius:20px;font-weight:700;font-size:0.85rem;
            "> {cliente.get('rfm_segment', '—')}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ============================================================================
# FILA 1: KPIs PRINCIPALES DEL CLIENTE
# ============================================================================
section_header("Métricas del cliente", color=COLORS["primary"])

c1, c2, c3, c4 = st.columns(4)
with c1:
    kpi_card("CLTV histórico", fmt_eur(cliente.get("cltv_historic", 0), 2),
             color=COLORS["primary"])
with c2:
    total_units_val = int(cliente.get('total_units', 0)) if pd.notna(cliente.get('total_units')) else 0
    kpi_card("Nº pedidos", fmt_int(cliente.get("num_orders", 0)),
             delta=f"{total_units_val} unidades totales",
             color=COLORS["secondary"])
with c3:
    kpi_card("Ticket medio", fmt_eur(cliente.get("avg_order_value", 0), 2),
             color=COLORS["success"])
with c4:
    kpi_card("Margen generado", fmt_eur(cliente.get("gross_margin", 0), 2),
             color=COLORS["accent"])

c1, c2, c3, c4 = st.columns(4)
with c1:
    days = int(cliente.get("days_since_last_order", 0)) if pd.notna(cliente.get("days_since_last_order")) else 0
    kpi_card("Última compra hace", f"{days} días",
             color=COLORS["blue"])
with c2:
    lifespan = int(cliente.get("customer_lifespan_days", 0)) if pd.notna(cliente.get("customer_lifespan_days")) else 0
    kpi_card("Antigüedad", f"{lifespan} días",
             color=COLORS["purple"])
with c3:
    return_pct = (cliente.get("return_rate", 0) * 100) if pd.notna(cliente.get("return_rate")) else 0
    color_ret = COLORS["danger"] if return_pct > 30 else COLORS["warning"] if return_pct > 10 else COLORS["success"]
    kpi_card("Tasa devolución", fmt_pct(return_pct, 1),
             color=color_ret)
with c4:
    is_churned = cliente.get("is_churned", False)
    risk_level = cliente.get("churn_risk_level", "Low")
    risk_color = {"High": COLORS["danger"], "Medium": COLORS["warning"], "Low": COLORS["success"]}.get(risk_level, COLORS["primary"])
    estado = "Churned" if is_churned else "Activo"
    kpi_card("Estado", estado,
             delta=f"Churn risk: {risk_level}",
             color=risk_color)


# ============================================================================
# FILA 2: HISTÓRICO DE COMPRAS
# ============================================================================
section_header("Histórico de compras", "Pedidos del cliente ordenados por fecha (más recientes primero)",
               color=COLORS["secondary"])

orders = load_customer_orders(customer_id_nk)

if len(orders) == 0:
    st.info("Este cliente no tiene pedidos en fact_sales.")
else:
    col1, col2 = st.columns([2, 1])

    with col1:
        # Timeline de compras
        fig_timeline = go.Figure()
        fig_timeline.add_trace(go.Scatter(
            x=orders["fecha"],
            y=orders["importe"],
            mode="markers+lines",
            line=dict(color=COLORS["secondary"], width=1.5, dash="dot"),
            marker=dict(
                size=orders["unidades"] * 4 + 8,
                color=orders["importe"],
                colorscale=[
                    [0.0, COLORS["accent"]],
                    [1.0, COLORS["primary"]],
                ],
                showscale=False,
                line=dict(width=1, color="white"),
                opacity=0.85,
            ),
            customdata=orders[["sale_id_nk", "n_items", "unidades", "tiene_devolucion"]].values,
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Venta ID: %{customdata[0]}<br>"
                "Importe: %{y:,.2f} €<br>"
                "Items: %{customdata[1]} · Unidades: %{customdata[2]}<br>"
                "Con devolución: %{customdata[3]}<extra></extra>"
            ),
            name="Pedido",
        ))
        fig_timeline.update_layout(**PLOTLY_LAYOUT, height=380, showlegend=False)
        fig_timeline.update_layout(
            xaxis_title="Fecha",
            yaxis_title="Importe (€)",
        )
        st.plotly_chart(fig_timeline, use_container_width=True)

    with col2:
        # Mini-stats
        n_pedidos = len(orders)
        total_gastado = orders["importe"].sum()
        ticket_medio = orders["importe"].mean()
        n_devoluciones = orders["tiene_devolucion"].sum()
        
        st.markdown(f"""
        <div style="
            background: {COLORS['card_bg']};
            border-radius: 10px;
            padding: 18px 22px;
            border: 1px solid #2D3748;
            margin-top: 28px;
        ">
            <div style="font-weight:700;color:{COLORS['text']};font-size:1rem;margin-bottom:14px;">
                Estadísticas del histórico
            </div>
            <div style="margin-bottom:10px;">
                <div style="color:{COLORS['text_dim']};font-size:0.78rem;text-transform:uppercase;">Total pedidos</div>
                <div style="color:{COLORS['secondary']};font-size:1.4rem;font-weight:700;">{n_pedidos}</div>
            </div>
            <div style="margin-bottom:10px;">
                <div style="color:{COLORS['text_dim']};font-size:0.78rem;text-transform:uppercase;">Total gastado</div>
                <div style="color:{COLORS['primary']};font-size:1.4rem;font-weight:700;">{fmt_eur(total_gastado, 2)}</div>
            </div>
            <div style="margin-bottom:10px;">
                <div style="color:{COLORS['text_dim']};font-size:0.78rem;text-transform:uppercase;">Ticket medio</div>
                <div style="color:{COLORS['success']};font-size:1.4rem;font-weight:700;">{fmt_eur(ticket_medio, 2)}</div>
            </div>
            <div>
                <div style="color:{COLORS['text_dim']};font-size:0.78rem;text-transform:uppercase;">Pedidos con devolución</div>
                <div style="color:{COLORS['warning']};font-size:1.4rem;font-weight:700;">{n_devoluciones}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # Tabla detalle
    with st.expander(f"Ver detalle de los {len(orders)} pedidos", expanded=False):
        orders_display = orders.copy()
        orders_display["fecha"] = pd.to_datetime(orders_display["fecha"]).dt.strftime("%Y-%m-%d")
        orders_display["importe"] = orders_display["importe"].apply(lambda x: fmt_eur(x, 2))
        orders_display["margen"] = orders_display["margen"].apply(lambda x: fmt_eur(x, 2))
        orders_display["tiene_devolucion"] = orders_display["tiene_devolucion"].map({True: "Sí", False: "—"})
        orders_display.columns = ["Venta ID", "Fecha", "Nº items", "Unidades", "Importe", "Margen", "Devolución"]
        st.dataframe(orders_display, use_container_width=True, hide_index=True)


# ============================================================================
# FILA 3: COMPARATIVA RELATIVA (PERCENTILES)
# ============================================================================
section_header("Posición relativa frente al resto",
               "Percentil del cliente en cada métrica (vs los 5.750 clientes)",
               color=COLORS["accent"])

# Calcular percentiles
metrics_to_compare = {
    "CLTV": "cltv_historic",
    "Frecuencia (pedidos)": "num_orders",
    "Ticket medio": "avg_order_value",
    "Volumen (unidades)": "total_units",
    "Margen generado": "gross_margin",
}

percentiles = {}
for label, col in metrics_to_compare.items():
    val = cliente.get(col, 0)
    if pd.notna(val) and df[col].std() > 0:
        pct = (df[col] < val).sum() / len(df) * 100
        percentiles[label] = (pct, val)

if percentiles:
    fig_pct = go.Figure()
    labels = list(percentiles.keys())
    pcts = [v[0] for v in percentiles.values()]
    
    # Color según percentil: rojo bajo, verde alto
    bar_colors = []
    for p in pcts:
        if p < 33:
            bar_colors.append(COLORS["danger"])
        elif p < 66:
            bar_colors.append(COLORS["warning"])
        else:
            bar_colors.append(COLORS["success"])
    
    fig_pct.add_trace(go.Bar(
        y=labels, x=pcts,
        orientation="h",
        marker_color=bar_colors,
        text=[f"P{p:.0f}" for p in pcts],
        textposition="outside",
        textfont=dict(color=COLORS["text"], size=12, weight="bold"),
        hovertemplate="<b>%{y}</b><br>Percentil: %{x:.1f}<extra></extra>",
    ))
    fig_pct.add_vline(x=50, line_dash="dot", line_color=COLORS["text_dim"],
                      annotation_text="Mediana", annotation_position="top",
                      annotation_font_color=COLORS["text_dim"])
    fig_pct.update_layout(**PLOTLY_LAYOUT, height=320, showlegend=False)
    fig_pct.update_layout(
        xaxis_title="Percentil (0 = peor del grupo, 100 = mejor)",
        xaxis=dict(range=[0, 110], gridcolor="#2D3748", linecolor="#4A5568", color="#A0A6B8"),
        yaxis=dict(autorange="reversed", gridcolor="#2D3748", linecolor="#4A5568", color="#A0A6B8"),
    )
    st.plotly_chart(fig_pct, use_container_width=True)


# ============================================================================
# FILA 4: ALERTAS Y RECOMENDACIONES
# ============================================================================
section_header("Alertas y recomendaciones", color=COLORS["danger"])

alerts = []

# Alerta 1: Churn risk
if cliente.get("is_churned"):
    alerts.append((
        "danger",
        "Cliente churned",
        f"Lleva {int(cliente.get('days_since_last_order', 0))} días sin comprar. Si su CLTV es alto, candidato a campaña de winback."
    ))
elif cliente.get("churn_risk_level") == "Medium":
    alerts.append((
        "warning",
        "Pre-churn detectado",
        f"Cliente todavía activo pero con riesgo Medium. Está alargando el tiempo entre compras. Acción: incentivo personalizado antes de los próximos 90 días."
    ))

# Alerta 2: Champion
if cliente.get("rfm_segment") == "Champions":
    alerts.append((
        "success",
        "Cliente Champion",
        f"Forma parte del 14,5% de clientes que generan el 89% del CLTV. Prioridad alta de retención y atención prioritaria."
    ))

# Alerta 3: Devolvedor
ret_rate = cliente.get("return_rate", 0)
if pd.notna(ret_rate) and ret_rate > 0.5:
    alerts.append((
        "danger",
        "Tasa de devolución anómala",
        f"Devuelve el {ret_rate*100:.1f}% de lo que compra. Patrón compatible con arbitraje. Considerar restricciones operativas."
    ))

# Alerta 4: One-shot reciente
if cliente.get("num_orders", 0) == 1 and cliente.get("days_since_last_order", 999) < 180:
    alerts.append((
        "blue",
        "Cliente nuevo / one-shot reciente",
        "Compra única en los últimos 6 meses. Ventana de oportunidad: campaña dirigida a la 2ª compra para activarlo."
    ))

# Alerta 5: VIP recurrente
if cliente.get("cluster_all_name") == "Champions Premium":
    alerts.append((
        "purple",
        "Champion Premium",
        f"Top 6,7% de la base. CLTV {fmt_eur(cliente.get('cltv_historic', 0), 0)}. Núcleo del valor — vale la pena cualquier inversión razonable en su retención."
    ))

if not alerts:
    alerts.append((
        "blue",
        "Cliente estándar",
        "No se detectan patrones anómalos ni oportunidades urgentes en este perfil."
    ))

# Render alerts
for kind, title, msg in alerts:
    color_map = {
        "danger":  COLORS["danger"],
        "warning": COLORS["warning"],
        "success": COLORS["success"],
        "blue":    COLORS["blue"],
        "purple":  COLORS["purple"],
    }
    bg_color = color_map.get(kind, COLORS["primary"])
    st.markdown(f"""
    <div style="
        background: linear-gradient(90deg, {bg_color}25 0%, {COLORS['card_bg']} 100%);
        border-left: 4px solid {bg_color};
        border-radius: 8px;
        padding: 14px 20px;
        margin-bottom: 10px;
    ">
        <div style="font-weight:700;color:{COLORS['text']};font-size:1rem;">{title}</div>
        <div style="color:{COLORS['text_dim']};font-size:0.92rem;margin-top:4px;line-height:1.5;">{msg}</div>
    </div>
    """, unsafe_allow_html=True)


# ============================================================================
# FOOTER
# ============================================================================
st.markdown("---")
st.caption(f"💾 Cliente {customer_id_nk} · Datos desde `marts.customer_360` y `dwh.fact_sales`")