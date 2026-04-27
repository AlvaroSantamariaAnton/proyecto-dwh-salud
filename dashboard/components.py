"""
Widgets reutilizables: KPI cards, headers, etc.
Versión robusta con concatenación de strings (evita problemas con f-strings multilínea).
"""
import streamlit as st
from dashboard.config import COLORS


def kpi_card(label: str, value: str, delta: str = None, color: str = None,
             icon: str = None):
    """KPI card sobria con barra superior de color."""
    color = color or COLORS["primary"]

    delta_html = ""
    if delta:
        delta_html = (
            '<div style="color:' + COLORS["text_dim"] + ';font-size:0.78rem;'
            'margin-top:6px;padding-top:8px;border-top:1px solid #2D3748;">'
            + str(delta) +
            '</div>'
        )

    html = (
        '<div style="background:' + COLORS["card_bg"] + ';'
        'border:1px solid #2D3748;border-radius:4px;'
        'padding:16px 20px 14px 20px;margin-bottom:10px;'
        'position:relative;overflow:hidden;">'

        '<div style="position:absolute;top:0;left:0;right:0;height:2px;'
        'background:linear-gradient(90deg,' + color + ' 0%,' + color + '40 100%);">'
        '</div>'

        '<div style="color:' + COLORS["text_dim"] + ';font-size:0.7rem;'
        'font-weight:600;text-transform:uppercase;letter-spacing:1px;">'
        + str(label) +
        '</div>'

        '<div style="color:' + COLORS["text"] + ';font-size:1.65rem;'
        'font-weight:700;margin-top:6px;line-height:1.15;letter-spacing:-0.3px;">'
        + str(value) +
        '</div>'

        + delta_html +

        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def section_header(title: str, subtitle: str = None, color: str = None):
    """Header sobrio para secciones, con barra vertical de color."""
    color = color or COLORS["primary"]

    sub_html = ""
    if subtitle:
        sub_html = (
            '<div style="color:' + COLORS["text_dim"] + ';font-size:0.88rem;'
            'margin-top:4px;letter-spacing:0.1px;">'
            + str(subtitle) +
            '</div>'
        )

    html = (
        '<div style="margin:32px 0 18px 0;display:flex;align-items:flex-start;gap:14px;">'

        '<div style="width:3px;min-height:38px;background:' + color + ';border-radius:2px;">'
        '</div>'

        '<div>'
        '<div style="font-size:1.25rem;font-weight:700;color:' + COLORS["text"] + ';'
        'letter-spacing:-0.2px;line-height:1.2;">'
        + str(title) +
        '</div>'
        + sub_html +
        '</div>'

        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = None, color: str = None):
    """Header grande de página con etiqueta superior en color."""
    color = color or COLORS["primary"]

    sub_html = ""
    if subtitle:
        sub_html = (
            '<div style="color:' + COLORS["text_dim"] + ';font-size:0.95rem;'
            'margin-top:6px;max-width:680px;line-height:1.5;">'
            + str(subtitle) +
            '</div>'
        )

    html = (
        '<div style="padding:18px 0 26px 0;border-bottom:1px solid #2D3748;'
        'margin-bottom:28px;">'

        '<div style="color:' + color + ';font-size:0.72rem;font-weight:700;'
        'text-transform:uppercase;letter-spacing:2.5px;">'
        'Saleshealth Analytics'
        '</div>'

        '<div style="font-size:1.85rem;font-weight:800;color:' + COLORS["text"] + ';'
        'margin-top:8px;letter-spacing:-0.5px;line-height:1.1;">'
        + str(title) +
        '</div>'

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