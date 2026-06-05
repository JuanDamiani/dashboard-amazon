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
    selected_tab = st.radio(
        "nav", tab_names,
        horizontal=True,
        label_visibility="collapsed",
        index=1,
        key="main_nav",
    )
    if selected_tab == "Overview":
        st.switch_page("pages/01_overview.py")
    elif selected_tab == "Logística":
        st.switch_page("pages/03_logistica.py")
    elif selected_tab == "Clientes":
        st.switch_page("pages/04_clientes.py")
    elif selected_tab == "Vendedores":
        st.switch_page("pages/05_vendedores.py")
    elif selected_tab == "Glosario":
        st.switch_page("pages/06_glosario.py")

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
        def fmt_ingresos(v):
            if v >= 1_000_000_000: return f"₹{v/1_000_000_000:.1f}B"
            if v >= 1_000_000:     return f"₹{v/1_000_000:.1f}M"
            return f"₹{v:,.0f}"
        df_cat["ingresos_label"] = df_cat["ingresos"].apply(fmt_ingresos)
        fig_c = px.bar(df_cat, x="category", y="ingresos",
                       color_discrete_sequence=[PALETTE["primary_light"]],
                       text="ingresos_label",
                       title="Ingresos por Categoría",
                       labels={"ingresos": "Ingresos (INR)", "category": ""})
        fig_c.update_traces(textposition="outside")
        fig_c.update_layout(
            plot_bgcolor="white", paper_bgcolor="white", height=320,
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
        fig_d.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
        fig_d.update_layout(
            plot_bgcolor="white", paper_bgcolor="white", height=320,
            font=dict(family=FONT, color=PALETTE["text"]),
            title=dict(font=dict(color="#6B7A8D", size=13)),
            margin=dict(t=40, b=20, l=10, r=10),
        )
        fig_d.update_yaxes(gridcolor="#EEF2F7")
        st.plotly_chart(fig_d, use_container_width=True)

    # Precio original vs precio final
    st.markdown("<br>", unsafe_allow_html=True)
    df_precios = query(f"""
        SELECT category,
               ROUND(AVG(price)::numeric, 0) AS precio_original,
               ROUND(AVG(final_price)::numeric, 0) AS precio_final,
               ROUND(AVG(discount)::numeric, 0) AS descuento_prom
        FROM analytics.fact_orders {where_ventas}
        GROUP BY category ORDER BY precio_original DESC
    """)
    fig_precios = go.Figure()
    fig_precios.add_trace(go.Bar(
        name="Precio original",
        x=df_precios["category"],
        y=df_precios["precio_original"],
        marker_color=PALETTE["primary"],
        text=df_precios["precio_original"].apply(lambda v: f"₹{v:,.0f}"),
        textposition="outside",
    ))
    fig_precios.add_trace(go.Bar(
        name="Precio final",
        x=df_precios["category"],
        y=df_precios["precio_final"],
        marker_color=PALETTE["accent"],
        text=df_precios["precio_final"].apply(lambda v: f"₹{v:,.0f}"),
        textposition="outside",
    ))
    fig_precios.update_layout(
        title=dict(text="Precio Original vs Precio Final por Categoría", font=dict(color="#6B7A8D", size=13)),
        barmode="group",
        plot_bgcolor="white", paper_bgcolor="white", height=340,
        font=dict(family=FONT, color=PALETTE["text"]),
        margin=dict(t=50, b=40, l=10, r=10),
        legend=dict(orientation="h", y=1.08),
        hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
    )
    fig_precios.update_yaxes(gridcolor="#EEF2F7", title="Precio promedio (INR)")
    fig_precios.update_xaxes(title="Categoría")
    st.plotly_chart(fig_precios, use_container_width=True)

with tab2:
    df_sub = query(f"""
        SELECT subcategory, category,
               COUNT(*) AS unidades_vendidas,
               ROUND(SUM(final_price)::numeric, 0) AS ingresos,
               ROUND(AVG(final_price)::numeric, 0) AS precio_promedio,
               ROUND(AVG(discount)::numeric, 0) AS descuento_prom,
               ROUND(AVG(rating)::numeric, 2) AS rating_prom,
               ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)*100, 1) AS tasa_dev
        FROM analytics.fact_orders {where_ventas}
        GROUP BY subcategory, category ORDER BY ingresos DESC LIMIT 20
    """)

    def fmt_m(v):
        if v >= 1_000_000_000: return f"₹{v/1_000_000_000:.1f}B"
        if v >= 1_000_000:     return f"₹{v/1_000_000:.0f}M"
        return f"₹{v:,.0f}"

    df_sub_display = df_sub.copy()
    df_sub_display["ingresos"]       = df_sub_display["ingresos"].apply(fmt_m)
    df_sub_display["precio_promedio"]= df_sub_display["precio_promedio"].apply(lambda v: f"₹{v:,.0f}")
    df_sub_display["descuento_prom"] = df_sub_display["descuento_prom"].apply(lambda v: f"{v:.0f}%")
    df_sub_display["tasa_dev"]       = df_sub_display["tasa_dev"].apply(lambda v: f"{v:.1f}%")
    df_sub_display["unidades_vendidas"] = df_sub_display["unidades_vendidas"].apply(lambda v: f"{v:,}")
    df_sub_display = df_sub_display.rename(columns={
        "subcategory":      "Subcategoría",
        "category":         "Categoría",
        "unidades_vendidas":"Unidades",
        "ingresos":         "Ingresos",
        "precio_promedio":  "Precio Prom.",
        "descuento_prom":   "Descuento",
        "rating_prom":      "Rating",
        "tasa_dev":         "Dev %",
    })

    def color_dev(val):
        try:
            v = float(val.replace("%",""))
            if v > 15: return "color:#C0392B;font-weight:600"
            if v < 5:  return "color:#1A7F4B;font-weight:600"
        except: pass
        return ""

    styled = df_sub_display.style        .applymap(color_dev, subset=["Dev %"])        .set_table_styles([
            {"selector":"th","props":[
                ("background","#F0F4F8"),("color","#5A6A7A"),
                ("font-size","0.75rem"),("padding","8px 12px"),
                ("font-weight","700"),("text-transform","uppercase"),
                ("letter-spacing","0.04em"),
            ]},
            {"selector":"td","props":[
                ("font-size","0.82rem"),("padding","7px 12px"),
                ("border-bottom","1px solid #F0F4F8"),
            ]},
            {"selector":"tr:hover td","props":[("background","#F8FAFC")]},
        ])        .hide(axis="index")

    st.dataframe(styled, use_container_width=True, height=480)

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
    df_brand["label"] = df_brand["ingresos"].apply(lambda v:
        f"₹{v/1_000_000_000:.1f}B" if v >= 1_000_000_000 else
        f"₹{v/1_000_000:.0f}M" if v >= 1_000_000 else f"₹{v:,.0f}"
    )
    # Calcular rango para que se vean diferencias
    min_ing = df_brand["ingresos"].min() * 0.95
    max_ing = df_brand["ingresos"].max() * 1.08

    fig_brand = px.bar(df_brand, x="ingresos", y="brand", orientation="h",
                       color_discrete_sequence=[PALETTE["primary_light"]],
                       text="label",
                       title="Top 20 Marcas por Ingresos",
                       labels={"ingresos": "Ingresos (INR)", "brand": ""},
                       custom_data=["precio_promedio","descuento_prom","rating_prom","unidades_vendidas"])
    fig_brand.update_traces(
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Ingresos: %{text}<br>Precio prom: ₹%{customdata[0]:,.0f}<br>Descuento: %{customdata[1]:.0f}%<br>Rating: %{customdata[2]:.2f}<br>Unidades: %{customdata[3]:,}<extra></extra>",
    )
    fig_brand.update_layout(
        plot_bgcolor="white", paper_bgcolor="white", height=520,
        font=dict(family=FONT, color=PALETTE["text"]),
        title=dict(font=dict(color="#6B7A8D", size=13)),
        margin=dict(t=40, b=20, l=10, r=90),
        hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
    )
    fig_brand.update_xaxes(gridcolor="#EEF2F7", range=[min_ing, max_ing])
    st.plotly_chart(fig_brand, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Correlacion descuento → ordenes en el tiempo ─────────

if True:
    df_corr = query(f"""
        SELECT DATE_TRUNC('month', purchase_date)::date AS mes,
               COUNT(*) AS ordenes,
               ROUND(AVG(discount)::numeric, 1) AS descuento_prom
        FROM analytics.fact_orders {where_ventas}
        AND DATE_TRUNC('month', purchase_date) < DATE_TRUNC('month', CURRENT_DATE)
        GROUP BY 1 ORDER BY mes
    """)
    df_corr["mes_label"] = pd.to_datetime(df_corr["mes"]).dt.strftime("%b %Y")

    def fmt_ord(v):
        return f"{v/1_000:.1f}k" if v >= 1_000 else str(int(v))

    fig_corr = go.Figure()
    fig_corr.add_trace(go.Scatter(
        x=df_corr["mes_label"], y=df_corr["ordenes"],
        name="Cantidad de órdenes",
        mode="lines+markers+text",
        text=df_corr["ordenes"].apply(fmt_ord),
        textposition="top center",
        textfont=dict(size=9, color=PALETTE["text_light"], family=FONT),
        line=dict(color=PALETTE["primary_light"], width=2.5, shape="spline"),
        marker=dict(size=7, color=PALETTE["primary_light"], line=dict(color="white", width=1.5)),
        fill="tozeroy", fillcolor="rgba(46,109,164,0.06)",
        yaxis="y1",
        customdata=df_corr[["descuento_prom"]].values,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Órdenes: <b>%{y:,.0f}</b><br>"
            "Descuento prom: %{customdata[0]:.1f}%"
            "<extra></extra>"
        ),
    ))
    fig_corr.add_trace(go.Scatter(
        x=df_corr["mes_label"], y=df_corr["descuento_prom"],
        name="Descuento promedio (%)",
        mode="lines+markers",
        line=dict(color=PALETTE["accent"], width=2, dash="dot", shape="spline"),
        marker=dict(size=7, color=PALETTE["accent"], line=dict(color="white", width=1.5)),
        yaxis="y2",
        hoverinfo="skip",
    ))
    fig_corr.update_layout(
        title=dict(text="Correlación: Descuento Promedio → Volumen de Órdenes", font=dict(color="#6B7A8D", size=13)),
        plot_bgcolor="white", paper_bgcolor="white", height=400,
        font=dict(family=FONT, color=PALETTE["text"]),
        margin=dict(t=50, b=50, l=10, r=60),
        legend=dict(orientation="h", y=1.08),
        hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12), align="left"),
        xaxis=dict(showgrid=False, tickangle=-30),
        yaxis=dict(title="Órdenes", gridcolor="#EEF2F7", side="left"),
        yaxis2=dict(title="Descuento %", overlaying="y", side="right", showgrid=False,
                   tickformat=".0f", ticksuffix="%"),
    )
    st.plotly_chart(fig_corr, use_container_width=True)
    st.markdown(
        '<div style="font-size:0.72rem;color:#9BAAB8;margin-top:-12px;">'
        'Cuando el descuento promedio sube (línea naranja), el volumen de órdenes suele aumentar en los meses siguientes.'
        '</div>',
        unsafe_allow_html=True,
    )