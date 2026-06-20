"""
Pagina de Analisis de Vendedores — RF6
Filtros: globales + categoria (global) + vendedor (local).
"""

import streamlit as st
import plotly.express as px

from utils.db import query
from utils.filters import render_filters
from utils.style import kpi_card, PALETTE, PLOTLY_COLORS, FONT

# ── FILTROS globales (sin locales de Mas filtros; RF6 usa vendedor abajo) ──
filters    = render_filters(extra_filters=[])
where_vend = filters["where"]

# ── Filtros propios de Vendedores (RF6: vendedor) ─────────
@st.cache_data(ttl=3600)
def load_seller_options():
    return query("SELECT DISTINCT seller_id FROM analytics.fact_orders ORDER BY seller_id")["seller_id"].tolist()

sellers = load_seller_options()

with st.expander("🏪 Filtros de Vendedores", expanded=False):
    vc = st.columns(2)
    with vc[0]:
        sel_vendedor = st.selectbox("Vendedor", ["Todos"] + sellers, key="vend_sel")
    with vc[1]:
        min_ordenes = st.slider("Mínimo de órdenes por vendedor", 1, 100, 10, key="vend_min_ord")

# Filtro local de vendedor (se inyecta en el WHERE de esta pagina)
if sel_vendedor != "Todos":
    _v = str(sel_vendedor).replace("'", "''")
    where_vend = where_vend.replace("WHERE ", f"WHERE seller_id = '{_v}' AND ", 1)

# ── KPIs ─────────────────────────────────────────────────
total_vend   = query(f"SELECT COUNT(DISTINCT seller_id) AS v FROM analytics.fact_orders {where_vend}")["v"].iloc[0]
avg_s_rating = query(f"SELECT ROUND(AVG(seller_rating)::numeric,2) AS v FROM analytics.fact_orders {where_vend}")["v"].iloc[0]
avg_ret      = query(f"SELECT ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric*100,1) AS v FROM analytics.fact_orders {where_vend}")["v"].iloc[0]
avg_ingreso  = query(f"""
    SELECT ROUND(AVG(ingresos)::numeric, 0) AS v FROM (
        SELECT seller_id, SUM(final_price) AS ingresos
        FROM analytics.fact_orders {where_vend}
        GROUP BY seller_id
    ) t
""")["v"].iloc[0]

def fmt_rev(v):
    if v >= 1_000_000_000: return f"₹{v/1_000_000_000:.1f}B"
    if v >= 1_000_000:     return f"₹{v/1_000_000:.1f}M"
    return f"₹{v:,.0f}"

ICON_STORE  = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>'
ICON_STAR   = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>'
ICON_RET    = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>'
ICON_TICKET = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>'

