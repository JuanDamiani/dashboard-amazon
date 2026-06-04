"""
Pagina de Experiencia del Cliente — RF5
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from utils.db import query
from utils.filters import render_global_filters
from utils.style import get_css, kpi_card, PALETTE, PLOTLY_COLORS

st.set_page_config(page_title="Clientes | Amazon Analytics", layout="wide")
st.markdown(get_css(), unsafe_allow_html=True)

filters = render_global_filters()
where = filters["where"]

# Filtro adicional RF5: rango de rating
with st.sidebar:
    st.markdown("---")
    st.markdown("**🔍 Filtros de Clientes**")
    rating_min, rating_max = st.slider("⭐ Rango de rating", 1.0, 5.0, (1.0, 5.0), 0.5)

where_cli = where + f" AND rating BETWEEN {rating_min} AND {rating_max}"

st.markdown("""
<div class="dashboard-header">
    <div class="dashboard-title">👥 Experiencia del Cliente</div>
    <div class="dashboard-subtitle">Rating, satisfacción, devoluciones y comportamiento de compra</div>
</div>
""", unsafe_allow_html=True)

# ── KPIs ─────────────────────────────────────────────────
st.markdown('<div class="section-title">Indicadores de Satisfacción</div>', unsafe_allow_html=True)

avg_rating = query(f"SELECT ROUND(AVG(rating)::numeric, 2) AS v FROM analytics.fact_orders {where_cli}")["v"].iloc[0]
ret_rate   = query(f"SELECT ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 1) AS v FROM analytics.fact_orders {where_cli}")["v"].iloc[0]
total_ord  = query(f"SELECT COUNT(*) AS v FROM analytics.fact_orders {where_cli}")["v"].iloc[0]

c1, c2, c3 = st.columns(3)
c1.markdown(kpi_card("Rating Promedio",    f"{avg_rating} ⭐", None, "🌟"), unsafe_allow_html=True)
c2.markdown(kpi_card("Tasa Devolución",    f"{ret_rate}%",     None, "↩️"), unsafe_allow_html=True)
c3.markdown(kpi_card("Total Órdenes",      f"{total_ord:,}",   None, "📦"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Distribucion de ratings ──────────────────────────────
st.markdown('<div class="section-title">Distribución de Ratings</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    df_dist = query("SELECT rating, total_orders, order_share_pct FROM analytics.mart_rating_distribution ORDER BY rating")
    fig1 = px.bar(df_dist, x="rating", y="total_orders",
                  text="order_share_pct", color_discrete_sequence=[PALETTE["secondary"]],
                  title="Distribución de Órdenes por Rating",
                  labels={"total_orders": "Órdenes", "rating": "Rating"})
    fig1.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig1.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=320, margin=dict(t=50,b=40,l=10,r=10), font=dict(family="IBM Plex Sans"))
    fig1.update_yaxes(gridcolor="#EEF2F7")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    df_range = query("SELECT rating_range, total_orders, order_share_pct, avg_rating, return_rate FROM analytics.mart_rating_by_range ORDER BY rating_range")
    fig2 = px.bar(df_range, x="order_share_pct", y="rating_range", orientation="h",
                  text="order_share_pct", color_discrete_sequence=[PALETTE["primary"]],
                  title="Rating por Rango (%)",
                  custom_data=["avg_rating", "return_rate", "total_orders"],
                  labels={"order_share_pct": "% del total", "rating_range": ""})
    fig2.update_traces(
        texttemplate="%{text:.1f}%", textposition="outside",
        hovertemplate="<b>%{y}</b><br>% órdenes: %{x:.1f}%<br>Rating prom: %{customdata[0]}<br>Tasa dev: %{customdata[1]}%<br>Órdenes: %{customdata[2]:,}<extra></extra>",
    )
    fig2.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=320, margin=dict(t=50,b=20,l=10,r=40), font=dict(family="IBM Plex Sans"))
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Rating por categoria + por ciudad ────────────────────
st.markdown('<div class="section-title">Satisfacción por Categoría y Ciudad</div>', unsafe_allow_html=True)

col3, col4 = st.columns(2)

with col3:
    df_cat = query(f"""
        SELECT category,
               ROUND(AVG(rating)::numeric, 2) AS avg_rating,
               ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 1) AS tasa_dev,
               COUNT(*) AS ordenes
        FROM analytics.fact_orders {where_cli}
        GROUP BY category ORDER BY avg_rating DESC
    """)
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(x=df_cat["category"], y=df_cat["avg_rating"], name="Rating promedio", marker_color=PALETTE["secondary"], text=df_cat["avg_rating"], textposition="outside"))
    fig3.add_trace(go.Scatter(x=df_cat["category"], y=df_cat["tasa_dev"], name="Tasa devolución (%)", mode="lines+markers", line=dict(color=PALETTE["danger"], width=2), yaxis="y2"))
    fig3.update_layout(
        title="Rating y Tasa de Devolución por Categoría",
        plot_bgcolor="white", paper_bgcolor="white",
        height=320, margin=dict(t=50,b=40,l=10,r=60),
        font=dict(family="IBM Plex Sans"),
        yaxis=dict(title="Rating promedio", gridcolor="#EEF2F7"),
        yaxis2=dict(title="Tasa devolución (%)", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", y=1.1),
    )
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    df_city = query(f"""
        SELECT location,
               ROUND(AVG(rating)::numeric, 2) AS avg_rating,
               ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 1) AS tasa_dev,
               COUNT(*) AS ordenes
        FROM analytics.fact_orders {where_cli}
        GROUP BY location ORDER BY avg_rating DESC
    """)
    fig4 = px.bar(df_city, x="avg_rating", y="location", orientation="h",
                  text="avg_rating", color_discrete_sequence=[PALETTE["success"]],
                  title="Rating Promedio por Ciudad",
                  custom_data=["tasa_dev", "ordenes"],
                  labels={"avg_rating": "Rating promedio", "location": ""})
    fig4.update_traces(
        texttemplate="%{text:.2f} ⭐", textposition="outside",
        hovertemplate="<b>%{y}</b><br>Rating: %{x:.2f}<br>Tasa dev: %{customdata[0]}%<br>Órdenes: %{customdata[1]:,}<extra></extra>",
    )
    fig4.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=320, margin=dict(t=50,b=20,l=10,r=60), font=dict(family="IBM Plex Sans"))
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Impacto tiempo envio + comportamiento dispositivo ────
st.markdown('<div class="section-title">Impacto del Envío y Comportamiento por Dispositivo</div>', unsafe_allow_html=True)

col5, col6 = st.columns(2)

with col5:
    df_ship = query(f"""
        SELECT shipping_time_days,
               ROUND(AVG(rating)::numeric, 2) AS avg_rating,
               COUNT(*) AS ordenes
        FROM analytics.fact_orders {where_cli}
        GROUP BY shipping_time_days ORDER BY shipping_time_days
    """)
    fig5 = px.line(df_ship, x="shipping_time_days", y="avg_rating", markers=True,
                   title="Impacto del Tiempo de Envío en el Rating",
                   labels={"shipping_time_days": "Días de envío", "avg_rating": "Rating promedio"},
                   color_discrete_sequence=[PALETTE["accent"]])
    fig5.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=300, margin=dict(t=50,b=40,l=10,r=10), font=dict(family="IBM Plex Sans"))
    fig5.update_yaxes(gridcolor="#EEF2F7")
    fig5.update_xaxes(gridcolor="#EEF2F7")
    st.plotly_chart(fig5, use_container_width=True)

with col6:
    df_dev = query(f"""
        SELECT device,
               COUNT(*) AS ordenes,
               ROUND(AVG(rating)::numeric, 2) AS avg_rating,
               ROUND(AVG(final_price)::numeric, 0) AS ticket_prom,
               ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 1) AS tasa_dev
        FROM analytics.fact_orders {where_cli}
        GROUP BY device ORDER BY ordenes DESC
    """)
    fig6 = go.Figure()
    fig6.add_trace(go.Bar(x=df_dev["device"], y=df_dev["ordenes"], name="Órdenes", marker_color=PALETTE["secondary"], yaxis="y"))
    fig6.add_trace(go.Scatter(x=df_dev["device"], y=df_dev["avg_rating"], name="Rating promedio", mode="lines+markers", line=dict(color=PALETTE["accent"], width=2), marker=dict(size=8), yaxis="y2"))
    fig6.update_layout(
        title="Comportamiento de Compra por Dispositivo",
        plot_bgcolor="white", paper_bgcolor="white",
        height=300, margin=dict(t=50,b=40,l=10,r=60),
        font=dict(family="IBM Plex Sans"),
        yaxis=dict(title="Órdenes", gridcolor="#EEF2F7"),
        yaxis2=dict(title="Rating promedio", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", y=1.1),
    )
    st.plotly_chart(fig6, use_container_width=True)