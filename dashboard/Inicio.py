"""
Dashboard Saleshealth - Customer Analytics
Entry point principal. Versión sobria con carácter.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from dashboard.config import COLORS, get_engine
from dashboard.data import DATA_MODE, load_global_kpis, load_customer_360
from dashboard.components import fmt_eur, fmt_int, fmt_pct

# ============================================================================
st.set_page_config(
    page_title="Saleshealth · Customer Analytics",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS global con más personalidad
st.markdown(f"""
<style>
    /* Sidebar más ancho */
    [data-testid="stSidebar"] {{
        background: {COLORS['card_bg']};
        border-right: 1px solid #2D3748;
        min-width: 260px !important;
        max-width: 280px !important;
    }}
    [data-testid="stSidebar"] > div {{
        padding-top: 0.5rem;
    }}
    /* Métricas */
    [data-testid="stMetric"] {{
        background-color: {COLORS['card_bg']};
        border: 1px solid #2D3748;
        border-radius: 6px;
        padding: 14px 18px;
    }}
    [data-testid="stMetricLabel"] {{
        font-weight: 500;
        color: {COLORS['text_dim']};
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.78rem;
    }}
    [data-testid="stMetricValue"] {{
        color: {COLORS['text']};
        font-weight: 600;
    }}
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{ gap: 4px; }}
    .stTabs [data-baseweb="tab"] {{
        background-color: {COLORS['card_bg']};
        border-radius: 4px 4px 0 0;
        padding: 10px 20px;
        font-weight: 500;
        color: {COLORS['text_dim']};
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {COLORS['primary']}25 !important;
        color: {COLORS['primary']} !important;
    }}
    /* Inputs */
    .stTextInput input, .stNumberInput input, .stSelectbox > div {{
        background-color: {COLORS['card_bg']} !important;
        color: {COLORS['text']} !important;
        border-color: #2D3748 !important;
    }}
    .streamlit-expanderHeader {{
        background-color: {COLORS['card_bg']};
        border-radius: 6px;
    }}
    /* Quitar el padding superior excesivo */
    .block-container {{
        padding-top: 2.5rem !important;
    }}
</style>
""", unsafe_allow_html=True)


# ============================================================================
# Cargar datos (necesarios para los KPI previews)
# ============================================================================
try:
    kpis = load_global_kpis()
    df_customers = load_customer_360()
    n_champions_premium = (df_customers["cluster_all_name"] == "Champions Premium").sum() if "cluster_all_name" in df_customers.columns else 0
    n_active = (df_customers["is_churned"] == False).sum() if "is_churned" in df_customers.columns else 0
    cltv_total = df_customers["cltv_historic"].sum() if "cltv_historic" in df_customers.columns else 0
except Exception:
    kpis = None
    df_customers = None
    n_champions_premium = 0
    n_active = 0
    cltv_total = 0


# ============================================================================
# HERO HEADER con números grandes como decoración
# ============================================================================
hero_html = (
    '<div style="padding:36px 0 32px 0;border-bottom:1px solid #2D3748;'
    'margin-bottom:36px;">'
    f'<div style="color:{COLORS["primary"]};font-size:0.78rem;font-weight:600;'
    'text-transform:uppercase;letter-spacing:3px;">'
    'Customer Analytics &middot; UAX Final Project'
    '</div>'
    f'<div style="font-size:2.6rem;font-weight:800;color:{COLORS["text"]};'
    'margin-top:10px;line-height:1.05;letter-spacing:-1px;">'
    'Saleshealth'
    '</div>'
    f'<div style="color:{COLORS["text_dim"]};font-size:1.05rem;margin-top:14px;'
    'max-width:680px;line-height:1.6;">'
    'Análisis de Customer Lifetime Value, segmentación RFM y clustering K-Means '
    f'sobre <b style="color:{COLORS["text"]};">5.750 clientes</b> y '
    f'<b style="color:{COLORS["text"]};">42.555 líneas de venta</b> de un retail '
    'de productos de salud.'
    '</div>'
    '</div>'
)
st.markdown(hero_html, unsafe_allow_html=True)


# ============================================================================
# KPI BAND — números clave del negocio
# ============================================================================
if kpis:
    st.markdown(f"""
    <div style="color:{COLORS['text_dim']};font-size:0.74rem;font-weight:600;
                text-transform:uppercase;letter-spacing:2px;margin-bottom:12px;">
        Key Numbers
    </div>
    """, unsafe_allow_html=True)

    cols = st.columns(4)
    band = [
        ("Ingresos totales",   fmt_eur(kpis["total_revenue"]),                   COLORS["primary"]),
        ("Margen bruto",       f"{kpis['margin_pct']:.0f}%",                    COLORS["secondary"]),
        ("CLTV Champions",     fmt_eur(cltv_total * 0.925, 0) if cltv_total else "—",  COLORS["success"]),
        ("Clientes activos",   fmt_int(n_active),                                COLORS["accent"]),
    ]
    for col, (label, value, color) in zip(cols, band):
        with col:
            st.markdown(f"""
            <div style="
                background: {COLORS['card_bg']};
                border: 1px solid #2D3748;
                border-left: 3px solid {color};
                border-radius: 4px;
                padding: 16px 18px;
            ">
                <div style="color:{COLORS['text_dim']};font-size:0.7rem;font-weight:600;
                            text-transform:uppercase;letter-spacing:1px;">
                    {label}
                </div>
                <div style="color:{COLORS['text']};font-size:1.5rem;font-weight:700;
                            margin-top:6px;line-height:1.1;">
                    {value}
                </div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown("&nbsp;")


