"""
Pagina de Analisis de Vendedores - RF6.
"""

import pandas as pd
import streamlit as st
import plotly.express as px

from utils.db import query
from utils.downloads import download_dataframe
from utils.filters import render_filters
from utils.style import kpi_card, PALETTE, PLOTLY_COLORS, FONT


filters = render_filters(extra_filters=[])
where_vend = filters["where"]
params = dict(filters["params"])


def load_seller_options():
    sellers = query(
        f"""
        SELECT DISTINCT seller_id
        FROM analytics.fact_orders {where_vend}
        ORDER BY seller_id
        """,
        params,
    )
    return sellers["seller_id"].dropna().tolist()


sellers = load_seller_options()

with st.expander("Filtros de Vendedores", expanded=False):
    vc = st.columns(2)
    with vc[0]:
        sel_vendedor = st.selectbox("Vendedor", ["Todos"] + sellers, key="vend_sel")
    with vc[1]:
        min_ordenes = st.slider("Minimo de ordenes por vendedor", 1, 100, 1, key="vend_min_ord")

if sel_vendedor != "Todos":
    params["seller_id"] = sel_vendedor
    where_vend = where_vend.replace("WHERE ", "WHERE seller_id = :seller_id AND ", 1)

params_rank = dict(params)
params_rank["min_ordenes"] = min_ordenes

df_export = query(
    f"""
    SELECT purchase_date, seller_id, category, brand, final_price,
           seller_rating, rating, is_returned, delivery_status
    FROM analytics.fact_orders {where_vend}
    ORDER BY purchase_date DESC
    """,
    params,
)
download_dataframe(
    df_export,
    "vendedores_ordenes_filtradas.csv",
    "Descargar ordenes filtradas de vendedores",
    "vendedores_export_csv",
)

kpis = query(
    f"""
    SELECT COUNT(DISTINCT seller_id) AS total_vend,
           ROUND(AVG(seller_rating)::numeric, 2) AS avg_s_rating,
           ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 1) AS avg_ret
    FROM analytics.fact_orders {where_vend}
    """,
    params,
)
avg_ingreso = query(
    f"""
    SELECT ROUND(AVG(ingresos)::numeric, 0) AS v
    FROM (
        SELECT seller_id, SUM(final_price) AS ingresos
        FROM analytics.fact_orders {where_vend}
        GROUP BY seller_id
    ) t
    """,
    params,
)["v"].iloc[0]


def fmt_rev(v):
    if pd.isna(v):
        return "0"
    if v >= 1_000_000_000:
        return f"₹{v/1_000_000_000:.1f}B"
    if v >= 1_000_000:
        return f"₹{v/1_000_000:.1f}M"
    return f"₹{v:,.0f}"


ICON_STORE = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>'
ICON_STAR = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>'
ICON_RET = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>'
ICON_TICKET = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>'

