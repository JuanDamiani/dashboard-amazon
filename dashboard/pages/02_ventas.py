"""
Pagina de Analisis de Ventas — RF3
"""

from datetime import timedelta

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from utils.db import query
from utils.filters import render_filters
from utils.style import kpi_card, export_icon, chart_header, PALETTE, FONT, PLOTLY_COLORS

# ── FILTROS: globales + locales (subcategoria, marca) — RF3 ──
filters      = render_filters(extra_filters=["subcategoria", "marca"])
where_ventas = filters["where"]
params       = filters["params"]


# ── KPIs RF3 ─────────────────────────────────────────────
kpis_v = query(f"""
    SELECT
        ROUND(SUM(final_price)::numeric, 0)    AS total_revenue,
        COUNT(*)                                AS total_orders,
        ROUND(AVG(final_price)::numeric, 0)    AS avg_ticket,
        ROUND(AVG(discount)::numeric, 1)        AS avg_discount
    FROM analytics.fact_orders {where_ventas}
""", params)

def previous_period_params(filters, current_params):
    fecha_inicio = filters["fecha_inicio"]
    fecha_fin = filters["fecha_fin"]
    period_days = max((fecha_fin - fecha_inicio).days, 0)
    prev_fin = fecha_inicio - timedelta(days=1)
    prev_inicio = prev_fin - timedelta(days=period_days)
    prev_params = dict(current_params)
    prev_params["fecha_inicio"] = prev_inicio
    prev_params["fecha_fin"] = prev_fin
    return prev_params


prev_params = previous_period_params(filters, params)
prev_kpis_v = query(f"""
    SELECT
        ROUND(SUM(final_price)::numeric, 0)    AS total_revenue,
        COUNT(*)                                AS total_orders,
        ROUND(AVG(final_price)::numeric, 0)    AS avg_ticket,
        ROUND(AVG(discount)::numeric, 1)        AS avg_discount
    FROM analytics.fact_orders {where_ventas}
""", prev_params)


