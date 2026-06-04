"""
Glosario de KPIs — RF9
"""

import streamlit as st
from utils.style import get_css, PALETTE

st.set_page_config(page_title="Glosario | Amazon Analytics", layout="wide")
st.markdown(get_css(), unsafe_allow_html=True)

st.markdown("""
<div class="dashboard-header">
    <div class="dashboard-title">📖 Glosario de KPIs</div>
    <div class="dashboard-subtitle">Definiciones, fórmulas e interpretación de cada indicador del dashboard</div>
</div>
""", unsafe_allow_html=True)

kpis = [
    ("💰", "Ingresos Totales", "SUM(final_price)", "Suma de todos los precios finales del período. Expresado en INR (Rupias indias). Cada fila del dataset representa 1 orden = 1 unidad vendida."),
    ("📦", "Total Órdenes / Unidades Vendidas", "COUNT(*)", "Cantidad total de órdenes procesadas. Equivale a unidades vendidas ya que cada fila representa una orden de 1 producto."),
    ("🎫", "Ticket Promedio", "AVG(final_price)", "Ingreso promedio por orden. Indica el valor medio de cada transacción en INR."),
    ("↩️", "Tasa de Devolución", "SUM(is_returned) / COUNT(*) × 100", "Porcentaje de órdenes devueltas. Valores altos (>15%) pueden indicar problemas de calidad, logística o expectativas del cliente."),
    ("⭐", "Rating Promedio de Productos", "AVG(rating)", "Calificación promedio de los productos en escala 1 a 5. Refleja la satisfacción del cliente con el producto recibido."),
    ("✅", "% Entregas a Tiempo", "delivery_status = 'Delivered' / COUNT(*) × 100", "Porcentaje de pedidos entregados exitosamente sin demoras."),
    ("⚠️", "% Pedidos Demorados", "delivery_status = 'Delayed' / COUNT(*) × 100", "Porcentaje de pedidos que sufrieron demoras. Valores altos pueden indicar problemas logísticos o de capacidad."),
    ("⏱️", "Tiempo Promedio de Envío", "AVG(shipping_time_days)", "Promedio de días transcurridos desde la compra hasta la entrega."),
    ("🏪", "Rating Promedio de Vendedores", "AVG(seller_rating)", "Calificación promedio de los vendedores en escala 1 a 5. Refleja la percepción del servicio del vendedor."),
    ("📈", "Variación % vs Período Anterior", "(valor_actual - valor_anterior) / valor_anterior × 100", "Cambio porcentual respecto al mes anterior. Verde indica crecimiento, rojo indica caída."),
    ("🏷️", "Descuento Promedio", "AVG(discount)", "Porcentaje de descuento promedio aplicado a las órdenes del período seleccionado."),
]

for icon, nombre, formula, interpretacion in kpis:
    with st.expander(f"{icon} **{nombre}**", expanded=False):
        col1, col2 = st.columns([1, 2])
        with col1:
            st.markdown(f"""
            <div style="background: {PALETTE['lighter']}; border-radius: 8px; padding: 12px 16px; margin-bottom: 8px;">
                <div style="font-size: 0.75rem; font-weight: 600; color: {PALETTE['text_light']}; text-transform: uppercase; margin-bottom: 4px;">Fórmula</div>
                <code style="font-size: 0.88rem; color: {PALETTE['primary']};">{formula}</code>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div style="background: white; border-radius: 8px; padding: 12px 16px; border-left: 3px solid {PALETTE['secondary']};">
                <div style="font-size: 0.75rem; font-weight: 600; color: {PALETTE['text_light']}; text-transform: uppercase; margin-bottom: 4px;">Interpretación</div>
                <div style="font-size: 0.9rem; color: {PALETTE['text']};">{interpretacion}</div>
            </div>
            """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown(f"""
<div style="background: {PALETTE['primary']}; border-radius: 12px; padding: 20px 24px; color: white;">
    <div style="font-weight: 700; margin-bottom: 8px;">📌 Nota sobre el dataset</div>
    <div style="font-size: 0.88rem; color: #A9CCE3;">
        Los datos provienen de un dataset sintético de e-commerce con 1.000.000 de órdenes del mercado indio.
        Los precios están expresados en INR (Rupias indias). Cada fila representa exactamente 1 orden de 1 unidad de producto.
        El sistema no cuenta con columna de cantidad por orden — se asume 1 unidad por transacción.
    </div>
</div>
""", unsafe_allow_html=True)