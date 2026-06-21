"""
Overview — RF1
"""

from datetime import timedelta

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from utils.db import query
from utils.downloads import download_dataframe
from utils.filters import render_filters
from utils.style import kpi_card, PALETTE, PLOTLY_COLORS, FONT

# ── FILTROS (solo globales, RF1) ─────────────────────────
filters      = render_filters(extra_filters=[])
where        = filters["where"]
where_rating = filters["where_rating"]
params       = filters["params"]

df_export = query(f"""
    SELECT purchase_date, category, location, device, payment_method,
           delivery_status, final_price, rating, is_returned, seller_id
    FROM analytics.fact_orders {where}
    ORDER BY purchase_date DESC
""", params)
download_dataframe(
    df_export,
    "overview_ordenes_filtradas.csv",
    "Descargar ordenes filtradas del overview",
    "overview_export_csv",
)

# ── KPIs ─────────────────────────────────────────────────
kpis = query(f"""
    SELECT ROUND(SUM(final_price)::numeric, 0) AS total_revenue,
           COUNT(*) AS total_orders,
           ROUND(AVG(final_price)::numeric, 0) AS avg_ticket,
           ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 1) AS return_rate,
           ROUND(AVG(rating)::numeric, 2) AS avg_rating
    FROM analytics.fact_orders {where}
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
prev_kpis = query(f"""
    SELECT ROUND(SUM(final_price)::numeric, 0) AS total_revenue,
           COUNT(*) AS total_orders,
           ROUND(AVG(final_price)::numeric, 0) AS avg_ticket,
           ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 1) AS return_rate,
           ROUND(AVG(rating)::numeric, 2) AS avg_rating
    FROM analytics.fact_orders {where}
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

ICONS = {
    "revenue": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5" stroke-linecap="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
    "orders":  '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5" stroke-linecap="round"><path d="M20 7H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
    "ticket":  '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5" stroke-linecap="round"><path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v2z"/></svg>',
    "return":  '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5" stroke-linecap="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>',
    "rating":  '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5" stroke-linecap="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
}

