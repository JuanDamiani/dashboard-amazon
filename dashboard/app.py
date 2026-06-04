"""
Amazon E-Commerce Analytics Dashboard
Layout con tabs horizontales — sin sidebar.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from utils.db import query
from utils.style import get_css, kpi_card, PALETTE, PLOTLY_COLORS, FONT

st.set_page_config(
    page_title="Amazon Analytics",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(get_css(), unsafe_allow_html=True)

# ── CSS adicional para ocultar sidebar completamente ─────
st.markdown("""
<style>
[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
.block-container { padding-top: 0 !important; max-width: 100% !important; }
</style>
""", unsafe_allow_html=True)

# ── Inicializar estado de filtros ────────────────────────
if "show_filters" not in st.session_state:
    st.session_state["show_filters"] = True

# ── Cargar opciones de filtros ───────────────────────────
@st.cache_data(ttl=3600)
def load_filter_options():
    dr    = query("SELECT MIN(purchase_date) AS mn, MAX(purchase_date) AS mx FROM analytics.fact_orders")
    cats  = query("SELECT DISTINCT category       FROM analytics.fact_orders ORDER BY category")["category"].tolist()
    locs  = query("SELECT DISTINCT location       FROM analytics.fact_orders ORDER BY location")["location"].tolist()
    devs  = query("SELECT DISTINCT device         FROM analytics.fact_orders ORDER BY device")["device"].tolist()
    pays  = query("SELECT DISTINCT payment_method FROM analytics.fact_orders ORDER BY payment_method")["payment_method"].tolist()
    subs  = query("SELECT DISTINCT subcategory    FROM analytics.fact_orders ORDER BY subcategory")["subcategory"].tolist()
    brands= query("SELECT DISTINCT brand          FROM analytics.fact_orders ORDER BY brand")["brand"].tolist()
    stats = query("SELECT DISTINCT delivery_status FROM analytics.fact_orders ORDER BY delivery_status")["delivery_status"].tolist()
    return dr, cats, locs, devs, pays, subs, brands, stats

dr, cats, locs, devs, pays, subs, brands, stats = load_filter_options()
min_date = dr["mn"].iloc[0]
max_date = dr["mx"].iloc[0]

# ── HEADER: Logo + Tabs ──────────────────────────────────
from dateutil.relativedelta import relativedelta

header_col, tabs_col = st.columns([1, 5])

with header_col:
    st.markdown("""
    <div style="padding: 12px 0 0 8px;">
        <img src="https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg"
             style="width: 90px; margin-bottom: 0;" />
    </div>
    """, unsafe_allow_html=True)

with tabs_col:
    tab_names = ["Overview", "Ventas", "Logística", "Clientes", "Vendedores", "Glosario"]
    selected_tab = st.radio(
        "nav", tab_names,
        horizontal=True,
        label_visibility="collapsed",
        key="main_nav",
    )

st.markdown('<hr style="margin: 0 0 8px 0; border-color: #E4E9F0;">', unsafe_allow_html=True)

# ── BARRA DE FILTROS ─────────────────────────────────────
from dateutil.relativedelta import relativedelta

periodo_opciones = {
    "Últimos 6 meses": relativedelta(months=6),
    "Último mes":      relativedelta(months=1),
    "Últimos 3 meses": relativedelta(months=3),
    "Último año":      relativedelta(years=1),
    "Todo el período": None,
}

# Inicializar más filtros
if "more_filters_open" not in st.session_state:
    st.session_state["more_filters_open"] = False

# Fila principal de filtros
# Calcular fecha default antes de usarla en el date_input
_delta_default = periodo_opciones.get("Últimos 6 meses")
_default_inicio = max_date - _delta_default

fc = st.columns([1.4, 1.8, 1.4, 1.4, 1.4, 1.1, 0.5])

with fc[0]:
    st.caption("Rango de fechas")
    fecha_inicio = st.date_input("Desde", value=_default_inicio, min_value=min_date, max_value=max_date, label_visibility="collapsed")

with fc[1]:
    st.caption("Período")
    periodo_sel = st.selectbox("Período", list(periodo_opciones.keys()), index=0, label_visibility="collapsed")

with fc[2]:
    st.caption("Categoría")
    categoria = st.selectbox("Categoría", ["Todas"] + cats, label_visibility="collapsed")

with fc[3]:
    st.caption("Ciudad")
    ciudad = st.selectbox("Ciudad", ["Todas"] + locs, label_visibility="collapsed")

with fc[4]:
    st.caption("Dispositivo")
    dispositivo = st.selectbox("Dispositivo", ["Todos"] + devs, label_visibility="collapsed")

with fc[5]:
    st.caption(" ")
    if st.button("🎛️ Más filtros", key="toggle_more", use_container_width=True):
        st.session_state["more_filters_open"] = not st.session_state["more_filters_open"]

with fc[6]:
    st.caption(" ")
    if st.button("🗑️", help="Limpiar filtros", key="clear_filters"):
        for k in list(st.session_state.keys()):
            if k not in ["main_nav", "more_filters_open"]:
                del st.session_state[k]
        st.rerun()

# Más filtros — aparecen debajo cuando se activan
if st.session_state["more_filters_open"]:
    with st.container():
        mc = st.columns([1.5, 1.5, 1.5, 1.5, 2])
        with mc[0]:
            st.caption("Método de pago")
            metodo_pago = st.selectbox("Método de pago", ["Todos"] + pays, label_visibility="collapsed")
        with mc[1]:
            st.caption("Subcategoría")
            subcategoria = st.selectbox("Subcategoría", ["Todas"] + subs, label_visibility="collapsed")
        with mc[2]:
            st.caption("Marca")
            marca = st.selectbox("Marca", ["Todas"] + brands, label_visibility="collapsed")
        with mc[3]:
            st.caption("Estado de entrega")
            estado_entrega = st.selectbox("Estado de entrega", ["Todos"] + stats, label_visibility="collapsed")
        with mc[4]:
            st.caption("Rango de rating")
            rating_min, rating_max = st.slider("Rating", 1.0, 5.0, (1.0, 5.0), 0.5, label_visibility="collapsed")
else:
    metodo_pago    = "Todos"
    subcategoria   = "Todas"
    marca          = "Todas"
    estado_entrega = "Todos"
    rating_min     = 1.0
    rating_max     = 5.0

fecha_fin = max_date

# ── Construir WHERE — fecha_inicio ya viene del date_input ──

conds = [f"purchase_date BETWEEN '{fecha_inicio}' AND '{fecha_fin}'"]
if categoria     != "Todas":  conds.append(f"category = '{categoria}'")
if ciudad        != "Todas":  conds.append(f"location = '{ciudad}'")
if dispositivo   != "Todos":  conds.append(f"device = '{dispositivo}'")
if metodo_pago   != "Todos":  conds.append(f"payment_method = '{metodo_pago}'")
if subcategoria  != "Todas":  conds.append(f"subcategory = '{subcategoria}'")
if marca         != "Todas":  conds.append(f"brand = '{marca}'")
if estado_entrega!= "Todos":  conds.append(f"delivery_status = '{estado_entrega}'")

where        = "WHERE " + " AND ".join(conds)
where_rating = "WHERE " + " AND ".join(conds + [f"rating BETWEEN {rating_min} AND {rating_max}"])

st.markdown('<hr style="margin: 4px 0 12px 0; border-color: #E4E9F0;">', unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════
# TAB: OVERVIEW
# ═══════════════════════════════════════════════════════
if selected_tab == "Overview":

    # ── KPIs con st.metric nativo ────────────────────────
    kpis = query(f"""
        SELECT ROUND(SUM(final_price)::numeric, 0) AS total_revenue,
               COUNT(*) AS total_orders,
               ROUND(AVG(final_price)::numeric, 0) AS avg_ticket,
               ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric * 100, 1) AS return_rate,
               ROUND(AVG(rating)::numeric, 2) AS avg_rating
        FROM analytics.fact_orders {where}
    """)

    variacion = query("""
        SELECT total_orders_pct_change, total_revenue_pct_change,
               avg_ticket_pct_change, return_rate_pct_change, avg_product_rating_pct_change
        FROM analytics.mart_period_variation ORDER BY period_month DESC LIMIT 1
    """)

    def get_delta(df, col):
        try:
            v = df[col].iloc[0]
            return float(v) if v is not None else None
        except: return None

    def fmt_rev(v):
        if v >= 1_000_000_000: return f"₹{v/1_000_000_000:.1f}B"
        if v >= 1_000_000:     return f"₹{v/1_000_000:.1f}M"
        return f"₹{v:,.0f}"

    def fmt_num(v):
        if v >= 1_000_000: return f"{v/1_000_000:.1f}M"
        if v >= 1_000:     return f"{v/1_000:.1f}k"
        return f"{v:,.0f}"

    def fmt_delta(v):
        if v is None: return None
        return f"{v:+.1f}%"

    # SVG icons
    ICONS = {
        "revenue": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5" stroke-linecap="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>',
        "orders":  '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5" stroke-linecap="round"><path d="M20 7H4a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
        "ticket":  '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5" stroke-linecap="round"><path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v2z"/></svg>',
        "return":  '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5" stroke-linecap="round"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>',
        "rating":  '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5" stroke-linecap="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
    }

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.markdown(kpi_card("Ingresos Totales", fmt_rev(kpis["total_revenue"].iloc[0]),  get_delta(variacion, "total_revenue_pct_change"),      ICONS["revenue"], "Suma de todos los precios finales del período, en INR (Rupias indias)."), unsafe_allow_html=True)
    c2.markdown(kpi_card("Total Órdenes",    fmt_num(kpis["total_orders"].iloc[0]),   get_delta(variacion, "total_orders_pct_change"),       ICONS["orders"],  "Cantidad total de órdenes. Cada fila = 1 orden = 1 unidad vendida."), unsafe_allow_html=True)
    c3.markdown(kpi_card("Ticket Promedio",  fmt_rev(kpis["avg_ticket"].iloc[0]),     get_delta(variacion, "avg_ticket_pct_change"),         ICONS["ticket"],  "Ingreso promedio por orden en INR."), unsafe_allow_html=True)
    c4.markdown(kpi_card("Tasa Devolución",  f'{kpis["return_rate"].iloc[0]}%',      get_delta(variacion, "return_rate_pct_change"),        ICONS["return"],  "% de órdenes devueltas. >15% puede indicar problemas de calidad o logística."), unsafe_allow_html=True)
    c5.markdown(kpi_card("Rating Promedio",  str(kpis["avg_rating"].iloc[0]),         get_delta(variacion, "avg_product_rating_pct_change"), ICONS["rating"],  "Calificación promedio de productos, escala 1 a 5."), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Tendencia de órdenes — línea con área ────────────
    st.markdown('<div class="section-title">Evolución Mensual Ventas</div>', unsafe_allow_html=True)

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
    """)
    df_evol["mes_label"] = pd.to_datetime(df_evol["mes"]).dt.strftime("%b %Y")

    metric_sel = st.radio(
        "metric", ["Revenue", "Cantidad"],
        horizontal=True, label_visibility="collapsed", key="overview_metric"
    )

    y_col   = "ingresos" if metric_sel == "Revenue" else "ordenes"
    y_label = "Ingresos (INR)" if metric_sel == "Revenue" else "Ordenes"

    idx_max = int(df_evol[y_col].idxmax())
    idx_min = int(df_evol[y_col].idxmin())
    avg_val = float(df_evol[y_col].mean())

    def fmt_v(v):
        if metric_sel == "Revenue":
            if v >= 1_000_000:
                return f"₹{v/1_000_000:.1f}M"
            return f"₹{v:,.0f}"
        else:
            if v >= 1_000:
                return f"{v/1_000:.1f}k"
            return str(int(v))

    fig_trend = go.Figure()

    fig_trend.add_trace(go.Scatter(
        x=df_evol["mes_label"],
        y=[avg_val] * len(df_evol),
        mode="lines",
        name="Promedio",
        line=dict(color="#9BAAB8", width=1.5, dash="dot"),
        hoverinfo="skip",
    ))

    fig_trend.add_trace(go.Scatter(
        x=df_evol["mes_label"],
        y=df_evol[y_col],
        mode="lines+markers+text",
        text=df_evol[y_col].apply(fmt_v),
        textposition="top center",
        textfont=dict(size=9, color=PALETTE["text_light"], family=FONT),
        name=metric_sel,
        line=dict(color=PALETTE["primary_light"], width=2.5, shape="spline"),
        #marker=dict(size=7, color=PALETTE["primary_light"], line=dict(color="white", width=2)),
        marker=dict(
            size=[7] * (len(df_evol) - 1) + [12],
            color=[PALETTE["primary_light"]] * (len(df_evol) - 1) + [PALETTE["accent"]],
            line=dict(color="white", width=2)
        ),
        fill="tozeroy",
        fillcolor="rgba(46,109,164,0.08)",
        customdata=df_evol[["ingresos", "ordenes", "ticket_prom", "tasa_dev", "avg_rating"]].values,
        hovertemplate=(
            "<b style='font-size:14px'>%{x}</b><br>"
            "<br>"
            "<b>₹%{customdata[0]:,.0f}</b> ingresos<br>"
            "<b>%{customdata[1]:,.0f}</b> órdenes<br>"
            "<br>"
            "Ticket: ₹%{customdata[2]:,.0f}<br>"
            "Devolución: %{customdata[3]:.1f}%<br>"
            "Rating: %{customdata[4]:.2f}"
            "<extra></extra>"
        ),
    ))

    fig_trend.add_annotation(
        x=df_evol["mes_label"].iloc[idx_max],
        y=df_evol[y_col].iloc[idx_max],
        text=f"↑ Max: {fmt_v(df_evol[y_col].iloc[idx_max])}",
        showarrow=False,
        font=dict(color=PALETTE["success"], size=11, family=FONT),
        yshift=40,
    )

    fig_trend.add_annotation(
        x=df_evol["mes_label"].iloc[idx_min],
        y=df_evol[y_col].iloc[idx_min],
        text=f"↓ Min: {fmt_v(df_evol[y_col].iloc[idx_min])}",
        showarrow=False,
        font=dict(color=PALETTE["danger"], size=11, family=FONT),
        yshift=-20,
    )

    fig_trend.add_annotation(
        x=df_evol["mes_label"].iloc[-1],
        y=avg_val,
        text=f"Prom: {fmt_v(avg_val)}",
        showarrow=False,
        font=dict(color="#9BAAB8", size=10, family=FONT),
        xanchor="left", xshift=8,
    )

    fig_trend.update_layout(
        plot_bgcolor="white", paper_bgcolor="white",
        font=dict(family=FONT, color=PALETTE["text"]),
        margin=dict(t=20, b=50, l=10, r=90),
        height=380,
        showlegend=False,
        xaxis=dict(showgrid=False, tickangle=-30),
        yaxis=dict(gridcolor="#EEF2F7", title=y_label),
        hoverlabel=dict(bgcolor="white", bordercolor="#E4E9F0", font=dict(family=FONT, size=13),align="left",
),
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Distribución ─────────────────────────────────────
   
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        df_cat = query(f"""
            SELECT category,
                   ROUND(SUM(final_price)::numeric, 0) AS ingresos,
                   ROUND(SUM(final_price) * 100.0 / SUM(SUM(final_price)) OVER (), 1) AS pct
            FROM analytics.fact_orders {where} GROUP BY category ORDER BY pct ASC
        """)
        fig1 = px.bar(df_cat, x="pct", y="category", orientation="h", text="pct",
                     color_discrete_sequence=[PALETTE["primary_light"]],
                     title="Ingresos por Categoría (%)",
                     custom_data=["ingresos"],
                     labels={"pct":"% ingresos","category":""})
        fig1.update_traces(
            texttemplate="%{text:.1f}%", textposition="outside",
            hovertemplate="<b>%{y}</b><br>% ingresos: %{x:.1f}%<br>Total: ₹%{customdata[0]:,.0f}<extra></extra>",
        )
        fig1.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=300,
                          font=dict(family=FONT), margin=dict(t=40,b=20,l=10,r=50))
        fig1.update_xaxes(showgrid=True, gridcolor="#EEF2F7", range=[0, df_cat["pct"].max() * 1.2])
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        df_ent = query(f"""
            SELECT delivery_status,
                   COUNT(*) AS ordenes,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct,
                   ROUND(AVG(shipping_time_days)::numeric,1) AS dias_prom,
                   ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)*100,1) AS tasa_dev
            FROM analytics.fact_orders {where} GROUP BY delivery_status ORDER BY pct DESC
        """)
        fig2 = px.pie(df_ent, names="delivery_status", values="pct",
                     color_discrete_sequence=PLOTLY_COLORS,
                     title="Estado de Entregas", hole=0.4,
                     custom_data=["dias_prom","tasa_dev","ordenes"])
        fig2.update_traces(
            textposition="inside", textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>%: %{value:.1f}%<br>Días prom: %{customdata[0]}<br>Dev: %{customdata[1]}%<br>Órdenes: %{customdata[2]:,}<extra></extra>",
        )
        fig2.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=300,
                          font=dict(family=FONT), margin=dict(t=40,b=20,l=10,r=10), showlegend=False)
        st.plotly_chart(fig2, use_container_width=True)

    with col3:
        df_pay = query(f"""
            SELECT payment_method,
                   COUNT(*) AS ordenes,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct,
                   ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)*100,1) AS tasa_dev,
                   ROUND(AVG(final_price)::numeric, 0) AS ticket_prom
            FROM analytics.fact_orders {where} GROUP BY payment_method ORDER BY pct DESC
        """)
        fig3 = px.pie(df_pay, names="payment_method", values="pct",
                     color_discrete_sequence=PLOTLY_COLORS,
                     title="Métodos de Pago", hole=0.4,
                     custom_data=["tasa_dev","ticket_prom","ordenes"])
        fig3.update_traces(
            textposition="inside", textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>%: %{value:.1f}%<br>Dev: %{customdata[0]}%<br>Ticket: ₹%{customdata[1]:,.0f}<br>Órdenes: %{customdata[2]:,}<extra></extra>",
        )
        fig3.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=300,
                          font=dict(family=FONT), margin=dict(t=40,b=20,l=10,r=10), showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        df_dev = query(f"""
            SELECT device,
                   COUNT(*) AS ordenes,
                   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS pct,
                   ROUND(AVG(final_price)::numeric, 0) AS ticket_prom,
                   ROUND(AVG(rating)::numeric, 2) AS avg_rating
            FROM analytics.fact_orders {where} GROUP BY device ORDER BY pct DESC
        """)
        fig4 = px.pie(df_dev, names="device", values="pct",
                     color_discrete_sequence=[PALETTE["primary"], PALETTE["primary_light"], PALETTE["light"]],
                     title="Ventas por Dispositivo", hole=0.4,
                     custom_data=["ticket_prom","avg_rating","ordenes"])
        fig4.update_traces(
            textposition="inside", textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>%: %{value:.1f}%<br>Ticket: ₹%{customdata[0]:,.0f}<br>Rating: %{customdata[1]}<br>Órdenes: %{customdata[2]:,}<extra></extra>",
        )
        fig4.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=300,
                          font=dict(family=FONT), margin=dict(t=40,b=20,l=10,r=10), showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)

