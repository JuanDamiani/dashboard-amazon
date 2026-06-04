"""
Pagina de Analisis de Vendedores — RF6
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from utils.db import query
from utils.filters import render_global_filters
from utils.style import get_css, kpi_card, PALETTE, PLOTLY_COLORS

st.set_page_config(page_title="Vendedores | Amazon Analytics", layout="wide")
st.markdown(get_css(), unsafe_allow_html=True)

filters = render_global_filters()
where = filters["where"]

# Filtros adicionales RF6: vendedor y categoria
with st.sidebar:
    st.markdown("---")
    st.markdown("**🔍 Filtros de Vendedores**")
    vendedores = ["Todos"] + sorted(query("SELECT DISTINCT seller_id FROM analytics.fact_orders ORDER BY seller_id LIMIT 200")["seller_id"].tolist())
    vendedor = st.selectbox("🏪 Vendedor", vendedores)
    categorias = ["Todas"] + sorted(query("SELECT DISTINCT category FROM analytics.fact_orders ORDER BY category")["category"].tolist())
    cat_vend = st.selectbox("🏷️ Categoría", categorias)

where_vend = where
if vendedor != "Todos":
    where_vend += f" AND seller_id = '{vendedor}'"
if cat_vend != "Todas":
    where_vend += f" AND category = '{cat_vend}'"

st.markdown("""
<div class="dashboard-header">
    <div class="dashboard-title">🏪 Análisis de Vendedores</div>
    <div class="dashboard-subtitle">Ranking, rating, devoluciones y categorías por vendedor</div>
</div>
""", unsafe_allow_html=True)

# ── KPIs ─────────────────────────────────────────────────
st.markdown('<div class="section-title">Indicadores de Vendedores</div>', unsafe_allow_html=True)

total_vend   = query(f"SELECT COUNT(DISTINCT seller_id) AS v FROM analytics.fact_orders {where_vend}")["v"].iloc[0]
avg_s_rating = query(f"SELECT ROUND(AVG(seller_rating)::numeric, 2) AS v FROM analytics.fact_orders {where_vend}")["v"].iloc[0]
avg_ret      = query(f"SELECT ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 1) AS v FROM analytics.fact_orders {where_vend}")["v"].iloc[0]

c1, c2, c3 = st.columns(3)
c1.markdown(kpi_card("Vendedores Activos",      f"{total_vend:,}",    None, "🏪"), unsafe_allow_html=True)
c2.markdown(kpi_card("Rating Prom. Vendedores", f"{avg_s_rating} ⭐", None, "⭐"), unsafe_allow_html=True)
c3.markdown(kpi_card("Tasa Dev. Global",        f"{avg_ret}%",        None, "↩️"), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Ranking de vendedores ────────────────────────────────
st.markdown('<div class="section-title">Ranking de Vendedores por Ingresos</div>', unsafe_allow_html=True)

df_rank = query(f"""
    SELECT seller_id,
           COUNT(*) AS ordenes,
           ROUND(SUM(final_price)::numeric, 0) AS ingresos,
           ROUND(AVG(final_price)::numeric, 0) AS ticket_prom,
           ROUND(AVG(seller_rating)::numeric, 2) AS rating_vendedor,
           ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 1) AS tasa_dev
    FROM analytics.fact_orders {where_vend}
    GROUP BY seller_id ORDER BY ingresos DESC LIMIT 50
""")

def color_ret(val):
    if val > 15: return "color: #C0392B; font-weight: 600"
    if val < 5:  return "color: #1E8449; font-weight: 600"
    return ""

styled = df_rank.style\
    .applymap(color_ret, subset=["tasa_dev"])\
    .format({
        "ingresos":       "₹{:,.0f}",
        "ticket_prom":    "₹{:,.0f}",
        "tasa_dev":       "{:.1f}%",
        "rating_vendedor":"{:.2f}",
    })

st.dataframe(styled, use_container_width=True, height=350)

st.markdown("<br>", unsafe_allow_html=True)

# ── Scatter rating vs devolucion + categorias ────────────
st.markdown('<div class="section-title">Perfiles de Vendedores</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    df_scatter = query(f"""
        SELECT seller_id,
               COUNT(*) AS ordenes,
               ROUND(SUM(final_price)::numeric, 0) AS ingresos,
               ROUND(AVG(seller_rating)::numeric, 2) AS rating_vendedor,
               ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 1) AS tasa_dev
        FROM analytics.fact_orders {where_vend}
        GROUP BY seller_id HAVING COUNT(*) >= 10
        ORDER BY ingresos DESC
    """)
    fig1 = px.scatter(df_scatter,
                      x="rating_vendedor", y="tasa_dev",
                      size="ordenes", color="ingresos",
                      color_continuous_scale=[[0, PALETTE["lighter"]], [1, PALETTE["primary"]]],
                      title="Rating vs Tasa de Devolución por Vendedor",
                      labels={"rating_vendedor": "Rating del vendedor", "tasa_dev": "Tasa devolución (%)", "ordenes": "Órdenes"},
                      hover_data={"seller_id": True, "ingresos": ":,.0f"},
                      )
    fig1.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=360, margin=dict(t=50,b=40,l=10,r=10), font=dict(family="IBM Plex Sans"))
    fig1.update_yaxes(gridcolor="#EEF2F7")
    fig1.update_xaxes(gridcolor="#EEF2F7")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    df_cats = query(f"""
        SELECT seller_id, category, total_orders, total_revenue, return_rate
        FROM analytics.mart_categories_by_seller
        ORDER BY total_revenue DESC LIMIT 50
    """)
    fig2 = px.bar(df_cats, x="total_revenue", y="seller_id", color="category",
                  color_discrete_sequence=PLOTLY_COLORS,
                  title="Distribución de Categorías por Vendedor (Top 50)",
                  labels={"total_revenue": "Ingresos (INR)", "seller_id": "Vendedor", "category": "Categoría"})
    fig2.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=360, margin=dict(t=50,b=20,l=10,r=10), font=dict(family="IBM Plex Sans"), legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Vendedores con mayor devolucion ──────────────────────
st.markdown('<div class="section-title">Vendedores con Mayor Tasa de Devolución</div>', unsafe_allow_html=True)

df_worst = query(f"""
    SELECT seller_id,
           COUNT(*) AS ordenes,
           ROUND(SUM(final_price)::numeric, 0) AS ingresos,
           ROUND(AVG(seller_rating)::numeric, 2) AS rating_vendedor,
           ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 1) AS tasa_dev
    FROM analytics.fact_orders {where_vend}
    GROUP BY seller_id HAVING COUNT(*) >= 10
    ORDER BY tasa_dev DESC LIMIT 20
""")

fig3 = px.bar(df_worst, x="seller_id", y="tasa_dev",
              text="tasa_dev", color_discrete_sequence=[PALETTE["danger"]],
              title="Top 20 Vendedores con Mayor Tasa de Devolución (%)",
              labels={"tasa_dev": "Tasa devolución (%)", "seller_id": "Vendedor"})
fig3.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
fig3.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=320, margin=dict(t=50,b=60,l=10,r=10), font=dict(family="IBM Plex Sans"), xaxis_tickangle=-45)
fig3.update_yaxes(gridcolor="#EEF2F7")
st.plotly_chart(fig3, use_container_width=True)