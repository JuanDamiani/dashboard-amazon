"""
Pagina de Analisis de Vendedores — RF6.

Filtros locales (en "Más filtros"): vendedor y minimo de ordenes por vendedor.
La categoria se filtra con el filtro global. Color: azul institucional; rojo solo
para el de peor desempeño (mayor devolucion).
"""

import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import timedelta

from utils.db import query
from utils.filters import render_filters
from utils.style import kpi_card, chart_header, PALETTE, PLOTLY_COLORS, FONT

# ── FILTROS: globales + locales (vendedor, min_ordenes) — RF6 ──
filters     = render_filters(extra_filters=["vendedor", "min_ordenes"])
where_vend  = filters["where"]
params      = dict(filters["params"])
min_ordenes = filters["min_ordenes"]

params_rank = dict(params)
params_rank["min_ordenes"] = min_ordenes


def previous_period_params(filters, current_params):
    fecha_inicio = filters["fecha_inicio"]
    fecha_fin = filters["fecha_fin"]
    period_days = max((fecha_fin - fecha_inicio).days, 0)
    prev_fin = fecha_inicio - timedelta(days=1)
    prev_inicio = prev_fin - timedelta(days=period_days)
    pp = dict(current_params)
    pp["fecha_inicio"] = prev_inicio
    pp["fecha_fin"] = prev_fin
    return pp


def pct_delta_val(cur, prev):
    try:
        if pd.isna(cur) or pd.isna(prev) or float(prev) == 0:
            return None
        return ((float(cur) - float(prev)) / abs(float(prev))) * 100
    except Exception:
        return None


def fmt_rev(v):
    if pd.isna(v):
        return "0"
    if v >= 1_000_000_000:
        return f"₹{v/1_000_000_000:.1f}B"
    if v >= 1_000_000:
        return f"₹{v/1_000_000:.1f}M"
    return f"₹{v:,.0f}"


def highlight_max(values, normal=PALETTE["primary"], alert=PALETTE["danger"]):
    vals = [v for v in values if pd.notna(v)]
    if not vals:
        return [normal] * len(values)
    mx = max(vals)
    return [alert if (pd.notna(v) and v == mx) else normal for v in values]


# ── KPIs (con variación vs período anterior) ─────────────
KPIS_SQL = f"""
    SELECT COUNT(DISTINCT seller_id) AS total_vend,
           ROUND(AVG(seller_rating)::numeric, 2) AS avg_s_rating,
           ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 1) AS avg_ret
    FROM analytics.fact_orders {where_vend}
"""
ING_SQL = f"""
    SELECT ROUND(AVG(ingresos)::numeric, 0) AS v
    FROM (
        SELECT seller_id, SUM(final_price) AS ingresos
        FROM analytics.fact_orders {where_vend}
        GROUP BY seller_id
    ) t
"""
prev_params = previous_period_params(filters, params)

kpis             = query(KPIS_SQL, params)
prev_kpis        = query(KPIS_SQL, prev_params)
avg_ingreso      = query(ING_SQL, params)["v"].iloc[0]
prev_avg_ingreso = query(ING_SQL, prev_params)["v"].iloc[0]

d_vend   = pct_delta_val(kpis["total_vend"].iloc[0],   prev_kpis["total_vend"].iloc[0])
d_rating = pct_delta_val(kpis["avg_s_rating"].iloc[0], prev_kpis["avg_s_rating"].iloc[0])
d_ret    = pct_delta_val(kpis["avg_ret"].iloc[0],      prev_kpis["avg_ret"].iloc[0])
d_ing    = pct_delta_val(avg_ingreso,                  prev_avg_ingreso)

ICON_STORE  = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>'
ICON_STAR   = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>'
ICON_RET    = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>'
ICON_TICKET = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>'