def pct_delta(current_df, previous_df, col):
    try:
        current = current_df[col].iloc[0]
        previous = previous_df[col].iloc[0]
        if pd.isna(current) or pd.isna(previous) or float(previous) == 0:
            return None
        return ((float(current) - float(previous)) / abs(float(previous))) * 100
    except Exception:
        return None

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
c1.markdown(kpi_card("Ingresos Totales",  fmt_rev(kpis_v["total_revenue"].iloc[0]), pct_delta(kpis_v, prev_kpis_v, "total_revenue"), ICON_REV, "Suma de ingresos del período seleccionado en INR."), unsafe_allow_html=True)
c2.markdown(kpi_card("Unidades Vendidas", fmt_num(kpis_v["total_orders"].iloc[0]),  pct_delta(kpis_v, prev_kpis_v, "total_orders"),  ICON_BOX, "Total de órdenes procesadas. Cada fila = 1 orden = 1 unidad vendida."), unsafe_allow_html=True)
c3.markdown(kpi_card("Precio Promedio",   fmt_rev(kpis_v["avg_ticket"].iloc[0]),    pct_delta(kpis_v, prev_kpis_v, "avg_ticket"),    ICON_TAG, "Precio final promedio por orden en INR."), unsafe_allow_html=True)
c4.markdown(kpi_card("Descuento Prom.",   f'{kpis_v["avg_discount"].iloc[0]}%',     pct_delta(kpis_v, prev_kpis_v, "avg_discount"), ICON_PCT, "Porcentaje de descuento promedio aplicado en el período."), unsafe_allow_html=True)

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
""", params)
df_evol["mes"] = pd.to_datetime(df_evol["mes"]).dt.strftime("%b %Y")

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Bar(
    x=df_evol["mes"], y=df_evol["ingresos"],
    name="Ingresos", marker_color=PALETTE["primary_light"], opacity=0.85,
    hovertemplate="Ingresos: ₹%{y:,.0f}<extra></extra>",
), secondary_y=False)
fig.add_trace(go.Scatter(
    x=df_evol["mes"], y=df_evol["unidades_vendidas"],
    name="Unidades vendidas", mode="lines+markers",
    line=dict(color=PALETTE["accent"], width=2.5), marker=dict(size=6),
    hovertemplate="Unidades: %{y:,.0f}<extra></extra>",
), secondary_y=True)
fig.update_layout(
    plot_bgcolor="white", paper_bgcolor="white",
    font=dict(family=FONT, color=PALETTE["text"]),
    legend=dict(orientation="h", y=1.1, x=0),
    margin=dict(t=50, b=40, l=10, r=10), height=340,
    hovermode="x unified",
    hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
)
fig.update_yaxes(title_text="Ingresos (INR)", secondary_y=False, gridcolor="#EEF2F7")
fig.update_yaxes(title_text="Unidades vendidas", secondary_y=True, showgrid=False)
fig.update_xaxes(gridcolor="#EEF2F7")
with st.container(key="chartcard_v_evol"):
    chart_header("Evolución Mensual de Ventas", df_evol, "evolucion_ventas.csv", "exp_v_evol", ratio=(24, 1), info="Ingresos (suma de los precios finales) y unidades vendidas (cantidad de órdenes) por mes. Sirve para ver la tendencia del negocio en el tiempo y detectar estacionalidad o crecimiento.")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

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
    """, params)
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
                       labels={"ingresos": "Ingresos (INR)", "category": ""})
        fig_c.update_traces(textposition="outside")
        fig_c.update_layout(
            plot_bgcolor="white", paper_bgcolor="white", height=320,
            font=dict(family=FONT, color=PALETTE["text"]),
            margin=dict(t=15, b=20, l=10, r=10),
        )
        fig_c.update_yaxes(gridcolor="#EEF2F7")
        with st.container(key="chartcard_v_cat"):
            chart_header("Ingresos por Categoría", df_cat, "ingresos_categoria_ventas.csv", "exp_v_cat", ratio=(18, 1), info="Suma de los ingresos (precio final) agrupada por categoría. Muestra qué categorías concentran la mayor facturación.")
            st.plotly_chart(fig_c, use_container_width=True, config={"displayModeBar": False})
    with col2:
        fig_d = px.bar(df_cat, x="category", y="descuento_prom",
                       color_discrete_sequence=[PALETTE["accent"]],
                       text="descuento_prom",
                       labels={"descuento_prom": "Descuento (%)", "category": ""})
        fig_d.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
        fig_d.update_layout(
            plot_bgcolor="white", paper_bgcolor="white", height=320,
            font=dict(family=FONT, color=PALETTE["text"]),
            margin=dict(t=15, b=20, l=10, r=10),
        )
        fig_d.update_yaxes(gridcolor="#EEF2F7")
        with st.container(key="chartcard_v_desc"):
            chart_header("Descuento Promedio por Categoría (%)", df_cat, "descuento_categoria.csv", "exp_v_desc", ratio=(18, 1), info="Promedio del porcentaje de descuento aplicado, por categoría. Indica en qué categorías se resigna más margen para vender.")
            st.plotly_chart(fig_d, use_container_width=True, config={"displayModeBar": False})

    # Precio original vs precio final
    st.markdown("<br>", unsafe_allow_html=True)
    df_precios = query(f"""
        SELECT category,
               ROUND(AVG(price)::numeric, 0) AS precio_original,
               ROUND(AVG(final_price)::numeric, 0) AS precio_final,
               ROUND(AVG(discount)::numeric, 0) AS descuento_prom
        FROM analytics.fact_orders {where_ventas}
        GROUP BY category ORDER BY precio_original DESC
    """, params)
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
        barmode="group",
        plot_bgcolor="white", paper_bgcolor="white", height=340,
        font=dict(family=FONT, color=PALETTE["text"]),
        margin=dict(t=50, b=40, l=10, r=10),
        legend=dict(orientation="h", y=1.08),
        hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
    )
    fig_precios.update_yaxes(gridcolor="#EEF2F7", title="Precio promedio (INR)")
    fig_precios.update_xaxes(title="Categoría")
    with st.container(key="chartcard_v_prec"):
        chart_header("Precio Original vs Precio Final por Categoría", df_precios, "precio_original_vs_final.csv", "exp_v_prec", ratio=(24, 1), info="Promedio del precio de lista (original) frente al precio efectivamente pagado (final), por categoría. La brecha entre ambos es el descuento promedio aplicado.")
        st.plotly_chart(fig_precios, use_container_width=True, config={"displayModeBar": False})

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
    """, params)

    def fmt_m(v):
        if v >= 1_000_000_000: return f"₹{v/1_000_000_000:.1f}B"
        if v >= 1_000_000:     return f"₹{v/1_000_000:.0f}M"
        return f"₹{v:,.0f}"

    df_sub_display = df_sub.copy().rename(columns={
        "subcategory":       "Subcategoría",
        "category":          "Categoría",
        "unidades_vendidas": "Unidades",
        "ingresos":          "Ingresos",
        "precio_promedio":   "Precio Prom.",
        "descuento_prom":    "Descuento",
        "rating_prom":       "Rating",
        "tasa_dev":          "Dev %",
    })

    def color_dev(v):
        try:
            if v > 15: return "color:#C0392B;font-weight:600"
            if v < 5:  return "color:#1A7F4B;font-weight:600"
        except: pass
        return ""

    styled = (
        df_sub_display.style
        .format({
            "Unidades":     lambda v: f"{v:,.0f}",
            "Ingresos":     fmt_m,
            "Precio Prom.": lambda v: f"₹{v:,.0f}",
            "Descuento":    lambda v: f"{v:.0f}%",
            "Rating":       lambda v: f"{v:.2f}",
            "Dev %":        lambda v: f"{v:.1f}%",
        })
        .applymap(color_dev, subset=["Dev %"])
        .set_table_styles([
            {"selector": "th", "props": [
                ("background", "#F0F4F8"), ("color", "#5A6A7A"),
                ("font-size", "0.75rem"), ("padding", "8px 12px"),
                ("font-weight", "700"), ("text-transform", "uppercase"),
                ("letter-spacing", "0.04em"),
            ]},
            {"selector": "td", "props": [
                ("font-size", "0.82rem"), ("padding", "7px 12px"),
                ("border-bottom", "1px solid #F0F4F8"),
            ]},
            {"selector": "tr:hover td", "props": [("background", "#F8FAFC")]},
        ])
        .hide(axis="index")
    )

    with st.container(key="chartcard_v_sub"):
        chart_header("Detalle por Subcategoría (Top 20)", df_sub, "detalle_subcategorias.csv", "exp_v_sub", ratio=(24, 1), info="Métricas por subcategoría: unidades, ingresos, precio promedio, descuento, rating y porcentaje de devolución. Top 20 ordenado por ingresos.")
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
    """, params)
    df_brand["label"] = df_brand["ingresos"].apply(lambda v:
        f"₹{v/1_000_000_000:.1f}B" if v >= 1_000_000_000 else
        f"₹{v/1_000_000:.0f}M" if v >= 1_000_000 else f"₹{v:,.0f}"
    )
    # Rango para que se vean las diferencias
    min_ing = df_brand["ingresos"].min() * 0.95
    max_ing = df_brand["ingresos"].max() * 1.08

    fig_brand = px.bar(df_brand, x="ingresos", y="brand", orientation="h",
                       color_discrete_sequence=[PALETTE["primary_light"]],
                       text="label",
                       labels={"ingresos": "Ingresos (INR)", "brand": ""},
                       custom_data=["precio_promedio", "descuento_prom", "rating_prom", "unidades_vendidas"])
    fig_brand.update_traces(
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Ingresos: %{text}<br>Precio prom: ₹%{customdata[0]:,.0f}<br>Descuento: %{customdata[1]:.0f}%<br>Rating: %{customdata[2]:.2f}<br>Unidades: %{customdata[3]:,}<extra></extra>",
    )
    fig_brand.update_layout(
        plot_bgcolor="white", paper_bgcolor="white", height=520,
        font=dict(family=FONT, color=PALETTE["text"]),
        margin=dict(t=15, b=20, l=10, r=90),
        hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
    )
    fig_brand.update_xaxes(gridcolor="#EEF2F7", range=[min_ing, max_ing])
    with st.container(key="chartcard_v_brand"):
        chart_header("Top 20 Marcas por Ingresos", df_brand, "top_marcas.csv", "exp_v_brand", ratio=(24, 1), info="Ingresos totales (suma de precios finales) por marca, top 20. Identifica las marcas que más facturan en el período seleccionado.")
        st.plotly_chart(fig_brand, use_container_width=True, config={"displayModeBar": False})