c1, c2, c3, c4, c5 = st.columns(5)
c1.markdown(kpi_card("Ingresos Totales", fmt_rev(kpis["total_revenue"].iloc[0]),  pct_delta(kpis, prev_kpis, "total_revenue"), ICONS["revenue"], "Suma de todos los precios finales del período, en INR."), unsafe_allow_html=True)
c2.markdown(kpi_card("Total Órdenes",    fmt_num(kpis["total_orders"].iloc[0]),   pct_delta(kpis, prev_kpis, "total_orders"),  ICONS["orders"],  "Cantidad total de órdenes. Cada fila = 1 orden = 1 unidad vendida."), unsafe_allow_html=True)
c3.markdown(kpi_card("Ticket Promedio",  fmt_rev(kpis["avg_ticket"].iloc[0]),     pct_delta(kpis, prev_kpis, "avg_ticket"),    ICONS["ticket"],  "Ingreso promedio por orden en INR."), unsafe_allow_html=True)
c4.markdown(kpi_card("Tasa Devolución",  f'{kpis["return_rate"].iloc[0]}%',       pct_delta(kpis, prev_kpis, "return_rate"),   ICONS["return"],  "% de órdenes devueltas. >15% puede indicar problemas."), unsafe_allow_html=True)
c5.markdown(kpi_card("Rating Promedio",  str(kpis["avg_rating"].iloc[0]),         pct_delta(kpis, prev_kpis, "avg_rating"),    ICONS["rating"],  "Calificación promedio de productos, escala 1 a 5."), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tendencia ─────────────────────────────────────────────
df_evol = query(f"""
    SELECT DATE_TRUNC('month', purchase_date)::date AS mes,
           ROUND(SUM(final_price)::numeric, 0) AS ingresos,
           COUNT(*) AS ordenes,
           ROUND(AVG(final_price)::numeric, 0) AS ticket_prom,
           ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)*100,1) AS tasa_dev,
           ROUND(AVG(rating)::numeric, 2) AS avg_rating
    FROM analytics.fact_orders {where}
    AND DATE_TRUNC('month', purchase_date) < DATE_TRUNC('month', CURRENT_DATE)
    GROUP BY 1 ORDER BY mes
""", params)
df_evol["mes_label"] = pd.to_datetime(df_evol["mes"]).dt.strftime("%b %Y")

metric_sel = st.radio("metric", ["Revenue", "Cantidad"], horizontal=True, label_visibility="collapsed", key="overview_metric")
y_col   = "ingresos" if metric_sel == "Revenue" else "ordenes"
y_label = "Ingresos (INR)" if metric_sel == "Revenue" else "Órdenes"

idx_max = int(df_evol[y_col].idxmax())
idx_min = int(df_evol[y_col].idxmin())
avg_val = float(df_evol[y_col].mean())

def fmt_v(v):
    if metric_sel == "Revenue":
        return f"₹{v/1_000_000:.1f}M" if v >= 1_000_000 else f"₹{v:,.0f}"
    else:
        return f"{v/1_000:.1f}k" if v >= 1_000 else str(int(v))

fig_trend = go.Figure()
fig_trend.add_trace(go.Scatter(
    x=df_evol["mes_label"], y=[avg_val] * len(df_evol),
    mode="lines", name="Promedio",
    line=dict(color="#9BAAB8", width=1.5, dash="dot"),
    hoverinfo="skip",
))
fig_trend.add_trace(go.Scatter(
    x=df_evol["mes_label"], y=df_evol[y_col],
    mode="lines+markers+text",
    text=df_evol[y_col].apply(fmt_v),
    textposition="top center",
    textfont=dict(size=9, color=PALETTE["text_light"], family=FONT),
    name=metric_sel,
    line=dict(color=PALETTE["primary_light"], width=2.5, shape="spline"),
    marker=dict(
        size=[7] * (len(df_evol) - 1) + [12],
        color=[PALETTE["primary_light"]] * (len(df_evol) - 1) + [PALETTE["accent"]],
        line=dict(color="white", width=2),
    ),
    fill="tozeroy", fillcolor="rgba(46,109,164,0.08)",
    customdata=df_evol[["ingresos","ordenes","ticket_prom","tasa_dev","avg_rating"]].values,
    hovertemplate=(
        "<b style='font-size:14px'>%{x}</b><br><br>"
        "<b>₹%{customdata[0]:,.0f}</b> ingresos<br>"
        "<b>%{customdata[1]:,.0f}</b> órdenes<br><br>"
        "Ticket: ₹%{customdata[2]:,.0f}<br>"
        "Devolución: %{customdata[3]:.1f}%<br>"
        "Rating: %{customdata[4]:.2f}"
        "<extra></extra>"
    ),
))
fig_trend.add_annotation(x=df_evol["mes_label"].iloc[idx_max], y=df_evol[y_col].iloc[idx_max],
    text=f"↑ Max: {fmt_v(df_evol[y_col].iloc[idx_max])}", showarrow=False,
    font=dict(color=PALETTE["success"], size=11, family=FONT), yshift=40)
fig_trend.add_annotation(x=df_evol["mes_label"].iloc[idx_min], y=df_evol[y_col].iloc[idx_min],
    text=f"↓ Min: {fmt_v(df_evol[y_col].iloc[idx_min])}", showarrow=False,
    font=dict(color=PALETTE["danger"], size=11, family=FONT), yshift=-20)
fig_trend.add_annotation(x=df_evol["mes_label"].iloc[-1], y=avg_val,
    text=f"Prom: {fmt_v(avg_val)}", showarrow=False,
    font=dict(color="#9BAAB8", size=10, family=FONT), xanchor="left", xshift=8)
fig_trend.update_layout(
    plot_bgcolor="white", paper_bgcolor="white",
    font=dict(family=FONT, color=PALETTE["text"]),
    margin=dict(t=20, b=50, l=10, r=90), height=380, showlegend=False,
    xaxis=dict(showgrid=False, tickangle=-30),
    yaxis=dict(gridcolor="#EEF2F7", title=y_label),
    hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=13), align="left"),
)
st.plotly_chart(fig_trend, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Distribución ─────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

with col1:
    df_cat = query(f"""
        SELECT category,
               ROUND(SUM(final_price)::numeric, 0) AS ingresos,
               ROUND(SUM(final_price)*100.0/SUM(SUM(final_price)) OVER(),1) AS pct
        FROM analytics.fact_orders {where} GROUP BY category ORDER BY pct ASC
    """, params)
    fig1 = px.bar(df_cat, x="pct", y="category", orientation="h", text="pct",
                 color_discrete_sequence=[PALETTE["primary_light"]],
                 title="Ingresos por Categoría (%)",
                 custom_data=["ingresos"], labels={"pct":"% ingresos","category":""})
    fig1.update_traces(texttemplate="%{text:.1f}%", textposition="outside",
                      hovertemplate="<b>%{y}</b><br>%: %{x:.1f}%<br>Total: ₹%{customdata[0]:,.0f}<extra></extra>")
    fig1.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=300,
                      font=dict(family=FONT), margin=dict(t=40,b=20,l=10,r=50),
                      title=dict(font=dict(color="#6B7A8D", size=13)))
    fig1.update_xaxes(showgrid=True, gridcolor="#EEF2F7", range=[0, df_cat["pct"].max()*1.2])
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    df_ent = query(f"""
        SELECT delivery_status, COUNT(*) AS ordenes,
               ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER(),1) AS pct,
               ROUND(AVG(shipping_time_days)::numeric,1) AS dias_prom,
               ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)*100,1) AS tasa_dev
        FROM analytics.fact_orders {where} GROUP BY delivery_status ORDER BY pct DESC
    """, params)
    fig2 = px.pie(df_ent, names="delivery_status", values="pct",
                 color_discrete_sequence=PLOTLY_COLORS, title="Estado de Entregas",
                 hole=0.4, custom_data=["dias_prom","tasa_dev","ordenes"])
    fig2.update_traces(textposition="inside", textinfo="percent+label",
                      hovertemplate="<b>%{label}</b><br>%: %{value:.1f}%<br>Días: %{customdata[0]}<br>Dev: %{customdata[1]}%<extra></extra>")
    fig2.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=300,
                      font=dict(family=FONT), margin=dict(t=40,b=20,l=10,r=10),
                      showlegend=False, title=dict(font=dict(color="#6B7A8D", size=13)))
    st.plotly_chart(fig2, use_container_width=True)

