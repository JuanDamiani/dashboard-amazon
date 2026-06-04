"""
Filtros globales con session_state — RF2.
Los filtros se mantienen al navegar entre páginas.
"""

import streamlit as st
from dateutil.relativedelta import relativedelta
from utils.db import query


PERIODO_OPCIONES = {
    "Últimos 6 meses": relativedelta(months=6),
    "Último mes":      relativedelta(months=1),
    "Últimos 3 meses": relativedelta(months=3),
    "Último año":      relativedelta(years=1),
    "Todo el período": None,
}


@st.cache_data(ttl=3600)
def load_filter_options():
    """Carga las opciones de filtros una sola vez."""
    dr     = query("SELECT MIN(purchase_date) AS mn, MAX(purchase_date) AS mx FROM analytics.fact_orders")
    cats   = query("SELECT DISTINCT category        FROM analytics.fact_orders ORDER BY category")["category"].tolist()
    locs   = query("SELECT DISTINCT location        FROM analytics.fact_orders ORDER BY location")["location"].tolist()
    devs   = query("SELECT DISTINCT device          FROM analytics.fact_orders ORDER BY device")["device"].tolist()
    pays   = query("SELECT DISTINCT payment_method  FROM analytics.fact_orders ORDER BY payment_method")["payment_method"].tolist()
    subs   = query("SELECT DISTINCT subcategory     FROM analytics.fact_orders ORDER BY subcategory")["subcategory"].tolist()
    brands = query("SELECT DISTINCT brand           FROM analytics.fact_orders ORDER BY brand")["brand"].tolist()
    stats  = query("SELECT DISTINCT delivery_status FROM analytics.fact_orders ORDER BY delivery_status")["delivery_status"].tolist()
    return dr, cats, locs, devs, pays, subs, brands, stats