# ═══════════════════════════════════════════════════════
# TAB: VENTAS
# ═══════════════════════════════════════════════════════
elif selected_tab == "Ventas":
    st.markdown('<div class="section-title">Análisis de Ventas — RF3</div>', unsafe_allow_html=True)

    df_evol = query(f"""
        SELECT DATE_TRUNC('month', purchase_date)::date AS mes,
               COUNT(*) AS unidades, ROUND(SUM(final_price)::numeric,0) AS ingresos,
               ROUND(AVG(final_price)::numeric,0) AS precio_prom, ROUND(AVG(discount)::numeric,1) AS desc_prom
        FROM analytics.fact_orders {where} GROUP BY 1 ORDER BY mes
    """)
    df_evol["mes"] = pd.to_datetime(df_evol["mes"]).dt.strftime("%b %Y")
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=df_evol["mes"], y=df_evol["ingresos"], name="Ingresos", marker_color=PALETTE["primary_light"], opacity=0.85), secondary_y=False)
    fig.add_trace(go.Scatter(x=df_evol["mes"], y=df_evol["unidades"], name="Unidades vendidas", mode="lines+markers", line=dict(color=PALETTE["accent"], width=2.5), marker=dict(size=6)), secondary_y=True)
    fig.update_layout(title="Evolución Mensual", plot_bgcolor="white", paper_bgcolor="white",
                     font=dict(family=FONT), legend=dict(orientation="h",y=1.1), margin=dict(t=50,b=40,l=10,r=10), height=320)
    fig.update_yaxes(title_text="Ingresos (INR)", secondary_y=False, gridcolor="#EEF2F7")
    fig.update_yaxes(title_text="Unidades", secondary_y=True, showgrid=False)
    st.plotly_chart(fig, use_container_width=True)

    tab1, tab2, tab3 = st.tabs(["Por Categoría", "Por Subcategoría", "Por Marca"])
    with tab1:
        df = query(f"SELECT category, COUNT(*) AS unidades, ROUND(SUM(final_price)::numeric,0) AS ingresos, ROUND(AVG(discount)::numeric,1) AS desc_prom FROM analytics.fact_orders {where} GROUP BY category ORDER BY ingresos DESC")
        c1,c2 = st.columns(2)
        with c1:
            fig = px.bar(df, x="category", y="ingresos", text="ingresos", color_discrete_sequence=[PALETTE["primary_light"]], title="Ingresos por Categoría")
            fig.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
            fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=300, font=dict(family=FONT), margin=dict(t=40,b=40,l=10,r=10))
            fig.update_yaxes(gridcolor="#EEF2F7")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            fig = px.bar(df, x="category", y="desc_prom", text="desc_prom", color_discrete_sequence=[PALETTE["accent"]], title="Descuento Promedio (%)")
            fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
            fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=300, font=dict(family=FONT), margin=dict(t=40,b=40,l=10,r=10))
            fig.update_yaxes(gridcolor="#EEF2F7")
            st.plotly_chart(fig, use_container_width=True)
        st.dataframe(df, use_container_width=True)

    with tab2:
        df = query(f"SELECT subcategory, category, COUNT(*) AS unidades, ROUND(SUM(final_price)::numeric,0) AS ingresos FROM analytics.fact_orders {where} GROUP BY subcategory, category ORDER BY ingresos DESC LIMIT 20")
        fig = px.bar(df, x="ingresos", y="subcategory", orientation="h", color="category", color_discrete_sequence=PLOTLY_COLORS, title="Top 20 Subcategorías", labels={"ingresos":"Ingresos","subcategory":""})
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=400, font=dict(family=FONT), margin=dict(t=40,b=20,l=10,r=10))
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        df = query(f"SELECT brand, COUNT(*) AS unidades, ROUND(SUM(final_price)::numeric,0) AS ingresos, ROUND(AVG(discount)::numeric,1) AS desc_prom FROM analytics.fact_orders {where} GROUP BY brand ORDER BY ingresos DESC LIMIT 20")
        fig = px.bar(df, x="ingresos", y="brand", orientation="h", text="ingresos", color_discrete_sequence=[PALETTE["primary"]], title="Top 20 Marcas", labels={"ingresos":"Ingresos","brand":""})
        fig.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=400, font=dict(family=FONT), margin=dict(t=40,b=20,l=10,r=80))
        st.plotly_chart(fig, use_container_width=True)

    c1,c2 = st.columns(2)
    with c1:
        df = query("SELECT discount_range, total_orders, total_revenue FROM analytics.mart_discount_vs_orders ORDER BY discount_range")
        fig = make_subplots(specs=[[{"secondary_y":True}]])
        fig.add_trace(go.Bar(x=df["discount_range"], y=df["total_orders"], name="Órdenes", marker_color=PALETTE["primary_light"], opacity=0.85), secondary_y=False)
        fig.add_trace(go.Scatter(x=df["discount_range"], y=df["total_revenue"], name="Ingresos", mode="lines+markers", line=dict(color=PALETTE["accent"],width=2)), secondary_y=True)
        fig.update_layout(title="Descuento vs Volumen", plot_bgcolor="white", paper_bgcolor="white", height=300, font=dict(family=FONT), margin=dict(t=50,b=40,l=10,r=10), legend=dict(orientation="h",y=1.1))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        df = query(f"SELECT device, category, COUNT(*) AS ordenes, ROUND(SUM(final_price)::numeric,0) AS ingresos FROM analytics.fact_orders {where} GROUP BY device, category ORDER BY device, ingresos DESC")
        fig = px.bar(df, x="device", y="ingresos", color="category", barmode="stack", color_discrete_sequence=PLOTLY_COLORS, title="Ingresos por Dispositivo y Categoría", labels={"ingresos":"Ingresos","device":"Dispositivo","category":"Categoría"})
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=300, font=dict(family=FONT), margin=dict(t=50,b=40,l=10,r=10), legend=dict(orientation="h",y=1.1))
        st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════