c1, c2, c3, c4 = st.columns(4)
c1.markdown(kpi_card("Vendedores Activos", f"{int(kpis['total_vend'].iloc[0] or 0):,}", None, ICON_STORE, "Total de vendedores con al menos una orden en el periodo."), unsafe_allow_html=True)
c2.markdown(kpi_card("Rating Prom. Vendedores", str(kpis["avg_s_rating"].iloc[0]), None, ICON_STAR, "Calificacion promedio de vendedores, escala 1 a 5."), unsafe_allow_html=True)
c3.markdown(kpi_card("Tasa Dev. Global", f"{kpis['avg_ret'].iloc[0]}%", None, ICON_RET, "% de ordenes devueltas en el periodo."), unsafe_allow_html=True)
c4.markdown(kpi_card("Ingreso Prom. Vendedor", fmt_rev(avg_ingreso), None, ICON_TICKET, "Ingreso promedio por vendedor en el periodo."), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

df_rank = query(
    f"""
    SELECT seller_id, COUNT(*) AS ordenes,
           ROUND(SUM(final_price)::numeric, 0) AS ingresos,
           ROUND(AVG(final_price)::numeric, 0) AS ticket_prom,
           ROUND(AVG(seller_rating)::numeric, 2) AS rating_vendedor,
           ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 1) AS tasa_dev
    FROM analytics.fact_orders {where_vend}
    GROUP BY seller_id
    HAVING COUNT(*) >= :min_ordenes
    ORDER BY ingresos DESC
    LIMIT 50
    """,
    params_rank,
)

if df_rank.empty:
    st.info("No hay vendedores para los filtros seleccionados. Baja el minimo de ordenes o limpia filtros.")
else:
    display = df_rank.copy()
    display["ingresos"] = display["ingresos"].apply(fmt_rev)
    display["ticket_prom"] = display["ticket_prom"].apply(fmt_rev)
    display["tasa_dev"] = display["tasa_dev"].apply(lambda v: f"{v:.1f}%")
    display["ordenes"] = display["ordenes"].apply(lambda v: f"{v:,}")
    display = display.rename(columns={
        "seller_id": "Vendedor",
        "ordenes": "Ordenes",
        "ingresos": "Ingresos",
        "ticket_prom": "Ticket Prom.",
        "rating_vendedor": "Rating",
        "tasa_dev": "Dev %",
    })
    st.dataframe(display, use_container_width=True, height=380)

st.markdown("<br>", unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    if df_rank.empty:
        st.info("Sin datos para rating vs devolucion con los filtros actuales.")
    else:
        fig1 = px.scatter(
            df_rank,
            x="rating_vendedor",
            y="tasa_dev",
            size="ordenes",
            color="ingresos",
            color_continuous_scale=[[0, PALETTE["lighter"]], [0.5, PALETTE["primary_light"]], [1, PALETTE["primary"]]],
            title="Rating vs Devolucion por Vendedor",
            labels={"rating_vendedor": "Rating", "tasa_dev": "Dev (%)", "ordenes": "Ordenes"},
            hover_data={"seller_id": True, "ingresos": ":,.0f"},
        )
        fig1.update_layout(
            title=dict(font=dict(color="#6B7A8D", size=13)),
            plot_bgcolor="white",
            paper_bgcolor="white",
            height=380,
            font=dict(family=FONT, color=PALETTE["text"]),
            margin=dict(t=50, b=40, l=10, r=10),
            hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
        )
        fig1.update_yaxes(gridcolor="#EEF2F7")
        fig1.update_xaxes(gridcolor="#EEF2F7")
        st.plotly_chart(fig1, use_container_width=True)

with col2:
    df_cats = query(
        f"""
        WITH filtered_orders AS (
            SELECT *
            FROM analytics.fact_orders {where_vend}
        ),
        category_sellers AS (
            SELECT seller_id,
                   category,
                   COUNT(*) AS total_orders,
                   ROUND(SUM(final_price)::numeric, 0) AS total_revenue,
                   ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 1) AS return_rate,
                   ROW_NUMBER() OVER (
                       PARTITION BY category
                       ORDER BY SUM(final_price) DESC
                   ) AS category_rank
            FROM filtered_orders
            GROUP BY seller_id, category
            HAVING COUNT(*) >= :min_ordenes
        )
        SELECT seller_id, category, total_orders, total_revenue, return_rate
        FROM category_sellers
        WHERE category_rank <= 10
        ORDER BY category, total_revenue DESC
        """,
        params_rank,
    )
    if df_cats.empty:
        st.info("Sin categorias por vendedor para los filtros actuales.")
    else:
        fig2 = px.bar(
            df_cats,
            x="total_revenue",
            y="seller_id",
            color="category",
            color_discrete_sequence=PLOTLY_COLORS,
            title="Categorias por Vendedor (Top 10 por Categoria)",
            labels={"total_revenue": "Ingresos", "seller_id": "Vendedor", "category": "Categoria"},
        )
        fig2.update_layout(
            title=dict(font=dict(color="#6B7A8D", size=13)),
            plot_bgcolor="white",
            paper_bgcolor="white",
            height=380,
            font=dict(family=FONT, color=PALETTE["text"]),
            margin=dict(t=50, b=20, l=10, r=10),
            legend=dict(orientation="h", y=1.08),
            hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
        )
        fig2.update_xaxes(gridcolor="#EEF2F7")
        st.plotly_chart(fig2, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

df_worst = query(
    f"""
    SELECT seller_id, COUNT(*) AS ordenes,
           ROUND(SUM(final_price)::numeric, 0) AS ingresos,
           ROUND(AVG(seller_rating)::numeric, 2) AS rating_vendedor,
           ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 1) AS tasa_dev
    FROM analytics.fact_orders {where_vend}
    GROUP BY seller_id
    HAVING COUNT(*) >= :min_ordenes
    ORDER BY tasa_dev DESC
    LIMIT 15
    """,
    params_rank,
)
if df_worst.empty:
    st.info("Sin vendedores con devoluciones para los filtros actuales.")
else:
    df_worst["label"] = df_worst["tasa_dev"].apply(lambda v: f"{v:.1f}%")
    fig3 = px.bar(
        df_worst,
        x="seller_id",
        y="tasa_dev",
        text="label",
        color_discrete_sequence=[PALETTE["danger"]],
        title="Top 15 Vendedores con Mayor Tasa de Devolucion (%)",
        labels={"tasa_dev": "Dev (%)", "seller_id": "Vendedor"},
        custom_data=["ordenes", "rating_vendedor", "ingresos"],
    )
    fig3.update_traces(
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Dev: %{y:.1f}%<br>Ordenes: %{customdata[0]:,}<br>Rating: %{customdata[1]:.2f}<br>Ingresos: ₹%{customdata[2]:,.0f}<extra></extra>",
    )
    fig3.update_layout(
        title=dict(font=dict(color="#6B7A8D", size=13)),
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=320,
        font=dict(family=FONT, color=PALETTE["text"]),
        margin=dict(t=50, b=60, l=10, r=10),
        xaxis_tickangle=-45,
        hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
    )
    fig3.update_yaxes(gridcolor="#EEF2F7")
    st.plotly_chart(fig3, use_container_width=True)