def init_filters():
    """Inicializa los filtros en session_state si no existen."""
    defaults = {
        "f_periodo":        "Últimos 6 meses",
        "f_categoria":      "Todas",
        "f_ciudad":         "Todas",
        "f_dispositivo":    "Todos",
        "f_metodo_pago":    "Todos",
        "f_subcategoria":   "Todas",
        "f_marca":          "Todas",
        "f_estado_entrega": "Todos",
        "f_rating_min":     1.0,
        "f_rating_max":     5.0,
        "more_filters_open": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def render_filters(extra_filters=None):
    """
    Renderiza la barra de filtros globales.
    extra_filters: lista de filtros adicionales para mostrar en 'Más filtros'
    Opciones: 'subcategoria', 'marca', 'estado_entrega', 'rating'
    """
    init_filters()
    dr, cats, locs, devs, pays, subs, brands, stats = load_filter_options()
    min_date = dr["mn"].iloc[0]
    max_date = dr["mx"].iloc[0]

    # ── Fila principal de filtros ────────────────────────
    fc = st.columns([2, 1.5, 1.5, 1.5, 1.5, 1.1, 0.5])

    with fc[0]:
        st.caption("Período")
        st.session_state["f_periodo"] = st.selectbox(
            "Período", list(PERIODO_OPCIONES.keys()),
            index=list(PERIODO_OPCIONES.keys()).index(st.session_state["f_periodo"]),
            label_visibility="collapsed", key="_sel_periodo",
        )

    with fc[1]:
        st.caption("Categoría")
        st.session_state["f_categoria"] = st.selectbox(
            "Categoría", ["Todas"] + cats,
            index=(["Todas"] + cats).index(st.session_state["f_categoria"]) if st.session_state["f_categoria"] in ["Todas"] + cats else 0,
            label_visibility="collapsed", key="_sel_categoria",
        )

    with fc[2]:
        st.caption("Ciudad")
        st.session_state["f_ciudad"] = st.selectbox(
            "Ciudad", ["Todas"] + locs,
            index=(["Todas"] + locs).index(st.session_state["f_ciudad"]) if st.session_state["f_ciudad"] in ["Todas"] + locs else 0,
            label_visibility="collapsed", key="_sel_ciudad",
        )

    with fc[3]:
        st.caption("Dispositivo")
        st.session_state["f_dispositivo"] = st.selectbox(
            "Dispositivo", ["Todos"] + devs,
            index=(["Todos"] + devs).index(st.session_state["f_dispositivo"]) if st.session_state["f_dispositivo"] in ["Todos"] + devs else 0,
            label_visibility="collapsed", key="_sel_dispositivo",
        )

    with fc[4]:
        st.caption("Método de pago")
        st.session_state["f_metodo_pago"] = st.selectbox(
            "Método de pago", ["Todos"] + pays,
            index=(["Todos"] + pays).index(st.session_state["f_metodo_pago"]) if st.session_state["f_metodo_pago"] in ["Todos"] + pays else 0,
            label_visibility="collapsed", key="_sel_metodo",
        )

    with fc[5]:
        st.caption(" ")
        if st.button("🎛️ Más filtros", key="_btn_more", use_container_width=True):
            st.session_state["more_filters_open"] = not st.session_state["more_filters_open"]

    with fc[6]:
        st.caption(" ")
        if st.button("🗑️", help="Limpiar filtros", key="_btn_clear"):
            keys_to_clear = [k for k in st.session_state.keys() if k.startswith("f_") or k == "more_filters_open"]
            for k in keys_to_clear:
                del st.session_state[k]
            st.rerun()

    # ── Más filtros ──────────────────────────────────────
    if st.session_state.get("more_filters_open", False):
        extra = extra_filters or ["subcategoria", "marca", "estado_entrega", "rating"]
        mc = st.columns(len(extra))

        for i, filtro in enumerate(extra):
            with mc[i]:
                if filtro == "subcategoria":
                    st.caption("Subcategoría")
                    st.session_state["f_subcategoria"] = st.selectbox(
                        "Subcategoría", ["Todas"] + subs,
                        index=(["Todas"] + subs).index(st.session_state["f_subcategoria"]) if st.session_state["f_subcategoria"] in ["Todas"] + subs else 0,
                        label_visibility="collapsed", key="_sel_sub",
                    )
                elif filtro == "marca":
                    st.caption("Marca")
                    st.session_state["f_marca"] = st.selectbox(
                        "Marca", ["Todas"] + brands,
                        index=(["Todas"] + brands).index(st.session_state["f_marca"]) if st.session_state["f_marca"] in ["Todas"] + brands else 0,
                        label_visibility="collapsed", key="_sel_marca",
                    )
                elif filtro == "estado_entrega":
                    st.caption("Estado de entrega")
                    st.session_state["f_estado_entrega"] = st.selectbox(
                        "Estado", ["Todos"] + stats,
                        index=(["Todos"] + stats).index(st.session_state["f_estado_entrega"]) if st.session_state["f_estado_entrega"] in ["Todos"] + stats else 0,
                        label_visibility="collapsed", key="_sel_estado",
                    )
                elif filtro == "rating":
                    st.caption("Rango de rating")
                    vals = st.slider(
                        "Rating", 1.0, 5.0,
                        (st.session_state["f_rating_min"], st.session_state["f_rating_max"]),
                        0.5, label_visibility="collapsed", key="_sel_rating",
                    )
                    st.session_state["f_rating_min"] = vals[0]
                    st.session_state["f_rating_max"] = vals[1]

    # ── Indicador filtros activos ─────────────────────────
    n_activos = sum([
        st.session_state["f_categoria"]      != "Todas",
        st.session_state["f_ciudad"]         != "Todas",
        st.session_state["f_dispositivo"]    != "Todos",
        st.session_state["f_metodo_pago"]    != "Todos",
        st.session_state["f_subcategoria"]   != "Todas",
        st.session_state["f_marca"]          != "Todas",
        st.session_state["f_estado_entrega"] != "Todos",
        st.session_state["f_periodo"]        != "Últimos 6 meses",
    ])
    if n_activos > 0:
        st.markdown(
            f'<div style="font-size:0.72rem;color:#FF9900;padding:2px 0 6px 0;">'
            f'● {n_activos} filtro{"s" if n_activos>1 else ""} activo{"s" if n_activos>1 else ""}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Construir WHERE ───────────────────────────────────
    _delta = PERIODO_OPCIONES.get(st.session_state["f_periodo"])
    from utils.db import query as _q
    dr2 = _q("SELECT MAX(purchase_date) AS mx FROM analytics.fact_orders")
    max_d = dr2["mx"].iloc[0]
    min_d = dr["mn"].iloc[0]

    fecha_inicio = max_d - _delta if _delta else min_d
    fecha_fin    = max_d

    conds = [f"purchase_date BETWEEN '{fecha_inicio}' AND '{fecha_fin}'"]

    if st.session_state["f_categoria"]      != "Todas":  conds.append(f"category = '{st.session_state['f_categoria']}'")
    if st.session_state["f_ciudad"]         != "Todas":  conds.append(f"location = '{st.session_state['f_ciudad']}'")
    if st.session_state["f_dispositivo"]    != "Todos":  conds.append(f"device = '{st.session_state['f_dispositivo']}'")
    if st.session_state["f_metodo_pago"]    != "Todos":  conds.append(f"payment_method = '{st.session_state['f_metodo_pago']}'")
    if st.session_state["f_subcategoria"]   != "Todas":  conds.append(f"subcategory = '{st.session_state['f_subcategoria']}'")
    if st.session_state["f_marca"]          != "Todas":  conds.append(f"brand = '{st.session_state['f_marca']}'")
    if st.session_state["f_estado_entrega"] != "Todos":  conds.append(f"delivery_status = '{st.session_state['f_estado_entrega']}'")

    conds_rating = conds + [f"rating BETWEEN {st.session_state['f_rating_min']} AND {st.session_state['f_rating_max']}"]

    return {
        "where":           "WHERE " + " AND ".join(conds),
        "where_rating":    "WHERE " + " AND ".join(conds_rating),
        "fecha_inicio":    fecha_inicio,
        "fecha_fin":       fecha_fin,
        "periodo":         st.session_state["f_periodo"],
        "categoria":       st.session_state["f_categoria"],
        "ciudad":          st.session_state["f_ciudad"],
        "dispositivo":     st.session_state["f_dispositivo"],
        "metodo_pago":     st.session_state["f_metodo_pago"],
        "subcategoria":    st.session_state["f_subcategoria"],
        "marca":           st.session_state["f_marca"],
        "estado_entrega":  st.session_state["f_estado_entrega"],
        "rating_min":      st.session_state["f_rating_min"],
        "rating_max":      st.session_state["f_rating_max"],
        "filtros_activos": n_activos,
    }