# TAB: LOGÍSTICA
# ═══════════════════════════════════════════════════════
elif selected_tab == "Logística":
    st.markdown('<div class="section-title">Indicadores Logísticos</div>', unsafe_allow_html=True)

    df_perf = query("SELECT * FROM analytics.mart_delivery_performance")
    avg_ship = query(f"SELECT ROUND(AVG(shipping_time_days)::numeric,1) AS v FROM analytics.fact_orders {where}")["v"].iloc[0]
    ret_rate = query(f"SELECT ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric*100,1) AS v FROM analytics.fact_orders {where}")["v"].iloc[0]

    ICONS_LOG = {
        "ontime": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
        "ship":   '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><rect x="1" y="3" width="15" height="13"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>',
        "delay":  '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>',
        "return": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>',
    }

    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(kpi_card("Entregas a Tiempo",  f'{df_perf["pct_on_time"].iloc[0]}%',  None, ICONS_LOG["ontime"]), unsafe_allow_html=True)
    c2.markdown(kpi_card("Tiempo Prom. Envío", f"{avg_ship} días",                    None, ICONS_LOG["ship"]),   unsafe_allow_html=True)
    c3.markdown(kpi_card("Pedidos Demorados",  f'{df_perf["pct_delayed"].iloc[0]}%',  None, ICONS_LOG["delay"]),  unsafe_allow_html=True)
    c4.markdown(kpi_card("Tasa Devolución",    f"{ret_rate}%",                        None, ICONS_LOG["return"]), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        df = query(f"SELECT delivery_status, COUNT(*) AS ordenes, ROUND(COUNT(*)*100.0/SUM(COUNT(*)) OVER(),1) AS pct, ROUND(AVG(shipping_time_days)::numeric,1) AS dias_prom, ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)*100,1) AS tasa_dev FROM analytics.fact_orders {where} GROUP BY delivery_status ORDER BY ordenes DESC")
        fig = px.bar(df, x="pct", y="delivery_status", orientation="h", text="pct", color_discrete_sequence=[PALETTE["primary"]], title="Distribución por Estado de Entrega (%)", custom_data=["dias_prom","tasa_dev"], labels={"pct":"%","delivery_status":""})
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside", hovertemplate="<b>%{y}</b><br>%: %{x:.1f}%<br>Días prom: %{customdata[0]}<br>Dev: %{customdata[1]}%<extra></extra>")
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=300, font=dict(family=FONT), margin=dict(t=50,b=20,l=10,r=40))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        df = query(f"SELECT location, ROUND(AVG(shipping_time_days)::numeric,1) AS dias_prom, ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)*100,1) AS tasa_dev FROM analytics.fact_orders {where} GROUP BY location ORDER BY dias_prom DESC")
        fig = px.bar(df, x="dias_prom", y="location", orientation="h", text="dias_prom", color_discrete_sequence=[PALETTE["primary_light"]], title="Tiempo Prom. de Envío por Ciudad", custom_data=["tasa_dev"], labels={"dias_prom":"Días","location":""})
        fig.update_traces(texttemplate="%{text:.1f}d", textposition="outside", hovertemplate="<b>%{y}</b><br>Días: %{x:.1f}<br>Dev: %{customdata[0]}%<extra></extra>")
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=300, font=dict(family=FONT), margin=dict(t=50,b=20,l=10,r=50))
        st.plotly_chart(fig, use_container_width=True)

    c1,c2,c3 = st.columns(3)
    with c1:
        df = query(f"SELECT category, ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)*100,1) AS tasa_dev FROM analytics.fact_orders {where} GROUP BY category ORDER BY tasa_dev DESC")
        fig = px.bar(df, x="tasa_dev", y="category", orientation="h", text="tasa_dev", color_discrete_sequence=["#C0392B"], title="Dev. por Categoría (%)", labels={"tasa_dev":"%","category":""})
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=280, font=dict(family=FONT), margin=dict(t=40,b=20,l=10,r=40))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        df = query("SELECT payment_method, return_rate, total_orders FROM analytics.mart_payment_vs_returns ORDER BY return_rate DESC")
        fig = px.bar(df, x="payment_method", y="return_rate", text="return_rate", color_discrete_sequence=[PALETTE["warning"]], title="Método de Pago vs Dev. (%)", labels={"return_rate":"%","payment_method":""})
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=280, font=dict(family=FONT), margin=dict(t=40,b=40,l=10,r=10))
        fig.update_yaxes(gridcolor="#EEF2F7")
        st.plotly_chart(fig, use_container_width=True)
    with c3:
        df = query(f"SELECT DATE_TRUNC('month',purchase_date)::date AS mes, ROUND(AVG(CASE WHEN delivery_status='Delayed' THEN 1.0 ELSE 0.0 END)*100,1) AS pct_demorados FROM analytics.fact_orders {where} GROUP BY 1 ORDER BY mes")
        df["mes"] = pd.to_datetime(df["mes"]).dt.strftime("%b %Y")
        fig = px.line(df, x="mes", y="pct_demorados", markers=True, title="Tendencia Pedidos Demorados (%)", labels={"pct_demorados":"%","mes":"Mes"}, color_discrete_sequence=["#C0392B"])
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=280, font=dict(family=FONT), margin=dict(t=40,b=40,l=10,r=10))
        fig.update_yaxes(gridcolor="#EEF2F7")
        st.plotly_chart(fig, use_container_width=True)

    df = query("SELECT shipping_time_days, return_rate, total_orders FROM analytics.mart_delays_vs_returns ORDER BY shipping_time_days")
    fig = px.line(df, x="shipping_time_days", y="return_rate", markers=True, title="Días de Envío vs Tasa de Devolución", labels={"shipping_time_days":"Días de envío","return_rate":"Tasa dev (%)"}, color_discrete_sequence=["#C0392B"])
    fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=280, font=dict(family=FONT), margin=dict(t=40,b=40,l=10,r=10))
    fig.update_yaxes(gridcolor="#EEF2F7"); fig.update_xaxes(gridcolor="#EEF2F7")
    st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════