with col3:
    df_pay = query(f"""
        SELECT payment_method, COUNT(*) AS ordenes,
               ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER(),1) AS pct,
               ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)*100,1) AS tasa_dev,
               ROUND(AVG(final_price)::numeric,0) AS ticket_prom
        FROM analytics.fact_orders {where} GROUP BY payment_method ORDER BY pct DESC
    """, params)
    fig3 = px.pie(df_pay, names="payment_method", values="pct",
                 color_discrete_sequence=PLOTLY_COLORS, title="Métodos de Pago",
                 hole=0.4, custom_data=["tasa_dev","ticket_prom","ordenes"])
    fig3.update_traces(textposition="inside", textinfo="percent+label",
                      hovertemplate="<b>%{label}</b><br>%: %{value:.1f}%<br>Dev: %{customdata[0]}%<br>Ticket: ₹%{customdata[1]:,.0f}<extra></extra>")
    fig3.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=300,
                      font=dict(family=FONT), margin=dict(t=40,b=20,l=10,r=10),
                      showlegend=False, title=dict(font=dict(color="#6B7A8D", size=13)))
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    df_dev = query(f"""
        SELECT device, COUNT(*) AS ordenes,
               ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER(),1) AS pct,
               ROUND(AVG(final_price)::numeric,0) AS ticket_prom,
               ROUND(AVG(rating)::numeric,2) AS avg_rating
        FROM analytics.fact_orders {where} GROUP BY device ORDER BY pct DESC
    """, params)
    fig4 = px.pie(df_dev, names="device", values="pct",
                 color_discrete_sequence=[PALETTE["primary"],PALETTE["primary_light"],PALETTE["light"]],
                 title="Ventas por Dispositivo", hole=0.4,
                 custom_data=["ticket_prom","avg_rating","ordenes"])
    fig4.update_traces(textposition="inside", textinfo="percent+label",
                      hovertemplate="<b>%{label}</b><br>%: %{value:.1f}%<br>Ticket: ₹%{customdata[0]:,.0f}<br>Rating: %{customdata[1]}<extra></extra>")
    fig4.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=300,
                      font=dict(family=FONT), margin=dict(t=40,b=20,l=10,r=10),
                      showlegend=False, title=dict(font=dict(color="#6B7A8D", size=13)))
    st.plotly_chart(fig4, use_container_width=True)