st.markdown("<br>", unsafe_allow_html=True)

# ── Distribucion de ventas por dispositivo y categoria — RF3 ──
df_dev = query(f"""
    SELECT device, category,
           COUNT(*) AS unidades,
           ROUND(SUM(final_price)::numeric, 0) AS ingresos
    FROM analytics.fact_orders {where_ventas}
    GROUP BY device, category
    ORDER BY category
""", params)

fig_dev = px.bar(
    df_dev, x="category", y="ingresos", color="device",
    barmode="stack",
    color_discrete_sequence=PLOTLY_COLORS,
    labels={"ingresos": "Ingresos (INR)", "category": "", "device": "Dispositivo"},
    custom_data=["device", "unidades"],
)
fig_dev.update_traces(
    hovertemplate="<b>%{x}</b><br>Dispositivo: %{customdata[0]}<br>Ingresos: ₹%{y:,.0f}<br>Unidades: %{customdata[1]:,}<extra></extra>",
)
fig_dev.update_layout(
    plot_bgcolor="white", paper_bgcolor="white", height=380,
    font=dict(family=FONT, color=PALETTE["text"]),
    margin=dict(t=50, b=40, l=10, r=10),
    legend=dict(orientation="h", y=1.1, x=0, title=""),
    hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
)
fig_dev.update_yaxes(gridcolor="#EEF2F7")
fig_dev.update_xaxes(gridcolor="#EEF2F7")
with st.container(key="chartcard_v_dev"):
    chart_header("Ventas por Dispositivo y Categoría", df_dev, "ventas_dispositivo_categoria.csv", "exp_v_dev", ratio=(24, 1), info="Distribución de los ingresos por categoría, desglosados según el dispositivo desde el que se realizó la compra (móvil, desktop, etc.). Muestra qué canal predomina en cada categoría.")
    st.plotly_chart(fig_dev, use_container_width=True, config={"displayModeBar": False})

