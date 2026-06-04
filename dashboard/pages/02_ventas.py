"""
Pagina de Analisis de Ventas — RF3
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from utils.db import query
from utils.filters import render_filters, PERIODO_OPCIONES
from utils.style import get_css, kpi_card, PALETTE, PLOTLY_COLORS, FONT

st.set_page_config(
    page_title="Ventas | Amazon Analytics",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(get_css(), unsafe_allow_html=True)

# ── Ocultar sidebar ──────────────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
.block-container { padding-top: 0 !important; max-width: 100% !important; }
</style>
""", unsafe_allow_html=True)

# ── HEADER: Logo + Tabs ──────────────────────────────────
header_col, tabs_col = st.columns([1, 5])

with header_col:
    st.markdown("""
    <div style="padding: 12px 0 0 8px;">
        <img src="https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg"
             style="width: 90px;" />
    </div>
    """, unsafe_allow_html=True)

with tabs_col:
    tab_names = ["Overview", "Ventas", "Logística", "Clientes", "Vendedores", "Glosario"]
    pages = {
        "Overview":   "app.py",
        "Ventas":     "pages/02_ventas.py",
        "Logística":  "pages/03_logistica.py",
        "Clientes":   "pages/04_clientes.py",
        "Vendedores": "pages/05_vendedores.py",
        "Glosario":   "pages/06_glosario.py",
    }
    for name, page in pages.items():
        is_active = name == "Ventas"
        color = PALETTE["accent"] if is_active else PALETTE["text_light"]
        border = f"border-bottom: 3px solid {PALETTE['accent']};" if is_active else "border-bottom: 3px solid transparent;"
        st.markdown(f"""
        <a href="/{page.replace('pages/', '').replace('.py', '').replace('app', '')}"
           style="padding: 10px 20px; font-size: 0.88rem; font-weight: {'700' if is_active else '500'};
                  color: {color}; text-decoration: none; display: inline-block;
                  {border} margin-bottom: -2px;">
           {name}
        </a>
        """, unsafe_allow_html=True)

st.markdown('<hr style="margin: 0 0 8px 0; border-color: #E4E9F0;">', unsafe_allow_html=True)

# ── FILTROS GLOBALES (con session_state — RF2) ───────────
filters = render_filters(extra_filters=["subcategoria", "marca"])
where        = filters["where"]
where_ventas = where

st.markdown('<hr style="margin: 4px 0 12px 0; border-color: #E4E9F0;">', unsafe_allow_html=True)

# ── KPIs RF3 ─────────────────────────────────────────────
kpis_v = query(f"""
    SELECT
        ROUND(SUM(final_price)::numeric, 0)    AS total_revenue,
        COUNT(*)                                AS total_orders,
        ROUND(AVG(final_price)::numeric, 0)    AS avg_ticket,
        ROUND(AVG(discount)::numeric, 1)        AS avg_discount
    FROM analytics.fact_orders {where_ventas}
""")

var_v = query("""
    SELECT total_revenue_pct_change, total_orders_pct_change, avg_ticket_pct_change
    FROM analytics.mart_period_variation
    ORDER BY period_month DESC LIMIT 1
""")

def get_delta(df, col):
    try:
        v = df[col].iloc[0]
        return float(v) if v is not None else None
    except: return None

def fmt_rev(v):
    if v >= 1_000_000_000: return f"₹{v/1_000_000_000:.1f}B"
    if v >= 1_000_000:     return f"₹{v/1_000_000:.1f}M"
    return f"₹{v:,.0f}"

def fmt_num(v):
    if v >= 1_000_000: return f"{v/1_000_000:.1f}M"
    if v >= 1_000:     return f"{v/1_000:.1f}k"
    return f"{v:,.0f}"

ICON_REV = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5" stroke-linecap="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>'
ICON_BOX = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5" stroke-linecap="round"><path d="M20 7H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>'
ICON_TAG = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5" stroke-linecap="round"><path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v2z"/></svg>'
ICON_PCT = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5" stroke-linecap="round"><line x1="19" y1="5" x2="5" y2="19"/><circle cx="6.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/></svg>'

