"""
Dashboard Saleshealth - Customer Analytics
Entry point principal. Versión dark mode.
"""
import sys
from pathlib import Path

# Asegurar que la raíz del proyecto está en sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from dashboard.config import COLORS, get_engine

# ============================================================================
# CONFIGURACIÓN GLOBAL
# ============================================================================
st.set_page_config(
    page_title="Saleshealth · Inicio",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS global - dark mode con acentos coloridos
st.markdown(f"""
<style>
    /* Sidebar con gradiente sutil */
    [data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {COLORS['card_bg']} 0%, {COLORS['dark']} 100%);
        border-right: 1px solid #2D3748;
    }}
    
    /* Métricas Streamlit */
    [data-testid="stMetric"] {{
        background-color: {COLORS['card_bg']};
        border: 1px solid #2D3748;
        border-radius: 10px;
        padding: 14px 18px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }}
    [data-testid="stMetricLabel"] {{
        font-weight: 600;
        color: {COLORS['text_dim']};
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    [data-testid="stMetricValue"] {{
        color: {COLORS['text']};
        font-weight: 700;
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{ gap: 8px; }}
    .stTabs [data-baseweb="tab"] {{
        background-color: {COLORS['card_bg']};
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        font-weight: 600;
        color: {COLORS['text_dim']};
    }}
    .stTabs [aria-selected="true"] {{
        background-color: {COLORS['primary']}30 !important;
        color: {COLORS['primary']} !important;
    }}
    
    /* Inputs */
    .stTextInput input, .stNumberInput input, .stSelectbox > div {{
        background-color: {COLORS['card_bg']} !important;
        color: {COLORS['text']} !important;
        border-color: #2D3748 !important;
    }}
    
    /* Expander */
    .streamlit-expanderHeader {{
        background-color: {COLORS['card_bg']};
        border-radius: 8px;
    }}
</style>
""", unsafe_allow_html=True)


# ============================================================================
# HOME PAGE
# ============================================================================
st.markdown(f"""
<div style="
    background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['purple']} 50%, {COLORS['blue']} 100%);
    color: white;
    padding: 44px 50px;
    border-radius: 14px;
    margin-bottom: 30px;
    box-shadow: 0 8px 24px rgba(255,107,157,0.2);
">
    <div style="font-size:2.4rem;font-weight:800;line-height:1.1;">
        📊 Saleshealth Customer Analytics
    </div>
    <div style="font-size:1.1rem;opacity:0.95;margin-top:10px;">
        Dashboard interactivo sobre <code style="background:rgba(0,0,0,0.25);padding:2px 8px;border-radius:4px;color:white;">marts.customer_360</code>
        · 5.750 clientes · CLTV · RFM · Clustering K-Means
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown(f"### 👋 Bienvenido")
st.markdown(f"""
<div style="color:{COLORS['text_dim']};font-size:1rem;line-height:1.6;">
Este dashboard explora el Data Warehouse construido sobre la base de datos operacional
de venta retail de productos de salud. Usa el menú de la izquierda para navegar entre las páginas:
</div>
""", unsafe_allow_html=True)

st.markdown("&nbsp;")

cols = st.columns(4)
pages = [
    ("📈 KPIs Globales",    "Vista ejecutiva: ingresos, márgenes, evolución temporal", COLORS["primary"]),
    ("👥 Análisis Cliente", "Distribución de CLTV, segmentos RFM, top clientes",       COLORS["secondary"]),
    ("🎯 Clustering",       "Visualización de los 4 clusters K-Means",                 COLORS["purple"]),
    ("🔍 Customer 360",     "Buscador individual con ficha completa por cliente",      COLORS["success"]),
]

for col, (title, desc, color) in zip(cols, pages):
    with col:
        st.markdown(f"""
        <div style="
            background: {COLORS['card_bg']};
            border-top: 4px solid {color};
            border-radius: 10px;
            padding: 18px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            min-height: 140px;
            transition: transform 0.2s;
        ">
            <div style="font-weight:700;font-size:1.05rem;color:{COLORS['text']};">{title}</div>
            <div style="color:{COLORS['text_dim']};font-size:0.88rem;margin-top:10px;line-height:1.5;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Test de conexión
with st.expander("⚙️ Estado de la conexión a la BD", expanded=False):
    try:
        eng = get_engine()
        with eng.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text("SELECT COUNT(*) FROM marts.customer_360")).scalar()
        st.success(f"✅ Conectado a saleshealth_dwh. Clientes en customer_360: **{result:,}**")
    except Exception as e:
        st.error(f"❌ No se ha podido conectar a la BD: {e}")
        st.info("Verifica tu .env y que PostgreSQL esté corriendo.")

# ============================================================================
# SIDEBAR
# ============================================================================
st.sidebar.markdown(f"""
<div style="padding:24px 10px 30px 10px;text-align:center;">
    <div style="font-size:2rem;">📊</div>
    <div style="font-weight:700;color:{COLORS['text']};font-size:1.15rem;margin-top:8px;">
        Saleshealth
    </div>
    <div style="color:{COLORS['text_dim']};font-size:0.85rem;">Customer Analytics</div>
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.markdown(f"""
<div style="padding:10px;font-size:0.85rem;color:{COLORS['text_dim']};line-height:1.6;">
    <b style="color:{COLORS['text']};">Proyecto Final · UAX 2025/26</b><br>
    Álvaro Santamaría Antón<br><br>
    Conectado a:<br>
    <code style="background:{COLORS['card_bg']};padding:2px 6px;border-radius:4px;color:{COLORS['accent']};">marts.customer_360</code>
</div>
""", unsafe_allow_html=True)