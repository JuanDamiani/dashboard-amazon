"""
Pagina de Analisis Logistico — RF4
Todos los indicadores responden a los filtros globales + estado_entrega (RF2/RF4).
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from utils.db import query
from utils.filters import render_filters
from utils.style import kpi_card, PALETTE, FONT

# ── Etiquetas de delivery_status (ajustar si tu dataset usa otras) ──
STATUS_ON_TIME = "On Time"
STATUS_DELAYED = "Delayed"

# ── FILTROS: globales + local (estado_entrega) — RF4 ─────
filters   = render_filters(extra_filters=["estado_entrega"])
where_log = filters["where"]

# ── KPIs (todos filtrados, una sola query) ───────────────
kpis_log = query(f"""
    SELECT
        ROUND(AVG(shipping_time_days)::numeric, 1) AS avg_ship,
        ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 1) AS ret_rate,
        ROUND(AVG(CASE WHEN delivery_status = '{STATUS_ON_TIME}' THEN 1.0 ELSE 0.0 END)::numeric * 100, 1) AS pct_on_time,
        ROUND(AVG(CASE WHEN delivery_status = '{STATUS_DELAYED}' THEN 1.0 ELSE 0.0 END)::numeric * 100, 1) AS pct_delayed
    FROM analytics.fact_orders {where_log}
