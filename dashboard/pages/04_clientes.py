"""
Pagina de Experiencia del Cliente — RF5
Todos los indicadores responden a los filtros globales + rango de rating.

Color: rating = azul (un valor alto es bueno, no una alerta); la tasa de
devolucion (metrica "mala") va en rojo.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from utils.db import query
from utils.filters import render_filters
from utils.style import kpi_card, chart_header, PALETTE, FONT

# ── FILTROS: globales + local (rating) — RF5 ─────────────
filters   = render_filters(extra_filters=["rating"])
where_cli = filters["where_rating"]   # ya incluye el rango de rating
params    = filters["params_rating"]

# ── KPIs ─────────────────────────────────────────────────
kpis_cli = query(f"""
    SELECT
        ROUND(AVG(rating)::numeric, 2) AS avg_rating,
        ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 1) AS ret_rate,
        COUNT(*) AS total_ord,
        ROUND(AVG(final_price)::numeric, 0) AS avg_ticket
    FROM analytics.fact_orders {where_cli}
""", params)
avg_rating = kpis_cli["avg_rating"].iloc[0]
ret_rate   = kpis_cli["ret_rate"].iloc[0]
total_ord  = kpis_cli["total_ord"].iloc[0]
avg_ticket = kpis_cli["avg_ticket"].iloc[0]


def fmt_num(v):
    if v >= 1_000_000: return f"{v/1_000_000:.1f}M"
    if v >= 1_000:     return f"{v/1_000:.1f}k"
    return f"{v:,.0f}"


ICON_STAR   = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>'
ICON_RET    = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>'
ICON_BOX    = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><path d="M20 7H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>'
ICON_TICKET = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v2z"/></svg>'

c1, c2, c3, c4 = st.columns(4)
c1.markdown(kpi_card("Rating Promedio",  str(avg_rating),       None, ICON_STAR,   "Calificación promedio de productos, escala 1 a 5."), unsafe_allow_html=True)
c2.markdown(kpi_card("Tasa Devolución",  f"{ret_rate}%",        None, ICON_RET,    "% de órdenes devueltas en el período."), unsafe_allow_html=True)
c3.markdown(kpi_card("Total Órdenes",    fmt_num(total_ord),    None, ICON_BOX,    "Órdenes en el rango de rating seleccionado."), unsafe_allow_html=True)
c4.markdown(kpi_card("Ticket Promedio",  f"₹{avg_ticket:,.0f}", None, ICON_TICKET, "Ingreso promedio por orden en INR."), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

LAYOUT = dict(
    plot_bgcolor="white", paper_bgcolor="white", height=300,
    font=dict(family=FONT, color=PALETTE["text"]),
    hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
)

# ── Distribución de ratings (filtrada) ───────────────────
col1, col2 = st.columns(2)

with col1:
    with st.container(key="chartcard_cli_dist"):
        df_dist = query(f"""
            SELECT rating,
                   COUNT(*) AS total_orders,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS order_share_pct
            FROM analytics.fact_orders {where_cli}
            GROUP BY rating ORDER BY rating
        """, params)
        chart_header("Distribución de Órdenes por Rating", df_dist, "distribucion_rating.csv", "exp_cli_dist",
                     ratio=(18, 1),
                     info="Cantidad de órdenes por cada valor de rating (1 a 5) y su porcentaje sobre el total. Muestra cómo se reparten las calificaciones de los clientes.")
        fig1 = px.bar(df_dist, x="rating", y="total_orders", text="order_share_pct",
                      color_discrete_sequence=[PALETTE["primary_light"]],
                      labels={"total_orders": "Órdenes", "rating": "Rating"})
        fig1.update_traces(
            texttemplate="%{text:.1f}%", textposition="outside",
            hovertemplate="<b>Rating %{x}</b><br>Órdenes: %{y:,}<br>% del total: %{text:.1f}%<extra></extra>",
        )
        fig1.update_layout(**LAYOUT, margin=dict(t=25, b=40, l=10, r=10))
        fig1.update_yaxes(gridcolor="#EEF2F7")
        st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})

with col2:
    with st.container(key="chartcard_cli_range"):
        df_range = query(f"""
            SELECT CASE WHEN rating >= 4 THEN '4-5'
                        WHEN rating >= 3 THEN '3-4'
                        WHEN rating >= 2 THEN '2-3'
                        ELSE '1-2' END AS rating_range,
                   COUNT(*) AS total_orders,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS order_share_pct,
                   ROUND(AVG(rating)::numeric, 2) AS avg_rating,
                   ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100, 1) AS return_rate
            FROM analytics.fact_orders {where_cli}
            GROUP BY 1 ORDER BY 1
        """, params)
        chart_header("Órdenes por Rango de Rating (%)", df_range, "ordenes_rango_rating.csv", "exp_cli_range",
                     ratio=(18, 1),
                     info="Órdenes agrupadas en rangos de rating (1-2, 2-3, 3-4, 4-5) y su porcentaje del total. Resume la distribución en bloques; el hover muestra rating y devolución promedio de cada rango.")
        fig2 = px.bar(df_range, x="order_share_pct", y="rating_range", orientation="h",
                      text="order_share_pct",
                      color_discrete_sequence=[PALETTE["primary"]],
                      custom_data=["avg_rating", "return_rate", "total_orders"],
                      labels={"order_share_pct": "% del total", "rating_range": ""})
        fig2.update_traces(
            texttemplate="%{text:.1f}%", textposition="outside",
            hovertemplate="<b>%{y}</b><br>% órdenes: %{x:.1f}%<br>Rating prom: %{customdata[0]}<br>Dev: %{customdata[1]}%<br>Órdenes: %{customdata[2]:,}<extra></extra>",
        )
        fig2.update_layout(**LAYOUT, margin=dict(t=10, b=20, l=10, r=50))
        fig2.update_xaxes(gridcolor="#EEF2F7")
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

st.markdown("<br>", unsafe_allow_html=True)

# ── Rating y devolucion por categoria (ancho completo) ───
with st.container(key="chartcard_cli_cat"):
    df_cat = query(f"""
        SELECT category,
               ROUND(AVG(rating)::numeric, 2) AS avg_rating,
               ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)*100,1) AS tasa_dev,
               COUNT(*) AS ordenes
        FROM analytics.fact_orders {where_cli}
        GROUP BY category ORDER BY avg_rating DESC
    """, params)
    chart_header("Rating y Devolución por Categoría", df_cat, "rating_devolucion_categoria.csv", "exp_cli_cat",
                 ratio=(24, 1),
                 info="Rating promedio (barras azules) y tasa de devolución (línea roja) por categoría. Permite ver si las categorías peor calificadas son también las que más se devuelven.")
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(
        x=df_cat["category"], y=df_cat["avg_rating"],
        name="Rating promedio", marker_color=PALETTE["primary_light"],
        text=df_cat["avg_rating"], textposition="outside",
    ))
    fig3.add_trace(go.Scatter(
        x=df_cat["category"], y=df_cat["tasa_dev"],
        name="Dev %", mode="lines+markers",
        line=dict(color=PALETTE["danger"], width=2),
        marker=dict(size=7), yaxis="y2",
    ))
    fig3.update_layout(
        **dict(LAYOUT, height=340), margin=dict(t=30, b=40, l=10, r=60),
        yaxis=dict(title="Rating", gridcolor="#EEF2F7"),
        yaxis2=dict(title="Dev %", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", y=1.12),
    )
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

st.markdown("<br>", unsafe_allow_html=True)

# ── Impacto tiempo envio + comportamiento dispositivo ────
col5, col6 = st.columns(2)

with col5:
    with st.container(key="chartcard_cli_ship"):
        df_ship = query(f"""
            SELECT shipping_time_days,
                   ROUND(AVG(rating)::numeric, 2) AS avg_rating,
                   COUNT(*) AS ordenes
            FROM analytics.fact_orders {where_cli}
            GROUP BY shipping_time_days ORDER BY shipping_time_days
        """, params)
        chart_header("Impacto del Tiempo de Envío en el Rating", df_ship, "impacto_envio_rating.csv", "exp_cli_ship",
                     ratio=(18, 1),
                     info="Rating promedio según los días que tardó el envío. Ayuda a ver si los envíos más lentos bajan la satisfacción del cliente.")
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
            **LAYOUT, margin=dict(t=20, b=40, l=10, r=10),
            xaxis=dict(title="Días de envío", gridcolor="#EEF2F7"),
            yaxis=dict(title="Rating promedio", gridcolor="#EEF2F7"),
            showlegend=False,
        )
        st.plotly_chart(fig5, use_container_width=True, config={"displayModeBar": False})

with col6:
    with st.container(key="chartcard_cli_dev"):
        df_dev = query(f"""
            SELECT device, COUNT(*) AS ordenes,
                   ROUND(AVG(rating)::numeric, 2) AS avg_rating,
                   ROUND(AVG(final_price)::numeric, 0) AS ticket_prom,
                   ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)*100,1) AS tasa_dev
            FROM analytics.fact_orders {where_cli}
            GROUP BY device ORDER BY ordenes DESC
        """, params)
        chart_header("Comportamiento por Dispositivo", df_dev, "comportamiento_dispositivo.csv", "exp_cli_dev",
                     ratio=(18, 1),
                     info="Órdenes (barras) y rating promedio (línea) por dispositivo. Compara volumen de compra y satisfacción entre los distintos dispositivos.")
        fig6 = go.Figure()
        fig6.add_trace(go.Bar(
            x=df_dev["device"], y=df_dev["ordenes"],
            name="Órdenes", marker_color=PALETTE["primary_light"], yaxis="y",
            customdata=df_dev[["ticket_prom", "tasa_dev"]].values,
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
            **LAYOUT, margin=dict(t=30, b=40, l=10, r=60),
            yaxis=dict(title="Órdenes", gridcolor="#EEF2F7"),
            yaxis2=dict(title="Rating", overlaying="y", side="right", showgrid=False),
            legend=dict(orientation="h", y=1.12),
        )
        st.plotly_chart(fig6, use_container_width=True, config={"displayModeBar": False})

st.markdown("<br>", unsafe_allow_html=True)

# ── Distribución geográfica de la satisfacción — RF5 ─────
with st.container(key="chartcard_cli_map"):
    df_map = query(f"""
        SELECT location,
               ROUND(AVG(rating)::numeric, 2) AS avg_rating,
               ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)*100,1) AS tasa_dev,
               COUNT(*) AS ordenes
        FROM analytics.fact_orders {where_cli}
        GROUP BY location
    """, params)
    chart_header("Satisfacción por Ciudad — Mapa", df_map, "satisfaccion_geografica.csv", "exp_cli_map",
                 ratio=(24, 1),
                 info="Mapa de ciudades: el tamaño del punto es el volumen de órdenes y el color el rating promedio (azul más oscuro = clientes más satisfechos).")

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
        df_map, lat="lat", lon="lon", size="ordenes", color="avg_rating",
        hover_name="location",
        color_continuous_scale=["#D6EAF8", PALETTE["primary_light"], PALETTE["primary"]],
        custom_data=["avg_rating", "tasa_dev", "ordenes"],
        labels={"avg_rating": "Rating"},
    )
    fig_map.update_traces(
        mode="markers+text",
        text=df_map["avg_rating"].map(lambda v: f"{v:.2f}"),
        textposition="top center",
        textfont=dict(size=11, color=PALETTE["text"], family=FONT),
        hovertemplate="<b>%{hovertext}</b><br>Rating: %{customdata[0]:.2f}<br>Dev: %{customdata[1]:.1f}%<br>Órdenes: %{customdata[2]:,}<extra></extra>",
        marker=dict(sizemin=15, line=dict(color="white", width=1.5)),
    )
    fig_map.update_geos(
        scope="asia", center=dict(lat=20, lon=78), projection_scale=3.5,
        showland=True, landcolor="#F5F7FA",
        showocean=True, oceancolor="#EEF2F7", showlakes=False,
        showcountries=True, countrycolor="#D6E0EA",
        showcoastlines=True, coastlinecolor="#D6E0EA", bgcolor="white",
    )
    fig_map.update_layout(
        plot_bgcolor="white", paper_bgcolor="white", height=420,
        font=dict(family=FONT, color=PALETTE["text"]),
        margin=dict(t=10, b=10, l=0, r=0),
        coloraxis_colorbar=dict(title="Rating", thickness=12, len=0.6, tickfont=dict(size=10)),
        hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=12)),
    )
    st.plotly_chart(fig_map, use_container_width=True, config={"displayModeBar": False})