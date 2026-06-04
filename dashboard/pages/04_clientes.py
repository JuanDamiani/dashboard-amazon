"""
Pagina de Experiencia del Cliente — RF5
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from utils.db import query
from utils.filters import render_filters
from utils.style import get_css, kpi_card, PALETTE, PLOTLY_COLORS, FONT

st.set_page_config(
    page_title="Clientes | Amazon Analytics",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(get_css(), unsafe_allow_html=True)

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
        index=3,
        key="main_nav",
    )
    if selected_tab == "Overview":
        st.switch_page("app.py")
    elif selected_tab == "Ventas":
        st.switch_page("pages/02_ventas.py")
    elif selected_tab == "Logística":
        st.switch_page("pages/03_logistica.py")
    elif selected_tab == "Vendedores":
        st.switch_page("pages/05_vendedores.py")
    elif selected_tab == "Glosario":
        st.switch_page("pages/06_glosario.py")

st.markdown('<hr style="margin: 0 0 8px 0; border-color: #E4E9F0;">', unsafe_allow_html=True)

# ── FILTROS (RF2 + filtro adicional rating) ───────────────
filters   = render_filters(extra_filters=["rating"])
where     = filters["where"]
r_min     = filters["rating_min"]
r_max     = filters["rating_max"]
where_cli = where + f" AND rating BETWEEN {r_min} AND {r_max}"

st.markdown('<hr style="margin: 4px 0 12px 0; border-color: #E4E9F0;">', unsafe_allow_html=True)

# ── KPIs ─────────────────────────────────────────────────
avg_rating = query(f"SELECT ROUND(AVG(rating)::numeric,2) AS v FROM analytics.fact_orders {where_cli}")["v"].iloc[0]
ret_rate   = query(f"SELECT ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric*100,1) AS v FROM analytics.fact_orders {where_cli}")["v"].iloc[0]
total_ord  = query(f"SELECT COUNT(*) AS v FROM analytics.fact_orders {where_cli}")["v"].iloc[0]
avg_ticket = query(f"SELECT ROUND(AVG(final_price)::numeric,0) AS v FROM analytics.fact_orders {where_cli}")["v"].iloc[0]

def fmt_num(v):
    if v >= 1_000_000: return f"{v/1_000_000:.1f}M"
    if v >= 1_000:     return f"{v/1_000:.1f}k"
    return f"{v:,.0f}"

ICON_STAR  = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>'
ICON_RET   = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>'
ICON_BOX   = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><path d="M20 7H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>'
ICON_TICKET= '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v2z"/></svg>'

c1, c2, c3, c4 = st.columns(4)
c1.markdown(kpi_card("Rating Promedio",  str(avg_rating),       None, ICON_STAR,   "Calificación promedio de productos, escala 1 a 5."), unsafe_allow_html=True)
c2.markdown(kpi_card("Tasa Devolución",  f"{ret_rate}%",        None, ICON_RET,    "% de órdenes devueltas en el período."), unsafe_allow_html=True)
c3.markdown(kpi_card("Total Órdenes",    fmt_num(total_ord),    None, ICON_BOX,    "Órdenes en el rango de rating seleccionado."), unsafe_allow_html=True)
c4.markdown(kpi_card("Ticket Promedio",  f"₹{avg_ticket:,.0f}", None, ICON_TICKET, "Ingreso promedio por orden en INR."), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Distribución de ratings ──────────────────────────────
col1, col2 = st.columns(2)

with col1:
    df_dist = query("SELECT rating, total_orders, order_share_pct FROM analytics.mart_rating_distribution ORDER BY rating")
    fig1 = px.bar(df_dist, x="rating", y="total_orders",
                  text="order_share_pct",
                  color_discrete_sequence=[PALETTE["primary_light"]],
                  title="Distribución de Órdenes por Rating",
                  labels={"total_orders":"Órdenes","rating":"Rating"})
    fig1.update_traces(
        texttemplate="%{text:.1f}%", textposition="outside",
        hovertemplate="<b>Rating %{x}</b><br>Órdenes: %{y:,}<br>% del total: %{text:.1f}%<extra></extra>",
    )
    fig1.update_layout(
        title=dict(font=dict(color="#6B7A8D", size=13)),
        plot_bgcolor="white", paper_bgcolor="white", height=300,
        font=dict(family=FONT, color=PALETTE["text"]),
        margin=dict(t=50,b=40,l=10,r=10),
        hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
    )
    fig1.update_yaxes(gridcolor="#EEF2F7")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    df_range = query("SELECT rating_range, total_orders, order_share_pct, avg_rating, return_rate FROM analytics.mart_rating_by_range ORDER BY rating_range")
    fig2 = px.bar(df_range, x="order_share_pct", y="rating_range", orientation="h",
                  text="order_share_pct",
                  color_discrete_sequence=[PALETTE["primary"]],
                  title="Órdenes por Rango de Rating (%)",
                  custom_data=["avg_rating","return_rate","total_orders"],
                  labels={"order_share_pct":"% del total","rating_range":""})
    fig2.update_traces(
        texttemplate="%{text:.1f}%", textposition="outside",
        hovertemplate="<b>%{y}</b><br>% órdenes: %{x:.1f}%<br>Rating prom: %{customdata[0]}<br>Dev: %{customdata[1]}%<br>Órdenes: %{customdata[2]:,}<extra></extra>",
    )
    fig2.update_layout(
        title=dict(font=dict(color="#6B7A8D", size=13)),
        plot_bgcolor="white", paper_bgcolor="white", height=300,
        font=dict(family=FONT, color=PALETTE["text"]),
        margin=dict(t=50,b=20,l=10,r=50),
        hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
    )
    fig2.update_xaxes(gridcolor="#EEF2F7")
    st.plotly_chart(fig2, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Rating por categoria + por ciudad ────────────────────
col3, col4 = st.columns(2)

with col3:
    df_cat = query(f"""
        SELECT category,
               ROUND(AVG(rating)::numeric, 2) AS avg_rating,
               ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)*100,1) AS tasa_dev,
               COUNT(*) AS ordenes
        FROM analytics.fact_orders {where_cli}
        GROUP BY category ORDER BY avg_rating DESC
    """)
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=df_cat["category"], y=df_cat["avg_rating"],
        name="Rating promedio",
        marker_color=PALETTE["primary_light"],
        text=df_cat["avg_rating"], textposition="outside",
    ))
    fig3.add_trace(go.Scatter(
        x=df_cat["category"], y=df_cat["tasa_dev"],
        name="Dev %", mode="lines+markers",
        line=dict(color=PALETTE["danger"], width=2),
        marker=dict(size=7), yaxis="y2",
    ))
    fig3.update_layout(
        title=dict(text="Rating y Devolución por Categoría", font=dict(color="#6B7A8D", size=13)),
        plot_bgcolor="white", paper_bgcolor="white", height=320,
        font=dict(family=FONT, color=PALETTE["text"]),
        margin=dict(t=50,b=40,l=10,r=60),
        yaxis=dict(title="Rating", gridcolor="#EEF2F7"),
        yaxis2=dict(title="Dev %", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", y=1.1),
        hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
    )
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    df_city = query(f"""
        SELECT location,
               ROUND(AVG(rating)::numeric, 2) AS avg_rating,
               ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)*100,1) AS tasa_dev,
               COUNT(*) AS ordenes
        FROM analytics.fact_orders {where_cli}
        GROUP BY location ORDER BY avg_rating DESC
    """)
    fig4 = px.bar(df_city, x="avg_rating", y="location", orientation="h",
                  text="avg_rating",
                  color_discrete_sequence=[PALETTE["primary_light"]],
                  title="Rating Promedio por Ciudad",
                  custom_data=["tasa_dev","ordenes"],
                  labels={"avg_rating":"Rating","location":""})
    fig4.update_traces(
        texttemplate="%{text:.2f} ⭐", textposition="outside",
        hovertemplate="<b>%{y}</b><br>Rating: %{x:.2f}<br>Dev: %{customdata[0]}%<br>Órdenes: %{customdata[1]:,}<extra></extra>",
    )
    fig4.update_layout(
        title=dict(font=dict(color="#6B7A8D", size=13)),
        plot_bgcolor="white", paper_bgcolor="white", height=320,
        font=dict(family=FONT, color=PALETTE["text"]),
        margin=dict(t=50,b=20,l=10,r=70),
        hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
    )
    fig4.update_xaxes(gridcolor="#EEF2F7")
    st.plotly_chart(fig4, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Impacto tiempo envio + comportamiento dispositivo ────
col5, col6 = st.columns(2)

with col5:
    df_ship = query(f"""
        SELECT shipping_time_days,
               ROUND(AVG(rating)::numeric, 2) AS avg_rating,
               COUNT(*) AS ordenes
        FROM analytics.fact_orders {where_cli}
        GROUP BY shipping_time_days ORDER BY shipping_time_days
    """)
    fig5 = go.Figure()
    fig5.add_trace(go.Scatter(
        x=df_ship["shipping_time_days"], y=df_ship["avg_rating"],
        mode="lines+markers",
        line=dict(color=PALETTE["accent"], width=2.5, shape="spline"),
        marker=dict(size=7, color=PALETTE["accent"], line=dict(color="white", width=1.5)),
        fill="tozeroy", fillcolor="rgba(255,153,0,0.07)",
        customdata=df_ship[["ordenes"]].values,
        hovertemplate="<b>%{x} días</b><br>Rating: %{y:.2f}<br>Órdenes: %{customdata[0]:,}<extra></extra>",
    ))
    fig5.update_layout(
        title=dict(text="Impacto del Tiempo de Envío en el Rating", font=dict(color="#6B7A8D", size=13)),
        plot_bgcolor="white", paper_bgcolor="white", height=300,
        font=dict(family=FONT, color=PALETTE["text"]),
        margin=dict(t=50,b=40,l=10,r=10),
        xaxis=dict(title="Días de envío", gridcolor="#EEF2F7"),
        yaxis=dict(title="Rating promedio", gridcolor="#EEF2F7"),
        showlegend=False,
        hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
    )
    st.plotly_chart(fig5, use_container_width=True)

with col6:
    df_dev = query(f"""
        SELECT device, COUNT(*) AS ordenes,
               ROUND(AVG(rating)::numeric, 2) AS avg_rating,
               ROUND(AVG(final_price)::numeric, 0) AS ticket_prom,
               ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)*100,1) AS tasa_dev
        FROM analytics.fact_orders {where_cli}
        GROUP BY device ORDER BY ordenes DESC
    """)
    fig6 = go.Figure()
    fig6.add_trace(go.Bar(
        x=df_dev["device"], y=df_dev["ordenes"],
        name="Órdenes", marker_color=PALETTE["primary_light"],
        yaxis="y",
        customdata=df_dev[["ticket_prom","tasa_dev"]].values,
        hovertemplate="<b>%{x}</b><br>Órdenes: %{y:,}<br>Ticket: ₹%{customdata[0]:,.0f}<br>Dev: %{customdata[1]}%<extra></extra>",
    ))
    fig6.add_trace(go.Scatter(
        x=df_dev["device"], y=df_dev["avg_rating"],
        name="Rating", mode="lines+markers",
        line=dict(color=PALETTE["accent"], width=2),
        marker=dict(size=8), yaxis="y2",
        hovertemplate="<b>%{x}</b><br>Rating: %{y:.2f}<extra></extra>",
    ))
    fig6.update_layout(
        title=dict(text="Comportamiento por Dispositivo", font=dict(color="#6B7A8D", size=13)),
        plot_bgcolor="white", paper_bgcolor="white", height=300,
        font=dict(family=FONT, color=PALETTE["text"]),
        margin=dict(t=50,b=40,l=10,r=60),
        yaxis=dict(title="Órdenes", gridcolor="#EEF2F7"),
        yaxis2=dict(title="Rating", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", y=1.1),
        hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
    )
    st.plotly_chart(fig6, use_container_width=True)