c1, c2, c3, c4 = st.columns(4)
c1.markdown(kpi_card("Vendedores Activos",     f"{int(kpis['total_vend'].iloc[0] or 0):,}", d_vend,   ICON_STORE,  "Total de vendedores con al menos una orden en el período. Subir es bueno.", invert=False), unsafe_allow_html=True)
c2.markdown(kpi_card("Rating Prom. Vendedores", str(kpis["avg_s_rating"].iloc[0]),          d_rating, ICON_STAR,   "Calificación promedio de vendedores, escala 1 a 5. Subir es bueno.", invert=False), unsafe_allow_html=True)
c3.markdown(kpi_card("Tasa Dev. Global",        f"{kpis['avg_ret'].iloc[0]}%",              d_ret,    ICON_RET,    "% de órdenes devueltas en el período. Subir es malo.", invert=True), unsafe_allow_html=True)
c4.markdown(kpi_card("Ingreso Prom. Vendedor",  fmt_rev(avg_ingreso),                       d_ing,    ICON_TICKET, "Ingreso promedio por vendedor en el período. Subir es bueno.", invert=False), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

LAYOUT = dict(
    plot_bgcolor="white", paper_bgcolor="white",
    font=dict(family=FONT, color=PALETTE["text"]),
    hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
)

# ── Ranking de vendedores (RF6: ingresos y cantidad de órdenes) ──
df_rank = query(f"""
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
""", params_rank)

with st.container(key="chartcard_vend_rank"):
    if df_rank.empty:
        st.info("No hay vendedores para los filtros seleccionados. Bajá el mínimo de órdenes o limpiá filtros.")
    else:
        chart_header("Ranking de Vendedores — Top 50 por Ingresos", df_rank,
                     "ranking_vendedores.csv", "exp_vend_rank", ratio=(24, 1),
                     info="Top 50 vendedores ordenados por ingresos. Muestra órdenes, ingresos, ticket promedio, rating y tasa de devolución de cada uno. Podés ordenar por cualquier columna haciendo clic en su encabezado.")
        display = df_rank.copy()
        display["ingresos"]    = display["ingresos"].apply(fmt_rev)
        display["ticket_prom"] = display["ticket_prom"].apply(fmt_rev)
        display["tasa_dev"]    = display["tasa_dev"].apply(lambda v: f"{v:.1f}%")
        display["ordenes"]     = display["ordenes"].apply(lambda v: f"{v:,}")
        display = display.rename(columns={
            "seller_id": "Vendedor", "ordenes": "Órdenes", "ingresos": "Ingresos",
            "ticket_prom": "Ticket Prom.", "rating_vendedor": "Rating", "tasa_dev": "Dev %",
        })
        st.dataframe(display, use_container_width=True, height=380)

st.markdown("<br>", unsafe_allow_html=True)

# ── Rating vs Devolución + Categorías por vendedor ───────
col1, col2 = st.columns(2)

with col1:
    with st.container(key="chartcard_vend_scatter"):
        if df_rank.empty:
            st.info("Sin datos para rating vs devolución con los filtros actuales.")
        else:
            chart_header("Rating vs Devolución por Vendedor", df_rank,
                         "rating_vs_devolucion_vendedor.csv", "exp_vend_scatter", ratio=(18, 1),
                         info="Cada punto es un vendedor: eje X = rating, eje Y = tasa de devolución, tamaño = órdenes, color = ingresos. Sirve para identificar perfiles: arriba-izquierda (bajo rating, alta devolución) son los problemáticos; abajo-derecha (alto rating, baja devolución) los mejores.")
            fig1 = px.scatter(
                df_rank, x="rating_vendedor", y="tasa_dev", size="ordenes", color="ingresos",
                color_continuous_scale=[[0, PALETTE["lighter"]], [0.5, PALETTE["primary_light"]], [1, PALETTE["primary"]]],
                labels={"rating_vendedor": "Rating", "tasa_dev": "Dev (%)", "ordenes": "Órdenes"},
                hover_data={"seller_id": True, "ingresos": ":,.0f"},
            )
            fig1.update_layout(**dict(LAYOUT, height=380), margin=dict(t=10, b=40, l=10, r=10))
            fig1.update_yaxes(gridcolor="#EEF2F7")
            fig1.update_xaxes(gridcolor="#EEF2F7")
            st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

with col2:
    with st.container(key="chartcard_vend_cats"):
        df_cats = query(f"""
            WITH filtered AS (
                SELECT * FROM analytics.fact_orders {where_vend}
            ),
            top_sellers AS (
                SELECT seller_id FROM filtered
                GROUP BY seller_id
                HAVING COUNT(*) >= :min_ordenes
                ORDER BY SUM(final_price) DESC
                LIMIT 10
            )
            SELECT f.seller_id, f.category,
                   ROUND(SUM(f.final_price)::numeric, 0) AS ingresos
            FROM filtered f
            JOIN top_sellers t ON f.seller_id = t.seller_id
            GROUP BY f.seller_id, f.category
        """, params_rank)
        if df_cats.empty:
            st.info("Sin categorías por vendedor para los filtros actuales.")
        else:
            chart_header("Mix de Categorías por Vendedor (Top 10)", df_cats,
                         "mix_categorias_vendedor.csv", "exp_vend_cats", ratio=(18, 1),
                         info="Mapa de calor: para cada vendedor (fila), qué % de sus ingresos viene de cada categoría. Azul más oscuro = más concentrado ahí. Permite ver de un vistazo si el vendedor está especializado o diversificado.")
            pivot = df_cats.pivot(index="seller_id", columns="category", values="ingresos").fillna(0)
            pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=False).index]
            share = pivot.div(pivot.sum(axis=1), axis=0).mul(100)
            fig2 = px.imshow(
                share, aspect="auto", text_auto=".0f",
                color_continuous_scale=["#EAF1F8", PALETTE["primary_light"], PALETTE["primary"]],
                labels=dict(x="Categoría", y="Vendedor", color="% ingresos"),
            )
            fig2.update_traces(
                texttemplate="%{z:.0f}%",
                hovertemplate="<b>%{y}</b><br>%{x}: %{z:.0f}% de sus ingresos<extra></extra>",
            )
            fig2.update_layout(
                **dict(LAYOUT, height=380), margin=dict(t=10, b=20, l=10, r=10),
                coloraxis_colorbar=dict(title="% ing.", thickness=12, len=0.6, tickfont=dict(size=10)),
            )
            fig2.update_xaxes(side="bottom")
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

