"""
Tutorial y Glosario de KPIs — RF9
"""

import streamlit as st
from utils.style import PALETTE

# ── Título ────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-bottom: 24px;">
    <div style="font-size: 1.3rem; font-weight: 700; color: {PALETTE['primary']};">Tutorial y Glosario</div>
    <div style="font-size: 0.88rem; color: {PALETTE['text_light']};">Cómo usar el dashboard y la definición, fórmula e interpretación de cada indicador</div>
</div>
""", unsafe_allow_html=True)

# ── Tutorial: cómo usar el dashboard ─────────────────────
st.markdown(f"""
<div style="font-size: 1.0rem; font-weight: 700; color: {PALETTE['primary']}; margin-bottom: 10px;">
    Cómo usar el dashboard
</div>
""", unsafe_allow_html=True)

pasos = [
    ("Navegación",
     "Las pestañas de arriba están disponibles en todas las páginas. Cambiás de sección sin perder los filtros que aplicaste."),
    ("Filtros globales",
     "La fila de filtros (Período, Categoría, Ciudad, Dispositivo, Método de pago) se aplica a toda la página y se mantiene al navegar entre secciones."),
    ("Más filtros",
     "Cada sección suma filtros propios en el botón “Más filtros”: subcategoría y marca (Ventas), estado de entrega (Logística), rango de rating (Clientes), vendedor (Vendedores)."),
    ("Comparación temporal",
     "Los KPIs muestran la variación % contra el período anterior. El color indica si es bueno o malo según la métrica (verde = mejora, rojo = empeora)."),
    ("Exportar datos",
     "Cada gráfico tiene un ícono de descarga arriba a la derecha para bajar los datos de ese gráfico en CSV."),
    ("Ayuda en contexto",
     "El ícono (i) al lado del título de cada gráfico explica qué calcula y cómo leerlo."),
    ("Carga de datos",
     "En la sección Carga subís un archivo CSV, lo guardás en el servidor y ejecutás el pipeline con un clic. Seguís el estado en “Últimas ejecuciones” y, cuando termina, el dashboard se actualiza con los datos nuevos. Las tablas de Validaciones y Archivos procesados indican si la carga fue exitosa."),
]

filas = ""
for titulo, desc in pasos:
    filas += (
        f'<div style="display:flex;gap:14px;padding:9px 0;border-bottom:1px solid {PALETTE["border"]};">'
        f'<div style="flex:0 0 150px;font-weight:700;font-size:0.85rem;color:{PALETTE["primary_light"]};">{titulo}</div>'
        f'<div style="flex:1;font-size:0.85rem;color:{PALETTE["text"]};">{desc}</div>'
        f'</div>'
    )

st.markdown(
    f'<div style="border:1px solid {PALETTE["border"]};border-radius:8px;'
    f'padding:6px 20px 10px 20px;margin-bottom:26px;background:white;">{filas}</div>',
    unsafe_allow_html=True,
)

# ── Glosario de indicadores ──────────────────────────────
st.markdown(f"""
<div style="font-size: 1.0rem; font-weight: 700; color: {PALETTE['primary']}; margin-bottom: 10px;">
    Glosario de indicadores
</div>
""", unsafe_allow_html=True)

kpis = [
    ("Ingresos Totales",              "SUM(final_price)",                                       "Suma de todos los precios finales del período en INR. Cada fila = 1 orden = 1 unidad vendida."),
    ("Total Órdenes / Unidades",      "COUNT(*)",                                               "Cantidad total de órdenes procesadas. Equivale a unidades vendidas, ya que cada fila representa 1 producto."),
    ("Ticket / Precio Promedio",      "AVG(final_price)",                                       "Ingreso promedio por orden en INR (en Ventas figura como “Precio Promedio”). Indica el valor medio de cada transacción."),
    ("Precio Original vs Final",      "AVG(price)  vs  AVG(final_price)",                        "Precio de lista promedio (price) frente al efectivamente pagado (final_price). La brecha entre ambos es el descuento promedio."),
    ("Descuento Promedio",            "AVG(discount)",                                          "% de descuento promedio aplicado a las órdenes del período. Cuánto margen se resigna para vender."),
    ("Tasa de Devolución",            "SUM(is_returned) / COUNT(*) × 100",                      "% de órdenes devueltas. Valores altos (>15%) pueden indicar problemas de calidad, expectativas mal seteadas o logística."),
    ("% de Participación",            "COUNT(grupo) / COUNT(total) × 100",                      "Peso de cada categoría, rango o segmento sobre el total de órdenes. Sirve para ver dónde se concentra el volumen."),
    ("Rating Promedio de Productos",  "AVG(rating)",                                            "Calificación promedio de productos, escala 1 a 5. Refleja la satisfacción del cliente."),
    ("% Entregas a Tiempo",           "(delivery_status = 'Delivered') / COUNT(*) × 100",       "% de pedidos entregados (estado Delivered) sobre el total. Mide la efectividad de entrega."),
    ("% Pedidos Demorados",           "(delivery_status = 'Delayed') / COUNT(*) × 100",         "% de pedidos demorados. Valores altos indican problemas logísticos o de capacidad."),
    ("Tiempo Promedio de Envío",      "AVG(shipping_time_days)",                                "Días promedio desde la compra hasta la entrega. Cuanto menor, mejor experiencia."),
    ("Vendedores Activos",            "COUNT(DISTINCT seller_id)",                              "Cantidad de vendedores con al menos una orden en el período."),
    ("Ingreso Promedio por Vendedor", "AVG( SUM(final_price) por seller_id )",                  "Ingreso promedio que genera cada vendedor en el período. Mide el tamaño típico de un vendedor."),
    ("Rating Promedio de Vendedores", "AVG(seller_rating)",                                     "Calificación promedio de vendedores, escala 1 a 5. Refleja la percepción del servicio del vendedor."),
    ("Mix de Categorías (Vendedor)",  "ingresos_categoria / ingresos_vendedor × 100",          "% de los ingresos de un vendedor que viene de cada categoría. Muestra si está especializado o diversificado."),
    ("Variación % vs Período Ant.",   "(valor_actual − valor_anterior) / valor_anterior × 100", "Cambio % respecto al período anterior de igual duración. El color depende de la métrica: verde = mejora, rojo = empeora."),
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