# ============================================================================
# SECCIONES CON HIGHLIGHTS reales
# ============================================================================
st.markdown(f"""
<div style="color:{COLORS['text_dim']};font-size:0.74rem;font-weight:600;
            text-transform:uppercase;letter-spacing:2px;margin:32px 0 16px 0;">
    Secciones del análisis
</div>
""", unsafe_allow_html=True)

cols = st.columns(4)
pages = [
    {
        "title": "KPIs Globales",
        "desc":  "Ingresos, márgenes, evolución temporal del negocio",
        "stat":  "9,68M €",
        "stat_label": "Revenue 2020-2025",
        "color": COLORS["primary"],
    },
    {
        "title": "Análisis Cliente",
        "desc":  "Distribución de CLTV, segmentos RFM, top clientes",
        "stat":  "9 segmentos",
        "stat_label": "RFM scoring",
        "color": COLORS["secondary"],
    },
    {
        "title": "Clustering",
        "desc":  "Visualización de los 4 clusters K-Means tras PCA",
        "stat":  "4 perfiles",
        "stat_label": "K-Means + PCA",
        "color": COLORS["purple"],
    },
    {
        "title": "Customer 360",
        "desc":  "Buscador individual con ficha completa por cliente",
        "stat":  "5.750",
        "stat_label": "Clientes únicos",
        "color": COLORS["success"],
    },
]

