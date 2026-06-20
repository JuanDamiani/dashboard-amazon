"""
Filtros globales + locales con session_state (RF2, RF8).

- Single source of truth: cada widget usa su propia key flt_*.
- Reset real via on_click.
- Locales (subcategoria, marca, estado_entrega, rating) solo aplican en las
  paginas que los declaran en extra_filters (RF2: filtros propios de cada seccion).
- Dimensiones (categoria, subcategoria, ciudad, dispositivo, metodo_pago, marca,
  estado_entrega) son MULTISELECT: vacio = todas, varias = IN (...). (SRS)
- Periodo: presets + opcion "Personalizado" con calendario (dia/mes/anio).
  El desplegable decide cual manda, asi nunca chocan preset y calendario.

  extra_filters=[]   -> sin filtros locales (y sin boton "Mas filtros").
  extra_filters=None -> todos los locales.
"""

import streamlit as st
import pandas as pd
from dateutil.relativedelta import relativedelta
from utils.db import query


PERIODO_OPCIONES = {
    "Últimos 6 meses": relativedelta(months=6),
    "Último mes":      relativedelta(months=1),
    "Últimos 3 meses": relativedelta(months=3),
    "Último año":      relativedelta(years=1),
    "Todo el período": None,
    "Personalizado":   None,   # se maneja por nombre, usa el calendario
}

# Dimensiones multiselect: vacio = todas
DEFAULTS = {
    "flt_periodo":        "Últimos 6 meses",
    "flt_categoria":      [],
    "flt_ciudad":         [],
    "flt_dispositivo":    [],
    "flt_metodo_pago":    [],
    "flt_subcategoria":   [],
    "flt_marca":          [],
    "flt_estado_entrega": [],
    "flt_rating":         (1.0, 5.0),
    "more_filters_open":  False,
}

ALL_LOCAL = ["subcategoria", "marca", "estado_entrega", "rating"]


@st.cache_data(ttl=3600)
def load_filter_options():
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
    for k, v in DEFAULTS.items():
        st.session_state.setdefault(k, v)


def _clear_filters():
    for k in list(st.session_state.keys()):
        if k.startswith("flt_"):
            del st.session_state[k]
    st.session_state["more_filters_open"] = False


def _toggle_more():
    st.session_state["more_filters_open"] = not st.session_state.get("more_filters_open", False)


def _clean_multi(key, options):
    """Quita de la seleccion valores que ya no existen (evita que el multiselect falle)."""
    cur = st.session_state.get(key, [])
    valid = [v for v in cur if v in options]
    if valid != cur:
        st.session_state[key] = valid


def _esc(v):
    return str(v).replace("'", "''")


def _in(col, values):
    inner = ", ".join(f"'{_esc(v)}'" for v in values)
    return f"{col} IN ({inner})"


