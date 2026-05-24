"""
KPI logistico por estado de entrega.

Cubre RF1 y RF4. Agrupa ordenes por delivery_status, tiempo promedio de envio y
tasa de devolucion. Alimenta visualizaciones de estado de entregas, demoras y
calidad logistica.
"""

from scripts.kpis.common import refresh_mart


def build_logistics():
    refresh_mart(
        "mart_logistics",
        """
        INSERT INTO analytics.mart_logistics
        SELECT
            CURRENT_DATE AS metric_date,
            delivery_status,
            COUNT(*) AS total_orders,
            AVG(shipping_time_days) AS avg_shipping_days,
            AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100 AS return_rate
        FROM analytics.fact_orders
        GROUP BY delivery_status
        """,
    )