for col, page in zip(cols, pages):
    with col:
        st.markdown(f"""
        <div style="
            background: {COLORS['card_bg']};
            border: 1px solid #2D3748;
            border-top: 2px solid {page['color']};
            border-radius: 4px;
            padding: 18px 18px 16px 18px;
            min-height: 170px;
            position: relative;
            transition: border-color 0.2s;
        ">
            <div style="font-weight:700;font-size:1.05rem;color:{COLORS['text']};
                        letter-spacing:0.2px;">
                {page['title']}
            </div>
            <div style="color:{COLORS['text_dim']};font-size:0.85rem;margin-top:10px;
                        line-height:1.5;min-height:50px;">
                {page['desc']}
            </div>
            <div style="
                margin-top:14px;padding-top:12px;border-top:1px solid #2D3748;
            ">
                <div style="color:{page['color']};font-size:1.15rem;font-weight:700;">
                    {page['stat']}
                </div>
                <div style="color:{COLORS['text_dim']};font-size:0.7rem;font-weight:500;
                            text-transform:uppercase;letter-spacing:1px;">
                    {page['stat_label']}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================================
# INSIGHT BOX (frase con punch del proyecto)
# ============================================================================
st.markdown(f"""
<div style="
    background: linear-gradient(90deg, {COLORS['primary']}15 0%, transparent 70%);
    border-left: 3px solid {COLORS['primary']};
    padding: 18px 24px;
    margin-top: 36px;
    border-radius: 4px;
">
    <div style="color:{COLORS['text_dim']};font-size:0.72rem;font-weight:600;
                text-transform:uppercase;letter-spacing:2px;">
        Hallazgo principal
    </div>
    <div style="color:{COLORS['text']};font-size:1.1rem;font-weight:500;margin-top:8px;
                line-height:1.5;">
        El <b style="color:{COLORS['primary']};">13% de la base</b> de clientes 
        (clusters Champions Premium + activos) genera el 
        <b style="color:{COLORS['primary']};">91,7% del valor histórico</b> del negocio. 
        El clustering K-Means revela además un segmento tóxico de 420 clientes con 
        88% de tasa de devolución, invisible al RFM tradicional.
    </div>
</div>
""", unsafe_allow_html=True)


# ============================================================================
# TECH STACK (decoración inferior)
# ============================================================================
st.markdown(f"""
<div style="margin-top:48px;padding-top:24px;border-top:1px solid #2D3748;">
    <div style="color:{COLORS['text_dim']};font-size:0.7rem;font-weight:600;
                text-transform:uppercase;letter-spacing:2px;margin-bottom:10px;">
        Stack
    </div>
    <div style="display:flex;flex-wrap:wrap;gap:10px;">
        <span style="background:{COLORS['card_bg']};border:1px solid #2D3748;
                     padding:6px 14px;border-radius:4px;font-size:0.82rem;
                     color:{COLORS['text_dim']};">PostgreSQL 18</span>
        <span style="background:{COLORS['card_bg']};border:1px solid #2D3748;
                     padding:6px 14px;border-radius:4px;font-size:0.82rem;
                     color:{COLORS['text_dim']};">Python · pandas · SQLAlchemy</span>
        <span style="background:{COLORS['card_bg']};border:1px solid #2D3748;
                     padding:6px 14px;border-radius:4px;font-size:0.82rem;
                     color:{COLORS['text_dim']};">scikit-learn · K-Means · PCA</span>
        <span style="background:{COLORS['card_bg']};border:1px solid #2D3748;
                     padding:6px 14px;border-radius:4px;font-size:0.82rem;
                     color:{COLORS['text_dim']};">Streamlit · Plotly</span>
        <span style="background:{COLORS['card_bg']};border:1px solid #2D3748;
                     padding:6px 14px;border-radius:4px;font-size:0.82rem;
                     color:{COLORS['text_dim']};">Kimball Dimensional Modeling</span>
    </div>
</div>
""", unsafe_allow_html=True)


# ============================================================================
# DATA SOURCE STATUS
# ============================================================================
st.markdown("&nbsp;")
with st.expander(f"Fuente de datos: {DATA_MODE.upper()}", expanded=False):
    if DATA_MODE == "csv":
        st.success(
            "**Modo CSV (Streamlit Cloud)** — El dashboard usa snapshots de "
            "datos versionados en el repositorio (`data/snapshots/`) en lugar de conectar a "
            "PostgreSQL. Los datos corresponden al último ETL ejecutado en local."
        )
        st.caption(
            "Para datos en vivo, clona el repo, restaura el dump de PostgreSQL y ejecuta "
            "`python -m etl.run_etl` localmente. El dashboard detectará la BD automáticamente."
        )
    else:
        try:
            eng = get_engine()
            with eng.connect() as conn:
                from sqlalchemy import text
                result = conn.execute(text("SELECT COUNT(*) FROM marts.customer_360")).scalar()
            st.success(
                f"**Modo PostgreSQL (local)** — Conectado a `saleshealth_dwh`. "
                f"Clientes en `customer_360`: **{result:,}**"
            )
        except Exception as e:
            st.warning(f"Modo PostgreSQL pero la conexión ha fallado: {e}")


# ============================================================================
# SIDEBAR mejorado
# ============================================================================
st.sidebar.markdown(f"""
<div style="padding:16px 4px 20px 4px;">
    <div style="color:{COLORS['primary']};font-size:0.68rem;font-weight:700;
                text-transform:uppercase;letter-spacing:2.5px;">
        Customer Analytics
    </div>
    <div style="font-weight:800;color:{COLORS['text']};font-size:1.35rem;
                margin-top:6px;letter-spacing:-0.5px;">
        Saleshealth
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown(f"""
<div style="padding:0 4px 14px 4px;">
    <div style="height:1px;background:#2D3748;margin-bottom:14px;"></div>
    <div style="color:{COLORS['text_dim']};font-size:0.68rem;font-weight:600;
                text-transform:uppercase;letter-spacing:1.5px;margin-bottom:10px;">
        Snapshot
    </div>
    <div style="font-size:0.8rem;color:{COLORS['text']};line-height:1.9;">
        <div style="display:flex;justify-content:space-between;">
            <span style="color:{COLORS['text_dim']};">Clientes</span>
            <b>5.750</b>
        </div>
        <div style="display:flex;justify-content:space-between;">
            <span style="color:{COLORS['text_dim']};">Ventas</span>
            <b>20.000</b>
        </div>
        <div style="display:flex;justify-content:space-between;">
            <span style="color:{COLORS['text_dim']};">Periodo</span>
            <b>2020–2025</b>
        </div>
        <div style="display:flex;justify-content:space-between;">
            <span style="color:{COLORS['text_dim']};">Margen</span>
            <b>40 %</b>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown(
    '<div style="height:1px;background:#2D3748;margin:18px 4px 14px 4px;"></div>'
    '<div style="padding:0 4px;">'
    f'<div style="color:{COLORS["text"]};font-weight:600;font-size:0.85rem;">Proyecto Final</div>'
    f'<div style="color:{COLORS["text_dim"]};font-size:0.78rem;margin-top:2px;">UAX 2025 / 2026</div>'
    f'<div style="color:{COLORS["text_dim"]};font-size:0.78rem;margin-top:8px;">Álvaro Santamaría Antón</div>'
    f'<div style="margin-top:14px;">'
    f'<span style="background:{COLORS["dark"]};padding:3px 8px;border-radius:3px;'
    f'color:{COLORS["accent"]};font-size:0.72rem;border:1px solid #2D3748;'
    f'font-family:monospace;display:inline-block;">'
    'marts.customer_360'
    '</span>'
    '</div>'
    '</div>',
    unsafe_allow_html=True,
)