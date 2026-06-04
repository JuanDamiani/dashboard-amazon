"""
Pagina de Analisis Logistico — RF4
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from utils.db import query
from utils.filters import render_global_filters
from utils.style import get_css, kpi_card, PALETTE, PLOTLY_COLORS

st.set_page_config(page_title="Logística | Amazon Analytics", layout="wide")
st.markdown(get_css(), unsafe_allow_html=True)

filters = render_global_filters()
where = filters["where"]

# Filtro adicional RF4: estado de entrega
with st.sidebar:
    st.markdown("---")
    st.markdown("**🔍 Filtros de Logística**")
    estados = ["Todos"] + sorted(query("SELECT DISTINCT delivery_status FROM analytics.fact_orders ORDER BY delivery_status")["delivery_status"].tolist())
    estado = st.selectbox("🚚 Estado de entrega", estados)

where_log = where
if estado != "Todos":
    where_log += f" AND delivery_status = '{estado}'"

st.markdown("""
<div class="dashboard-header">
    <div class="dashboard-title">🚚 Análisis Logístico</div>
    <div class="dashboard-subtitle">Entregas, demoras, devoluciones y tiempos de envío</div>
</div>
""", unsafe_allow_html=True)

# ── KPIs logísticos ──────────────────────────────────────
st.markdown('<div class="section-title">Indicadores Logísticos</div>', unsafe_allow_html=True)

df_perf = query("SELECT * FROM analytics.mart_delivery_performance")
pct_on_time  = float(df_perf["pct_on_time"].iloc[0])  if len(df_perf) > 0 else 0
pct_delayed  = float(df_perf["pct_delayed"].iloc[0])  if len(df_perf) > 0 else 0
avg_ship     = query(f"SELECT ROUND(AVG(shipping_time_days)::numeric, 1) AS v FROM analytics.fact_orders {where_log}")["v"].iloc[0]
ret_rate     = query(f"SELECT ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 1) AS v FROM analytics.fact_orders {where_log}")["v"].iloc[0]

c1, c2, c3, c4 = st.columns(4)
c1.markdown(kpi_card("Entregas a Tiempo",   f"{pct_on_time}%",  None, "✅"), unsafe_allow_html=True)
c2.markdown(kpi_card("Tiempo Prom. Envío",  f"{avg_ship} días", None, "⏱️"), unsafe_allow_html=True)
c3.markdown(kpi_card("Pedidos Demorados",   f"{pct_delayed}%",  None, "⚠️"), unsafe_allow_html=True)
c4.markdown(kpi_card("Tasa Devolución",     f"{ret_rate}%",     None, "↩️"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Distribucion + tiempo por ciudad ────────────────────
st.markdown('<div class="section-title">Estado de Entregas y Tiempos por Ciudad</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    df_est = query(f"""
        SELECT delivery_status,
               COUNT(*) AS ordenes,
               ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct,
               ROUND(AVG(shipping_time_days)::numeric, 1) AS dias_prom,
               ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 1) AS tasa_dev
        FROM analytics.fact_orders {where_log}
        GROUP BY delivery_status ORDER BY ordenes DESC
    """)
    fig = px.bar(df_est, x="pct", y="delivery_status", orientation="h",
                 text="pct", color_discrete_sequence=[PALETTE["primary"]],
                 title="Distribución por Estado de Entrega (%)",
                 custom_data=["dias_prom", "tasa_dev", "ordenes"],
                 labels={"pct": "%", "delivery_status": ""})
    fig.update_traces(
        texttemplate="%{text:.1f}%", textposition="outside",
        hovertemplate="<b>%{y}</b><br>%: %{x:.1f}%<br>Días prom: %{customdata[0]}<br>Tasa dev: %{customdata[1]}%<br>Órdenes: %{customdata[2]:,}<extra></extra>",
    )
    fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=300, margin=dict(t=50,b=20,l=10,r=40), font=dict(family="IBM Plex Sans"))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    df_city = query(f"""
        SELECT location,
               ROUND(AVG(shipping_time_days)::numeric, 1) AS dias_prom,
               ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 1) AS tasa_dev,
               COUNT(*) AS ordenes
        FROM analytics.fact_orders {where_log}
        GROUP BY location ORDER BY dias_prom DESC
    """)
    fig2 = px.bar(df_city, x="dias_prom", y="location", orientation="h",
                  text="dias_prom", color_discrete_sequence=[PALETTE["secondary"]],
                  title="Tiempo Promedio de Envío por Ciudad (días)",
                  custom_data=["tasa_dev", "ordenes"],
                  labels={"dias_prom": "Días promedio", "location": ""})
    fig2.update_traces(
        texttemplate="%{text:.1f} días", textposition="outside",
        hovertemplate="<b>%{y}</b><br>Días prom: %{x:.1f}<br>Tasa dev: %{customdata[0]}%<br>Órdenes: %{customdata[1]:,}<extra></extra>",
    )
    fig2.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=300, margin=dict(t=50,b=20,l=10,r=80), font=dict(family="IBM Plex Sans"))
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Devoluciones por categoria y ciudad ──────────────────
st.markdown('<div class="section-title">Devoluciones por Categoría y Ciudad</div>', unsafe_allow_html=True)

col3, col4 = st.columns(2)

with col3:
    df_ret_cat = query(f"""
        SELECT category,
               ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 1) AS tasa_dev,
               COUNT(*) AS ordenes,
               SUM(CASE WHEN is_returned THEN 1 ELSE 0 END) AS devueltas
        FROM analytics.fact_orders {where_log}
        GROUP BY category ORDER BY tasa_dev DESC
    """)
    fig3 = px.bar(df_ret_cat, x="tasa_dev", y="category", orientation="h",
                  text="tasa_dev", color_discrete_sequence=[PALETTE["danger"] if True else PALETTE["secondary"]],
                  title="Tasa de Devolución por Categoría (%)",
                  labels={"tasa_dev": "Tasa devolución (%)", "category": ""})
    fig3.update_traces(
        texttemplate="%{text:.1f}%", textposition="outside",
        marker_color=PALETTE["danger"],
    )
    fig3.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=300, margin=dict(t=50,b=20,l=10,r=40), font=dict(family="IBM Plex Sans"))
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
                  text="tasa_dev", color_discrete_sequence=[PALETTE["warning"]],
                  title="Tasa de Devolución por Ciudad (%)",
                  labels={"tasa_dev": "Tasa devolución (%)", "location": ""})
    fig4.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig4.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=300, margin=dict(t=50,b=20,l=10,r=40), font=dict(family="IBM Plex Sans"))
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tendencia demoras + demoras vs devoluciones ──────────
st.markdown('<div class="section-title">Tendencias y Correlaciones</div>', unsafe_allow_html=True)

col5, col6 = st.columns(2)

with col5:
    df_trend = query(f"""
        SELECT DATE_TRUNC('month', purchase_date)::date AS mes,
               ROUND(AVG(CASE WHEN delivery_status = 'Delayed' THEN 1.0 ELSE 0.0 END) * 100, 1) AS pct_demorados,
               COUNT(*) AS ordenes
        FROM analytics.fact_orders {where_log}
        GROUP BY 1 ORDER BY mes
    """)
    df_trend["mes"] = pd.to_datetime(df_trend["mes"]).dt.strftime("%b %Y")
    fig5 = px.line(df_trend, x="mes", y="pct_demorados", markers=True,
                   title="Tendencia Mensual de Pedidos Demorados (%)",
                   labels={"pct_demorados": "% Demorados", "mes": "Mes"},
                   color_discrete_sequence=[PALETTE["danger"]])
    fig5.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=300, margin=dict(t=50,b=40,l=10,r=10), font=dict(family="IBM Plex Sans"))
    fig5.update_yaxes(gridcolor="#EEF2F7")
    fig5.update_xaxes(gridcolor="#EEF2F7")
    st.plotly_chart(fig5, use_container_width=True)

with col6:
    df_dvr = query("SELECT shipping_time_days, total_orders, return_rate FROM analytics.mart_delays_vs_returns ORDER BY shipping_time_days")
    fig6 = go.Figure()
    fig6.add_trace(go.Scatter(x=df_dvr["shipping_time_days"], y=df_dvr["return_rate"],
                              mode="lines+markers", name="Tasa devolución (%)",
                              line=dict(color=PALETTE["danger"], width=2.5), marker=dict(size=6)))
    fig6.update_layout(
        title="Días de Envío vs Tasa de Devolución",
        plot_bgcolor="white", paper_bgcolor="white",
        height=300, margin=dict(t=50,b=40,l=10,r=10),
        font=dict(family="IBM Plex Sans"),
        xaxis=dict(title="Días de envío", gridcolor="#EEF2F7"),
        yaxis=dict(title="Tasa devolución (%)", gridcolor="#EEF2F7"),
    )
    st.plotly_chart(fig6, use_container_width=True)

# ── Metodo de pago vs devolucion ─────────────────────────
st.markdown('<div class="section-title">Método de Pago vs Devolución</div>', unsafe_allow_html=True)

df_pay_ret = query("SELECT payment_method, total_orders, returned_orders, return_rate FROM analytics.mart_payment_vs_returns ORDER BY return_rate DESC")
fig7 = px.bar(df_pay_ret, x="payment_method", y="return_rate",
              text="return_rate", color_discrete_sequence=[PALETTE["warning"]],
              title="Tasa de Devolución por Método de Pago (%)",
              labels={"return_rate": "Tasa devolución (%)", "payment_method": "Método de pago"},
              custom_data=["total_orders", "returned_orders"])
fig7.update_traces(
    texttemplate="%{text:.1f}%", textposition="outside",
    hovertemplate="<b>%{x}</b><br>Tasa dev: %{y:.1f}%<br>Total órdenes: %{customdata[0]:,}<br>Devueltas: %{customdata[1]:,}<extra></extra>",
)
fig7.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=300, margin=dict(t=50,b=40,l=10,r=10), font=dict(family="IBM Plex Sans"))
fig7.update_yaxes(gridcolor="#EEF2F7")
st.plotly_chart(fig7, use_container_width=True)