st.markdown("<br>", unsafe_allow_html=True)

# ── Top 15 con mayor tasa de devolución ──────────────────
df_worst = query(f"""
    SELECT seller_id, COUNT(*) AS ordenes,
           ROUND(SUM(final_price)::numeric, 0) AS ingresos,
           ROUND(AVG(seller_rating)::numeric, 2) AS rating_vendedor,
           ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 1) AS tasa_dev
    FROM analytics.fact_orders {where_vend}
    GROUP BY seller_id
    HAVING COUNT(*) >= :min_ordenes
    ORDER BY tasa_dev DESC
    LIMIT 15
""", params_rank)

with st.container(key="chartcard_vend_worst"):
    if df_worst.empty:
        st.info("Sin vendedores con devoluciones para los filtros actuales.")
    else:
        chart_header("Top 15 Vendedores con Mayor Tasa de Devolución (%)", df_worst,
                     "top15_devolucion_vendedores.csv", "exp_vend_worst", ratio=(24, 1),
                     info="Los 15 vendedores con mayor tasa de devolución (devueltas / total). Es una watchlist de los perfiles que más problemas de devolución generan. En rojo el peor.")
        df_worst["label"] = df_worst["tasa_dev"].apply(lambda v: f"{v:.1f}%")
        fig3 = px.bar(
            df_worst, x="seller_id", y="tasa_dev", text="label",
            labels={"tasa_dev": "Dev (%)", "seller_id": "Vendedor"},
            custom_data=["ordenes", "rating_vendedor", "ingresos"],
        )
        fig3.update_traces(
            marker_color=highlight_max(df_worst["tasa_dev"]),
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>Dev: %{y:.1f}%<br>Órdenes: %{customdata[0]:,}<br>Rating: %{customdata[1]:.2f}<br>Ingresos: ₹%{customdata[2]:,.0f}<extra></extra>",
        )
        fig3.update_layout(
            **dict(LAYOUT, height=320), margin=dict(t=20, b=60, l=10, r=10),
            xaxis_tickangle=-45,
        )
        fig3.update_yaxes(gridcolor="#EEF2F7")
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})