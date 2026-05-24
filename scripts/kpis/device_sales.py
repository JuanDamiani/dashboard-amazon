"""
KPI de ventas por dispositivo y categoria.

Cubre RF1, RF3 y RF5. Calcula ordenes e ingresos por device y category. Permite
analizar desde que canal compran los usuarios y como cambia el comportamiento
segun la categoria.
"""

from scripts.kpis.common import refresh_mart


def build_device_sales():
    refresh_mart(
        "mart_ventas_dispositivo",
        """
        INSERT INTO analytics.mart_ventas_dispositivo
        SELECT
            CURRENT_DATE AS metric_date,
            device,
            category,
            COUNT(*) AS total_orders,
            SUM(final_price) AS revenue
        FROM analytics.fact_orders
        GROUP BY device, category
        ORDER BY revenue DESC
        """,
    )