c1, c2, c3, c4 = st.columns(4)
c1.markdown(kpi_card("Ingresos Totales",  fmt_rev(kpis_v["total_revenue"].iloc[0]), get_delta(var_v, "total_revenue_pct_change"), ICON_REV, "Suma de ingresos del período seleccionado en INR."), unsafe_allow_html=True)
c2.markdown(kpi_card("Unidades Vendidas", fmt_num(kpis_v["total_orders"].iloc[0]),  get_delta(var_v, "total_orders_pct_change"),  ICON_BOX, "Total de órdenes procesadas. Cada fila = 1 orden = 1 unidad vendida."), unsafe_allow_html=True)
c3.markdown(kpi_card("Precio Promedio",   fmt_rev(kpis_v["avg_ticket"].iloc[0]),    get_delta(var_v, "avg_ticket_pct_change"),    ICON_TAG, "Precio final promedio por orden en INR."), unsafe_allow_html=True)
c4.markdown(kpi_card("Descuento Prom.",   f'{kpis_v["avg_discount"].iloc[0]}%',     None,                                         ICON_PCT, "Porcentaje de descuento promedio aplicado en el período."), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Evolucion mensual ────────────────────────────────────
df_evol = query(f"""
    SELECT DATE_TRUNC('month', purchase_date)::date AS mes,
           COUNT(*) AS unidades_vendidas,
           ROUND(SUM(final_price)::numeric, 0) AS ingresos,
           ROUND(AVG(final_price)::numeric, 0) AS precio_promedio,
           ROUND(AVG(discount)::numeric, 1) AS descuento_promedio
    FROM analytics.fact_orders {where_ventas}
    GROUP BY 1 ORDER BY mes
""")
df_evol["mes"] = pd.to_datetime(df_evol["mes"]).dt.strftime("%b %Y")

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Bar(
    x=df_evol["mes"], y=df_evol["ingresos"],
    name="Ingresos", marker_color=PALETTE["primary_light"], opacity=0.85,
), secondary_y=False)
fig.add_trace(go.Scatter(
    x=df_evol["mes"], y=df_evol["unidades_vendidas"],
    name="Unidades vendidas", mode="lines+markers",
    line=dict(color=PALETTE["accent"], width=2.5), marker=dict(size=6),
), secondary_y=True)
fig.update_layout(
    title=dict(text="Evolución Mensual de Ventas", font=dict(color="#6B7A8D", size=13)),
    plot_bgcolor="white", paper_bgcolor="white",
    font=dict(family=FONT, color=PALETTE["text"]),
    legend=dict(orientation="h", y=1.1, x=0),
    margin=dict(t=50, b=40, l=10, r=10), height=340,
    hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
)
fig.update_yaxes(title_text="Ingresos (INR)", secondary_y=False, gridcolor="#EEF2F7")
fig.update_yaxes(title_text="Unidades vendidas", secondary_y=True, showgrid=False)
fig.update_xaxes(gridcolor="#EEF2F7")
st.plotly_chart(fig, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Por categoria, subcategoria y marca ─────────────────
tab1, tab2, tab3 = st.tabs(["Por Categoría", "Por Subcategoría", "Por Marca"])

with tab1:
    df_cat = query(f"""
        SELECT category,
               COUNT(*) AS unidades_vendidas,
               ROUND(SUM(final_price)::numeric, 0) AS ingresos,
               ROUND(AVG(final_price)::numeric, 0) AS precio_promedio,
               ROUND(AVG(discount)::numeric, 1) AS descuento_prom,
               ROUND(AVG(rating)::numeric, 2) AS rating_prom,
               ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 1) AS tasa_dev
        FROM analytics.fact_orders {where_ventas}
        GROUP BY category ORDER BY ingresos DESC
    """)
    col1, col2 = st.columns(2)
    with col1:
        fig_c = px.bar(df_cat, x="category", y="ingresos",
                       color_discrete_sequence=[PALETTE["primary_light"]],
                       text="ingresos",
                       title="Ingresos por Categoría",
                       labels={"ingresos": "Ingresos (INR)", "category": ""})
        fig_c.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
        fig_c.update_layout(
            plot_bgcolor="white", paper_bgcolor="white", height=300,
            font=dict(family=FONT, color=PALETTE["text"]),
            title=dict(font=dict(color="#6B7A8D", size=13)),
            margin=dict(t=40, b=20, l=10, r=10),
        )
        fig_c.update_yaxes(gridcolor="#EEF2F7")
        st.plotly_chart(fig_c, use_container_width=True)
    with col2:
        fig_d = px.bar(df_cat, x="category", y="descuento_prom",
                       color_discrete_sequence=[PALETTE["accent"]],
                       text="descuento_prom",
                       title="Descuento Promedio por Categoría (%)",
                       labels={"descuento_prom": "Descuento (%)", "category": ""})
        fig_d.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_d.update_layout(
            plot_bgcolor="white", paper_bgcolor="white", height=300,
            font=dict(family=FONT, color=PALETTE["text"]),
            title=dict(font=dict(color="#6B7A8D", size=13)),
            margin=dict(t=40, b=20, l=10, r=10),
        )
        fig_d.update_yaxes(gridcolor="#EEF2F7")
        st.plotly_chart(fig_d, use_container_width=True)
    st.dataframe(df_cat.style.format({
        "ingresos": "₹{:,.0f}", "precio_promedio": "₹{:,.0f}",
        "descuento_prom": "{:.1f}%", "tasa_dev": "{:.1f}%",
    }), use_container_width=True)

with tab2:
    df_sub = query(f"""
        SELECT subcategory, category,
               COUNT(*) AS unidades_vendidas,
               ROUND(SUM(final_price)::numeric, 0) AS ingresos,
               ROUND(AVG(final_price)::numeric, 0) AS precio_promedio,
               ROUND(AVG(discount)::numeric, 1) AS descuento_prom
        FROM analytics.fact_orders {where_ventas}
        GROUP BY subcategory, category ORDER BY ingresos DESC LIMIT 20
    """)
    fig_sub = px.bar(df_sub, x="ingresos", y="subcategory", orientation="h",
                     color="category", color_discrete_sequence=PLOTLY_COLORS,
                     title="Top 20 Subcategorías por Ingresos",
                     labels={"ingresos": "Ingresos (INR)", "subcategory": ""})
    fig_sub.update_layout(
        plot_bgcolor="white", paper_bgcolor="white", height=420,
        font=dict(family=FONT, color=PALETTE["text"]),
        title=dict(font=dict(color="#6B7A8D", size=13)),
        margin=dict(t=40, b=20, l=10, r=10),
        legend=dict(orientation="h", y=1.05),
    )
    fig_sub.update_xaxes(gridcolor="#EEF2F7")
    st.plotly_chart(fig_sub, use_container_width=True)

with tab3:
    df_brand = query(f"""
        SELECT brand,
               COUNT(*) AS unidades_vendidas,
               ROUND(SUM(final_price)::numeric, 0) AS ingresos,
               ROUND(AVG(final_price)::numeric, 0) AS precio_promedio,
               ROUND(AVG(discount)::numeric, 1) AS descuento_prom,
               ROUND(AVG(rating)::numeric, 2) AS rating_prom
        FROM analytics.fact_orders {where_ventas}
        GROUP BY brand ORDER BY ingresos DESC LIMIT 20
    """)
    fig_brand = px.bar(df_brand, x="ingresos", y="brand", orientation="h",
                       color_discrete_sequence=[PALETTE["primary"]],
                       text="ingresos",
                       title="Top 20 Marcas por Ingresos",
                       labels={"ingresos": "Ingresos (INR)", "brand": ""})
    fig_brand.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
    fig_brand.update_layout(
        plot_bgcolor="white", paper_bgcolor="white", height=420,
        font=dict(family=FONT, color=PALETTE["text"]),
        title=dict(font=dict(color="#6B7A8D", size=13)),
        margin=dict(t=40, b=20, l=10, r=90),
    )
    fig_brand.update_xaxes(gridcolor="#EEF2F7")
    st.plotly_chart(fig_brand, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Descuento vs volumen + dispositivo x categoria ───────
col_desc, col_disp = st.columns(2)

with col_desc:
    df_desc = query("""
        SELECT discount_range, total_orders, total_revenue
        FROM analytics.mart_discount_vs_orders
        ORDER BY discount_range
    """)
    fig_desc = make_subplots(specs=[[{"secondary_y": True}]])
    fig_desc.add_trace(go.Bar(
        x=df_desc["discount_range"], y=df_desc["total_orders"],
        name="Órdenes", marker_color=PALETTE["primary_light"], opacity=0.85,
    ), secondary_y=False)
    fig_desc.add_trace(go.Scatter(
        x=df_desc["discount_range"], y=df_desc["total_revenue"],
        name="Ingresos", mode="lines+markers",
        line=dict(color=PALETTE["accent"], width=2),
    ), secondary_y=True)
    fig_desc.update_layout(
        title=dict(text="Descuento vs Volumen de Órdenes", font=dict(color="#6B7A8D", size=13)),
        plot_bgcolor="white", paper_bgcolor="white", height=320,
        font=dict(family=FONT, color=PALETTE["text"]),
        margin=dict(t=50, b=40, l=10, r=10),
        legend=dict(orientation="h", y=1.1),
        hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
    )
    fig_desc.update_xaxes(title_text="Rango de descuento", gridcolor="#EEF2F7")
    fig_desc.update_yaxes(title_text="Órdenes", secondary_y=False, gridcolor="#EEF2F7")
    fig_desc.update_yaxes(title_text="Ingresos (INR)", secondary_y=True, showgrid=False)
    st.plotly_chart(fig_desc, use_container_width=True)

with col_disp:
    df_disp = query(f"""
        SELECT device, category,
               COUNT(*) AS ordenes,
               ROUND(SUM(final_price)::numeric, 0) AS ingresos
        FROM analytics.fact_orders {where_ventas}
        GROUP BY device, category ORDER BY device, ingresos DESC
    """)
    fig_disp = px.bar(df_disp, x="device", y="ingresos", color="category",
                      color_discrete_sequence=PLOTLY_COLORS, barmode="stack",
                      title="Ingresos por Dispositivo y Categoría",
                      labels={"ingresos": "Ingresos (INR)", "device": "Dispositivo", "category": "Categoría"})
    fig_disp.update_layout(
        plot_bgcolor="white", paper_bgcolor="white", height=320,
        font=dict(family=FONT, color=PALETTE["text"]),
        title=dict(font=dict(color="#6B7A8D", size=13)),
        margin=dict(t=50, b=40, l=10, r=10),
        legend=dict(orientation="h", y=1.1),
        hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
    )
    fig_disp.update_yaxes(gridcolor="#EEF2F7")
    st.plotly_chart(fig_disp, use_container_width=True)