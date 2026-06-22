"""
Filtros globales + locales con session_state (RF2, RF8).

- Single source of truth: cada widget usa su propia key flt_*.
- Reset real via on_click.
- Locales (subcategoria, marca, estado_entrega, rating) solo aplican en las
  paginas que los declaran en extra_filters (RF2: filtros propios de cada seccion).
- Dimensiones (categoria, subcategoria, ciudad, dispositivo, metodo_pago, marca,
  estado_entrega) son MULTISELECT con CHECKBOXES dentro de un popover:
  vacio = todas, varias = IN (...). (SRS)
- Periodo: presets + opcion "Personalizado" con calendario (dia/mes/anio).

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
    "flt_vendedor":       "Todos",
    "flt_min_ordenes":    1,
}

ALL_LOCAL = ["subcategoria", "marca", "estado_entrega", "rating"]

# Alto del espacio sobre los botones "Más filtros" y "Limpiar", para alinearlos
# con los dropdowns. SUBÍ el número para BAJARLOS, bajalo para subirlos.
BTN_SPACER_PX = 37


@st.cache_data(ttl=600, show_spinner=False)
def load_filter_options():
    """Valores distintos para los filtros. Cacheado: no cambian salvo recarga
    de datos (TTL 10 min). Antes corria 8 SELECT DISTINCT en CADA interaccion."""
    dr     = query("SELECT MIN(purchase_date) AS mn, MAX(purchase_date) AS mx FROM analytics.fact_orders")
    cats   = query("SELECT DISTINCT category        FROM analytics.fact_orders ORDER BY category")["category"].tolist()
    locs   = query("SELECT DISTINCT location        FROM analytics.fact_orders ORDER BY location")["location"].tolist()
    devs   = query("SELECT DISTINCT device          FROM analytics.fact_orders ORDER BY device")["device"].tolist()
    pays   = query("SELECT DISTINCT payment_method  FROM analytics.fact_orders ORDER BY payment_method")["payment_method"].tolist()
    subs   = query("SELECT DISTINCT subcategory     FROM analytics.fact_orders ORDER BY subcategory")["subcategory"].tolist()
    brands = query("SELECT DISTINCT brand           FROM analytics.fact_orders ORDER BY brand")["brand"].tolist()
    stats  = query("SELECT DISTINCT delivery_status FROM analytics.fact_orders ORDER BY delivery_status")["delivery_status"].tolist()
    return dr, cats, locs, devs, pays, subs, brands, stats


@st.cache_data(ttl=600, show_spinner=False)
def load_seller_options():
    """Lista de vendedores para el filtro local de la pagina Vendedores (cacheado)."""
    s = query("SELECT DISTINCT seller_id FROM analytics.fact_orders WHERE seller_id IS NOT NULL ORDER BY seller_id")
    return s["seller_id"].tolist()


def init_filters():
    for k, v in DEFAULTS.items():
        st.session_state.setdefault(k, v)


def _clear_filters():
    for k in list(st.session_state.keys()):
        if k.startswith("flt_"):
            del st.session_state[k]


def _checkbox_multi(options, key, sel):
    """Renderiza checkboxes (sin popover) y devuelve la lista seleccionada."""
    new_sel = []
    for opt in options:
        ck_key = f"{key}__chk__{opt}"
        if ck_key not in st.session_state:
            st.session_state[ck_key] = opt in sel
        if st.checkbox(opt, key=ck_key):
            new_sel.append(opt)
    return new_sel


def multiselect_popover(options, key, placeholder="Todas"):
    """Selector multiple con CHECKBOXES dentro de un popover (en vez de chips).
    Mantiene la misma key flt_* con la lista de seleccionados, asi el resto del
    codigo (WHERE, params) no cambia. Altura fija -> no hay salto al filtrar."""
    st.session_state.setdefault(key, [])
    sel = [v for v in st.session_state[key] if v in options]  # limpia stale
    n = len(sel)
    resumen = placeholder if n == 0 else (sel[0] if n == 1 else f"{n} seleccionadas")
    with st.popover(resumen, use_container_width=True):
        new_sel = _checkbox_multi(options, key, sel)
    st.session_state[key] = new_sel
    return new_sel


def _local_multi(label, options, key):
    """Filtro multiple INLINE (para usar adentro del popover 'Mas filtros')."""
    st.session_state.setdefault(key, [])
    sel = [v for v in st.session_state[key] if v in options]
    st.caption(label)
    st.session_state[key] = _checkbox_multi(options, key, sel)


def _in(col, values, prefix, params):
    names = []
    for index, value in enumerate(values):
        name = f"{prefix}_{index}"
        params[name] = value
        names.append(f":{name}")
    return f"{col} IN ({', '.join(names)})"


def render_filters(extra_filters=None):
    init_filters()
    dr, cats, locs, devs, pays, subs, brands, stats = load_filter_options()
    if dr.empty or pd.isna(dr["mn"].iloc[0]) or pd.isna(dr["mx"].iloc[0]):
        st.info("Todavia no hay datos cargados. Subi un CSV desde la pestaña Carga y ejecuta el pipeline.")
        st.stop()

    min_date = pd.to_datetime(dr["mn"].iloc[0]).date()
    max_date = pd.to_datetime(dr["mx"].iloc[0]).date()

    extra = list(ALL_LOCAL) if extra_filters is None else list(extra_filters)
    local_active = set(extra)

    # ── Fila principal (globales) ───────────────────────────
    fc = st.columns([1.7, 1.6, 1.6, 1.6, 1.6, 1.1, 0.5])

    with fc[0]:
        periodo_sel = st.session_state["flt_periodo"]
        if periodo_sel == "Personalizado":
            rango = st.session_state.get("flt_fecha_rango")
            if isinstance(rango, (tuple, list)) and len(rango) == 2:
                cap = f"Período · {rango[0].strftime('%d/%m/%y')} – {rango[1].strftime('%d/%m/%y')}"
            else:
                cap = "Período · Personalizado"
            st.caption(cap)
            ps, pp = st.columns([4, 1])
            with ps:
                st.selectbox("Período", list(PERIODO_OPCIONES.keys()),
                             key="flt_periodo", label_visibility="collapsed")
            with pp:
                with st.popover("📅", use_container_width=True):
                    st.caption("Rango de fechas")
                    st.date_input(
                        "Rango", value=(min_date, max_date),
                        min_value=min_date, max_value=max_date,
                        key="flt_fecha_rango", label_visibility="collapsed",
                        format="DD/MM/YYYY",
                    )
        else:
            st.caption("Período")
            st.selectbox("Período", list(PERIODO_OPCIONES.keys()),
                         key="flt_periodo", label_visibility="collapsed")

    with fc[1]:
        st.caption("Categoría")
        multiselect_popover(cats, "flt_categoria", "Todas")

    with fc[2]:
        st.caption("Ciudad")
        multiselect_popover(locs, "flt_ciudad", "Todas")

    with fc[3]:
        st.caption("Dispositivo")
        multiselect_popover(devs, "flt_dispositivo", "Todos")

    with fc[4]:
        st.caption("Método de pago")
        multiselect_popover(pays, "flt_metodo_pago", "Todos")

    with fc[5]:
        st.markdown(f'<div style="height:{BTN_SPACER_PX}px"></div>', unsafe_allow_html=True)
        if extra:
            with st.popover("Más filtros", icon=":material/filter_alt:",
                            use_container_width=True):
                pcols = st.columns(len(extra))
                for pcol, filtro in zip(pcols, extra):
                    with pcol:
                        if filtro == "subcategoria":
                            _local_multi("Subcategoría", subs, "flt_subcategoria")
                        elif filtro == "marca":
                            _local_multi("Marca", brands, "flt_marca")
                        elif filtro == "estado_entrega":
                            _local_multi("Estado de entrega", stats, "flt_estado_entrega")
                        elif filtro == "rating":
                            st.caption("Rango de rating")
                            st.slider("Rating", 1.0, 5.0, step=0.5,
                                      key="flt_rating", label_visibility="collapsed")
                        elif filtro == "vendedor":
                            st.caption("Vendedor")
                            st.selectbox("Vendedor", ["Todos"] + load_seller_options(),
                                         key="flt_vendedor", label_visibility="collapsed")
                        elif filtro == "min_ordenes":
                            st.caption("Mín. órdenes / vendedor")
                            st.slider("Mín órdenes", 1, 100,
                                      key="flt_min_ordenes", label_visibility="collapsed")

    with fc[6]:
        st.markdown(f'<div style="height:{BTN_SPACER_PX}px"></div>', unsafe_allow_html=True)
        st.button("", icon=":material/filter_alt_off:", help="Limpiar todos los filtros", key="_btn_clear",
                  on_click=_clear_filters)

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
    if "vendedor"       in local_active: n_activos += st.session_state["flt_vendedor"] != "Todos"
    if "min_ordenes"    in local_active: n_activos += st.session_state["flt_min_ordenes"] != 1

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
    params = {
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
    }
    conds = ["purchase_date BETWEEN :fecha_inicio AND :fecha_fin"]

    # Globales (multiselect): siempre
    if st.session_state["flt_categoria"]:   conds.append(_in("category",       st.session_state["flt_categoria"],   "categoria", params))
    if st.session_state["flt_ciudad"]:      conds.append(_in("location",       st.session_state["flt_ciudad"],      "ciudad", params))
    if st.session_state["flt_dispositivo"]: conds.append(_in("device",         st.session_state["flt_dispositivo"], "dispositivo", params))
    if st.session_state["flt_metodo_pago"]: conds.append(_in("payment_method", st.session_state["flt_metodo_pago"], "metodo_pago", params))

    # Locales: solo si la pagina los declara
    if "subcategoria"   in local_active and st.session_state["flt_subcategoria"]:   conds.append(_in("subcategory",     st.session_state["flt_subcategoria"],   "subcategoria", params))
    if "marca"          in local_active and st.session_state["flt_marca"]:          conds.append(_in("brand",           st.session_state["flt_marca"],          "marca", params))
    if "estado_entrega" in local_active and st.session_state["flt_estado_entrega"]: conds.append(_in("delivery_status", st.session_state["flt_estado_entrega"], "estado_entrega", params))
    if "vendedor"       in local_active and st.session_state["flt_vendedor"] != "Todos":
        params["seller_id"] = st.session_state["flt_vendedor"]
        conds.append("seller_id = :seller_id")

    rating_min, rating_max = st.session_state["flt_rating"]
    params_rating = dict(params)
    if "rating" in local_active:
        params_rating["rating_min"] = rating_min
        params_rating["rating_max"] = rating_max
        conds_rating = conds + ["rating BETWEEN :rating_min AND :rating_max"]
    else:
        conds_rating = list(conds)

    return {
        "where":           "WHERE " + " AND ".join(conds),
        "where_rating":    "WHERE " + " AND ".join(conds_rating),
        "params":          params,
        "params_rating":   params_rating,
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
        "vendedor":        st.session_state["flt_vendedor"],
        "min_ordenes":     st.session_state["flt_min_ordenes"],
        "filtros_activos": n_activos,
    }