""")
avg_ship    = kpis_log["avg_ship"].iloc[0]
ret_rate    = kpis_log["ret_rate"].iloc[0]
pct_on_time = kpis_log["pct_on_time"].iloc[0]
pct_delayed = kpis_log["pct_delayed"].iloc[0]

ICON_CHECK = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>'
ICON_TRUCK = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>'
ICON_WARN  = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>'
ICON_RET   = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>'

c1, c2, c3, c4 = st.columns(4)
c1.markdown(kpi_card("Entregas a Tiempo",  f"{pct_on_time}%",  None, ICON_CHECK, "% de pedidos entregados a tiempo en el período filtrado."), unsafe_allow_html=True)
c2.markdown(kpi_card("Tiempo Prom. Envío", f"{avg_ship} días", None, ICON_TRUCK, "Días promedio desde la compra hasta la entrega."), unsafe_allow_html=True)
c3.markdown(kpi_card("Pedidos Demorados",  f"{pct_delayed}%",  None, ICON_WARN,  "% de pedidos con demoras. >20% requiere atención."), unsafe_allow_html=True)
c4.markdown(kpi_card("Tasa Devolución",    f"{ret_rate}%",     None, ICON_RET,   "% de órdenes devueltas en el período."), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Estado de entregas + tiempo por ciudad ───────────────
col1, col2 = st.columns(2)

with col1:
    df_est = query(f"""
        SELECT delivery_status, COUNT(*) AS ordenes,
               ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct,
               ROUND(AVG(shipping_time_days)::numeric, 1) AS dias_prom,
               ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 1) AS tasa_dev
        FROM analytics.fact_orders {where_log}
        GROUP BY delivery_status ORDER BY ordenes DESC
    """)
    fig1 = px.bar(df_est, x="pct", y="delivery_status", orientation="h",
                  text="pct", color_discrete_sequence=[PALETTE["primary"]],
                  title="Distribución por Estado de Entrega (%)",
                  custom_data=["dias_prom","tasa_dev","ordenes"],
                  labels={"pct":"%","delivery_status":""})
    fig1.update_traces(
        texttemplate="%{text:.1f}%", textposition="outside",
        hovertemplate="<b>%{y}</b><br>%: %{x:.1f}%<br>Días prom: %{customdata[0]}<br>Dev: %{customdata[1]}%<br>Órdenes: %{customdata[2]:,}<extra></extra>",
    )
    fig1.update_layout(
        title=dict(font=dict(color="#6B7A8D", size=13)),
        plot_bgcolor="white", paper_bgcolor="white", height=300,
        font=dict(family=FONT, color=PALETTE["text"]),
        margin=dict(t=50,b=20,l=10,r=40),
        hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
    )
    fig1.update_xaxes(gridcolor="#EEF2F7")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    df_city = query(f"""
        SELECT location,
               ROUND(AVG(shipping_time_days)::numeric, 0) AS dias_prom,
               ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 1) AS tasa_dev,
               COUNT(*) AS ordenes
        FROM analytics.fact_orders {where_log}
        GROUP BY location ORDER BY dias_prom DESC
    """)
    fig2 = px.bar(df_city, x="dias_prom", y="location", orientation="h",
                  text="dias_prom", color_discrete_sequence=[PALETTE["primary_light"]],
                  title="Tiempo Promedio de Envío por Ciudad (días)",
                  custom_data=["tasa_dev","ordenes"],
                  labels={"dias_prom":"Días","location":""})
    fig2.update_traces(
        texttemplate="%{text:.0f} días", textposition="outside",
        hovertemplate="<b>%{y}</b><br>Días prom: %{x:.0f}<br>Dev: %{customdata[0]}%<br>Órdenes: %{customdata[1]:,}<extra></extra>",
    )
    fig2.update_layout(
        title=dict(font=dict(color="#6B7A8D", size=13)),
        plot_bgcolor="white", paper_bgcolor="white", height=300,
        font=dict(family=FONT, color=PALETTE["text"]),
        margin=dict(t=50,b=20,l=10,r=60),
        hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
    )
    fig2.update_xaxes(gridcolor="#EEF2F7")
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Devoluciones por categoria y ciudad ──────────────────
col3, col4 = st.columns(2)

with col3:
    df_ret_cat = query(f"""
        SELECT category,
               ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 1) AS tasa_dev,
               COUNT(*) AS ordenes
        FROM analytics.fact_orders {where_log}
        GROUP BY category ORDER BY tasa_dev DESC
    """)
    fig3 = px.bar(df_ret_cat, x="tasa_dev", y="category", orientation="h",
                  text="tasa_dev", color_discrete_sequence=[PALETTE["danger"]],
                  title="Tasa de Devolución por Categoría (%)",
                  custom_data=["ordenes"],
                  labels={"tasa_dev":"%","category":""})
    fig3.update_traces(
        texttemplate="%{text:.1f}%", textposition="outside",
        hovertemplate="<b>%{y}</b><br>Dev: %{x:.1f}%<br>Órdenes: %{customdata[0]:,}<extra></extra>",
    )
    fig3.update_layout(
        title=dict(font=dict(color="#6B7A8D", size=13)),
        plot_bgcolor="white", paper_bgcolor="white", height=300,
        font=dict(family=FONT, color=PALETTE["text"]),
        margin=dict(t=50,b=20,l=10,r=40),
        hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
    )
    fig3.update_xaxes(gridcolor="#EEF2F7")
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    df_ret_city = query(f"""
        SELECT location,
               ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 1) AS tasa_dev,
               COUNT(*) AS ordenes
        FROM analytics.fact_orders {where_log}
        GROUP BY location ORDER BY tasa_dev DESC
    """)
    fig4 = px.bar(df_ret_city, x="tasa_dev", y="location", orientation="h",
                  text="tasa_dev", color_discrete_sequence=[PALETTE["danger"]],
                  title="Tasa de Devolución por Ciudad (%)",
                  custom_data=["ordenes"],
                  labels={"tasa_dev":"%","location":""})
    fig4.update_traces(
        texttemplate="%{text:.1f}%", textposition="outside",
        hovertemplate="<b>%{y}</b><br>Dev: %{x:.1f}%<br>Órdenes: %{customdata[0]:,}<extra></extra>",
    )
    fig4.update_layout(
        title=dict(font=dict(color="#6B7A8D", size=13)),
        plot_bgcolor="white", paper_bgcolor="white", height=300,
        font=dict(family=FONT, color=PALETTE["text"]),
        margin=dict(t=50,b=20,l=10,r=40),
        hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
    )
    fig4.update_xaxes(gridcolor="#EEF2F7")
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tendencia demoras + dias envio vs devolucion ─────────
col5, col6 = st.columns(2)

with col5:
    df_trend = query(f"""
        SELECT DATE_TRUNC('month', purchase_date)::date AS mes,
               ROUND(AVG(CASE WHEN delivery_status = '{STATUS_DELAYED}' THEN 1.0 ELSE 0.0 END) * 100, 1) AS pct_demorados,
               COUNT(*) AS ordenes
        FROM analytics.fact_orders {where_log}
        AND DATE_TRUNC('month', purchase_date) < DATE_TRUNC('month', CURRENT_DATE)
        GROUP BY 1 ORDER BY mes
    """)
    df_trend["mes_label"] = pd.to_datetime(df_trend["mes"]).dt.strftime("%b %Y")
    fig5 = px.line(df_trend, x="mes_label", y="pct_demorados", markers=True,
                   text=df_trend["pct_demorados"].apply(lambda v: f"{v:.1f}%"),
                   title="Tendencia Mensual de Pedidos Demorados (%)",
                   labels={"pct_demorados":"%","mes_label":"Mes"},
                   color_discrete_sequence=[PALETTE["danger"]])
    fig5.update_traces(
        textposition="top center",
        textfont=dict(size=9, color=PALETTE["text_light"]),
        hovertemplate="<b>%{x}</b><br>Demorados: %{y:.1f}%<extra></extra>",
    )
    fig5.update_layout(
        title=dict(font=dict(color="#6B7A8D", size=13)),
        plot_bgcolor="white", paper_bgcolor="white", height=300,
        font=dict(family=FONT, color=PALETTE["text"]),
        margin=dict(t=50,b=40,l=10,r=10),
        hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
        xaxis=dict(showgrid=False, tickangle=-30),
    )
    fig5.update_yaxes(gridcolor="#EEF2F7")
    st.plotly_chart(fig5, use_container_width=True)

with col6:
    # Filtrado: dias de envio vs tasa de devolucion (antes leia un mart global)
    df_dvr = query(f"""
        SELECT shipping_time_days,
               COUNT(*) AS total_orders,
               ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 1) AS return_rate
        FROM analytics.fact_orders {where_log}
        GROUP BY shipping_time_days ORDER BY shipping_time_days
    """)
    fig6 = go.Figure()
    fig6.add_trace(go.Scatter(
        x=df_dvr["shipping_time_days"], y=df_dvr["return_rate"],
        mode="lines+markers",
        line=dict(color=PALETTE["danger"], width=2.5, shape="spline"),
        marker=dict(size=7, color=PALETTE["danger"], line=dict(color="white", width=1.5)),
        fill="tozeroy", fillcolor="rgba(192,57,43,0.06)",
        customdata=df_dvr[["total_orders"]].values,
        hovertemplate="<b>%{x} días</b><br>Dev: %{y:.1f}%<br>Órdenes: %{customdata[0]:,}<extra></extra>",
    ))
    fig6.update_layout(
        title=dict(text="Días de Envío vs Tasa de Devolución", font=dict(color="#6B7A8D", size=13)),
        plot_bgcolor="white", paper_bgcolor="white", height=300,
        font=dict(family=FONT, color=PALETTE["text"]),
        margin=dict(t=50,b=40,l=10,r=10),
        hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
        xaxis=dict(title="Días de envío", gridcolor="#EEF2F7"),
        yaxis=dict(title="Tasa devolución (%)", gridcolor="#EEF2F7"),
        showlegend=False,
    )
    st.plotly_chart(fig6, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Mapa de ciudades indias ───────────────────────────────
df_map = query(f"""
    SELECT location,
           ROUND(AVG(shipping_time_days)::numeric, 0) AS dias_prom,
           ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)*100,1) AS tasa_dev,
           COUNT(*) AS ordenes
    FROM analytics.fact_orders {where_log}
    GROUP BY location
