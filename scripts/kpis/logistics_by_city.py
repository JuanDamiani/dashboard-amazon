"""
KPI logistico por ciudad.

Cubre RF4. Calcula tiempo promedio de envio, tasa de devolucion y cantidad de
ordenes por location. Sirve para comparar desempeno logistico entre ciudades.
"""

from scripts.kpis.common import refresh_mart


def build_logistics_by_city():
    refresh_mart(
        "mart_logistica_ciudad",
        """
        INSERT INTO analytics.mart_logistica_ciudad
        SELECT
            CURRENT_DATE AS metric_date,
            location,
            AVG(shipping_time_days) AS avg_shipping_days,
            AVG(CASE WHEN is_returned THEN 1.0 ELSE 0.0 END) * 100 AS return_rate,
            COUNT(*) AS total_orders
        FROM analytics.fact_orders
        GROUP BY location
        ORDER BY avg_shipping_days DESC
        """,
    )