# TAB: CLIENTES
# ═══════════════════════════════════════════════════════
elif selected_tab == "Clientes":
    st.markdown('<div class="section-title">Experiencia del Cliente — RF5</div>', unsafe_allow_html=True)

    avg_rating = query(f"SELECT ROUND(AVG(rating)::numeric,2) AS v FROM analytics.fact_orders {where_rating}")["v"].iloc[0]
    ret_rate   = query(f"SELECT ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric*100,1) AS v FROM analytics.fact_orders {where_rating}")["v"].iloc[0]

    ICON_STAR = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>'
    ICON_RET  = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>'

    c1,c2 = st.columns(2)
    c1.markdown(kpi_card("Rating Promedio", str(avg_rating), None, ICON_STAR), unsafe_allow_html=True)
    c2.markdown(kpi_card("Tasa Devolución", f"{ret_rate}%",  None, ICON_RET),  unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        df = query("SELECT rating, total_orders, order_share_pct FROM analytics.mart_rating_distribution ORDER BY rating")
        fig = px.bar(df, x="rating", y="total_orders", text="order_share_pct", color_discrete_sequence=[PALETTE["primary_light"]], title="Distribución de Ratings", labels={"total_orders":"Órdenes","rating":"Rating"})
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=300, font=dict(family=FONT), margin=dict(t=40,b=40,l=10,r=10))
        fig.update_yaxes(gridcolor="#EEF2F7")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        df = query("SELECT rating_range, total_orders, order_share_pct, avg_rating, return_rate FROM analytics.mart_rating_by_range ORDER BY rating_range")
        fig = px.bar(df, x="order_share_pct", y="rating_range", orientation="h", text="order_share_pct", color_discrete_sequence=[PALETTE["primary"]], title="Rating por Rango (%)", custom_data=["avg_rating","return_rate"], labels={"order_share_pct":"%","rating_range":""})
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside", hovertemplate="<b>%{y}</b><br>%: %{x:.1f}%<br>Rating prom: %{customdata[0]}<br>Dev: %{customdata[1]}%<extra></extra>")
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=300, font=dict(family=FONT), margin=dict(t=40,b=20,l=10,r=40))
        st.plotly_chart(fig, use_container_width=True)

    c1,c2 = st.columns(2)
    with c1:
        df = query(f"SELECT category, ROUND(AVG(rating)::numeric,2) AS avg_rating, ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)*100,1) AS tasa_dev FROM analytics.fact_orders {where_rating} GROUP BY category ORDER BY avg_rating DESC")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df["category"], y=df["avg_rating"], name="Rating", marker_color=PALETTE["primary_light"], text=df["avg_rating"], textposition="outside"))
        fig.add_trace(go.Scatter(x=df["category"], y=df["tasa_dev"], name="Dev%", mode="lines+markers", line=dict(color="#C0392B",width=2), yaxis="y2"))
        fig.update_layout(title="Rating y Devolución por Categoría", plot_bgcolor="white", paper_bgcolor="white", height=300, font=dict(family=FONT), margin=dict(t=50,b=40,l=10,r=60),
                         yaxis=dict(title="Rating",gridcolor="#EEF2F7"), yaxis2=dict(title="Dev%",overlaying="y",side="right",showgrid=False), legend=dict(orientation="h",y=1.1))
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        df = query(f"SELECT location, ROUND(AVG(rating)::numeric,2) AS avg_rating, COUNT(*) AS ordenes FROM analytics.fact_orders {where_rating} GROUP BY location ORDER BY avg_rating DESC")
        fig = px.bar(df, x="avg_rating", y="location", orientation="h", text="avg_rating", color_discrete_sequence=[PALETTE["primary_light"]], title="Rating por Ciudad", labels={"avg_rating":"Rating","location":""})
        fig.update_traces(texttemplate="%{text:.2f} ⭐", textposition="outside")
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=300, font=dict(family=FONT), margin=dict(t=40,b=20,l=10,r=60))
        st.plotly_chart(fig, use_container_width=True)

    c1,c2 = st.columns(2)
    with c1:
        df = query(f"SELECT shipping_time_days, ROUND(AVG(rating)::numeric,2) AS avg_rating FROM analytics.fact_orders {where_rating} GROUP BY shipping_time_days ORDER BY shipping_time_days")
        fig = px.line(df, x="shipping_time_days", y="avg_rating", markers=True, title="Impacto del Tiempo de Envío en Rating", labels={"shipping_time_days":"Días","avg_rating":"Rating"}, color_discrete_sequence=[PALETTE["accent"]])
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=280, font=dict(family=FONT), margin=dict(t=40,b=40,l=10,r=10))
        fig.update_yaxes(gridcolor="#EEF2F7"); fig.update_xaxes(gridcolor="#EEF2F7")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        df = query(f"SELECT device, COUNT(*) AS ordenes, ROUND(AVG(rating)::numeric,2) AS avg_rating, ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)*100,1) AS tasa_dev FROM analytics.fact_orders {where_rating} GROUP BY device ORDER BY ordenes DESC")
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df["device"], y=df["ordenes"], name="Órdenes", marker_color=PALETTE["primary_light"], yaxis="y"))
        fig.add_trace(go.Scatter(x=df["device"], y=df["avg_rating"], name="Rating", mode="lines+markers", line=dict(color=PALETTE["accent"],width=2), marker=dict(size=8), yaxis="y2"))
        fig.update_layout(title="Comportamiento por Dispositivo", plot_bgcolor="white", paper_bgcolor="white", height=280, font=dict(family=FONT), margin=dict(t=50,b=40,l=10,r=60),
                         yaxis=dict(title="Órdenes",gridcolor="#EEF2F7"), yaxis2=dict(title="Rating",overlaying="y",side="right",showgrid=False), legend=dict(orientation="h",y=1.1))
        st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════
