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
# PALETA CORPORATIVA LIGHT MODE — estilo Tableau/Power BI
# ============================================================================
COLORS = {
    "primary":    "#2563EB",   # Azul corporativo (acento principal)
    "secondary":  "#0891B2",   # Cyan/teal
    "accent":     "#7C3AED",   # Púrpura
    "purple":     "#7C3AED",
    "blue":       "#2563EB",
    "success":    "#059669",   # Verde
    "warning":    "#D97706",   # Ámbar
    "danger":     "#DC2626",   # Rojo
    "dark":       "#F8FAFC",   # Fondo página
    "card_bg":    "#FFFFFF",   # Fondo de cards
    "text":       "#1E293B",   # Texto principal
    "text_dim":   "#64748B",   # Texto secundario
    "border":     "#E2E8F0",   # Bordes
    "sidebar_bg": "#F1F5F9",   # Fondo sidebar
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

# Plantilla Plotly light (usaremos en TODOS los gráficos)
PLOTLY_TEMPLATE = "plotly_white"

# Layout base para gráficos Plotly (importar y aplicar a cada figura)
PLOTLY_LAYOUT = {
    "template":       PLOTLY_TEMPLATE,
    "paper_bgcolor":  "rgba(0,0,0,0)",
    "plot_bgcolor":   "rgba(0,0,0,0)",
    "font":           {"color": "#1E293B", "family": "sans-serif"},
    "title":          {"font": {"size": 16, "color": "#1E293B"}},
    "xaxis":          {"gridcolor": "#E2E8F0", "linecolor": "#CBD5E1",
                       "color": "#64748B"},
    "yaxis":          {"gridcolor": "#E2E8F0", "linecolor": "#CBD5E1",
                       "color": "#64748B"},
    "legend":         {"bgcolor": "rgba(255,255,255,0.95)",
                       "bordercolor": "#E2E8F0"},
    "hoverlabel":     {"bgcolor": "#FFFFFF",
                       "font": {"color": "#1E293B"},
                       "bordercolor": "#E2E8F0"},
    "margin":         {"t": 50, "b": 50, "l": 50, "r": 30},
}


def get_engine():
    """Crea engine SQLAlchemy. Usado por las funciones de data.py."""
    url = (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME_DWH}"
    )
    return create_engine(url, pool_pre_ping=True)