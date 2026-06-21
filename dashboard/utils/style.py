"""
Estilos globales — Amazon E-Commerce Analytics
Sin sidebar. Navegacion nativa arriba (st.navigation position="top").
"""

PALETTE = {
    "primary":       "#1C3F5E",
    "primary_dark":  "#152E45",
    "primary_light": "#2E6DA4",
    "secondary":     "#2E6DA4",
    "accent":        "#FF9900",
    "accent_light":  "#FEBD69",
    "light":         "#84BBE3",
    "lighter":       "#D6EAF8",
    "bg":            "#F5F7FA",
    "card_bg":       "#FFFFFF",
    "text":          "#1A2332",
    "text_light":    "#6B7A8D",
    "border":        "#E4E9F0",
    "success":       "#1A7F4B",
    "danger":        "#C0392B",
    "warning":       "#E67E22",
}

PLOTLY_COLORS = [
    "#2E6DA4", "#1C3F5E", "#84BBE3", "#FF9900",
    "#FEBD69", "#1A7F4B", "#C0392B", "#A9CCE3",
]

FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, Helvetica, sans-serif"


def get_css():
    p = PALETTE
    return f"""
<style>

/* ── Fuente global ── */
*, html, body, [class*="css"], .stApp, button, input, select, textarea {{
    font-family: {FONT} !important;
}}

/* Streamlit usa iconos Material como ligaduras de texto. Si se fuerza la
   fuente global sobre esos nodos, aparecen palabras como upload/arrow_down. */
[data-testid="stIconMaterial"],
.material-icons,
.material-icons-outlined,
.material-symbols-rounded,
.material-symbols-outlined {{
    font-family: "Material Symbols Rounded", "Material Icons" !important;
    font-weight: normal !important;
    font-style: normal !important;
    line-height: 1 !important;
    letter-spacing: normal !important;
    text-transform: none !important;
    display: inline-flex !important;
    white-space: nowrap !important;
    word-wrap: normal !important;
    direction: ltr !important;
    -webkit-font-feature-settings: "liga" !important;
    -webkit-font-smoothing: antialiased !important;
    font-feature-settings: "liga" !important;
}}

/* ── Fondo ── */
.stApp {{
    background-color: {p['bg']};
}}

/* ── Ocultar sidebar (incluye el duplicado de la nav en Streamlit 1.52) ── */
[data-testid="stSidebar"] {{
    display: none !important;
}}
[data-testid="collapsedControl"] {{
    display: none !important;
}}

/* ── Ocultar menu/footer, PERO NO el header (ahi va la nav nativa y el logo) ── */
#MainMenu, footer {{
    visibility: hidden;
}}

/* ── Ocultar solo decoracion / toolbar / status, sin tocar el header ── */
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stToolbar"] {{
    display: none !important;
}}

.block-container {{
    padding-top: 0.5rem !important;
    padding-bottom: 1rem !important;
    max-width: 100% !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}}

/* ── KPI cards ── */
.kpi-card {{
    background: {p['card_bg']};
    border-radius: 8px;
    padding: 16px 18px 12px 18px;
    border: 1px solid {p['border']};
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    height: 100%;
}}
.kpi-card:hover {{
    box-shadow: 0 3px 8px rgba(0,0,0,0.09);
}}
.kpi-label {{
    font-size: 0.70rem;
    font-weight: 600;
    color: {p['text_light']};
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 5px;
}}
.kpi-value {{
    font-size: 1.85rem;
    font-weight: 700;
    color: {p['primary']};
    line-height: 1.1;
    margin-bottom: 6px;
}}
.kpi-delta-positive {{
    font-size: 0.76rem;
    font-weight: 600;
    color: {p['success']};
}}
.kpi-delta-negative {{
    font-size: 0.76rem;
    font-weight: 600;
    color: {p['danger']};
}}
.kpi-delta-neutral {{
    font-size: 0.76rem;
    color: {p['text_light']};
}}

/* ── Section titles ── */
.section-title {{
    font-size: 0.75rem;
    font-weight: 700;
    color: {p['text_light']};
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin: 20px 0 12px 0;
    padding-bottom: 6px;
    border-bottom: 1px solid {p['border']};
}}

/* ── Radio horizontal estilo tabs (toggle Revenue/Cantidad, etc.) ── */
[data-testid="stRadio"] {{
    margin-top: 4px;
}}
[data-testid="stRadio"] > div {{
    display: flex !important;
    flex-direction: row !important;
    gap: 0 !important;
    background: transparent !important;
    border-bottom: 2px solid {p['border']} !important;
    padding-bottom: 0 !important;
    flex-wrap: nowrap !important;
}}
[data-testid="stRadio"] label {{
    padding: 10px 20px !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    color: {p['text_light']} !important;
    cursor: pointer !important;
    border-bottom: 3px solid transparent !important;
    margin-bottom: -2px !important;
    transition: all 0.15s ease !important;
    background: transparent !important;
    border-radius: 0 !important;
    white-space: nowrap !important;
}}
[data-testid="stRadio"] label:hover {{
    color: {p['primary']} !important;
    border-bottom-color: {p['light']} !important;
}}
[data-testid="stRadio"] label:has(input:checked) {{
    color: {p['accent']} !important;
    border-bottom: 3px solid {p['accent']} !important;
    font-weight: 700 !important;
}}
[data-testid="stRadio"] input {{
    display: none !important;
}}
[data-testid="stRadio"] > div > label > div:first-child {{
    display: none !important;
}}
[data-testid="stRadio"] label span:first-child {{
    display: none !important;
}}
[data-testid="stRadio"] {{
    accent-color: #FF9900 !important;
}}

/* ── Captions de filtros ── */
.stCaption p {{
    font-size: 0.68rem !important;
    font-weight: 600 !important;
    color: {p['text_light']} !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    margin-bottom: 2px !important;
}}

/* ── Plotly fonts ── */
/* Upload de CSV */
[data-testid="stFileUploader"] section {{
    min-height: 132px !important;
    padding: 18px !important;
}}
[data-testid="stFileUploader"] section button {{
    min-width: 112px !important;
    min-height: 40px !important;
    line-height: 1.2 !important;
    white-space: nowrap !important;
    writing-mode: horizontal-tb !important;
    transform: none !important;
}}
[data-testid="stFileUploader"] section button * {{
    writing-mode: horizontal-tb !important;
    transform: none !important;
    white-space: nowrap !important;
}}
[data-testid="stFileUploader"] section div,
[data-testid="stFileUploader"] section span,
[data-testid="stFileUploader"] section small {{
    line-height: 1.35 !important;
    white-space: normal !important;
    overflow-wrap: normal !important;
    word-break: normal !important;
}}

.js-plotly-plot .plotly text {{
    font-family: {FONT} !important;
}}

/* ── Subtabs (st.tabs) — color naranja ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {{
    border-bottom: 2px solid #E4E9F0 !important;
    gap: 0 !important;
}}
[data-testid="stTabs"] [data-baseweb="tab"] {{
    padding: 8px 20px !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    color: #6B7A8D !important;
    background: transparent !important;
    border-bottom: 3px solid transparent !important;
}}
[data-testid="stTabs"] [data-baseweb="tab"]:hover {{
    color: #1C3F5E !important;
}}
[data-testid="stTabs"] [aria-selected="true"] {{
    color: #FF9900 !important;
    border-bottom: 3px solid #FF9900 !important;
    font-weight: 700 !important;
    background: transparent !important;
}}
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {{
    background-color: #FF9900 !important;
    height: 3px !important;
}}
[data-testid="stTabs"] [data-baseweb="tab-border"] {{
    background-color: #E4E9F0 !important;
}}

</style>
"""


def kpi_card(label, value, delta=None, icon="", tooltip="", delta_label="vs periodo anterior"):
    if delta is not None:
        if delta > 0:
            delta_html = f'<div class="kpi-delta-positive">▲ {delta:+.1f}% {delta_label}</div>'
        elif delta < 0:
            delta_html = f'<div class="kpi-delta-negative">▼ {delta:.1f}% {delta_label}</div>'
        else:
            delta_html = '<div class="kpi-delta-neutral">— Sin variación</div>'
    else:
        delta_html = ""

    info_icon = (
        f'<span title="{tooltip}" style="cursor:help;margin-left:3px;display:inline-flex;vertical-align:middle;">'
        '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#9BAAB8" stroke-width="2">'
        '<circle cx="12" cy="12" r="10"/>'
        '<line x1="12" y1="16" x2="12" y2="12"/>'
        '<line x1="12" y1="8" x2="12.01" y2="8"/>'
        '</svg></span>'
    ) if tooltip else ""

    return (
        '<div class="kpi-card">'
        f'<div class="kpi-label">{icon} {label}{info_icon}</div>'
        f'<div class="kpi-value">{value}</div>'
        + delta_html
        + '</div>'
    )