def render_filters(extra_filters=None):
    init_filters()
    dr, cats, locs, devs, pays, subs, brands, stats = load_filter_options()
    min_date = pd.to_datetime(dr["mn"].iloc[0]).date()
    max_date = pd.to_datetime(dr["mx"].iloc[0]).date()

    extra = list(ALL_LOCAL) if extra_filters is None else list(extra_filters)
    local_active = set(extra)

    # ── Fila principal (globales) ───────────────────────────
    fc = st.columns([1.7, 1.6, 1.6, 1.6, 1.6, 1.1, 0.5])

    with fc[0]:
        st.caption("Período")
        st.selectbox("Período", list(PERIODO_OPCIONES.keys()),
                     key="flt_periodo", label_visibility="collapsed")

    with fc[1]:
        st.caption("Categoría")
        _clean_multi("flt_categoria", cats)
        st.multiselect("Categoría", cats, key="flt_categoria",
                       placeholder="Todas", label_visibility="collapsed")

    with fc[2]:
        st.caption("Ciudad")
        _clean_multi("flt_ciudad", locs)
        st.multiselect("Ciudad", locs, key="flt_ciudad",
                       placeholder="Todas", label_visibility="collapsed")

    with fc[3]:
        st.caption("Dispositivo")
        _clean_multi("flt_dispositivo", devs)
        st.multiselect("Dispositivo", devs, key="flt_dispositivo",
                       placeholder="Todos", label_visibility="collapsed")

    with fc[4]:
        st.caption("Método de pago")
        _clean_multi("flt_metodo_pago", pays)
        st.multiselect("Método de pago", pays, key="flt_metodo_pago",
                       placeholder="Todos", label_visibility="collapsed")

    with fc[5]:
        st.caption(" ")
        if extra:
            st.button("🎛️ Más filtros", key="_btn_more",
                      on_click=_toggle_more, use_container_width=True)

    with fc[6]:
        st.caption(" ")
        st.button("🗑️", help="Limpiar filtros", key="_btn_clear",
                  on_click=_clear_filters)

    # ── Calendario (solo si Período = Personalizado) ────────
    if st.session_state["flt_periodo"] == "Personalizado":
        dc = st.columns([2.3, 4.7])
        with dc[0]:
            st.caption("Rango de fechas")
            st.date_input(
                "Rango", value=(min_date, max_date),
                min_value=min_date, max_value=max_date,
                key="flt_fecha_rango", label_visibility="collapsed",
                format="DD/MM/YYYY",
            )

    # ── Fila de filtros locales ─────────────────────────────
    if extra and st.session_state.get("more_filters_open", False):
        mc = st.columns(len(extra))
        for i, filtro in enumerate(extra):
            with mc[i]:
                if filtro == "subcategoria":
                    st.caption("Subcategoría")
                    _clean_multi("flt_subcategoria", subs)
                    st.multiselect("Subcategoría", subs, key="flt_subcategoria",
                                   placeholder="Todas", label_visibility="collapsed")
                elif filtro == "marca":
                    st.caption("Marca")
                    _clean_multi("flt_marca", brands)
                    st.multiselect("Marca", brands, key="flt_marca",
                                   placeholder="Todas", label_visibility="collapsed")
                elif filtro == "estado_entrega":
                    st.caption("Estado de entrega")
                    _clean_multi("flt_estado_entrega", stats)
                    st.multiselect("Estado", stats, key="flt_estado_entrega",
                                   placeholder="Todos", label_visibility="collapsed")
                elif filtro == "rating":
                    st.caption("Rango de rating")
                    st.slider("Rating", 1.0, 5.0, step=0.5,
                              key="flt_rating", label_visibility="collapsed")

    # ── Indicador de filtros activos (alto fijo, sin salto) ─
    n_activos = sum([
        bool(st.session_state["flt_categoria"]),
        bool(st.session_state["flt_ciudad"]),
        bool(st.session_state["flt_dispositivo"]),
        bool(st.session_state["flt_metodo_pago"]),
        st.session_state["flt_periodo"] != "Últimos 6 meses",
    ])
    if "subcategoria"   in local_active: n_activos += bool(st.session_state["flt_subcategoria"])
    if "marca"          in local_active: n_activos += bool(st.session_state["flt_marca"])
    if "estado_entrega" in local_active: n_activos += bool(st.session_state["flt_estado_entrega"])
    if "rating"         in local_active: n_activos += tuple(st.session_state["flt_rating"]) != (1.0, 5.0)

    texto = (
        f'● {n_activos} filtro{"s" if n_activos > 1 else ""} '
        f'activo{"s" if n_activos > 1 else ""}'
        if n_activos > 0 else ""
    )
    st.markdown(
        f'<div style="font-size:0.72rem;color:#FF9900;height:1.1rem;'
        f'line-height:1.1rem;padding:2px 0 6px 0;">{texto}</div>',
        unsafe_allow_html=True,
    )

    # ── Rango de fechas efectivo ────────────────────────────
    periodo = st.session_state["flt_periodo"]
    if periodo == "Personalizado":
        rango = st.session_state.get("flt_fecha_rango")
        if isinstance(rango, (tuple, list)) and len(rango) == 2:
            fecha_inicio, fecha_fin = rango[0], rango[1]
        else:
            fecha_inicio, fecha_fin = min_date, max_date
    else:
        delta = PERIODO_OPCIONES.get(periodo)
        fecha_inicio = (max_date - delta) if delta else min_date
        fecha_fin    = max_date

    # ── Construir WHERE ─────────────────────────────────────
    conds = [f"purchase_date BETWEEN '{fecha_inicio}' AND '{fecha_fin}'"]

    # Globales (multiselect): siempre
    if st.session_state["flt_categoria"]:   conds.append(_in("category",       st.session_state["flt_categoria"]))
    if st.session_state["flt_ciudad"]:      conds.append(_in("location",       st.session_state["flt_ciudad"]))
    if st.session_state["flt_dispositivo"]: conds.append(_in("device",         st.session_state["flt_dispositivo"]))
    if st.session_state["flt_metodo_pago"]: conds.append(_in("payment_method", st.session_state["flt_metodo_pago"]))

    # Locales: solo si la pagina los declara
    if "subcategoria"   in local_active and st.session_state["flt_subcategoria"]:   conds.append(_in("subcategory",     st.session_state["flt_subcategoria"]))
    if "marca"          in local_active and st.session_state["flt_marca"]:          conds.append(_in("brand",           st.session_state["flt_marca"]))
    if "estado_entrega" in local_active and st.session_state["flt_estado_entrega"]: conds.append(_in("delivery_status", st.session_state["flt_estado_entrega"]))

    rating_min, rating_max = st.session_state["flt_rating"]
    if "rating" in local_active:
        conds_rating = conds + [f"rating BETWEEN {rating_min} AND {rating_max}"]
    else:
        conds_rating = list(conds)

    return {
        "where":           "WHERE " + " AND ".join(conds),
        "where_rating":    "WHERE " + " AND ".join(conds_rating),
        "fecha_inicio":    fecha_inicio,
        "fecha_fin":       fecha_fin,
        "periodo":         periodo,
        "categoria":       st.session_state["flt_categoria"],
        "ciudad":          st.session_state["flt_ciudad"],
        "dispositivo":     st.session_state["flt_dispositivo"],
        "metodo_pago":     st.session_state["flt_metodo_pago"],
        "subcategoria":    st.session_state["flt_subcategoria"],
        "marca":           st.session_state["flt_marca"],
        "estado_entrega":  st.session_state["flt_estado_entrega"],
        "rating_min":      rating_min,
        "rating_max":      rating_max,
        "filtros_activos": n_activos,
    }