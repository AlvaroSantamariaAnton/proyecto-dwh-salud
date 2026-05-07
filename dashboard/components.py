"""
Widgets reutilizables. Versión light mode Tableau/Power BI.
"""
import streamlit as st
from dashboard.config import COLORS


def kpi_card(label: str, value: str, delta: str = None,
             color: str = None, icon: str = None):
    """KPI card light mode: fondo blanco, sombra, borde superior de color."""
    color = color or COLORS["primary"]

    delta_html = ""
    if delta:
        delta_html = (
            '<div style="color:' + COLORS["text_dim"] + ';font-size:0.78rem;'
            'margin-top:6px;padding-top:8px;border-top:1px solid '
            + COLORS["border"] + ';">'
            + str(delta) + '</div>'
        )

    html = (
        '<div style="background:#FFFFFF;'
        'border:1px solid ' + COLORS["border"] + ';'
        'border-radius:6px;'
        'padding:16px 20px 14px 20px;'
        'margin-bottom:10px;'
        'position:relative;overflow:hidden;'
        'box-shadow:0 1px 3px rgba(0,0,0,0.06);">'

        '<div style="position:absolute;top:0;left:0;right:0;height:3px;'
        'background:' + color + ';"></div>'

        '<div style="color:' + COLORS["text_dim"] + ';font-size:0.7rem;'
        'font-weight:600;text-transform:uppercase;letter-spacing:1px;'
        'margin-top:4px;">'
        + str(label) + '</div>'

        '<div style="color:' + COLORS["text"] + ';font-size:1.65rem;'
        'font-weight:700;margin-top:6px;line-height:1.15;'
        'letter-spacing:-0.3px;">'
        + str(value) + '</div>'

        + delta_html +

        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def section_header(title: str, subtitle: str = None, color: str = None):
    """Section header light mode: uppercase gris, sin barra de color."""
    sub_html = ""
    if subtitle:
        sub_html = (
            '<div style="color:' + COLORS["text_dim"] + ';'
            'font-size:0.875rem;margin-top:3px;font-weight:400;">'
            + str(subtitle) + '</div>'
        )

    html = (
        '<div style="margin:32px 0 16px 0;">'
        '<div style="color:' + COLORS["text"] + ';font-size:0.72rem;'
        'font-weight:700;text-transform:uppercase;'
        'letter-spacing:1.5px;">'
        + str(title) + '</div>'
        + sub_html +
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = None, color: str = None):
    """Page header light mode: tipografía limpia, sin gradientes."""
    sub_html = ""
    if subtitle:
        sub_html = (
            '<div style="color:' + COLORS["text_dim"] + ';'
            'font-size:0.95rem;margin-top:6px;max-width:680px;'
            'line-height:1.5;">'
            + str(subtitle) + '</div>'
        )

    html = (
        '<div style="padding:18px 0 22px 0;'
        'border-bottom:1px solid ' + COLORS["border"] + ';'
        'margin-bottom:28px;">'
        '<div style="font-size:1.75rem;font-weight:700;'
        'color:' + COLORS["text"] + ';letter-spacing:-0.3px;">'
        + str(title) + '</div>'
        + sub_html +
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def fmt_eur(value: float, decimals: int = 0) -> str:
    if value is None:
        return "—"
    fmt = f"{{:,.{decimals}f}}"
    formatted = fmt.format(value).replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{formatted} €"


def fmt_int(value: int) -> str:
    if value is None:
        return "—"
    return f"{int(value):,}".replace(",", ".")


def fmt_pct(value: float, decimals: int = 1) -> str:
    if value is None:
        return "—"
    return f"{value:.{decimals}f} %"