c1, c2, c3, c4 = st.columns(4)
c1.markdown(kpi_card("Vendedores Activos",      f"{total_vend:,}",     None, ICON_STORE,  "Total de vendedores con al menos una orden en el período."), unsafe_allow_html=True)
c2.markdown(kpi_card("Rating Prom. Vendedores", str(avg_s_rating),     None, ICON_STAR,   "Calificación promedio de vendedores, escala 1 a 5."), unsafe_allow_html=True)
c3.markdown(kpi_card("Tasa Dev. Global",        f"{avg_ret}%",         None, ICON_RET,    "% de órdenes devueltas en el período."), unsafe_allow_html=True)
c4.markdown(kpi_card("Ingreso Prom. Vendedor",  fmt_rev(avg_ingreso),  None, ICON_TICKET, "Ingreso promedio por vendedor en el período."), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Ranking de vendedores ────────────────────────────────
df_rank = query(f"""
    SELECT seller_id, COUNT(*) AS ordenes,
           ROUND(SUM(final_price)::numeric, 0) AS ingresos,
           ROUND(AVG(final_price)::numeric, 0) AS ticket_prom,
           ROUND(AVG(seller_rating)::numeric, 2) AS rating_vendedor,
           ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)*100,1) AS tasa_dev
    FROM analytics.fact_orders {where_vend}
    GROUP BY seller_id HAVING COUNT(*) >= {min_ordenes}
    ORDER BY ingresos DESC LIMIT 50
""")

df_rank_display = df_rank.copy()
df_rank_display["ingresos"]    = df_rank_display["ingresos"].apply(lambda v:
    f"₹{v/1_000_000:.0f}M" if v >= 1_000_000 else f"₹{v:,.0f}")
df_rank_display["ticket_prom"] = df_rank_display["ticket_prom"].apply(lambda v: f"₹{v:,.0f}")
df_rank_display["tasa_dev"]    = df_rank_display["tasa_dev"].apply(lambda v: f"{v:.1f}%")
df_rank_display["ordenes"]     = df_rank_display["ordenes"].apply(lambda v: f"{v:,}")
df_rank_display = df_rank_display.rename(columns={
    "seller_id":       "Vendedor",
    "ordenes":         "Órdenes",
    "ingresos":        "Ingresos",
    "ticket_prom":     "Ticket Prom.",
    "rating_vendedor": "Rating",
    "tasa_dev":        "Dev %",
})

def color_dev(val):
    try:
        v = float(val.replace("%", ""))
        if v > 15: return "color:#C0392B;font-weight:600"
        if v < 5:  return "color:#1A7F4B;font-weight:600"
    except: pass
    return ""

styled = (
    df_rank_display.style
    .applymap(color_dev, subset=["Dev %"])
    .set_table_styles([
        {"selector": "th", "props": [
            ("background", "#F0F4F8"), ("color", "#5A6A7A"),
            ("font-size", "0.75rem"), ("padding", "8px 12px"),
            ("font-weight", "700"), ("text-transform", "uppercase"),
        ]},
        {"selector": "td", "props": [
            ("font-size", "0.82rem"), ("padding", "7px 12px"),
            ("border-bottom", "1px solid #F0F4F8"),
        ]},
    ])
    .hide(axis="index")
)

st.dataframe(styled, use_container_width=True, height=380)

st.markdown("<br>", unsafe_allow_html=True)

# ── Scatter + categorias por vendedor ────────────────────
col1, col2 = st.columns(2)

with col1:
    df_scatter = query(f"""
        SELECT seller_id, COUNT(*) AS ordenes,
               ROUND(SUM(final_price)::numeric, 0) AS ingresos,
               ROUND(AVG(seller_rating)::numeric, 2) AS rating_vendedor,
               ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)*100,1) AS tasa_dev
        FROM analytics.fact_orders {where_vend}
        GROUP BY seller_id HAVING COUNT(*) >= {min_ordenes}
        ORDER BY ingresos DESC
    """)
    fig1 = px.scatter(df_scatter,
        x="rating_vendedor", y="tasa_dev",
        size="ordenes", color="ingresos",
        color_continuous_scale=[[0, PALETTE["lighter"]], [0.5, PALETTE["primary_light"]], [1, PALETTE["primary"]]],
        title="Rating vs Devolución por Vendedor",
        labels={"rating_vendedor":"Rating","tasa_dev":"Dev (%)","ordenes":"Órdenes"},
        hover_data={"seller_id":True,"ingresos":":,.0f"},
    )
    fig1.update_layout(
        title=dict(font=dict(color="#6B7A8D", size=13)),
        plot_bgcolor="white", paper_bgcolor="white", height=380,
        font=dict(family=FONT, color=PALETTE["text"]),
        margin=dict(t=50,b=40,l=10,r=10),
        hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
    )
    fig1.update_yaxes(gridcolor="#EEF2F7")
    fig1.update_xaxes(gridcolor="#EEF2F7")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    # Filtrado: categorias por vendedor (antes leia mart_categories_by_seller global)
    df_cats = query(f"""
        SELECT seller_id, category,
               COUNT(*) AS total_orders,
               ROUND(SUM(final_price)::numeric, 0) AS total_revenue,
               ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)*100,1) AS return_rate
        FROM analytics.fact_orders {where_vend}
        GROUP BY seller_id, category
        ORDER BY total_revenue DESC LIMIT 50
    """)
    df_cats["label"] = df_cats["total_revenue"].apply(lambda v:
        f"₹{v/1_000_000:.0f}M" if v >= 1_000_000 else f"₹{v:,.0f}")
    fig2 = px.bar(df_cats, x="total_revenue", y="seller_id", color="category",
                  color_discrete_sequence=PLOTLY_COLORS,
                  title="Categorías por Vendedor (Top 50)",
                  labels={"total_revenue":"Ingresos","seller_id":"Vendedor","category":"Categoría"})
    fig2.update_layout(
        title=dict(font=dict(color="#6B7A8D", size=13)),
        plot_bgcolor="white", paper_bgcolor="white", height=380,
        font=dict(family=FONT, color=PALETTE["text"]),
        margin=dict(t=50,b=20,l=10,r=10),
        legend=dict(orientation="h", y=1.08),
        hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
    )
    fig2.update_xaxes(gridcolor="#EEF2F7")
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Top vendedores con mayor devolucion ──────────────────
df_worst = query(f"""
    SELECT seller_id, COUNT(*) AS ordenes,
           ROUND(SUM(final_price)::numeric, 0) AS ingresos,
           ROUND(AVG(seller_rating)::numeric, 2) AS rating_vendedor,
           ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)*100,1) AS tasa_dev
    FROM analytics.fact_orders {where_vend}
    GROUP BY seller_id HAVING COUNT(*) >= {min_ordenes}
    ORDER BY tasa_dev DESC LIMIT 15
""")
df_worst["label"] = df_worst["tasa_dev"].apply(lambda v: f"{v:.1f}%")

fig3 = px.bar(df_worst, x="seller_id", y="tasa_dev",
              text="label",
              color_discrete_sequence=[PALETTE["danger"]],
              title="Top 15 Vendedores con Mayor Tasa de Devolución (%)",
              labels={"tasa_dev":"Dev (%)","seller_id":"Vendedor"},
              custom_data=["ordenes","rating_vendedor","ingresos"])
fig3.update_traces(
    textposition="outside",
    hovertemplate="<b>%{x}</b><br>Dev: %{y:.1f}%<br>Órdenes: %{customdata[0]:,}<br>Rating: %{customdata[1]:.2f}<br>Ingresos: ₹%{customdata[2]:,.0f}<extra></extra>",
)
fig3.update_layout(
    title=dict(font=dict(color="#6B7A8D", size=13)),
    plot_bgcolor="white", paper_bgcolor="white", height=320,
    font=dict(family=FONT, color=PALETTE["text"]),
    margin=dict(t=50,b=60,l=10,r=10),
    xaxis_tickangle=-45,
    hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
)
fig3.update_yaxes(gridcolor="#EEF2F7")
st.plotly_chart(fig3, use_container_width=True)