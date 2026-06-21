"""
KPI por metodo de pago.

Cubre RF1 y RF7. Calcula ordenes, ingresos y ticket promedio por metodo de pago.
Se usa en el resumen ejecutivo y en tablas exportables desde Streamlit respetando
los filtros aplicados.
"""

from scripts.kpis.common import refresh_mart


def build_payment_methods():
    refresh_mart(
        "mart_payment_methods",
        """
        INSERT INTO analytics.mart_payment_methods
        SELECT
            CURRENT_DATE AS metric_date,
            payment_method,
            COUNT(*) AS total_orders,
            SUM(final_price) AS total_revenue,
            AVG(final_price) AS avg_ticket
        FROM analytics.fact_orders
        GROUP BY payment_method
        ORDER BY total_revenue DESC
        """,
    )