# TAB: VENDEDORES
# ═══════════════════════════════════════════════════════
elif selected_tab == "Vendedores":
    st.markdown('<div class="section-title">Análisis de Vendedores — RF6</div>', unsafe_allow_html=True)

    total_vend   = query(f"SELECT COUNT(DISTINCT seller_id) AS v FROM analytics.fact_orders {where}")["v"].iloc[0]
    avg_s_rating = query(f"SELECT ROUND(AVG(seller_rating)::numeric,2) AS v FROM analytics.fact_orders {where}")["v"].iloc[0]
    avg_ret      = query(f"SELECT ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)::numeric*100,1) AS v FROM analytics.fact_orders {where}")["v"].iloc[0]

    ICON_STORE = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>'
    ICON_STAR2 = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>'
    ICON_RET2  = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#6B7A8D" stroke-width="1.5"><path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/></svg>'

    c1,c2,c3 = st.columns(3)
    c1.markdown(kpi_card("Vendedores Activos",       f"{total_vend:,}",    None, ICON_STORE), unsafe_allow_html=True)
    c2.markdown(kpi_card("Rating Prom. Vendedores",  str(avg_s_rating),    None, ICON_STAR2), unsafe_allow_html=True)
    c3.markdown(kpi_card("Tasa Dev. Global",          f"{avg_ret}%",        None, ICON_RET2),  unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    df_rank = query(f"""
        SELECT seller_id, COUNT(*) AS ordenes, ROUND(SUM(final_price)::numeric,0) AS ingresos,
               ROUND(AVG(seller_rating)::numeric,2) AS rating_vendedor,
               ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)*100,1) AS tasa_dev
        FROM analytics.fact_orders {where} GROUP BY seller_id ORDER BY ingresos DESC LIMIT 50
    """)
    def color_ret(val):
        if val > 15: return "color:#C0392B;font-weight:600"
        if val < 5:  return "color:#1A7F4B;font-weight:600"
        return ""
    styled = df_rank.style.applymap(color_ret, subset=["tasa_dev"]).format({"ingresos":"₹{:,.0f}","tasa_dev":"{:.1f}%"})
    st.dataframe(styled, use_container_width=True, height=350)

    c1,c2 = st.columns(2)
    with c1:
        df = query(f"SELECT seller_id, COUNT(*) AS ordenes, ROUND(SUM(final_price)::numeric,0) AS ingresos, ROUND(AVG(seller_rating)::numeric,2) AS rating_vendedor, ROUND(AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END)*100,1) AS tasa_dev FROM analytics.fact_orders {where} GROUP BY seller_id HAVING COUNT(*)>=10 ORDER BY ingresos DESC")
        fig = px.scatter(df, x="rating_vendedor", y="tasa_dev", size="ordenes", color="ingresos",
                        color_continuous_scale=[[0,PALETTE["lighter"]],[1,PALETTE["primary"]]],
                        title="Rating vs Devolución por Vendedor",
                        labels={"rating_vendedor":"Rating","tasa_dev":"Dev (%)","ordenes":"Órdenes"},
                        hover_data={"seller_id":True,"ingresos":":,.0f"})
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=360, font=dict(family=FONT), margin=dict(t=50,b=40,l=10,r=10))
        fig.update_yaxes(gridcolor="#EEF2F7"); fig.update_xaxes(gridcolor="#EEF2F7")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        df = query("SELECT seller_id, category, total_orders, total_revenue FROM analytics.mart_categories_by_seller ORDER BY total_revenue DESC LIMIT 50")
        fig = px.bar(df, x="total_revenue", y="seller_id", color="category",
                    color_discrete_sequence=PLOTLY_COLORS, title="Categorías por Vendedor (Top 50)",
                    labels={"total_revenue":"Ingresos","seller_id":"Vendedor","category":"Categoría"})
        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=360, font=dict(family=FONT), margin=dict(t=50,b=20,l=10,r=10), legend=dict(orientation="h",y=1.1))
        st.plotly_chart(fig, use_container_width=True)