st.markdown("<br>", unsafe_allow_html=True)

# ── Correlacion descuento → ordenes en el tiempo ─────────
df_corr = query(f"""
    SELECT DATE_TRUNC('month', purchase_date)::date AS mes,
           COUNT(*) AS ordenes,
           ROUND(AVG(discount)::numeric, 1) AS descuento_prom
    FROM analytics.fact_orders {where_ventas}
    AND DATE_TRUNC('month', purchase_date) < DATE_TRUNC('month', CURRENT_DATE)
    GROUP BY 1 ORDER BY mes
""", params)
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
with st.container(key="chartcard_v_corr"):
    chart_header("Correlación: Descuento Promedio → Volumen de Órdenes", df_corr, "correlacion_descuento_ordenes.csv", "exp_v_corr", ratio=(24, 1), info="Compara el descuento promedio mensual con la cantidad de órdenes. Ayuda a ver si subir los descuentos impulsa el volumen de ventas en los meses siguientes.")
    st.plotly_chart(fig_corr, use_container_width=True, config={"displayModeBar": False})
st.markdown(
    '<div style="font-size:0.72rem;color:#9BAAB8;margin-top:-12px;">'
    'Cuando el descuento promedio sube (línea naranja), el volumen de órdenes suele aumentar en los meses siguientes.'
    '</div>',
    unsafe_allow_html=True,
)