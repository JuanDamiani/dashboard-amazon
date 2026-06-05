"""
Glosario de KPIs — RF9
"""

import streamlit as st
from utils.filters import render_filters
from utils.style import get_css, PALETTE, FONT

st.markdown(get_css(), unsafe_allow_html=True)

st.markdown("""
<style>
[data-testid="stSidebar"] { display: none !important; }
[data-testid="collapsedControl"] { display: none !important; }
.block-container { padding-top: 0 !important; max-width: 100% !important; }
</style>
""", unsafe_allow_html=True)

# ── HEADER ───────────────────────────────────────────────
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
        "nav", tab_names, horizontal=True,
        label_visibility="collapsed", index=5, key="main_nav",
    )
    if selected_tab == "Overview":
        st.switch_page("pages/01_overview.py")
    elif selected_tab == "Ventas":
        st.switch_page("pages/02_ventas.py")
    elif selected_tab == "Logística":
        st.switch_page("pages/03_logistica.py")
    elif selected_tab == "Clientes":
        st.switch_page("pages/04_clientes.py")
    elif selected_tab == "Vendedores":
        st.switch_page("pages/05_vendedores.py")

st.markdown('<hr style="margin: 0 0 8px 0; border-color: #E4E9F0;">', unsafe_allow_html=True)
st.markdown('<hr style="margin: 4px 0 20px 0; border-color: #E4E9F0;">', unsafe_allow_html=True)

# ── Título ────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-bottom: 24px;">
    <div style="font-size: 1.3rem; font-weight: 700; color: {PALETTE['primary']};">Glosario de KPIs</div>
    <div style="font-size: 0.88rem; color: {PALETTE['text_light']};">Definiciones, fórmulas e interpretación de cada indicador del dashboard</div>
</div>
""", unsafe_allow_html=True)

# ── KPIs ─────────────────────────────────────────────────
kpis = [
    ("Ingresos Totales",              "SUM(final_price)",                                    "Suma de todos los precios finales del período en INR. Cada fila = 1 orden = 1 unidad vendida."),
    ("Total Órdenes / Unidades",      "COUNT(*)",                                            "Cantidad total de órdenes procesadas. Equivale a unidades vendidas ya que cada fila representa 1 producto."),
    ("Ticket Promedio",               "AVG(final_price)",                                    "Ingreso promedio por orden en INR. Indica el valor medio de cada transacción."),
    ("Tasa de Devolución",            "SUM(is_returned) / COUNT(*) × 100",                   "% de órdenes devueltas. Valores >15% pueden indicar problemas de calidad o logística."),
    ("Rating Promedio de Productos",  "AVG(rating)",                                         "Calificación promedio de productos, escala 1 a 5. Refleja la satisfacción del cliente."),
    ("% Entregas a Tiempo",           "delivery_status = 'Delivered' / COUNT(*) × 100",      "% de pedidos entregados exitosamente sin demoras."),
    ("% Pedidos Demorados",           "delivery_status = 'Delayed' / COUNT(*) × 100",        "% de pedidos con demoras. Valores altos indican problemas logísticos o de capacidad."),
    ("Tiempo Promedio de Envío",      "AVG(shipping_time_days)",                             "Días promedio desde la compra hasta la entrega."),
    ("Rating Promedio de Vendedores", "AVG(seller_rating)",                                  "Calificación promedio de vendedores, escala 1 a 5. Refleja la percepción del servicio."),
    ("Variación % vs Período Ant.",   "(valor_actual - valor_anterior) / valor_anterior × 100", "Cambio % respecto al mes anterior. Verde = crecimiento, rojo = caída."),
    ("Descuento Promedio",            "AVG(discount)",                                       "% de descuento promedio aplicado a las órdenes del período seleccionado."),
]

for nombre, formula, interpretacion in kpis:
    st.markdown(f"""
    <div style="border: 1px solid {PALETTE['border']}; border-radius: 8px; padding: 16px 20px;
                margin-bottom: 10px; background: white;">
        <div style="font-size: 0.88rem; font-weight: 700; color: {PALETTE['primary']};
                    margin-bottom: 12px;">{nombre}</div>
        <div style="display: flex; gap: 16px; flex-wrap: wrap;">
            <div style="flex: 1; min-width: 200px; background: {PALETTE['bg']};
                        border-radius: 6px; padding: 10px 14px;">
                <div style="font-size: 0.68rem; font-weight: 700; color: {PALETTE['text_light']};
                            text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">
                    Fórmula
                </div>
                <code style="font-size: 0.82rem; color: {PALETTE['primary']};">{formula}</code>
            </div>
            <div style="flex: 2; min-width: 280px; background: white; border-radius: 6px;
                        padding: 10px 14px; border-left: 3px solid {PALETTE['primary_light']};">
                <div style="font-size: 0.68rem; font-weight: 700; color: {PALETTE['text_light']};
                            text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px;">
                    Interpretación
                </div>
                <div style="font-size: 0.85rem; color: {PALETTE['text']};">{interpretacion}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"""
<div style="background: {PALETTE['primary']}; border-radius: 8px; padding: 16px 20px; color: white;">
    <div style="font-weight: 700; margin-bottom: 6px;">Nota sobre el dataset</div>
    <div style="font-size: 0.85rem; color: {PALETTE['light']};">
        Dataset sintético de 1.000.000 de órdenes del mercado indio. Precios en INR (Rupias indias).
        Cada fila = 1 orden = 1 unidad. No existe columna de cantidad por orden.
    </div>
</div>
""", unsafe_allow_html=True)