# ═══════════════════════════════════════════════════════
# TAB: GLOSARIO
# ═══════════════════════════════════════════════════════
elif selected_tab == "Glosario":
    st.markdown('<div class="section-title">Glosario de KPIs e Indicadores — RF9</div>', unsafe_allow_html=True)

    kpis_list = [
        ("Ingresos Totales",         "SUM(final_price)",                                                    "Suma de todos los precios finales del período. En INR (Rupias indias)."),
        ("Total Órdenes / Unidades", "COUNT(*)",                                                            "Cantidad total de órdenes. Cada fila = 1 orden = 1 unidad vendida."),
        ("Ticket Promedio",          "AVG(final_price)",                                                    "Ingreso promedio por orden en INR."),
        ("Tasa de Devolución",       "SUM(is_returned) / COUNT(*) × 100",                                  "% de órdenes devueltas. >15% indica problemas logísticos o de calidad."),
        ("Rating Promedio",          "AVG(rating)",                                                         "Calificación promedio de productos, escala 1 a 5."),
        ("% Entregas a Tiempo",      "delivery_status = 'Delivered' / COUNT(*) × 100",                     "% de pedidos entregados sin demoras."),
        ("% Pedidos Demorados",      "delivery_status = 'Delayed' / COUNT(*) × 100",                       "% de pedidos con demoras en la entrega."),
        ("Tiempo Prom. de Envío",    "AVG(shipping_time_days)",                                             "Días promedio desde la compra hasta la entrega."),
        ("Rating Prom. Vendedores",  "AVG(seller_rating)",                                                  "Calificación promedio de vendedores, escala 1 a 5."),
        ("Variación % Período",      "(valor_actual - valor_anterior) / valor_anterior × 100",              "Cambio % respecto al mes anterior. Verde = crecimiento, rojo = caída."),
        ("Unidades Vendidas",        "COUNT(*)",                                                            "Cada fila representa 1 orden de 1 unidad. No existe columna de cantidad."),
    ]

    for nombre, formula, interpretacion in kpis_list:
        with st.expander(f"**{nombre}**", expanded=False):
            c1,c2 = st.columns([1,2])
            with c1:
                st.markdown(f"""
                <div style="background:#F0F4F8;border-radius:6px;padding:10px 14px;">
                    <div style="font-size:0.68rem;font-weight:700;color:#6B7A8D;text-transform:uppercase;margin-bottom:4px;">Fórmula</div>
                    <code style="font-size:0.85rem;color:{PALETTE['primary']};">{formula}</code>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div style="background:white;border-radius:6px;padding:10px 14px;border-left:3px solid {PALETTE['primary_light']};">
                    <div style="font-size:0.68rem;font-weight:700;color:#6B7A8D;text-transform:uppercase;margin-bottom:4px;">Interpretación</div>
                    <div style="font-size:0.88rem;color:{PALETTE['text']};">{interpretacion}</div>
                </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:{PALETTE['primary']};border-radius:8px;padding:16px 20px;color:white;margin-top:20px;">
        <div style="font-weight:700;margin-bottom:6px;">📌 Nota sobre el dataset</div>
        <div style="font-size:0.85rem;color:{PALETTE['light']};">
            Dataset sintético de 1.000.000 órdenes del mercado indio. Precios en INR (Rupias indias).
            Cada fila = 1 orden = 1 unidad. No existe columna de cantidad por orden.
        </div>
    </div>""", unsafe_allow_html=True)