""")

# Coordenadas de ciudades indias
coords = {
    "Mumbai":    (19.0760, 72.8777),
    "Delhi":     (28.6139, 77.2090),
    "Bangalore": (12.9716, 77.5946),
    "Chennai":   (13.0827, 80.2707),
    "Hyderabad": (17.3850, 78.4867),
}
df_map["lat"] = df_map["location"].map(lambda x: coords.get(x, (20, 77))[0])
df_map["lon"] = df_map["location"].map(lambda x: coords.get(x, (20, 77))[1])

fig_map = px.scatter_geo(
    df_map,
    lat="lat", lon="lon",
    size="ordenes",
    color="tasa_dev",
    hover_name="location",
    color_continuous_scale=[[0, PALETTE["lighter"]], [0.5, PALETTE["primary_light"]], [1, PALETTE["primary"]]],
    title="Distribución Geográfica — Ciudades",
    custom_data=["dias_prom","tasa_dev","ordenes"],
    labels={"tasa_dev":"Dev %"},
)
fig_map.update_traces(
    hovertemplate="<b>%{hovertext}</b><br>Órdenes: %{customdata[2]:,}<br>Días prom: %{customdata[0]:.0f}<br>Dev: %{customdata[1]:.1f}%<extra></extra>",
    marker=dict(sizemin=15, line=dict(color="white", width=1.5)),
)
fig_map.update_geos(
    scope="asia",
    center=dict(lat=20, lon=78),
    projection_scale=3.5,
    showland=True, landcolor="#F5F7FA",
    showocean=True, oceancolor="#EEF2F7",
    showlakes=False,
    showcountries=True, countrycolor="#D6E0EA",
    showcoastlines=True, coastlinecolor="#D6E0EA",
    bgcolor="white",
)
fig_map.update_layout(
    title=dict(font=dict(color="#6B7A8D", size=13)),
    plot_bgcolor="white", paper_bgcolor="white", height=420,
    font=dict(family=FONT, color=PALETTE["text"]),
    margin=dict(t=50, b=10, l=0, r=0),
    coloraxis_colorbar=dict(
        title="Dev %", thickness=12, len=0.6,
        tickfont=dict(size=10),
    ),
    hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
)
st.plotly_chart(fig_map, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Metodo de pago vs devolucion (filtrado) ──────────────
df_pay_ret = query(f"""
    SELECT payment_method,
           COUNT(*) AS total_orders,
           SUM(CASE WHEN is_returned THEN 1 ELSE 0 END) AS returned_orders,
           ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 1) AS return_rate
    FROM analytics.fact_orders {where_log}
    GROUP BY payment_method ORDER BY return_rate DESC
""")
fig7 = px.bar(df_pay_ret, x="payment_method", y="return_rate",
              text="return_rate", color_discrete_sequence=[PALETTE["warning"]],
              title="Tasa de Devolución por Método de Pago (%)",
              labels={"return_rate":"Tasa devolución (%)","payment_method":"Método de pago"},
              custom_data=["total_orders","returned_orders"])
fig7.update_traces(
    texttemplate="%{text:.1f}%", textposition="outside",
    hovertemplate="<b>%{x}</b><br>Dev: %{y:.1f}%<br>Total órdenes: %{customdata[0]:,}<br>Devueltas: %{customdata[1]:,}<extra></extra>",
)
fig7.update_layout(
    title=dict(font=dict(color="#6B7A8D", size=13)),
    plot_bgcolor="white", paper_bgcolor="white", height=300,
    font=dict(family=FONT, color=PALETTE["text"]),
    margin=dict(t=50,b=40,l=10,r=10),
    hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
)
fig7.update_yaxes(gridcolor="#EEF2F7")
st.plotly_chart(fig7, use_container_width=True)