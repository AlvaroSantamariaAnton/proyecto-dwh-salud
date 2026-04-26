"""
Widgets reutilizables: KPI cards, headers, etc. (versión modo oscuro)
"""
import streamlit as st
from dashboard.config import COLORS


def kpi_card(label: str, value: str, delta: str = None, color: str = None,
             icon: str = "📊"):
    """KPI card con estilo dark marketing."""
    color = color or COLORS["primary"]
    delta_html = ""
    if delta:
        delta_html = f'<div style="color:{COLORS["text_dim"]};font-size:0.85rem;margin-top:4px;">{delta}</div>'
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {color}25 0%, {COLORS['card_bg']} 100%);
        border-left: 4px solid {color};
        border-radius: 10px;
        padding: 18px 22px;
        margin-bottom: 10px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    ">
        <div style="font-size:1.6rem;line-height:1;">{icon}</div>
        <div style="
            color: {COLORS['text_dim']};
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            margin-top: 10px;
        ">{label}</div>
        <div style="
            color: {COLORS['text']};
            font-size: 1.7rem;
            font-weight: 700;
            margin-top: 4px;
            line-height: 1.1;
        ">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def section_header(title: str, subtitle: str = None, color: str = None):
    """Header colorido para una sección de la página (modo oscuro)."""
    color = color or COLORS["primary"]
    sub_html = f'<div style="color:{COLORS["text_dim"]};font-size:0.95rem;margin-top:2px;">{subtitle}</div>' if subtitle else ""
    st.markdown(f"""
    <div style="
        border-left: 5px solid {color};
        padding: 4px 16px;
        margin: 26px 0 16px 0;
    ">
        <div style="
            font-size: 1.4rem;
            font-weight: 700;
            color: {COLORS['text']};
        ">{title}</div>
        {sub_html}
    </div>
    """, unsafe_allow_html=True)


def fmt_eur(value: float, decimals: int = 0) -> str:
    """Formatea un valor en EUR estilo español: 1.234.567,89 €"""
    if value is None:
        return "—"
    fmt = f"{{:,.{decimals}f}}"
    formatted = fmt.format(value).replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted} €"


def fmt_int(value: int) -> str:
    """Entero con separador de miles."""
    if value is None:
        return "—"
    return f"{int(value):,}".replace(",", ".")


def fmt_pct(value: float, decimals: int = 1) -> str:
    if value is None:
        return "—"
    return f"{value:.{decimals}f} %"