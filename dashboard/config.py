"""
Configuración del dashboard - conexión a saleshealth_dwh.
Lee credenciales desde .env (mismo que el ETL).
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Cargar .env de la raíz del proyecto
ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DB_USER     = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = os.getenv("DB_PORT", "5432")
DB_NAME_DWH = os.getenv("DB_NAME_DWH", "saleshealth_dwh")

# ============================================================================
# PALETA "DARK MARKETING" — colores vibrantes que destacan sobre fondo oscuro
# ============================================================================
COLORS = {
    "primary":   "#FF6B9D",   # Rosa vibrante (acento principal)
    "secondary": "#4ECDC4",   # Turquesa brillante
    "accent":    "#FFE66D",   # Amarillo neón
    "purple":    "#C77DFF",   # Lavanda brillante
    "blue":      "#4CC9F0",   # Cian brillante
    "success":   "#06FFA5",   # Verde menta neón
    "warning":   "#FFB627",   # Naranja vivo
    "danger":    "#FF477E",   # Rojo coral
    "dark":      "#0E1117",   # Fondo Streamlit oscuro
    "card_bg":   "#1A1F2E",   # Fondo de cards (un poco más claro)
    "text":      "#FAFAFA",   # Texto principal blanco
    "text_dim":  "#A0A6B8",   # Texto secundario gris claro
}

# Colores para clusters (vivos para fondo oscuro)
CLUSTER_COLORS = {
    "Champions Premium":        "#06FFA5",   # Verde neón (élite)
    "Champions activos":        "#4CC9F0",   # Cian brillante
    "Compradores ocasionales":  "#FFB627",   # Naranja vivo
    "Devolvedores compulsivos": "#FF477E",   # Rojo coral (alerta)
    "Élite VIP":                "#C77DFF",   # Lavanda
    "Recurrentes Consolidados": "#4ECDC4",   # Turquesa
    "Recurrentes Estándar":     "#FFE66D",   # Amarillo neón
    "Recurrentes En Riesgo":    "#FF6B9D",   # Rosa vibrante
}

# Paleta para segmentos RFM
RFM_COLORS = {
    "Champions":           "#06FFA5",
    "Loyal Customers":     "#4CC9F0",
    "New Customers":       "#FFE66D",
    "Potential Loyalists": "#4ECDC4",
    "At Risk":             "#FFB627",
    "Cant Lose Them":      "#FF6B9D",
    "Hibernating":         "#C77DFF",
    "Lost":                "#FF477E",
    "Others":              "#8D99AE",
}

# Plantilla Plotly oscura (la usaremos en TODOS los gráficos)
PLOTLY_TEMPLATE = "plotly_dark"

# Layout base para gráficos Plotly (importar y aplicar a cada figura)
PLOTLY_LAYOUT = {
    "template": PLOTLY_TEMPLATE,
    "paper_bgcolor": "rgba(0,0,0,0)",      # Transparente
    "plot_bgcolor":  "rgba(0,0,0,0)",      # Transparente
    "font": {"color": "#FAFAFA", "family": "sans-serif"},
    "title": {"font": {"size": 16, "color": "#FAFAFA"}},
    "xaxis": {"gridcolor": "#2D3748", "linecolor": "#4A5568", "color": "#A0A6B8"},
    "yaxis": {"gridcolor": "#2D3748", "linecolor": "#4A5568", "color": "#A0A6B8"},
    "legend": {"bgcolor": "rgba(26,31,46,0.7)", "bordercolor": "#2D3748"},
    "hoverlabel": {"bgcolor": "#1A1F2E", "font": {"color": "#FAFAFA"}},
    "margin": {"t": 50, "b": 50, "l": 50, "r": 30},
}


def get_engine():
    """Crea engine SQLAlchemy. Usado por las funciones de data.py."""
    url = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME_DWH}"
    )
    return create_engine(url, pool_pre_ping=True)